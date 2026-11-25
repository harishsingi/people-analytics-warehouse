"""Row- and column-level access controls (in-memory enforcement).

This is the code counterpart of docs/access_controls.md. It operates on
plain dict rows so it can sit in front of any query result:

* Row level: a role may only see rows whose ``department`` is in its
  allowed set (``None`` means all departments).
* Column level: fields listed in ``SENSITIVE_FIELDS`` are replaced with
  ``***`` unless the role is explicitly approved for them.

The default role table is intentionally conservative: only ``hr_admin``
sees sensitive fields, and ``manager`` sees only their own department.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping

from .constants import MASKED_VALUE

logger = logging.getLogger(__name__)

# Fields that are masked by default. The synthetic dataset has no real
# compensation or identifier data; these names are the policy's field
# list, applied whenever a row carries them.
SENSITIVE_FIELDS = ("compensation_band", "national_id", "salary")

# role -> (allowed departments or None for all, sensitive fields allowed)
ROLE_POLICY: dict[str, tuple[set[str] | None, set[str]]] = {
    "hr_admin": (None, set(SENSITIVE_FIELDS)),
    "people_analyst": (None, set()),
    "manager": (None, set()),  # departments narrowed per-manager at call time
    "executive": (None, set()),
}


def allowed_departments(role: str,
                        own_departments: Iterable[str] | None = None) -> set[str] | None:
    """Departments a role may see. Managers are restricted to their own."""
    if role not in ROLE_POLICY:
        raise ValueError(f"unknown role: {role!r}")
    if role == "manager":
        if not own_departments:
            raise ValueError("manager role requires own_departments")
        return set(own_departments)
    return ROLE_POLICY[role][0]


def filter_by_department(rows: Iterable[Mapping],
                         departments: set[str] | None) -> list[Mapping]:
    """Row-level filter: keep rows whose department is allowed (None = all)."""
    rows = list(rows)
    if departments is None:
        return rows
    kept = [row for row in rows if row.get("department") in departments]
    logger.debug("row filter: %d of %d rows visible", len(kept), len(rows))
    return kept


def mask_sensitive(row: Mapping, role: str) -> dict:
    """Column-level masking: replace sensitive fields with *** unless allowed."""
    if role not in ROLE_POLICY:
        raise ValueError(f"unknown role: {role!r}")
    allowed_fields = ROLE_POLICY[role][1]
    masked = dict(row)
    for field_name in SENSITIVE_FIELDS:
        if field_name in masked and field_name not in allowed_fields:
            masked[field_name] = MASKED_VALUE
    return masked


def apply_access(rows: Iterable[Mapping], role: str,
                 own_departments: Iterable[str] | None = None) -> list[dict]:
    """Apply row filter then column masking for a role. Returns new dicts."""
    departments = allowed_departments(role, own_departments)
    visible = filter_by_department(rows, departments)
    result = [mask_sensitive(row, role) for row in visible]
    logger.info("access applied for role=%s: %d rows returned",
                role, len(result))
    return result
