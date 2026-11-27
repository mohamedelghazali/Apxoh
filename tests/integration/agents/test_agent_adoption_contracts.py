"""Repository-level contracts for AI-agent adoption metadata.

These tests validate repository structure and truthful status declarations only.
They do not claim external agents loaded or obeyed GENCODE-GOV instructions.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from arkhon.core.constants import ALL_RULE_DOMAINS

ROOT = Path(__file__).resolve().parents[3]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_model_registry_paths_resolve_to_packaged_adapters() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    models = registry["integrations"]["models"]
    assert len(models) == registry["totals"]["models"]
    for model in models:
        adapter_dir = ROOT / model["integration_path"]
        assert adapter_dir.is_dir(), model["id"]
        assert (adapter_dir / "adapter.py").is_file(), model["id"]
        assert (adapter_dir / "config.yaml").is_file(), model["id"]


def test_copilot_registry_separates_docs_from_runtime_adapter() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    copilot = registry["integrations"]["platforms"][0]
    assert copilot["id"] == "github-copilot"
    assert (ROOT / copilot["integration_path"]).is_dir()
    assert (ROOT / copilot["runtime_adapter"]).is_file()
    assert copilot["status"] == "scaffolded"


def test_generic_fallback_is_not_misreported_as_supported_behavior() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    generic = registry["integrations"]["generic"][0]
    assert generic["status"] == "manual"
    assert (ROOT / generic["integration_path"]).is_dir()


def test_generic_agent_scaffolds_require_consent_and_verification() -> None:
    root = ROOT / "integrations" / "generic-agents"
    adapters = sorted(path for path in root.iterdir() if path.is_dir() and path.name != "prompts")
    assert adapters
    for adapter in adapters:
        config_path = adapter / "config.yaml"
        assert config_path.is_file(), adapter.name
        config = _load_yaml(config_path)
        assert config["status"] == "scaffolded", adapter.name
        assert config["requires_user_consent"] is True, adapter.name
        assert config["verification_required"] is True, adapter.name


def test_application_security_rules_are_present_and_agent_pack_is_synchronized() -> None:
    sec_rules = ROOT / "rules" / "software-security"
    for rule_id in [f"SE-SEC-{number:03d}" for number in range(1, 11)]:
        assert len(list(sec_rules.glob(f"{rule_id}-*.yaml"))) == 1, rule_id

    consolidated_rules = [
        (ROOT / "rules" / "observability", "SE-OBS-003"),
        (ROOT / "rules" / "performance", "SE-PRF-002"),
        (ROOT / "rules" / "testing", "SE-TST-004"),
    ]
    for directory, rule_id in consolidated_rules:
        assert len(list(directory.glob(f"{rule_id}-*.yaml"))) == 1, rule_id

    canonical_skills = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
    packaged_root = ROOT / "src" / "arkhon" / "resources" / "agent_pack" / "skills"
    packaged_skills = sorted(p.name for p in packaged_root.iterdir() if p.is_dir())
    assert canonical_skills == packaged_skills
    for name in canonical_skills:
        source = ROOT / "skills" / name / "SKILL.md"
        packaged = packaged_root / name / "SKILL.md"
        assert source.is_file(), name
        assert packaged.is_file(), name
        assert source.read_text(encoding="utf-8") == packaged.read_text(encoding="utf-8"), name

    for doc_name in ("AGENTS.md", "SECURITY_AGENTS.md"):
        root_doc = (ROOT / doc_name).read_text(encoding="utf-8")
        pack_doc = (
            ROOT / "src" / "arkhon" / "resources" / "agent_pack" / doc_name
        ).read_text(encoding="utf-8")
        assert root_doc == pack_doc, doc_name

    agent_instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for required_id in ("SE-SEC-001", "SE-SEC-010", "SE-OBS-003", "SE-PRF-002", "SE-TST-004"):
        assert required_id in agent_instructions, required_id

    roles_data = _load_yaml(ROOT / "agents" / "_roles.yaml")
    covered_domains = {d for role in roles_data["roles"] for d in role["rule_domains"]}
    assert covered_domains == set(ALL_RULE_DOMAINS)
    roles_with_appsec = [
        role["id"] for role in roles_data["roles"] if "application-security" in role["skills"]
    ]
    assert {"security-engineer", "developer", "code-reviewer", "test-engineer"} <= set(
        roles_with_appsec
    )

    security_agent = (
        ROOT / "src" / "arkhon" / "resources" / "agent_pack"
        / "agents" / "security-engineer" / "AGENT.md"
    ).read_text(encoding="utf-8")
    for required_id in ("SE-SEC-001", "SE-OBS-003", "SE-PRF-002", "SE-TST-004"):
        assert required_id in security_agent, required_id
