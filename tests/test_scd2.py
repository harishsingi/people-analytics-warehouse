"""Tests for src/scd2.py (and the thin src/scd2_demo.py wrapper)."""

import pytest

from src.errors import SCD2Error
from src.models import SCD2Row
from src.scd2 import apply_change, apply_changes
from src.scd2_demo import demo


def current_row(**overrides):
    base = {"employee_id": "E1", "department": "Eng",
            "valid_from": "2024-01-01", "manager_id": "Eng-MGR-1"}
    base.update(overrides)
    return SCD2Row(**base)


def test_no_change_returns_current_row_unchanged():
    row = current_row()
    assert apply_change(row, new_department="Eng",
                        change_date="2025-03-01") == [row]


def test_department_change_closes_and_opens():
    closed, opened = apply_change(current_row(), new_department="Data",
                                  change_date="2025-03-01")
    assert closed.is_current is False
    assert closed.valid_to.isoformat() == "2025-03-01"
    assert closed.department == "Eng"  # history preserved
    assert opened.is_current is True
    assert opened.department == "Data"
    assert opened.valid_from.isoformat() == "2025-03-01"
    assert opened.valid_to is None
    assert opened.manager_id == "Eng-MGR-1"  # unchanged attribute carried over


def test_manager_change_alone_triggers_scd2():
    closed, opened = apply_change(current_row(), new_manager_id="Eng-MGR-2",
                                  change_date="2025-03-01")
    assert closed.manager_id == "Eng-MGR-1"
    assert opened.manager_id == "Eng-MGR-2"
    assert opened.department == "Eng"


def test_change_before_valid_from_raises():
    with pytest.raises(SCD2Error, match="before valid_from"):
        apply_change(current_row(), new_department="Data",
                     change_date="2023-12-31")


def test_change_on_closed_row_raises():
    closed = SCD2Row("E1", "Eng", "2024-01-01", "2025-03-01", False)
    with pytest.raises(SCD2Error, match="current"):
        apply_change(closed, new_department="Data", change_date="2025-04-01")


def test_apply_change_is_pure():
    row = current_row()
    apply_change(row, new_department="Data", change_date="2025-03-01")
    assert row.department == "Eng" and row.is_current is True


def test_apply_changes_batch():
    rows = [current_row(), current_row(employee_id="E2", department="Sales")]
    updated = apply_changes(rows, [
        ("E1", "Data", None, "2025-03-01"),
        ("E2", "Sales", None, "2025-03-01"),  # no-op: same department
    ])
    assert len(updated) == 3  # E1 closed+opened, E2 unchanged
    assert sum(1 for r in updated if r.is_current) == 2
    assert {r.employee_id for r in updated if not r.is_current} == {"E1"}


def test_apply_changes_unknown_employee_raises():
    with pytest.raises(SCD2Error, match="no current row"):
        apply_changes([current_row()], [("E9", "Data", None, "2025-03-01")])


def test_apply_changes_duplicate_current_rows_raise():
    rows = [current_row(), current_row(valid_from="2024-06-01")]
    with pytest.raises(SCD2Error, match="multiple current rows"):
        apply_changes(rows, [("E1", "Data", None, "2025-03-01")])


def test_demo_matches_original_example():
    closed, opened = demo()
    assert closed.department == "Eng" and opened.department == "Data"
    assert opened.valid_from.isoformat() == "2025-03-01"
