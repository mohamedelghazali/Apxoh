"""ARKHON package module."""
from __future__ import annotations
class ArkhonError(Exception): pass
class ConfigurationError(ArkhonError): pass
class ValidationError(ArkhonError): pass
class VerificationBlocked(ArkhonError): pass
