"""Deterministic structural and semantic validators for security audit artifacts."""

from __future__ import annotations

import json
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from gencode_gov.security_audit.coverage import build_canonical_coverage_id
from gencode_gov.security_audit.findings import (
    SEVERITY_RANK,
    VALID_STATE_TRANSITIONS,
    finding_id_from_fingerprint,
)
from gencode_gov.security_audit.sandbox import WINDOWS_RESERVED_NAMES, validate_agent_id

MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_NESTING_DEPTH = 64
MAX_COLLECTION_ITEMS = 10000
MAX_REPORTED_ERRORS = 100


@dataclass(frozen=True)
class ArtifactValidationResult:
    """Controlled validation result that never raises on malformed user artifacts."""

    ok: bool
    errors: tuple[str, ...]


def _schemas_dir() -> Path:
    repo_candidate = Path(__file__).resolve().parents[3] / "schemas"
    if repo_candidate.is_dir():
        return repo_candidate
    return Path(__file__).resolve().parent / "schemas"


def is_safe_relative_path(value: str) -> bool:
    """Verify repository-relative POSIX path with no traversal, control chars, or devices."""
    if not value or value != value.strip() or "\\" in value:
        return False
    if unicodedata.normalize("NFC", value) != value:
        return False
    if value.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", value):
        return False
    for ch in value:
        cat = unicodedata.category(ch)
        if cat.startswith("C"):
            return False
    segments = value.split("/")
    for seg in segments:
        if not seg or seg in {".", ".."} or seg.endswith((" ", ".")):
            return False
        if seg.split(".", 1)[0].lower() in WINDOWS_RESERVED_NAMES:
            return False
    return True


def _read_regular_json(path: Path) -> tuple[Any | None, list[str]]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError as exc:
        return None, [f"cannot open artifact safely ({path.name}): {exc}"]
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return None, [f"artifact is not a regular file: {path.name}"]
        if st.st_size > MAX_INPUT_BYTES:
            return None, [f"artifact exceeds {MAX_INPUT_BYTES} byte limit: {path.name}"]
        raw_bytes = os.read(fd, MAX_INPUT_BYTES + 1)
        if len(raw_bytes) > MAX_INPUT_BYTES:
            return None, [f"artifact grew past {MAX_INPUT_BYTES} byte limit: {path.name}"]
    except OSError as exc:
        return None, [f"failed reading artifact ({path.name}): {exc}"]
    finally:
        os.close(fd)

    try:
        text = raw_bytes.decode("utf-8")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        return None, [f"malformed UTF-8 or JSON in {path.name}: {exc}"]

    limit_errors: list[str] = []
    _check_structural_bounds(parsed, depth=0, errors=limit_errors)
    if limit_errors:
        return None, limit_errors[:MAX_REPORTED_ERRORS]
    return parsed, []


def _check_structural_bounds(node: Any, *, depth: int, errors: list[str]) -> None:
    if len(errors) >= MAX_REPORTED_ERRORS:
        return
    if depth > MAX_NESTING_DEPTH:
        errors.append(f"JSON nesting depth exceeds {MAX_NESTING_DEPTH}")
        return
    if isinstance(node, list):
        if len(node) > MAX_COLLECTION_ITEMS:
            errors.append(f"array exceeds {MAX_COLLECTION_ITEMS} item limit")
            return
        for item in node:
            _check_structural_bounds(item, depth=depth + 1, errors=errors)
    elif isinstance(node, dict):
        if len(node) > MAX_COLLECTION_ITEMS:
            errors.append(f"object exceeds {MAX_COLLECTION_ITEMS} key limit")
            return
        for val in node.values():
            _check_structural_bounds(val, depth=depth + 1, errors=errors)


def _validate_against_schema(payload: Any, schema_filename: str) -> list[str]:
    schema_path = _schemas_dir() / schema_filename
    if not schema_path.is_file():
        return [f"missing schema file: {schema_filename}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errs: list[str] = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "<root>"
        errs.append(f"schema[{loc}]: {err.message}")
        if len(errs) >= MAX_REPORTED_ERRORS:
            break
    return errs


def validate_coverage_ledger_data(payload: Any) -> ArtifactValidationResult:
    """Validate coverage ledger structure, schema, state invariants, and wave history."""
    errors = _validate_against_schema(payload, "security-coverage-ledger.schema.json")
    if errors:
        return ArtifactValidationResult(False, tuple(errors[:MAX_REPORTED_ERRORS]))

    units: list[dict[str, Any]] = payload["units"]
    prev_id: str | None = None
    counts = {
        "examined": 0,
        "partially_examined": 0,
        "planned": 0,
        "in_progress": 0,
        "not_examined": 0,
        "blocked": 0,
        "not_applicable": 0,
    }

    for idx, unit in enumerate(units):
        cid = unit["coverage_id"]
        if prev_id is not None and cid <= prev_id:
            errors.append(f"units[{idx}]: coverage_id must be unique and sorted ({cid!r})")
        prev_id = cid

        expected_cid = build_canonical_coverage_id(
            entry_point=unit["entry_point"],
            trust_boundary=unit["trust_boundary"],
            component=unit["component"],
            attack_class=unit["attack_class"],
            interface=unit["interface"],
            lifecycle=unit.get("lifecycle"),
        )
        if cid != expected_cid:
            errors.append(f"units[{idx}]: coverage_id {cid!r} != canonical {expected_cid!r}")

        for sp in unit["starting_paths"]:
            if not is_safe_relative_path(sp):
                errors.append(f"units[{idx}]: unsafe starting_path {sp!r}")

        status = unit["status"]
        counts[status] += 1
        inv = unit["investigator_id"]
        rpaths = unit["reviewed_paths"]
        checks = unit["checks"]
        lims = unit["limitations"]

        if inv is not None and not validate_agent_id(inv):
            errors.append(f"units[{idx}]: invalid investigator_id {inv!r}")

        if status == "planned" and (inv is not None or rpaths or checks or lims):
            errors.append(f"units[{idx}]: planned unit cannot carry owner, checks, or limitations")
        elif status in {"not_applicable", "not_examined"} and (
            inv is not None or rpaths or checks or not lims
        ):
            errors.append(
                f"units[{idx}]: {status} unit requires null investigator and non-empty limitations"
            )
        elif status == "in_progress" and (inv is None or rpaths or checks):
            errors.append(f"units[{idx}]: in_progress unit requires investigator and empty checks")
        elif status == "examined" and (inv is None or not rpaths or not checks or lims):
            errors.append(
                f"units[{idx}]: examined unit requires investigator, paths, checks, and 0 blockers"
            )
        elif status in {"partially_examined", "blocked"} and (
            inv is None or not rpaths or not checks or not lims
        ):
            errors.append(
                f"units[{idx}]: {status} unit requires investigator, paths, checks, and limitations"
            )

        check_paths_union: set[str] = set()
        for c_idx, chk in enumerate(checks):
            c_owner = chk["investigator_id"]
            if not validate_agent_id(c_owner):
                errors.append(f"units[{idx}].checks[{c_idx}]: invalid investigator_id {c_owner!r}")
            for rp in chk["reviewed_paths"]:
                if not is_safe_relative_path(rp):
                    errors.append(f"units[{idx}].checks[{c_idx}]: unsafe reviewed_path {rp!r}")
                check_paths_union.add(rp)
            art = chk["artifact_path"]
            if chk["method"] == "source" and art is not None:
                errors.append(f"units[{idx}].checks[{c_idx}]: source check must have null artifact")
            if chk["method"] == "sandbox_local":
                prefix = f"agents/{c_owner}/artifacts/"
                if art is None or not is_safe_relative_path(art) or not art.startswith(prefix):
                    errors.append(
                        f"units[{idx}].checks[{c_idx}]: sandbox_local check requires {prefix}*"
                    )

        if checks and set(rpaths) != check_paths_union:
            errors.append(f"units[{idx}]: unit.reviewed_paths must equal union of check paths")

        seen_owners: set[str] = set()
        prev_wave = 0
        for a_idx, att in enumerate(unit["attempts"]):
            awave = att["wave"]
            aowner = att["investigator_id"]
            if awave <= prev_wave or awave >= unit["wave"]:
                errors.append(f"units[{idx}].attempts[{a_idx}]: invalid wave {awave}")
            prev_wave = awave
            if aowner in seen_owners:
                errors.append(f"units[{idx}].attempts[{a_idx}]: reused investigator {aowner!r}")
            seen_owners.add(aowner)
        if inv is not None and inv in seen_owners:
            errors.append(f"units[{idx}]: live investigator {inv!r} reused from prior wave")

    if payload["execution_mode"] == "multi_agent_independent_sessions":
        orch = payload.get("orchestration")
        if not isinstance(orch, dict) or not orch.get("independent_sessions_verified"):
            errors.append("multi_agent_independent_sessions ledger requires verified orchestration")
        else:
            sess_ids = {s["session_id"] for s in orch["sessions"] if s["status"] == "completed"}
            if len(sess_ids) < 2 or orch["distinct_session_ids"] != len(sess_ids):
                errors.append("multi_agent_independent_sessions requires >=2 distinct session_ids")

    comp = payload["completeness"]
    incomplete = (
        counts["planned"]
        + counts["in_progress"]
        + counts["partially_examined"]
        + counts["not_examined"]
        + counts["blocked"]
    )
    expected_complete = len(units) > 0 and counts["examined"] > 0 and incomplete == 0
    if comp["total_units"] != len(units) or comp["is_complete"] != expected_complete:
        errors.append("completeness summary disagrees with computed unit counts")
    for k, v in counts.items():
        if comp[k] != v:
            errors.append(f"completeness.{k} ({comp[k]}) != actual count ({v})")

    if payload["audit_status"] == "completed" and not expected_complete:
        errors.append("audit_status cannot be 'completed' while incomplete coverage units exist")

    return ArtifactValidationResult(not errors, tuple(errors[:MAX_REPORTED_ERRORS]))


def validate_findings_data(payload: Any) -> ArtifactValidationResult:
    """Validate structured findings schema and semantic invariants."""
    errors = _validate_against_schema(payload, "security-finding.schema.json")
    if errors:
        return ArtifactValidationResult(False, tuple(errors[:MAX_REPORTED_ERRORS]))

    records: list[dict[str, Any]] = payload["records"]
    prev_fp: str | None = None
    for idx, rec in enumerate(records):
        fp = rec["fingerprint"]
        if prev_fp is not None and fp <= prev_fp:
            errors.append(f"records[{idx}]: fingerprints must be unique and sorted ({fp!r})")
        prev_fp = fp

        expected_fid = finding_id_from_fingerprint(fp)
        if rec["finding_id"] != expected_fid:
            errors.append(f"records[{idx}]: finding_id {rec['finding_id']!r} != {expected_fid!r}")

        for loc in rec["affected_locations"]:
            if not is_safe_relative_path(loc["file"]):
                errors.append(f"records[{idx}]: unsafe location file {loc['file']!r}")
            if loc.get("end_line") is not None and loc["end_line"] < loc["line"]:
                errors.append(f"records[{idx}]: end_line < line")

        trace = rec["trace"]
        for step in trace:
            if not is_safe_relative_path(step["file"]):
                errors.append(f"records[{idx}]: unsafe trace file {step['file']!r}")
        if len(trace) == 1 and trace[0]["kind"] not in {"entrypoint", "sink"}:
            errors.append(f"records[{idx}]: single-step trace must be entrypoint or sink")
        elif len(trace) > 1:
            if trace[0]["kind"] != "entrypoint" or trace[-1]["kind"] != "sink":
                errors.append(f"records[{idx}]: multi-step trace must go entrypoint -> sink")
            if any(step["kind"] != "propagation" for step in trace[1:-1]):
                errors.append(f"records[{idx}]: intermediate trace steps must be propagation")

        vstatus = rec["verification_status"]
        sev = rec["severity"]
        vprov = rec["verification_provenance"]
        dprov = rec["discovery_provenance"]

        if vprov is not None and vprov["verifier_id"] == dprov["agent_id"]:
            errors.append(f"records[{idx}]: self-confirmation forbidden ({dprov['agent_id']!r})")
        if (
            vprov is not None
            and dprov.get("session_id") is not None
            and vprov.get("session_id") is not None
            and dprov.get("session_id") == vprov.get("session_id")
        ):
            errors.append(f"records[{idx}]: discovering session cannot verify its own finding")

        if vstatus == "confirmed":
            if sev is None or rec["root_cause"] is None or rec["remediation"] is None:
                errors.append(
                    f"records[{idx}]: confirmed record requires severity, root_cause, remediation"
                )
            if vprov is None:
                errors.append(f"records[{idx}]: confirmed record requires verification_provenance")
            if sev is not None and (
                SEVERITY_RANK[sev["overall_severity"]] > SEVERITY_RANK[sev["impact"]["score"]]
            ):
                errors.append(f"records[{idx}]: overall_severity exceeds impact.score")
            if rec["unresolved_blockers"] or rec["rejection_reason"] is not None:
                errors.append(f"records[{idx}]: confirmed record cannot carry blockers/rejection")
            if rec["remediation"] is not None:
                for chg in rec["remediation"]["code_changes"]:
                    if not is_safe_relative_path(chg["file"]):
                        errors.append(f"records[{idx}]: unsafe remediation file {chg['file']!r}")
        else:
            if sev is not None:
                errors.append(f"records[{idx}]: severity forbidden for status {vstatus!r}")
            if rec["root_cause"] is not None or rec["remediation"] is not None:
                errors.append(
                    f"records[{idx}]: confirmed root_cause/remediation forbidden for {vstatus!r}"
                )
            if vstatus in {"needs_validation", "blocked"}:
                vplan = rec["validation_plan"]
                has_plan = isinstance(vplan, dict) and bool(
                    vplan.get("local_check") or vplan.get("owner_deployment_check")
                )
                if not rec["unresolved_blockers"] or not has_plan:
                    errors.append(
                        f"records[{idx}]: {vstatus} requires unresolved_blockers & validation_plan"
                    )
            if vstatus == "rejected" and not rec["rejection_reason"]:
                errors.append(f"records[{idx}]: rejected record requires rejection_reason")

        history = rec["state_history"]
        for h_idx in range(1, len(history)):
            prev_st = history[h_idx - 1]["state"]
            curr_st = history[h_idx]["state"]
            if curr_st not in VALID_STATE_TRANSITIONS.get(prev_st, frozenset()):
                errors.append(
                    f"records[{idx}]: invalid history transition {prev_st!r} -> {curr_st!r}"
                )

    return ArtifactValidationResult(not errors, tuple(errors[:MAX_REPORTED_ERRORS]))


def validate_audit_report_data(payload: Any) -> ArtifactValidationResult:
    """Validate machine-readable security audit report against its schema and invariants."""
    errors = _validate_against_schema(payload, "security-audit-report.schema.json")
    if errors:
        return ArtifactValidationResult(False, tuple(errors[:MAX_REPORTED_ERRORS]))
    if payload["audit_status"] == "completed" and not payload["coverage_summary"]["is_complete"]:
        errors.append("report cannot claim audit_status='completed' with incomplete coverage")
    if payload["governance_gate_status"] == "PASS":
        has_high = any(
            item["severity"] in {"critical", "high"} for item in payload["confirmed_findings"]
        )
        if (
            has_high
            or payload["needs_validation_leads"]
            or payload["blocked_items"]
            or payload["not_verified_items"]
            or not payload["coverage_summary"]["is_complete"]
        ):
            errors.append("governance_gate_status cannot be PASS with unresolved/blocking items")
    return ArtifactValidationResult(not errors, tuple(errors[:MAX_REPORTED_ERRORS]))


def validate_coverage_ledger_file(path: Path) -> ArtifactValidationResult:
    data, errs = _read_regular_json(path)
    if errs:
        return ArtifactValidationResult(False, tuple(errs))
    return validate_coverage_ledger_data(data)


def validate_findings_file(path: Path) -> ArtifactValidationResult:
    data, errs = _read_regular_json(path)
    if errs:
        return ArtifactValidationResult(False, tuple(errs))
    return validate_findings_data(data)


def validate_audit_report_file(path: Path) -> ArtifactValidationResult:
    data, errs = _read_regular_json(path)
    if errs:
        return ArtifactValidationResult(False, tuple(errs))
    return validate_audit_report_data(data)


def validate_audit_directory(audit_dir: Path) -> ArtifactValidationResult:
    """Validate ledger, findings, report, and cross-artifact consistency in audit_dir."""
    errors: list[str] = []
    ledger_path = audit_dir / "coverage-ledger.json"
    findings_path = audit_dir / "findings.json"
    report_path = audit_dir / "security-audit-report.json"

    ledger_data, l_read_errs = _read_regular_json(ledger_path)
    errors.extend(l_read_errs)
    if ledger_data is not None:
        errors.extend(validate_coverage_ledger_data(ledger_data).errors)

    findings_data, f_read_errs = _read_regular_json(findings_path)
    errors.extend(f_read_errs)
    if findings_data is not None:
        errors.extend(validate_findings_data(findings_data).errors)

    report_data: Any | None = None
    if report_path.exists() or report_path.is_symlink():
        report_data, r_read_errs = _read_regular_json(report_path)
        errors.extend(r_read_errs)
        if report_data is not None:
            errors.extend(validate_audit_report_data(report_data).errors)

    if not errors and ledger_data is not None and findings_data is not None:
        if ledger_data["audit_run_id"] != findings_data["audit_run_id"]:
            errors.append("coverage-ledger and findings have mismatched audit_run_id")
        if ledger_data["commit_sha"] != findings_data["commit_sha"]:
            errors.append("coverage-ledger and findings have mismatched commit_sha")

        records_by_id = {r["finding_id"]: r for r in findings_data["records"]}
        records_by_fp = {r["fingerprint"]: r for r in findings_data["records"]}
        referenced_ids: set[str] = set()

        for unit in ledger_data["units"]:
            for fid in unit["finding_ids"]:
                if fid not in records_by_id:
                    errors.append(
                        f"unit {unit['coverage_id']!r} references missing finding {fid!r}"
                    )
                else:
                    referenced_ids.add(fid)
            for fp in unit["candidate_fingerprints"]:
                if fp not in records_by_fp:
                    errors.append(
                        f"unit {unit['coverage_id']!r} references missing fingerprint {fp!r}"
                    )
            for chk in unit["checks"]:
                art = chk["artifact_path"]
                if art is not None:
                    art_file = audit_dir / art
                    if not art_file.is_file() or art_file.is_symlink():
                        errors.append(f"promoted check artifact missing or symlink: {art!r}")

        if ledger_data["execution_mode"] == "multi_agent_independent_sessions":
            for rec in findings_data["records"]:
                if rec["lifecycle_state"] == "remediated":
                    continue
                vp_rec = rec["verification_provenance"]
                dp_rec = rec["discovery_provenance"]
                if vp_rec is not None and (
                    not dp_rec.get("session_id")
                    or not vp_rec.get("session_id")
                    or dp_rec.get("session_id") == vp_rec.get("session_id")
                ):
                    errors.append(
                        f"finding {rec['finding_id']!r} lacks distinct multi-agent "
                        "discovery/verification session_ids"
                    )

        for fid, rec in records_by_id.items():
            if rec["lifecycle_state"] != "remediated" and fid not in referenced_ids:
                errors.append(f"finding {fid!r} is not linked to any coverage unit")

        if report_data is not None:
            if report_data["commit_sha"] != ledger_data["commit_sha"]:
                errors.append("report commit_sha disagrees with coverage-ledger")
            if report_data["audit_status"] != ledger_data["audit_status"]:
                errors.append("report audit_status disagrees with coverage-ledger")
            if report_data["execution_mode"] != ledger_data["execution_mode"]:
                errors.append("report execution_mode disagrees with coverage-ledger")
            if report_data["coverage_summary"] != ledger_data["completeness"]:
                errors.append("report coverage_summary disagrees with coverage-ledger")
            expected_confirmed = [
                r["finding_id"]
                for r in findings_data["records"]
                if r["verification_status"] == "confirmed" and r["lifecycle_state"] != "remediated"
            ]
            actual_confirmed = [c["finding_id"] for c in report_data["confirmed_findings"]]
            if sorted(actual_confirmed) != sorted(expected_confirmed):
                errors.append("report confirmed_findings disagrees with findings.json")

    return ArtifactValidationResult(not errors, tuple(errors[:MAX_REPORTED_ERRORS]))
