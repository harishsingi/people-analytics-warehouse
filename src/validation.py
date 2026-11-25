"""Schema validation for raw employee records.

Rules (see docs/data_quality.md for the full policy):
* required fields present and non-null: employee_id, department,
  tenure_months, exited
* department must be in the configured department list
* tenure_months an integer within bounds; exited 0 or 1
* duplicate employee_id: first occurrence wins, later ones quarantined

Invalid rows are quarantined with a reason, never silently dropped and
never allowed to crash a load. A single bad row therefore cannot fail
the whole batch.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from .constants import MAX_TENURE_MONTHS, MIN_TENURE_MONTHS
from .errors import ValidationError
from .models import EmployeeRecord, QuarantinedRecord, ValidationResult

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ("employee_id", "department", "tenure_months", "exited")


def _coerce_int(value: Any, field_name: str) -> int:
    """Coerce an int-like value; bool and non-numeric strings are errors."""
    if isinstance(value, bool):
        raise ValidationError(f"{field_name} must be an integer, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise ValidationError(f"{field_name} must be an integer, got {value!r}")


def validate_record(raw: Mapping[str, Any],
                    allowed_departments: Iterable[str]) -> EmployeeRecord:
    """Validate one raw mapping and return an EmployeeRecord.

    Raises ValidationError with a human-readable reason on any failure.
    """
    for field_name in REQUIRED_FIELDS:
        if raw.get(field_name) is None:
            raise ValidationError(f"missing or null field: {field_name}")

    employee_id = raw["employee_id"]
    if not isinstance(employee_id, str) or not employee_id.strip():
        raise ValidationError("employee_id must be a non-empty string")

    department = raw["department"]
    if not isinstance(department, str) or not department.strip():
        raise ValidationError("department must be a non-empty string")
    if department not in set(allowed_departments):
        raise ValidationError(f"unknown department: {department!r}")

    tenure_months = _coerce_int(raw["tenure_months"], "tenure_months")
    if not MIN_TENURE_MONTHS <= tenure_months <= MAX_TENURE_MONTHS:
        raise ValidationError(
            f"tenure_months {tenure_months} outside "
            f"{MIN_TENURE_MONTHS}..{MAX_TENURE_MONTHS}")

    exited = _coerce_int(raw["exited"], "exited")
    if exited not in (0, 1):
        raise ValidationError(f"exited must be 0 or 1, got {exited!r}")

    manager_id = raw.get("manager_id")
    if manager_id is not None and (not isinstance(manager_id, str)
                                   or not manager_id.strip()):
        raise ValidationError("manager_id must be a non-empty string or null")

    return EmployeeRecord(employee_id=employee_id.strip(),
                          department=department,
                          tenure_months=tenure_months,
                          exited=exited,
                          manager_id=manager_id)


def validate_records(raw_rows: Iterable[Mapping[str, Any]],
                     allowed_departments: Iterable[str]) -> ValidationResult:
    """Validate a batch; return valid records plus quarantined rejects.

    Duplicate employee_ids are quarantined (first occurrence wins).
    Logs a summary: rows in, rows out, rejected count.
    """
    result = ValidationResult()
    seen_ids: set[str] = set()
    for raw in raw_rows:
        raw_dict = dict(raw)
        try:
            record = validate_record(raw_dict, allowed_departments)
        except ValidationError as exc:
            result.quarantined.append(
                QuarantinedRecord(raw=raw_dict, reason=str(exc)))
            continue
        if record.employee_id in seen_ids:
            result.quarantined.append(QuarantinedRecord(
                raw=raw_dict,
                reason=f"duplicate employee_id: {record.employee_id}"))
            continue
        seen_ids.add(record.employee_id)
        result.valid.append(record)

    logger.info("validation: %d in, %d valid, %d quarantined",
                result.rows_in, result.rows_out, result.rejected)
    return result
