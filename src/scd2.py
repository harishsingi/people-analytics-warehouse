"""SCD Type 2 logic for dim_employee.

A change to a tracked attribute (department and/or manager_id) closes
the current row and opens a new one; anything else leaves the row
untouched. The convention (shared with sql/dim_employee.sql):

* ``valid_from`` is inclusive, ``valid_to`` is the change date.
* A current row has ``valid_to=None`` and ``is_current=True``.
* The closed row keeps the old values; the new row starts at the
  change date, so history is never overwritten.

``apply_change`` is pure: it returns new rows and mutates nothing, so a
caller can validate the result before writing it to the warehouse.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import date

from .errors import SCD2Error
from .models import SCD2Row

logger = logging.getLogger(__name__)


def apply_change(current: SCD2Row,
                 new_department: str | None = None,
                 new_manager_id: str | None = None,
                 change_date: date | str | None = None) -> list[SCD2Row]:
    """Apply one change to the current SCD2 row for an employee.

    Args:
        current: the current (open) row; must have ``is_current=True``.
        new_department: new department, or None to keep the current one.
        new_manager_id: new manager, or None to keep the current one.
        change_date: date the change takes effect; defaults to today.
            Must be on or after ``current.valid_from``.

    Returns:
        ``[current]`` when nothing tracked changed, otherwise
        ``[closed_row, opened_row]``.
    """
    if not current.is_current:
        raise SCD2Error("apply_change requires the current (open) row")
    if change_date is None:
        effective = date.today()
    elif isinstance(change_date, date):
        effective = change_date
    else:
        effective = date.fromisoformat(str(change_date))
    if effective < current.valid_from:
        raise SCD2Error(
            f"change_date {effective} is before valid_from {current.valid_from}")

    next_department = new_department if new_department is not None else current.department
    next_manager = new_manager_id if new_manager_id is not None else current.manager_id
    if next_department == current.department and next_manager == current.manager_id:
        logger.debug("no tracked change for %s on %s", current.employee_id, effective)
        return [current]

    closed = SCD2Row(employee_id=current.employee_id,
                     department=current.department,
                     manager_id=current.manager_id,
                     valid_from=current.valid_from,
                     valid_to=effective,
                     is_current=False)
    opened = SCD2Row(employee_id=current.employee_id,
                     department=next_department,
                     manager_id=next_manager,
                     valid_from=effective,
                     valid_to=None,
                     is_current=True)
    logger.info("SCD2 change for %s: %s -> %s on %s",
                current.employee_id, current.department, next_department, effective)
    return [closed, opened]


def apply_changes(rows: list[SCD2Row],
                  changes: Iterable[tuple[str, str | None, str | None, date | str]]
                  ) -> list[SCD2Row]:
    """Apply a batch of changes to a dim_employee snapshot.

    Each change is ``(employee_id, new_department, new_manager_id,
    change_date)``. Employees with no current row, or with more than one
    current row, raise :class:`SCD2Error` instead of guessing.
    """
    by_employee: dict[str, list[SCD2Row]] = {}
    for row in rows:
        by_employee.setdefault(row.employee_id, []).append(row)

    result = list(rows)
    for employee_id, new_dept, new_manager, change_date in changes:
        current_rows = [r for r in by_employee.get(employee_id, [])
                        if r.is_current]
        if not current_rows:
            raise SCD2Error(f"no current row for employee {employee_id}")
        if len(current_rows) > 1:
            raise SCD2Error(
                f"multiple current rows for employee {employee_id}")
        updated = apply_change(current_rows[0], new_dept, new_manager, change_date)
        if len(updated) == 2:  # a real change: replace the current row
            result = [r for r in result if r is not current_rows[0]]
            result.extend(updated)
            by_employee[employee_id] = [
                r for r in by_employee[employee_id] if r is not current_rows[0]
            ] + updated
    return result
