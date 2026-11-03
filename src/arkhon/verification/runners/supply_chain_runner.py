"""SBOM generation and release-attestation verification runners."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import sha256_of
from arkhon.evidence.supply_chain import identity_regexp_for_tag
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.runners.supply_chain")
_SOURCE_URI = "github.com/mohamedelghazali/Apxoh"
_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


def _commit_sha(project_root: Path) -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - resolved executable and fixed arguments
            [git, "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if _COMMIT_RE.fullmatch(value) else None


def _tag_commit_sha(project_root: Path, source_tag: str) -> str | None:
    """Resolve a release tag to a commit without invoking a shell."""
    if not _TAG_RE.fullmatch(source_tag):
        return None
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - resolved git executable and fixed arguments
            [git, "rev-parse", f"refs/tags/{source_tag}^{{commit}}"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if _COMMIT_RE.fullmatch(value) else None


def _safe_directory(root: Path, path: Path) -> Path | None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _safe_file(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return None
    unresolved = root / candidate
    if unresolved.is_symlink():
        return None
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return resolved


class SyftRunner(Runner):
    """Generate and validate a CycloneDX SBOM using the Syft executable."""

    @property
    def name(self) -> str:
        return "syft"

    def run(self, project_root: Path) -> RunnerResult:
        root = project_root.resolve()
        commit = _commit_sha(root)
        if commit is None:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "cannot resolve a full Git commit SHA"
            )
        syft = shutil.which("syft")
        if syft is None:
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, "Syft executable not found")
        try:
            result = subprocess.run(  # noqa: S603 - resolved executable and fixed arguments
                [syft, f"dir:{root}", "-o", "cyclonedx-json"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, f"Syft execution failed: {exc}")
        if result.returncode != 0:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                f"Syft exited with {result.returncode}: {result.stderr.strip()[:300]}",
            )
        try:
            bom = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, f"Syft output is invalid JSON: {exc}"
            )
        if not isinstance(bom, dict) or bom.get("bomFormat") != "CycloneDX":
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, "Syft output is not CycloneDX")
        if bom.get("specVersion") not in {"1.4", "1.5", "1.6", "1.7"}:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "unsupported CycloneDX specVersion"
            )
        metadata = bom.get("metadata")
        components = bom.get("components")
        if not isinstance(metadata, dict) or not isinstance(components, list):
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "CycloneDX metadata/components are malformed"
            )
        tools = metadata.get("tools")
        tool_components = tools.get("components") if isinstance(tools, dict) else tools
        if not isinstance(tool_components, list) or not any(
            isinstance(tool, dict) and str(tool.get("name", "")).lower() == "syft"
            for tool in tool_components
        ):
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "CycloneDX metadata does not identify Syft"
            )
        component = metadata.get("component")
        if not isinstance(component, dict):
            component = {"type": "application", "name": root.name}
            metadata["component"] = component
        properties = component.get("properties")
        if not isinstance(properties, list):
            properties = []
            component["properties"] = properties
        properties[:] = [
            item
            for item in properties
            if not isinstance(item, dict) or item.get("name") != "arkhon:commit-sha"
        ]
        properties.append({"name": "arkhon:commit-sha", "value": commit})
        properties.append({"name": "arkhon:generator", "value": "Apxoh SyftRunner"})
        output_dir = _safe_directory(root, root / ".arkhon" / "reports" / "supply-chain")
        if output_dir is None:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "SBOM output directory escapes project root"
            )
        output = output_dir / f"sbom-{commit[:12]}.cdx.json"
        if output.is_symlink():
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, "refusing symlinked SBOM output")
        try:
            output.write_text(json.dumps(bom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, f"cannot persist SBOM: {exc}")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[output])


class SupplyChainAttestationRunner(Runner):
    """Verify SLSA provenance and Sigstore bundle for a release artifact.

    Configure relative artifact paths in .arkhon/supply-chain.json. Trust roots,
    repository identity, workflow identity, and OIDC issuer are pinned in code.
    """

    CONFIG_PATH = ".arkhon/supply-chain.json"

    @property
    def name(self) -> str:
        return "supply-chain-attestations"

    def run(self, project_root: Path) -> RunnerResult:
        root = project_root.resolve()
        commit = _commit_sha(root)
        if commit is None:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "cannot resolve a full Git commit SHA"
            )
        config_path = _safe_file(root, self.CONFIG_PATH)
        if config_path is None:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                f"required release attestation config is missing: {self.CONFIG_PATH}",
            )
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, f"attestation config is invalid: {exc}"
            )
        if not isinstance(config, dict):
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "attestation config must be an object"
            )
        source_tag = config.get("source_tag")
        if not isinstance(source_tag, str) or not _TAG_RE.fullmatch(source_tag):
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                "attestation config must contain a semantic source_tag such as v1.2.3",
            )
        if _tag_commit_sha(root, source_tag) != commit:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                f"release tag {source_tag} does not resolve to the checked-out commit",
            )
        identity_regexp = identity_regexp_for_tag(source_tag)
        artifact = _safe_file(root, config.get("artifact"))
        provenance = _safe_file(root, config.get("provenance"))
        signature = _safe_file(root, config.get("signature_bundle"))
        if artifact is None or provenance is None or signature is None:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                "artifact, provenance, and signature_bundle must be existing in-project files",
            )
        slsa = shutil.which("slsa-verifier")
        cosign = shutil.which("cosign")
        if slsa is None or cosign is None:
            missing = [
                name for name, path in (("slsa-verifier", slsa), ("cosign", cosign)) if path is None
            ]
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                f"required verifier(s) not found: {', '.join(missing)}",
            )
        commands = [
            (
                "slsa",
                [
                    slsa,
                    "verify-artifact",
                    str(artifact),
                    "--provenance-path",
                    str(provenance),
                    "--source-uri",
                    _SOURCE_URI,
                    "--source-tag",
                    source_tag,
                ],
            ),
            (
                "sigstore",
                [
                    cosign,
                    "verify-blob",
                    "--bundle",
                    str(signature),
                    "--certificate-identity-regexp",
                    identity_regexp,
                    "--certificate-oidc-issuer",
                    _OIDC_ISSUER,
                    str(artifact),
                ],
            ),
        ]
        outcomes: dict[str, dict[str, Any]] = {}
        overall = RunnerOutcome.PASS
        for label, command in commands:
            try:
                result = subprocess.run(  # noqa: S603 - executable resolved and fixed argument vector
                    command,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
                outcomes[label] = {
                    "verified": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                }
                if result.returncode != 0:
                    overall = RunnerOutcome.FAIL
            except (OSError, subprocess.SubprocessError) as exc:
                outcomes[label] = {"verified": False, "error": f"{type(exc).__name__}: {exc}"}
                overall = RunnerOutcome.BLOCKED
        report_dir = _safe_directory(root, root / ".arkhon" / "reports" / "supply-chain")
        if report_dir is None:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                "attestation report directory escapes project root",
            )
        report_path = report_dir / f"attestation-{commit[:12]}.attestation.json"
        if report_path.is_symlink():
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, "refusing symlinked attestation report"
            )
        report = {
            "schema_version": 1,
            "commit_sha": commit,
            "source_uri": _SOURCE_URI,
            "source_tag": source_tag,
            "oidc_issuer": _OIDC_ISSUER,
            "certificate_identity_regexp": identity_regexp,
            "artifact": artifact.relative_to(root).as_posix(),
            "artifact_sha256": sha256_of(artifact),
            "provenance": provenance.relative_to(root).as_posix(),
            "provenance_sha256": sha256_of(provenance),
            "signature_bundle": signature.relative_to(root).as_posix(),
            "signature_bundle_sha256": sha256_of(signature),
            "verification": outcomes,
        }
        try:
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            return RunnerResult(
                self.name, RunnerOutcome.BLOCKED, f"cannot persist attestation report: {exc}"
            )
        artifacts = [artifact, provenance, signature, report_path]
        reason = (
            ""
            if overall == RunnerOutcome.PASS
            else "SLSA provenance or Sigstore verification failed"
        )
        return RunnerResult(self.name, overall, reason, artifacts)
