"""Exception policy: approve, expire, and revoke exceptions to blocking rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from arkhon.core.errors import GovernanceError
from arkhon.core.logging import get_logger

logger = get_logger("policies.exceptions")


@dataclass(frozen=True)
class Exception:
    exception_id: str
    rule_id: str
    scope: dict[str, Any]
    rationale: str
    owner: str
    approver: str
    approved_at: str
    expires_at: str
    compensating_control: str
    status: str = "active"

    def is_expired(self, *, now: datetime | None = None) -> bool:
        now_dt = now or datetime.now(UTC)
        expires = _parse_iso(self.expires_at)
        return now_dt > expires

    def is_active(self, *, now: datetime | None = None) -> bool:
        return self.status == "active" and not self.is_expired(now=now)


def _parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


@dataclass
class ExceptionRegistry:
    exceptions: list[Exception] = field(default_factory=list)

    def active_for_rule(self, rule_id: str, *, now: datetime | None = None) -> list[Exception]:
        return [e for e in self.exceptions if e.rule_id == rule_id and e.is_active(now=now)]

    def all_active(self, *, now: datetime | None = None) -> list[Exception]:
        return [e for e in self.exceptions if e.is_active(now=now)]


def load_exceptions(registry_path: Path) -> ExceptionRegistry:
    if not registry_path.is_file():
        return ExceptionRegistry()

    with registry_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    exceptions: list[Exception] = []
    for raw in data.get("exceptions", []):
        if not isinstance(raw, dict):
            continue
        required = (
            "exception_id",
            "rule_id",
            "scope",
            "rationale",
            "owner",
            "approver",
            "approved_at",
            "expires_at",
            "compensating_control",
        )
        missing = [k for k in required if k not in raw]
        if missing:
            logger.warning("skipping malformed exception: missing %s", missing)
            continue
        try:
            exceptions.append(
                Exception(
                    exception_id=str(raw["exception_id"]),
                    rule_id=str(raw["rule_id"]),
                    scope=raw["scope"],
                    rationale=str(raw["rationale"]),
                    owner=str(raw["owner"]),
                    approver=str(raw["approver"]),
                    approved_at=str(raw["approved_at"]),
                    expires_at=str(raw["expires_at"]),
                    compensating_control=str(raw["compensating_control"]),
                    status=str(raw.get("status", "active")),
                )
            )
        except (KeyError, ValueError) as exc:
            logger.warning("skipping exception due to error: %s", exc)

    return ExceptionRegistry(exceptions=exceptions)


def add_exception(registry_path: Path, exception: Exception) -> None:
    data: dict[str, Any] = {"exceptions": []}
    if registry_path.is_file():
        with registry_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {"exceptions": []}
        if "exceptions" not in data:
            data["exceptions"] = []

    existing_ids = {e.get("exception_id") for e in data["exceptions"] if isinstance(e, dict)}
    if exception.exception_id in existing_ids:
        raise GovernanceError(f"exception already exists: {exception.exception_id}")

    data["exceptions"].append(
        {
            "exception_id": exception.exception_id,
            "rule_id": exception.rule_id,
            "scope": exception.scope,
            "rationale": exception.rationale,
            "owner": exception.owner,
            "approver": exception.approver,
            "approved_at": exception.approved_at,
            "expires_at": exception.expires_at,
            "compensating_control": exception.compensating_control,
            "status": exception.status,
        }
    )

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    logger.info("added exception %s", exception.exception_id)
