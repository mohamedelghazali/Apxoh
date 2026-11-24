"""Cryptographic re-verification for accepted supply-chain evidence."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceError, EvidenceTamperedError
from arkhon.evidence.integrity import sha256_of

SOURCE_URI = "github.com/mohamedelghazali/Apxoh"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
IDENTITY_REGEXP = (
    r"^https://github\.com/mohamedelghazali/Apxoh/"
    r"\.github/workflows/slsa-release\.yml@refs/tags/v.*$"
)
_TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


def identity_regexp_for_tag(source_tag: str) -> str:
    """Return an exact GitHub Actions certificate identity for a release tag."""
    if not _TAG_RE.fullmatch(source_tag):
        raise EvidenceTamperedError("supply-chain source tag is not a valid semantic version tag")
    return (
        r"^https://github\.com/mohamedelghazali/Apxoh/"
        r"\.github/workflows/slsa-release\.yml@refs/tags/"
        + re.escape(source_tag)
        + r"$"
    )


def _in_root(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise EvidenceTamperedError("supply-chain evidence contains an invalid relative path")
    candidate = root / value
    if candidate.is_symlink():
        raise EvidenceTamperedError(f"supply-chain evidence path is a symlink: {value}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceTamperedError(f"supply-chain evidence path escapes project: {value}") from exc
    if not resolved.is_file():
        raise EvidenceTamperedError(f"supply-chain evidence file is missing: {value}")
    return resolved


def verify_cyclonedx_sbom(path: Path, *, expected_commit_sha: str) -> None:
    """Validate the SBOM format and the commit property added by Apxoh."""
    try:
        bom = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceTamperedError(f"CycloneDX SBOM is unreadable: {exc}") from exc
    if not isinstance(bom, dict) or bom.get("bomFormat") != "CycloneDX":
        raise EvidenceTamperedError("SBOM is not CycloneDX")
    if bom.get("specVersion") not in {"1.4", "1.5", "1.6", "1.7"}:
        raise EvidenceTamperedError("SBOM has an unsupported CycloneDX specVersion")
    metadata = bom.get("metadata")
    component = metadata.get("component") if isinstance(metadata, dict) else None
    properties = component.get("properties") if isinstance(component, dict) else None
    if not isinstance(properties, list):
        raise EvidenceTamperedError("SBOM is missing Apxoh commit-binding properties")
    binding = [
        item.get("value")
        for item in properties
        if isinstance(item, dict) and item.get("name") == "arkhon:commit-sha"
    ]
    if binding != [expected_commit_sha]:
        raise EvidenceTamperedError("SBOM commit binding is missing, duplicated, or mismatched")
    if not isinstance(bom.get("components"), list):
        raise EvidenceTamperedError("SBOM components must be an array")


def _verify_source_tag_commit(
    evidence_root: Path, source_tag: str, expected_commit_sha: str
) -> None:
    """Require the signed release tag to resolve to the evidence commit."""
    git = shutil.which("git")
    if git is None:
        raise EvidenceError("git is required to verify release-tag commit binding")
    try:
        result = subprocess.run(  # noqa: S603 - resolved git executable and fixed arguments
            [git, "rev-parse", f"refs/tags/{source_tag}^{{commit}}"],
            cwd=evidence_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EvidenceError(f"cannot resolve release tag {source_tag}: {exc}") from exc
    actual_commit = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", actual_commit):
        raise EvidenceTamperedError("release tag resolved to an invalid commit SHA")
    if actual_commit != expected_commit_sha:
        raise EvidenceTamperedError("release tag commit does not match evidence commit")

def verify_supply_chain_attestation_report(
    report_path: Path,
    *,
    evidence_root: Path,
    expected_commit_sha: str,
    evidence_artifacts: list[dict[str, Any]],
) -> None:
    """Re-run SLSA and Sigstore verification when a PASS evidence record is consumed."""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceTamperedError(f"attestation report is unreadable: {exc}") from exc
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise EvidenceTamperedError("attestation report schema is invalid")
    if report.get("commit_sha") != expected_commit_sha:
        raise EvidenceTamperedError("attestation report commit binding mismatch")
    source_tag = report.get("source_tag")
    if not isinstance(source_tag, str):
        raise EvidenceTamperedError("attestation report is missing its source tag")
    identity_regexp = identity_regexp_for_tag(source_tag)
    if (
        report.get("source_uri") != SOURCE_URI
        or report.get("oidc_issuer") != OIDC_ISSUER
        or report.get("certificate_identity_regexp") != identity_regexp
    ):
        raise EvidenceTamperedError("attestation report trust identity does not match policy")
    verification = report.get("verification")
    if not isinstance(verification, dict) or any(
        not isinstance(verification.get(name), dict)
        or verification[name].get("verified") is not True
        for name in ("slsa", "sigstore")
    ):
        raise EvidenceTamperedError(
            "attestation report does not record both verifications as passed"
        )

    registered: dict[str, str] = {}
    for entry in evidence_artifacts:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            registered[entry["path"]] = str(entry.get("sha256", ""))
    artifact_refs = (
        ("artifact", "artifact_sha256"),
        ("provenance", "provenance_sha256"),
        ("signature_bundle", "signature_bundle_sha256"),
    )
    resolved: dict[str, Path] = {}
    for path_key, digest_key in artifact_refs:
        relative = report.get(path_key)
        digest = report.get(digest_key)
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise EvidenceTamperedError(f"attestation report is missing {path_key} binding")
        if registered.get(relative) != digest:
            raise EvidenceTamperedError(f"{path_key} is not bound by the evidence record")
        candidate = _in_root(evidence_root, relative)
        if sha256_of(candidate) != digest:
            raise EvidenceTamperedError(f"{path_key} digest mismatch")
        resolved[path_key] = candidate
    if report_path.resolve() not in {_in_root(evidence_root, path) for path in registered}:
        raise EvidenceTamperedError("attestation report is not itself bound by the evidence record")

    _verify_source_tag_commit(evidence_root, source_tag, expected_commit_sha)

    slsa = shutil.which("slsa-verifier")
    cosign = shutil.which("cosign")
    if slsa is None or cosign is None:
        raise EvidenceError(
            "cannot accept signed supply-chain evidence: slsa-verifier and cosign are required"
        )
    commands = (
        [
            slsa,
            "verify-artifact",
            str(resolved["artifact"]),
            "--provenance-path",
            str(resolved["provenance"]),
            "--source-uri",
            SOURCE_URI,
            "--source-tag",
            source_tag,
        ],
        [
            cosign,
            "verify-blob",
            "--bundle",
            str(resolved["signature_bundle"]),
            "--certificate-identity-regexp",
            identity_regexp,
            "--certificate-oidc-issuer",
            OIDC_ISSUER,
            str(resolved["artifact"]),
        ],
    )
    for command in commands:
        try:
            result = subprocess.run(  # noqa: S603 - fixed executable and argument vectors
                command,
                cwd=evidence_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceError(f"attestation re-verification could not run: {exc}") from exc
        if result.returncode != 0:
            raise EvidenceTamperedError(
                f"cryptographic attestation verification failed: {result.stderr.strip()[:500]}"
            )
