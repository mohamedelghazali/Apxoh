"""Tests for the JSON reporter."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError
from arkhon.evidence.store import EvidenceStore
from arkhon.evidence.supply_chain import OIDC_ISSUER, SOURCE_URI, identity_regexp_for_tag
from arkhon.reporting.json_reporter import SECTION_MAP, JsonReporter


def _write_evidence(
    project: Path,
    domain: str,
    evidence_id: str,
    status: str = "PASS",
    commit_sha: str = "a" * 40,
    executed_at: str = "2026-11-01T00:00:00Z",
) -> Path:
    target_dir = project / ".arkhon" / "evidence" / domain
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact = project / "x"
    artifact.write_text("report evidence", encoding="utf-8")
    target = target_dir / f"{evidence_id}.json"
    target.write_text(
        json.dumps(
            {
                "evidence_id": evidence_id,
                "source": "arkhon",
                "source_version": "0.1.0.dev1",
                "commit_sha": commit_sha,
                "executed_at": executed_at,
                "status": status,
                "artifacts": [
                    {
                        "path": "x",
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return target


def _write_supply_chain_evidence(project: Path, evidence_id: str) -> None:
    def write(relative: str, content: str) -> Path:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    artifact = write("dist/release.whl", "wheel")
    provenance = write("dist/provenance.intoto.jsonl", "provenance")
    signature = write("dist/release.whl.sigstore.json", "signature")
    sbom = write(
        ".arkhon/reports/supply-chain/sbom.cdx.json",
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.7",
                "components": [],
                "metadata": {
                    "component": {"properties": [{"name": "arkhon:commit-sha", "value": "a" * 40}]}
                },
            }
        ),
    )
    report = write(
        ".arkhon/reports/supply-chain/release.attestation.json",
        json.dumps(
            {
                "schema_version": 1,
                "commit_sha": "a" * 40,
                "source_uri": SOURCE_URI,
                "oidc_issuer": OIDC_ISSUER,
                "source_tag": "v1.2.3",
                "certificate_identity_regexp": identity_regexp_for_tag("v1.2.3"),
                "artifact": "dist/release.whl",
                "artifact_sha256": digest(artifact),
                "provenance": "dist/provenance.intoto.jsonl",
                "provenance_sha256": digest(provenance),
                "signature_bundle": "dist/release.whl.sigstore.json",
                "signature_bundle_sha256": digest(signature),
                "verification": {"slsa": {"verified": True}, "sigstore": {"verified": True}},
            }
        ),
    )
    EvidenceStore(project).write(
        "supply-chain",
        {
            "evidence_id": evidence_id,
            "source": "arkhon",
            "source_version": "0.1.0.dev1",
            "commit_sha": "a" * 40,
            "executed_at": "2026-11-03T00:00:00Z",
            "status": "PASS",
            "artifacts": [
                {"path": item.relative_to(project).as_posix(), "sha256": digest(item)}
                for item in (sbom, report, artifact, provenance, signature)
            ],
        },
    )


def test_build_fails_with_no_evidence(tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="no evidence"):
        JsonReporter().build(tmp_path)


def test_build_aggregates_sections(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-ARKHON-1", "PASS")
    _write_evidence(tmp_path, "software-security", "EVID-TSAR-2", "PASS")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"] == "PASS"
    assert report["sections"]["security"]["status"] == "PASS"
    assert "EVID-ARKHON-1" in report["sections"]["testing"]["evidence_ids"]


def test_evidence_ids_are_isolated_by_section(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-TEST")
    _write_evidence(tmp_path, "software-security", "EVID-SEC")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["evidence_ids"] == ["EVID-TEST"]
    assert report["sections"]["security"]["evidence_ids"] == ["EVID-SEC"]


def test_fail_status_takes_precedence_over_blocked(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A-FAIL", "FAIL")
    _write_evidence(tmp_path, "testing", "EVID-B-BLOCKED", "BLOCKED")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"] == "FAIL"
    assert report["final_decision"] == "REJECTED"


def test_build_final_decision_approved(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "PASS")
    assert JsonReporter().build(tmp_path)["final_decision"] == "PENDING_EVIDENCE"


def test_build_final_decision_rejected_on_fail(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "FAIL")
    assert JsonReporter().build(tmp_path)["final_decision"] == "REJECTED"


def test_build_final_decision_pending_on_blocked(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "BLOCKED")
    assert JsonReporter().build(tmp_path)["final_decision"] == "PENDING_EVIDENCE"


def test_write_creates_file(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "PASS")
    output = tmp_path / "out"
    path = JsonReporter().write(tmp_path, output)
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))["project"] == tmp_path.name


def test_build_rejects_invalid_commit_and_ignores_unknown_domain(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "unmapped-domain", "EVID-UNKNOWN")
    report = JsonReporter().build(tmp_path)
    assert report["final_decision"] == "PENDING_EVIDENCE"
    (tmp_path / ".arkhon" / "evidence" / "testing").mkdir(parents=True)
    (tmp_path / ".arkhon" / "evidence" / "testing" / "EVID-BAD.json").write_text(
        json.dumps({"evidence_id": "EVID-BAD", "commit_sha": "short", "status": "PASS"}),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="valid commit_sha"):
        JsonReporter().build(tmp_path)


def test_build_approves_only_when_every_section_has_verified_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for index, domain in enumerate(SECTION_MAP):
        evidence_id = f"EVID-ALL-{index}"
        if domain == "supply-chain":
            _write_supply_chain_evidence(tmp_path, evidence_id)
        else:
            _write_evidence(tmp_path, domain, evidence_id)
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which", lambda name: f"/usr/bin/{name}"
    )
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "verified", ""),
    )
    report = JsonReporter().build(tmp_path)
    assert report["final_decision"] == "APPROVED"
    assert all(section["status"] == "PASS" for section in report["sections"].values())


def test_build_filters_evidence_to_expected_commit(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", commit_sha="a" * 40)
    _write_evidence(tmp_path, "software-security", "EVID-B", commit_sha="c" * 40)
    report = JsonReporter().build(tmp_path, expected_commit_sha="a" * 40)
    assert report["commit_sha"] == "a" * 40
    assert report["sections"]["testing"]["evidence_ids"] == ["EVID-A"]
    assert report["sections"]["security"]["status"] == "BLOCKED"


def test_build_selects_latest_commit_group_when_unspecified(tmp_path: Path) -> None:
    _write_evidence(
        tmp_path,
        "testing",
        "EVID-OLD",
        commit_sha="a" * 40,
        executed_at="2026-11-01T00:00:00Z",
    )
    _write_evidence(
        tmp_path,
        "software-security",
        "EVID-NEW",
        commit_sha="c" * 40,
        executed_at="2026-11-02T00:00:00Z",
    )
    report = JsonReporter().build(tmp_path)
    assert report["commit_sha"] == "c" * 40
    assert report["sections"]["security"]["evidence_ids"] == ["EVID-NEW"]
    assert report["sections"]["testing"]["status"] == "BLOCKED"


def test_build_requires_evidence_for_expected_commit(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", commit_sha="a" * 40)
    with pytest.raises(EvidenceError, match="no evidence found for commit"):
        JsonReporter().build(tmp_path, expected_commit_sha="c" * 40)


def test_build_rejects_tampered_artifact(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A")
    (tmp_path / "x").write_text("modified", encoding="utf-8")
    with pytest.raises(EvidenceError, match="verification failed"):
        JsonReporter().build(tmp_path)


def test_build_rejects_stale_evidence(tmp_path: Path) -> None:
    target = _write_evidence(tmp_path, "testing", "EVID-STALE")
    data = json.loads(target.read_text(encoding="utf-8"))
    data["executed_at"] = "2026-01-01T00:00:00Z"
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceError, match="stale"):
        JsonReporter().build(tmp_path)


def test_accepted_risk_cannot_create_unconditional_approval(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-RISK", "ACCEPTED_RISK")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"] == "BLOCKED"
    assert report["final_decision"] == "PENDING_EVIDENCE"


def test_build_rejects_unknown_evidence_status(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-UNKNOWN-STATUS", "MAYBE")
    with pytest.raises(EvidenceError, match="invalid status"):
        JsonReporter().build(tmp_path)


def test_build_rejects_naive_execution_timestamp(tmp_path: Path) -> None:
    _write_evidence(
        tmp_path,
        "testing",
        "EVID-NAIVE",
        executed_at="2026-11-01T00:00:00",
    )
    with pytest.raises(EvidenceError, match="must include a timezone"):
        JsonReporter().build(tmp_path)


def test_build_rejects_non_string_evidence_status(tmp_path: Path) -> None:
    target = _write_evidence(tmp_path, "testing", "EVID-STATUS-TYPE")
    data = json.loads(target.read_text(encoding="utf-8"))
    data["status"] = []
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceError, match="invalid status"):
        JsonReporter().build(tmp_path)


@pytest.mark.parametrize("timestamp", ["not-a-timestamp", None])
def test_build_rejects_invalid_execution_timestamp(tmp_path: Path, timestamp: str | None) -> None:
    _write_evidence(tmp_path, "testing", "EVID-BAD-TIME")
    target = tmp_path / ".arkhon" / "evidence" / "testing" / "EVID-BAD-TIME.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    data["executed_at"] = timestamp
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceError, match="invalid executed_at"):
        JsonReporter().build(tmp_path)


def test_build_rejects_invalid_expected_commit_sha(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A")
    with pytest.raises(EvidenceError, match="expected commit_sha is invalid"):
        JsonReporter().build(tmp_path, expected_commit_sha="not-a-sha")
