"""Custom exceptions for the people-analytics warehouse.

Callers catch the specific subclass they can handle; the base class is
for logging a failure without leaking internals to a user-facing message.
"""


class PeopleAnalyticsError(Exception):
    """Base class for all errors raised by this package."""


class ConfigurationError(PeopleAnalyticsError):
    """Raised when config.yaml is missing, malformed, or invalid."""


class ValidationError(PeopleAnalyticsError):
    """Raised when a single record or row fails schema validation."""


class LoadError(PeopleAnalyticsError):
    """Raised when a database load fails (wrapped DB error included)."""


class SCD2Error(PeopleAnalyticsError):
    """Raised when an SCD2 change cannot be applied (bad dates, unknown
    employee, or more than one current row for an employee)."""
