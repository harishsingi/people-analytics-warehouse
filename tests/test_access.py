"""Tests for src/access.py."""

import pytest

from src.access import allowed_departments, apply_access, mask_sensitive
from src.constants import MASKED_VALUE

ROWS = [
    {"employee_id": "E1", "department": "Eng", "salary": 90000,
     "compensation_band": "B3"},
    {"employee_id": "E2", "department": "Sales", "salary": 80000,
     "compensation_band": "B2"},
]


def test_hr_admin_sees_everything_unmasked():
    result = apply_access(ROWS, "hr_admin")
    assert len(result) == 2
    assert result[0]["salary"] == 90000


def test_people_analyst_masked_but_all_rows():
    result = apply_access(ROWS, "people_analyst")
    assert len(result) == 2
    assert result[0]["salary"] == MASKED_VALUE
    assert result[0]["compensation_band"] == MASKED_VALUE
    assert result[0]["employee_id"] == "E1"  # non-sensitive field untouched


def test_manager_restricted_to_own_departments():
    result = apply_access(ROWS, "manager", own_departments=["Eng"])
    assert len(result) == 1
    assert result[0]["department"] == "Eng"
    assert result[0]["salary"] == MASKED_VALUE


def test_manager_without_departments_raises():
    with pytest.raises(ValueError, match="own_departments"):
        allowed_departments("manager")


def test_unknown_role_raises():
    with pytest.raises(ValueError, match="unknown role"):
        apply_access(ROWS, "superuser")
    with pytest.raises(ValueError, match="unknown role"):
        mask_sensitive(ROWS[0], "superuser")


def test_apply_access_does_not_mutate_input():
    apply_access(ROWS, "people_analyst")
    assert ROWS[0]["salary"] == 90000
