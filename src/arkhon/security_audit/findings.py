"""Structured security findings lifecycle, deterministic fingerprinting, and reconciliation."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FINDINGS_SCHEMA_VERSION = "1.0.0"

SEVERITY_RANK: dict[str, int] = {
    "informational": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

VERIFICATION_STATUSES = frozenset(
    {"confirmed", "needs_validation", "rejected", "blocked", "not_verified"}
)

LIFECYCLE_STATES = frozenset(
    {
        "candidate",
        "confirmed",
        "needs_validation",
        "rejected",
        "blocked",
        "remediated",
        "reopened",
    }
)

VALID_STATE_TRANSITIONS: dict[str, frozenset[str]] = {
    "candidate": frozenset(
        {"candidate", "confirmed", "needs_validation", "rejected", "blocked"}
    ),
    "confirmed": frozenset({"confirmed", "remediated", "needs_validation", "rejected"}),
    "needs_validation": frozenset(
        {"needs_validation", "confirmed", "rejected", "blocked", "remediated"}
    ),
    "blocked": frozenset({"blocked", "needs_validation", "confirmed", "rejected"}),
    "rejected": frozenset({"rejected", "needs_validation", "confirmed"}),
    "remediated": frozenset({"remediated", "reopened"}),
    "reopened": frozenset({"reopened", "confirmed", "remediated", "needs_validation"}),
}

_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9._:/@+-]+")


def _clean_token(raw: str) -> str:
    cleaned = _SAFE_TOKEN_RE.sub("-", raw.strip()).strip("-")
    if cleaned and not cleaned[0].isalnum():
        cleaned = f"dot-{cleaned.lstrip('.')}"
    return cleaned if (cleaned and cleaned[0].isalnum()) else "root"


def compute_finding_fingerprint(
    *,
    component: str,
    attack_class: str,
    primary_file: str,
    symbol: str,
    invariant_key: str,
) -> str:
    """Compute stable line-independent fingerprint matching schema pattern."""
    normalized_file = primary_file.replace("\\", "/").strip("/")
    parts = (
        _clean_token(component),
        _clean_token(attack_class),
        _clean_token(normalized_file),
        _clean_token(symbol),
        _clean_token(invariant_key),
    )
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{digest}"


def finding_id_from_fingerprint(fingerprint: str) -> str:
    """Derive deterministic SEC-FIND-<8HEX> identifier from a canonical fingerprint."""
    suffix = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:8].upper()
    return f"SEC-FIND-{suffix}"


@dataclass(frozen=True)
class LocationRef:
    file: str
    line: int
    symbol: str
    end_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "file": self.file,
            "line": self.line,
            "symbol": self.symbol,
        }
        if self.end_line is not None:
            out["end_line"] = self.end_line
        return out

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LocationRef:
        return cls(
            file=str(payload["file"]),
            line=int(payload["line"]),
            symbol=str(payload["symbol"]),
            end_line=(
                None if payload.get("end_line") is None else int(payload["end_line"])
            ),
        )


@dataclass(frozen=True)
class TraceStep:
    kind: str
    file: str
    line: int
    scope: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "file": self.file,
            "line": self.line,
            "scope": self.scope,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TraceStep:
        return cls(
            kind=str(payload["kind"]),
            file=str(payload["file"]),
            line=int(payload["line"]),
            scope=str(payload["scope"]),
            description=str(payload["description"]),
        )


@dataclass(frozen=True)
class DiscoveryProvenance:
    agent_id: str
    role: str
    run_id: str
    timestamp: str
    method: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "method": self.method,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DiscoveryProvenance:
        return cls(
            agent_id=str(payload["agent_id"]),
            role=str(payload["role"]),
            run_id=str(payload["run_id"]),
            timestamp=str(payload["timestamp"]),
            method=str(payload["method"]),
        )


@dataclass(frozen=True)
class VerificationProvenance:
    verifier_id: str
    role: str
    run_id: str
    timestamp: str
    method: str
    supporting_evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...]
    disprove_attempts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_id": self.verifier_id,
            "role": self.role,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "method": self.method,
            "supporting_evidence": list(self.supporting_evidence),
            "contradictory_evidence": list(self.contradictory_evidence),
            "disprove_attempts": list(self.disprove_attempts),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VerificationProvenance:
        return cls(
            verifier_id=str(payload["verifier_id"]),
            role=str(payload["role"]),
            run_id=str(payload["run_id"]),
            timestamp=str(payload["timestamp"]),
            method=str(payload["method"]),
            supporting_evidence=tuple(str(x) for x in payload["supporting_evidence"]),
            contradictory_evidence=tuple(
                str(x) for x in payload["contradictory_evidence"]
            ),
            disprove_attempts=tuple(str(x) for x in payload["disprove_attempts"]),
        )


@dataclass(frozen=True)
class SeverityAssessment:
    """Calibrated severity permitted ONLY on independently confirmed findings."""

    likelihood_score: str
    likelihood_reason: str
    impact_score: str
    impact_reason: str
    overall_severity: str

    def __post_init__(self) -> None:
        for label in (self.likelihood_score, self.impact_score, self.overall_severity):
            if label not in SEVERITY_RANK:
                raise ValueError(f"invalid severity level: {label!r}")
        if SEVERITY_RANK[self.overall_severity] > SEVERITY_RANK[self.impact_score]:
            raise ValueError("overall_severity must not exceed demonstrated impact_score")

    def to_dict(self) -> dict[str, Any]:
        return {
            "likelihood": {
                "score": self.likelihood_score,
                "reason": self.likelihood_reason,
            },
            "impact": {
                "score": self.impact_score,
                "reason": self.impact_reason,
            },
            "overall_severity": self.overall_severity,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SeverityAssessment:
        return cls(
            likelihood_score=str(payload["likelihood"]["score"]),
            likelihood_reason=str(payload["likelihood"]["reason"]),
            impact_score=str(payload["impact"]["score"]),
            impact_reason=str(payload["impact"]["reason"]),
            overall_severity=str(payload["overall_severity"]),
        )


@dataclass(frozen=True)
class RemediationGuidance:
    strategy: str
    invariant_to_enforce: str
    code_changes: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "invariant_to_enforce": self.invariant_to_enforce,
            "code_changes": [
                {"file": file_path, "summary": summary}
                for file_path, summary in self.code_changes
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RemediationGuidance:
        return cls(
            strategy=str(payload["strategy"]),
            invariant_to_enforce=str(payload["invariant_to_enforce"]),
            code_changes=tuple(
                (str(item["file"]), str(item["summary"]))
                for item in payload["code_changes"]
            ),
        )


@dataclass
class SecurityFinding:
    """Lifecycle-managed security finding or candidate record."""

    finding_id: str
    fingerprint: str
    title: str
    description: str
    attack_class: str
    component: str
    affected_locations: list[LocationRef]
    trace: list[TraceStep]
    trust_boundary: str
    entry_point: str
    affected_principal_or_resource: str
    preconditions: list[str]
    scenario_summary: str
    reproduction_steps: list[str]
    security_impact: str
    evidence_refs: list[str]
    discovery_provenance: DiscoveryProvenance
    verification_provenance: VerificationProvenance | None
    verification_status: str
    lifecycle_state: str
    confidence_score: str
    confidence_reason: str
    uncertainty_notes: list[str]
    severity: SeverityAssessment | None
    root_cause: str | None
    claimed_root_cause: str | None
    remediation: RemediationGuidance | None
    unresolved_blockers: list[str]
    validation_plan: dict[str, str] | None
    rejection_reason: str | None
    related_rules: list[str]
    related_requirements: list[str]
    commit_sha: str
    first_seen_run: str
    last_seen_run: str
    first_seen_commit: str
    last_seen_commit: str
    state_history: list[dict[str, str]] = field(default_factory=list)

    def enforce_policy_invariants(self) -> None:
        """Enforce severity/verdict separation and self-confirmation prohibition."""
        if self.verification_status != "confirmed" and self.severity is not None:
            raise ValueError(
                f"severity is forbidden when verification_status is {self.verification_status!r}"
            )
        if self.verification_status == "confirmed":
            if self.severity is None or self.root_cause is None or self.remediation is None:
                raise ValueError(
                    "confirmed findings require severity, root_cause, and remediation"
                )
            if self.verification_provenance is None:
                raise ValueError("confirmed findings require independent verification_provenance")
            if self.verification_provenance.verifier_id == self.discovery_provenance.agent_id:
                raise ValueError("discovering agent may never self-confirm its own finding")

    def transition_to(
        self,
        new_state: str,
        *,
        run_id: str,
        commit_sha: str,
        actor: str,
        reason: str,
    ) -> None:
        allowed = VALID_STATE_TRANSITIONS.get(self.lifecycle_state, frozenset())
        if new_state not in allowed:
            raise ValueError(
                f"invalid finding state transition: {self.lifecycle_state!r} -> {new_state!r}"
            )
        self.lifecycle_state = new_state
        self.last_seen_run = run_id
        self.last_seen_commit = commit_sha
        self.commit_sha = commit_sha
        self.state_history.append(
            {
                "state": new_state,
                "run_id": run_id,
                "commit_sha": commit_sha,
                "actor": actor,
                "reason": reason,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        self.enforce_policy_invariants()
        return {
            "finding_id": self.finding_id,
            "fingerprint": self.fingerprint,
            "title": self.title,
            "description": self.description,
            "attack_class": self.attack_class,
            "component": self.component,
            "affected_locations": [loc.to_dict() for loc in self.affected_locations],
            "trace": [step.to_dict() for step in self.trace],
            "trust_boundary": self.trust_boundary,
            "entry_point": self.entry_point,
            "affected_principal_or_resource": self.affected_principal_or_resource,
            "preconditions": list(self.preconditions),
            "scenario_summary": self.scenario_summary,
            "reproduction_steps": list(self.reproduction_steps),
            "security_impact": self.security_impact,
            "evidence_refs": list(self.evidence_refs),
            "discovery_provenance": self.discovery_provenance.to_dict(),
            "verification_provenance": (
                None
                if self.verification_provenance is None
                else self.verification_provenance.to_dict()
            ),
            "verification_status": self.verification_status,
            "lifecycle_state": self.lifecycle_state,
            "confidence": {
                "score": self.confidence_score,
                "reason": self.confidence_reason,
                "uncertainty_notes": list(self.uncertainty_notes),
            },
            "severity": None if self.severity is None else self.severity.to_dict(),
            "root_cause": self.root_cause,
            "claimed_root_cause": self.claimed_root_cause,
            "remediation": (
                None if self.remediation is None else self.remediation.to_dict()
            ),
            "unresolved_blockers": list(self.unresolved_blockers),
            "validation_plan": (
                None if self.validation_plan is None else dict(self.validation_plan)
            ),
            "rejection_reason": self.rejection_reason,
            "related_rules": list(self.related_rules),
            "related_requirements": list(self.related_requirements),
            "commit_sha": self.commit_sha,
            "first_seen_run": self.first_seen_run,
            "last_seen_run": self.last_seen_run,
            "first_seen_commit": self.first_seen_commit,
            "last_seen_commit": self.last_seen_commit,
            "state_history": [dict(entry) for entry in self.state_history],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SecurityFinding:
        conf = payload["confidence"]
        return cls(
            finding_id=str(payload["finding_id"]),
            fingerprint=str(payload["fingerprint"]),
            title=str(payload["title"]),
            description=str(payload["description"]),
            attack_class=str(payload["attack_class"]),
            component=str(payload["component"]),
            affected_locations=[
                LocationRef.from_dict(item) for item in payload["affected_locations"]
            ],
            trace=[TraceStep.from_dict(item) for item in payload["trace"]],
            trust_boundary=str(payload["trust_boundary"]),
            entry_point=str(payload["entry_point"]),
            affected_principal_or_resource=str(payload["affected_principal_or_resource"]),
            preconditions=[str(p) for p in payload["preconditions"]],
            scenario_summary=str(payload["scenario_summary"]),
            reproduction_steps=[str(s) for s in payload["reproduction_steps"]],
            security_impact=str(payload["security_impact"]),
            evidence_refs=[str(e) for e in payload["evidence_refs"]],
            discovery_provenance=DiscoveryProvenance.from_dict(
                payload["discovery_provenance"]
            ),
            verification_provenance=(
                None
                if payload.get("verification_provenance") is None
                else VerificationProvenance.from_dict(payload["verification_provenance"])
            ),
            verification_status=str(payload["verification_status"]),
            lifecycle_state=str(payload["lifecycle_state"]),
            confidence_score=str(conf["score"]),
            confidence_reason=str(conf["reason"]),
            uncertainty_notes=[str(n) for n in conf["uncertainty_notes"]],
            severity=(
                None
                if payload.get("severity") is None
                else SeverityAssessment.from_dict(payload["severity"])
            ),
            root_cause=(
                None if payload.get("root_cause") is None else str(payload["root_cause"])
            ),
            claimed_root_cause=(
                None
                if payload.get("claimed_root_cause") is None
                else str(payload["claimed_root_cause"])
            ),
            remediation=(
                None
                if payload.get("remediation") is None
                else RemediationGuidance.from_dict(payload["remediation"])
            ),
            unresolved_blockers=[str(b) for b in payload["unresolved_blockers"]],
            validation_plan=(
                None
                if payload.get("validation_plan") is None
                else {str(k): str(v) for k, v in payload["validation_plan"].items()}
            ),
            rejection_reason=(
                None
                if payload.get("rejection_reason") is None
                else str(payload["rejection_reason"])
            ),
            related_rules=[str(r) for r in payload["related_rules"]],
            related_requirements=[str(r) for r in payload["related_requirements"]],
            commit_sha=str(payload["commit_sha"]),
            first_seen_run=str(payload["first_seen_run"]),
            last_seen_run=str(payload["last_seen_run"]),
            first_seen_commit=str(payload["first_seen_commit"]),
            last_seen_commit=str(payload["last_seen_commit"]),
            state_history=[
                {str(k): str(v) for k, v in item.items()}
                for item in payload["state_history"]
            ],
        )


@dataclass
class FindingsCollection:
    """Sorted, deduplicated collection of security finding records for an audit run."""

    audit_run_id: str
    commit_sha: str
    records: list[SecurityFinding] = field(default_factory=list)

    def deduplicate_and_sort(self) -> None:
        """Consolidate duplicate fingerprints keeping the richest trace, sorted by fingerprint."""
        by_fp: dict[str, SecurityFinding] = {}
        for item in self.records:
            existing = by_fp.get(item.fingerprint)
            if existing is None or len(item.trace) > len(existing.trace):
                by_fp[item.fingerprint] = item
        self.records = [by_fp[fp] for fp in sorted(by_fp)]

    def to_dict(self) -> dict[str, Any]:
        self.deduplicate_and_sort()
        return {
            "schema_version": FINDINGS_SCHEMA_VERSION,
            "audit_run_id": self.audit_run_id,
            "commit_sha": self.commit_sha,
            "records": [r.to_dict() for r in self.records],
        }

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".findings-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        temp_path.replace(path)
        return path

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FindingsCollection:
        return cls(
            audit_run_id=str(payload["audit_run_id"]),
            commit_sha=str(payload["commit_sha"]),
            records=[SecurityFinding.from_dict(r) for r in payload["records"]],
        )

    @classmethod
    def load(cls, path: Path) -> FindingsCollection:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(raw)
