"""Typed record models with validation in ``__post_init__``.

These are the in-memory shapes every other module agrees on. Nothing
here touches a database or a file, so the models are trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .constants import MAX_TENURE_MONTHS, MIN_TENURE_MONTHS
from .errors import ValidationError


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError(f"invalid ISO date: {value!r}") from exc


@dataclass(frozen=True)
class EmployeeRecord:
    """One synthetic employee in the bronze layer.

    ``exited`` is 0 (still employed) or 1 (left). ``manager_id`` may be
    None for employees with no manager recorded in the synthetic source.
    """

    employee_id: str
    department: str
    tenure_months: int
    exited: int = 0
    manager_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.employee_id, str) or not self.employee_id.strip():
            raise ValidationError("employee_id must be a non-empty string")
        if not isinstance(self.department, str) or not self.department.strip():
            raise ValidationError("department must be a non-empty string")
        if not isinstance(self.tenure_months, int) or isinstance(self.tenure_months, bool):
            raise ValidationError("tenure_months must be an integer")
        if not MIN_TENURE_MONTHS <= self.tenure_months <= MAX_TENURE_MONTHS:
            raise ValidationError(
                f"tenure_months {self.tenure_months} outside "
                f"{MIN_TENURE_MONTHS}..{MAX_TENURE_MONTHS}")
        if self.exited not in (0, 1):
            raise ValidationError(f"exited must be 0 or 1, got {self.exited!r}")

    def to_row(self) -> tuple[str, str, int, int, str | None]:
        """Tuple in bronze_employees column order."""
        return (self.employee_id, self.department, self.tenure_months,
                self.exited, self.manager_id)


@dataclass(frozen=True)
class SCD2Row:
    """One version of an employee in dim_employee (SCD Type 2).

    Invariants enforced here, not left to callers:
    * ``valid_to`` (when present) is on or after ``valid_from``.
    * A current row (``is_current=True``) has ``valid_to is None``.
    * A closed row (``is_current=False``) has a ``valid_to`` date.
    """

    employee_id: str
    department: str
    valid_from: date
    valid_to: date | None = None
    is_current: bool = True
    manager_id: str | None = None

    def __post_init__(self) -> None:
        # Accept ISO strings so rows built from dicts/SQL still validate.
        object.__setattr__(self, "valid_from", _parse_date(self.valid_from))
        object.__setattr__(self, "valid_to",
                           None if self.valid_to is None
                           else _parse_date(self.valid_to))
        if not isinstance(self.employee_id, str) or not self.employee_id.strip():
            raise ValidationError("employee_id must be a non-empty string")
        if not isinstance(self.department, str) or not self.department.strip():
            raise ValidationError("department must be a non-empty string")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValidationError(
                f"valid_to {self.valid_to} is before valid_from {self.valid_from}")
        if self.is_current and self.valid_to is not None:
            raise ValidationError("a current row must have valid_to=None")
        if not self.is_current and self.valid_to is None:
            raise ValidationError("a closed row must have a valid_to date")

    def to_dict(self) -> dict:
        """Plain dict (dates as ISO strings) for display / tests."""
        return {
            "employee_id": self.employee_id,
            "department": self.department,
            "manager_id": self.manager_id,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_current": 1 if self.is_current else 0,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SCD2Row":
        """Build from a dict as produced by :meth:`to_dict`."""
        return cls(
            employee_id=data["employee_id"],
            department=data["department"],
            manager_id=data.get("manager_id"),
            valid_from=data["valid_from"],
            valid_to=data.get("valid_to"),
            is_current=bool(data.get("is_current", 1)),
        )


@dataclass
class QuarantinedRecord:
    """A raw record rejected by validation, kept for inspection.

    Bad rows are never silently dropped: they land in
    ``quarantine_employees`` with the reason, so a load can be audited.
    """

    raw: dict
    reason: str

    def to_row(self) -> tuple[str, str]:
        import json

        return (json.dumps(self.raw, default=str, sort_keys=True), self.reason)


@dataclass
class ValidationResult:
    """Outcome of validating a batch of raw records."""

    valid: list[EmployeeRecord] = field(default_factory=list)
    quarantined: list[QuarantinedRecord] = field(default_factory=list)

    @property
    def rows_in(self) -> int:
        return len(self.valid) + len(self.quarantined)

    @property
    def rows_out(self) -> int:
        return len(self.valid)

    @property
    def rejected(self) -> int:
        return len(self.quarantined)
