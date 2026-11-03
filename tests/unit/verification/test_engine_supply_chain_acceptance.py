"""Supply-chain evidence is cryptographically checked before the engine records PASS."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from arkhon.evidence.collector import EvidenceCollector
from arkhon.evidence.store import EvidenceStore
from arkhon.evidence.supply_chain import (
    OIDC_ISSUER,
    SOURCE_URI,
    identity_regexp_for_tag,
)
from arkhon.verification.engine import VerificationEngine
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

COMMIT = "a" * 40
SOURCE_TAG = "v1.2.3"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(root: Path) -> list[Path]:
    files: dict[str, Path] = {}
    for key, relative, value in (
        ("artifact", "dist/apxoh.whl", "wheel"),
        ("provenance", "dist/provenance.intoto.jsonl", "signed provenance"),
        ("signature_bundle", "dist/apxoh.whl.sigstore.json", "sigstore bundle"),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        files[key] = path

    sbom = root / ".arkhon" / "reports" / "supply-chain" / f"sbom-{COMMIT[:12]}.cdx.json"
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
                        "name": "Apxoh",
                        "properties": [{"name": "arkhon:commit-sha", "value": COMMIT}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    report = sbom.with_name(f"attestation-{COMMIT[:12]}.attestation.json")
    report.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit_sha": COMMIT,
                "source_uri": SOURCE_URI,
                "source_tag": SOURCE_TAG,
                "oidc_issuer": OIDC_ISSUER,
                "certificate_identity_regexp": identity_regexp_for_tag(SOURCE_TAG),
                "artifact": files["artifact"].relative_to(root).as_posix(),
                "artifact_sha256": _digest(files["artifact"]),
                "provenance": files["provenance"].relative_to(root).as_posix(),
                "provenance_sha256": _digest(files["provenance"]),
                "signature_bundle": files["signature_bundle"].relative_to(root).as_posix(),
                "signature_bundle_sha256": _digest(files["signature_bundle"]),
                "verification": {
                    "slsa": {"verified": True, "returncode": 0},
                    "sigstore": {"verified": True, "returncode": 0},
                },
            }
        ),
        encoding="utf-8",
    )
    return [sbom, files["artifact"], files["provenance"], files["signature_bundle"], report]


class FixtureRunner(Runner):
    def __init__(self, artifacts: list[Path]) -> None:
        self.artifacts = artifacts

    @property
    def name(self) -> str:
        return "fixture-supply-chain"

    def run(self, project_root: Path) -> RunnerResult:
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=self.artifacts)


def _engine(root: Path) -> VerificationEngine:
    return VerificationEngine(
        store=EvidenceStore(root),
        collector=EvidenceCollector(root=root),
    )


def _enable_verifiers(monkeypatch: pytest.MonkeyPatch, *, returncode: int = 0) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        "arkhon.evidence.supply_chain.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, returncode, "verified", "invalid" if returncode else "")

    monkeypatch.setattr("arkhon.evidence.supply_chain.subprocess.run", run)
    return calls


def test_engine_accepts_commit_bound_sbom_before_recording_pass(tmp_path: Path) -> None:
    artifacts = _fixture(tmp_path)
    run = _engine(tmp_path).run(
        domain="supply-chain",
        commit_sha=COMMIT,
        runners=[FixtureRunner([artifacts[0]])],
        project_root=tmp_path,
    )
    record = EvidenceStore(tmp_path).read("supply-chain", run.evidence_id)
    assert run.status == "PASS"
    assert record.status == "PASS"
    assert record.data["artifacts"][0]["path"].endswith(".cdx.json")


def test_engine_blocks_supply_chain_pass_without_required_artifacts(tmp_path: Path) -> None:
    sbom = tmp_path / "not-a-sbom.json"
    sbom.write_text("{}", encoding="utf-8")
    run = _engine(tmp_path).run(
        domain="supply-chain",
        commit_sha=COMMIT,
        runners=[FixtureRunner([sbom])],
        project_root=tmp_path,
    )
    record = EvidenceStore(tmp_path).read("supply-chain", run.evidence_id)
    assert run.status == "BLOCKED"
    assert record.status == "BLOCKED"
    assert record.data["summary"]["blocked"] == 1


def test_engine_rechecks_slsa_and_sigstore_before_release_attestation_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = _fixture(tmp_path)
    calls = _enable_verifiers(monkeypatch)
    run = _engine(tmp_path).run(
        domain="release-attestations",
        commit_sha=COMMIT,
        runners=[FixtureRunner(artifacts[1:])],
        project_root=tmp_path,
    )
    record = EvidenceStore(tmp_path).read("release-attestations", run.evidence_id)
    assert run.status == "PASS"
    assert record.status == "PASS"
    assert len(calls) == 2
    assert calls[0][calls[0].index("--source-tag") + 1] == SOURCE_TAG
    assert calls[1][1] == "verify-blob"


def test_engine_blocks_when_crypto_verification_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = _fixture(tmp_path)
    _enable_verifiers(monkeypatch, returncode=1)
    run = _engine(tmp_path).run(
        domain="release-attestations",
        commit_sha=COMMIT,
        runners=[FixtureRunner(artifacts[1:])],
        project_root=tmp_path,
    )
    record = EvidenceStore(tmp_path).read("release-attestations", run.evidence_id)
    assert run.status == "BLOCKED"
    assert record.status == "BLOCKED"
    assert record.data["summary"]["blocked"] == 1
