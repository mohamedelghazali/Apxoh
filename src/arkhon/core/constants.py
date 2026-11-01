"""ARKHON package module."""
from __future__ import annotations
from enum import StrEnum
class Status(StrEnum):
    PASS="PASS"
    FAIL="FAIL"
    BLOCKED="BLOCKED"
    NOT_APPLICABLE="NOT_APPLICABLE"
    ACCEPTED_RISK="ACCEPTED_RISK"
MATURITY_STATES=("planned","detected","analyzable","verified")
