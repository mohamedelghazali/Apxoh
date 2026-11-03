"""Evidence acceptance tests for SBOM commit binding and cryptographic attestations."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError, EvidenceTamperedError
from arkhon.evidence.supply_chain import (
    IDENTITY_REGEXP,
    OIDC_ISSUER,
    SOURCE_URI,
    verify_cyclonedx_sbom,
    verify_supply_chain_attestation_report,
)

SHA = "a" * 40


def _bom(commit: str = SHA) -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "components": [],
        "metadata": {
            "component": {
                "type": "application",
                "name": "fixture",
                "properties": [{"name": "arkhon:commit-sha", "value": commit}],
            }
        },
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _attestation_fixture(root: Path) -> tuple[Path, list[dict]]:
    files = {}
    for key, name, value in (
        ("artifact", "release.whl", "wheel"),
        ("provenance", "provenance.intoto.jsonl", "provenance"),
        ("signature_bundle", "release.whl.sigstore.json", "bundle"),
    ):
        path = root / "dist" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        files[key] = path
    report_path = root / ".arkhon" / "reports" / "attestation.attestation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "commit_sha": SHA,
        "source_uri": SOURCE_URI,
        "oidc_issuer": OIDC_ISSUER,
        "certificate_identity_regexp": IDENTITY_REGEXP,
        "artifact": "dist/release.whl",
        "artifact_sha256": _sha(files["artifact"]),
        "provenance": "dist/provenance.intoto.jsonl",
        "provenance_sha256": _sha(files["provenance"]),
        "signature_bundle": "dist/release.whl.sigstore.json",
        "signature_bundle_sha256": _sha(files["signature_bundle"]),
        "verification": {
            "slsa": {"verified": True, "returncode": 0},
            "sigstore": {"verified": True, "returncode": 0},
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    artifacts = [
        {"path": path.relative_to(root).as_posix(), "sha256": _sha(path)}
        for path in [*files.values(), report_path]
    ]
    return report_path, artifacts


def test_verify_cyclonedx_sbom_accepts_only_commit_bound_bom(tmp_path: Path) -> None:
    path = tmp_path / "sbom.cdx.json"
    path.write_text(json.dumps(_bom()), encoding="utf-8")
    verify_cyclonedx_sbom(path, expected_commit_sha=SHA)
    with pytest.raises(EvidenceTamperedError, match="mismatched"):
        verify_cyclonedx_sbom(path, expected_commit_sha="b" * 40)
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="unreadable"):
        verify_cyclonedx_sbom(path, expected_commit_sha=SHA)


@pytest.mark.parametrize(
    ("bom", "message"),
    [
        ([], "not CycloneDX"),
        ({"bomFormat": "SPDX"}, "not CycloneDX"),
        ({"bomFormat": "CycloneDX", "specVersion": "1.3"}, "unsupported"),
        (
            {"bomFormat": "CycloneDX", "specVersion": "1.6", "metadata": {}, "components": []},
            "commit-binding",
        ),
        (
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "metadata": {
                    "component": {"properties": [{"name": "arkhon:commit-sha", "value": "bad"}]}
                },
                "components": [],
            },
            "mismatched",
        ),
        (
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "metadata": {
                    "component": {"properties": [{"name": "arkhon:commit-sha", "value": SHA}]}
                },
                "components": {},
            },
            "components",
        ),
    ],
)
def test_verify_cyclonedx_sbom_rejects_invalid_shapes(
    tmp_path: Path, bom: object, message: str
) -> None:
    path = tmp_path / "sbom.json"
    path.write_text(json.dumps(bom), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match=message):
        verify_cyclonedx_sbom(path, expected_commit_sha=SHA)


def test_attestation_reverification_accepts_and_runs_both_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, artifacts = _attestation_fixture(tmp_path)
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which", lambda name: f"/usr/bin/{name}"
    )
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "verified", "")

    monkeypatch.setattr("arkhon.evidence.supply_chain.subprocess.run", run)
    verify_supply_chain_attestation_report(
        report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=artifacts
    )
    assert len(calls) == 2
    assert calls[0][1] == "verify-artifact"
    assert calls[1][1] == "verify-blob"


def test_attestation_report_rejects_unreadable_or_wrong_schema(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("bad json", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="unreadable"):
        verify_supply_chain_attestation_report(
            report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=[]
        )
    report.write_text("[]", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="schema"):
        verify_supply_chain_attestation_report(
            report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=[]
        )


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("commit_sha", "b" * 40, "commit binding"),
        ("source_uri", "github.com/attacker/repo", "trust identity"),
        ("oidc_issuer", "https://attacker.invalid", "trust identity"),
        ("certificate_identity_regexp", ".*", "trust identity"),
        (
            "verification",
            {"slsa": {"verified": False}, "sigstore": {"verified": True}},
            "both verifications",
        ),
    ],
)
def test_attestation_report_rejects_wrong_trust_metadata(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    report_path, artifacts = _attestation_fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report[field] = value
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match=message):
        verify_supply_chain_attestation_report(
            report_path,
            evidence_root=tmp_path,
            expected_commit_sha=SHA,
            evidence_artifacts=artifacts,
        )


def test_attestation_report_requires_bound_paths_and_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_path, artifacts = _attestation_fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["artifact"] = "../outside.whl"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="not bound"):
        verify_supply_chain_attestation_report(
            report_path,
            evidence_root=tmp_path,
            expected_commit_sha=SHA,
            evidence_artifacts=artifacts,
        )
    report["artifact"] = "dist/release.whl"
    report["artifact_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="not bound"):
        verify_supply_chain_attestation_report(
            report_path,
            evidence_root=tmp_path,
            expected_commit_sha=SHA,
            evidence_artifacts=artifacts,
        )
    report["artifact_sha256"] = artifacts[0]["sha256"]
    report_path.write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "dist" / "release.whl").write_text("tampered", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="digest mismatch"):
        verify_supply_chain_attestation_report(
            report_path,
            evidence_root=tmp_path,
            expected_commit_sha=SHA,
            evidence_artifacts=artifacts,
        )


def test_attestation_report_must_be_an_evidence_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, artifacts = _attestation_fixture(tmp_path)
    artifacts.pop()
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which", lambda name: f"/usr/bin/{name}"
    )
    with pytest.raises(EvidenceTamperedError, match="not itself bound"):
        verify_supply_chain_attestation_report(
            report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=artifacts
        )


def test_attestation_verification_blocks_without_verifiers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, artifacts = _attestation_fixture(tmp_path)
    monkeypatch.setattr("arkhon.evidence.supply_chain.shutil.which", lambda _name: None)
    with pytest.raises(EvidenceError, match="slsa-verifier and cosign"):
        verify_supply_chain_attestation_report(
            report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=artifacts
        )


@pytest.mark.parametrize("mode", ["nonzero", "spawn"])
def test_attestation_verification_rejects_invalid_crypto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    report, artifacts = _attestation_fixture(tmp_path)
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which", lambda name: f"/usr/bin/{name}"
    )

    def fail(command, **kwargs):
        if mode == "spawn":
            raise OSError("missing executable")
        return subprocess.CompletedProcess(command, 1, "", "signature invalid")

    monkeypatch.setattr("arkhon.evidence.supply_chain.subprocess.run", fail)
    error = EvidenceError if mode == "spawn" else EvidenceTamperedError
    with pytest.raises(error):
        verify_supply_chain_attestation_report(
            report, evidence_root=tmp_path, expected_commit_sha=SHA, evidence_artifacts=artifacts
        )
