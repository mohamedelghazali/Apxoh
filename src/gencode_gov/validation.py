"""First-class repository and wheel governance validator (rules, schemas, methods, roles, links)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

from gencode_gov.core.constants import ALL_RULE_DOMAINS
from gencode_gov.rules.loader import load_rules_dir
from gencode_gov.rules.validator import validate_against_schema, validate_semantics
from gencode_gov.verification.methods import METHOD_REGISTRY

_MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True)
class ValidationSummary:
    """Comprehensive governance validation result."""

    ok: bool
    rules_checked: int
    schemas_checked: int
    skills_checked: int
    errors: tuple[str, ...]


def _check_markdown_links(repo_root: Path, md_file: Path) -> list[str]:
    errors: list[str] = []
    txt = md_file.read_text(encoding="utf-8", errors="ignore")
    # Strip fenced code blocks to avoid matching markdown-like code examples
    stripped = re.sub(r"```.*?```", "", txt, flags=re.DOTALL)
    for match in _MD_LINK_RE.finditer(stripped):
        raw_target = match.group(1).strip().split()[0]
        if (
            not raw_target
            or raw_target.startswith(("#", "http:", "https:", "mailto:", "tel:"))
            or "{" in raw_target
        ):
            continue
        path_part = raw_target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (md_file.parent / path_part).resolve()
        try:
            resolved.relative_to(repo_root)
        except ValueError:
            errors.append(f"{md_file.relative_to(repo_root)}: link escapes root -> {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"{md_file.relative_to(repo_root)}: broken relative link -> {raw_target}")
    return errors


def validate_repository(repo_root: Path | None = None) -> ValidationSummary:
    """Validate rules, schemas, METHOD_REGISTRY coverage, roles, skills, and links."""
    root = (repo_root or Path.cwd()).resolve()
    pkg_resources = Path(__file__).resolve().parent / "resources"
    errors: list[str] = []

    # If invoked inside an installed wheel outside a repo checkout, validate bundled agent_pack
    if not (root / "rules").is_dir() and (pkg_resources / "agent_pack").is_dir():
        skills_checked = 0
        pack_root = pkg_resources / "agent_pack"
        for skill_md in sorted((pack_root / "skills").glob("*/SKILL.md")):
            skills_checked += 1
            errors.extend(_check_markdown_links(pack_root, skill_md))
        return ValidationSummary(
            ok=not errors,
            rules_checked=0,
            schemas_checked=0,
            skills_checked=skills_checked,
            errors=tuple(errors),
        )

    # 1. Validate JSON Schemas
    schemas_dir = root / "schemas"
    schemas_checked = 0
    rule_schema_path = schemas_dir / "rule.schema.json"
    if not schemas_dir.is_dir():
        errors.append("missing schemas/ directory")
    else:
        for sp in sorted(schemas_dir.glob("*.json")):
            schemas_checked += 1
            try:
                schema_obj = json.loads(sp.read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator.check_schema(schema_obj)
            except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
                errors.append(f"invalid schema {sp.name}: {exc}")

    # 2. Validate ALL rules in rules/ AND languages/*/rules/
    rule_dirs = [root / "rules"]
    lang_dir = root / "languages"
    if lang_dir.is_dir():
        rule_dirs.extend(sorted(p for p in lang_dir.glob("*/rules") if p.is_dir()))

    rules_checked = 0
    seen_ids: dict[str, Path] = {}
    for rdir in rule_dirs:
        if not rdir.is_dir():
            errors.append(f"missing rules directory: {rdir}")
            continue
        load_res = load_rules_dir(rdir)
        if not load_res.ok:
            errors.extend(str(e) for e in load_res.errors)
        loaded_rules = getattr(load_res, "rules", ())
        for rule in loaded_rules:
            rules_checked += 1
            rpath = getattr(rule, "path", rdir)
            if rule.id in seen_ids:
                errors.append(f"duplicate rule id {rule.id}: {seen_ids[rule.id]} vs {rpath}")
            else:
                seen_ids[rule.id] = rpath

            if rule_schema_path.is_file():
                for serr in validate_against_schema(rule, rule_schema_path):
                    errors.append(str(serr))
            for sem_err in validate_semantics(rule):
                errors.append(str(sem_err))

            # Enforce 100% METHOD_REGISTRY registration and domain authorization
            raw = getattr(rule, "raw", {})
            dom = str(raw.get("metadata", {}).get("domain", "")) if isinstance(raw, dict) else ""
            methods = (
                raw.get("verification", {}).get("methods", []) if isinstance(raw, dict) else []
            )
            if isinstance(methods, list):
                for m_id in methods:
                    impl = METHOD_REGISTRY.get(str(m_id))
                    if impl is None:
                        errors.append(f"{rule.id}: method {m_id!r} unregistered in METHOD_REGISTRY")
                    elif impl.allowed_domains and dom not in impl.allowed_domains:
                        errors.append(f"{rule.id}: method {m_id!r} does not allow domain {dom!r}")

    # 3. Validate agents/_roles.yaml & skills/*/SKILL.md
    skills_checked = 0
    skills_dir = root / "skills"
    known_skills: set[str] = set()
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            skills_checked += 1
            known_skills.add(skill_md.parent.name)
            txt = skill_md.read_text(encoding="utf-8", errors="ignore")
            if not txt.startswith("---"):
                errors.append(f"{skill_md.relative_to(root)}: missing YAML frontmatter")
            errors.extend(_check_markdown_links(root, skill_md))

    roles_file = root / "agents" / "_roles.yaml"
    if roles_file.is_file():
        try:
            roles_doc = yaml.safe_load(roles_file.read_text(encoding="utf-8"))
            roles_list = roles_doc.get("roles", []) if isinstance(roles_doc, dict) else []
            covered = {
                d
                for r in roles_list
                if isinstance(r, dict)
                for d in r.get("rule_domains", [])
                if isinstance(d, str)
            }
            missing_doms = sorted(set(ALL_RULE_DOMAINS) - covered)
            if missing_doms:
                errors.append(f"agents/_roles.yaml missing rule_domains coverage: {missing_doms}")
            for r in roles_list:
                if isinstance(r, dict):
                    for sname in r.get("skills", []):
                        if known_skills and sname not in known_skills:
                            errors.append(
                                f"role {r.get('id')!r} references unknown skill {sname!r}"
                            )
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"invalid agents/_roles.yaml: {exc}")

    # 4. Validate packaged agent_pack links & parity
    pack_dir = root / "src" / "gencode_gov" / "resources" / "agent_pack"
    if pack_dir.is_dir():
        for pack_skill_md in sorted((pack_dir / "skills").glob("*/SKILL.md")):
            errors.extend(_check_markdown_links(pack_dir, pack_skill_md))

    # 5. Validate top-level & docs Markdown relative links
    for top_md in ("README.md", "AGENTS.md", "SECURITY_AGENTS.md", "COMPATIBILITY.md"):
        fp = root / top_md
        if fp.is_file():
            errors.extend(_check_markdown_links(root, fp))
    for sub_dir in ("docs", "rules"):
        sd = root / sub_dir
        if sd.is_dir():
            for md_fp in sorted(sd.rglob("*.md")):
                if not md_fp.is_symlink():
                    errors.extend(_check_markdown_links(root, md_fp))

    return ValidationSummary(
        ok=not errors,
        rules_checked=rules_checked,
        schemas_checked=schemas_checked,
        skills_checked=skills_checked,
        errors=tuple(errors),
    )


def run_cli_validate(repo_root: Path | None = None, *, as_json: bool = False) -> int:
    """CLI entrypoint for gencode-gov validate."""
    summary = validate_repository(repo_root)
    if as_json:
        print(
            json.dumps(
                {
                    "ok": summary.ok,
                    "rules_checked": summary.rules_checked,
                    "schemas_checked": summary.schemas_checked,
                    "skills_checked": summary.skills_checked,
                    "errors": list(summary.errors),
                },
                indent=2,
            )
        )
        return 0 if summary.ok else 1

    if not summary.ok:
        for err in summary.errors:
            print(f"[FAIL] {err}")
        return 1
    print(
        f"[OK] Validated {summary.rules_checked} rules, {summary.schemas_checked} schemas, "
        f"and {summary.skills_checked} skills with 0 errors."
    )
    return 0
