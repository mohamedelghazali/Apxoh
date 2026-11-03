"""The report/acceptance path must re-run supply-chain cryptographic checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError
from arkhon.evidence.store import EvidenceStore
from arkhon.evidence.supply_chain import (
    identity_regexp_for_tag,
    OIDC_ISSUER,
    SOURCE_URI,
)
from arkhon.reporting.json_reporter import JsonReporter

SHA = "a" * 40


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _accepted_supply_chain_record(root: Path) -> None:
    paths = {}
    for name, value in (
        ("dist/app.whl", "wheel"),
        ("dist/provenance.intoto.jsonl", "provenance"),
        ("dist/app.sigstore.json", "bundle"),
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        paths[name] = path
    sbom = root / ".arkhon" / "reports" / "supply-chain" / f"sbom-{SHA[:12]}.cdx.json"
    sbom.parent.mkdir(parents=True, exist_ok=True)
    sbom.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.7",
                "components": [],
                "metadata": {
                    "component": {
                        "type": "application",
                        "name": "fixture",
                        "properties": [{"name": "arkhon:commit-sha", "value": SHA}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    report = root / ".arkhon" / "reports" / "supply-chain" / "release.attestation.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit_sha": SHA,
                "source_uri": SOURCE_URI,
                "oidc_issuer": OIDC_ISSUER,
                "source_tag": "v1.2.3",
                "certificate_identity_regexp": identity_regexp_for_tag("v1.2.3"),
                "artifact": "dist/app.whl",
                "artifact_sha256": _hash(paths["dist/app.whl"]),
                "provenance": "dist/provenance.intoto.jsonl",
                "provenance_sha256": _hash(paths["dist/provenance.intoto.jsonl"]),
                "signature_bundle": "dist/app.sigstore.json",
                "signature_bundle_sha256": _hash(paths["dist/app.sigstore.json"]),
                "verification": {"slsa": {"verified": True}, "sigstore": {"verified": True}},
            }
        ),
        encoding="utf-8",
    )
    EvidenceStore(root).write(
        "supply-chain",
        {
            "evidence_id": "EVID-SUPPLY-CHAIN",
            "source": "arkhon",
            "source_version": "0.1.0",
            "commit_sha": SHA,
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
            "artifacts": [{"path": sbom.relative_to(root).as_posix(), "sha256": _hash(sbom)}],
        },
    )
    EvidenceStore(root).write(
        "release-attestations",
        {
            "evidence_id": "EVID-RELEASE-ATTEST",
            "source": "arkhon",
            "source_version": "0.1.0",
            "commit_sha": SHA,
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
            "artifacts": [
                {"path": path.relative_to(root).as_posix(), "sha256": _hash(path)}
                for path in [report, *paths.values()]
            ],
        },
    )


def test_report_reverifies_sbom_provenance_and_signature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _accepted_supply_chain_record(tmp_path)
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which", lambda name: f"/usr/bin/{name}"
    )
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        output = SHA if command[1] == "rev-parse" else "verified"
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr("arkhon.evidence.supply_chain.subprocess.run", run)
    report = JsonReporter().build(tmp_path, expected_commit_sha=SHA)
    assert report["sections"]["supply_chain"]["status"] == "PASS"
    assert report["sections"]["final_acceptance"]["status"] == "PASS"
    assert len(calls) == 3
    assert calls[0][1] == "rev-parse"
    assert calls[1][1] == "verify-artifact"
    assert calls[2][1] == "verify-blob"


def test_report_accepts_commit_bound_sbom_without_release_attestation(tmp_path: Path) -> None:
    artifact = tmp_path / f"sbom-{SHA[:12]}.cdx.json"
    artifact.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [],
                "metadata": {
                    "component": {"properties": [{"name": "arkhon:commit-sha", "value": SHA}]}
                },
            }
        ),
        encoding="utf-8",
    )
    EvidenceStore(tmp_path).write(
        "supply-chain",
        {
            "evidence_id": "EVID-SUPPLY-NO-ATTEST",
            "source": "arkhon",
            "source_version": "0.1.0",
            "commit_sha": SHA,
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
            "artifacts": [{"path": artifact.name, "sha256": _hash(artifact)}],
        },
    )
    report = JsonReporter().build(tmp_path, expected_commit_sha=SHA)
    assert report["sections"]["supply_chain"]["status"] == "PASS"


def test_report_never_accepts_release_attestation_pass_without_report(tmp_path: Path) -> None:
    artifact = tmp_path / "release.whl"
    artifact.write_text("wheel", encoding="utf-8")
    EvidenceStore(tmp_path).write(
        "release-attestations",
        {
            "evidence_id": "EVID-RELEASE-NO-ATTEST",
            "source": "arkhon",
            "source_version": "0.1.0",
            "commit_sha": SHA,
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
            "artifacts": [{"path": artifact.name, "sha256": _hash(artifact)}],
        },
    )
    with pytest.raises(EvidenceError, match="exactly one attestation report"):
        JsonReporter().build(tmp_path, expected_commit_sha=SHA)
