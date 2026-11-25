"""Tests for src/models.py and src/errors.py."""

import pytest

from src.errors import (
    ConfigurationError,
    LoadError,
    PeopleAnalyticsError,
    SCD2Error,
    ValidationError,
)
from src.models import EmployeeRecord, SCD2Row, ValidationResult


def test_error_hierarchy():
    for exc in (ConfigurationError, ValidationError, LoadError, SCD2Error):
        assert issubclass(exc, PeopleAnalyticsError)


def test_employee_record_valid():
    record = EmployeeRecord("E0001", "Eng", 12, 0, "Eng-MGR-1")
    assert record.to_row() == ("E0001", "Eng", 12, 0, "Eng-MGR-1")


@pytest.mark.parametrize("kwargs", [
    {"employee_id": ""},
    {"employee_id": "   "},
    {"department": ""},
    {"tenure_months": -1},
    {"tenure_months": 481},
    {"tenure_months": True},
    {"tenure_months": "12"},
    {"exited": 2},
    {"exited": -1},
])
def test_employee_record_rejects_bad_values(kwargs):
    base = {"employee_id": "E0001", "department": "Eng",
            "tenure_months": 12, "exited": 0}
    base.update(kwargs)
    with pytest.raises(ValidationError):
        EmployeeRecord(**base)


def test_scd2_row_current_and_closed_invariants():
    current = SCD2Row("E1", "Eng", "2024-01-01")
    assert current.is_current and current.valid_to is None
    closed = SCD2Row("E1", "Eng", "2024-01-01", "2025-03-01", False)
    assert not closed.is_current
    assert closed.to_dict()["valid_to"] == "2025-03-01"


@pytest.mark.parametrize("kwargs", [
    {"valid_to": "2023-12-31"},                    # before valid_from
    {"valid_to": "2025-03-01", "is_current": True},  # current with valid_to
    {"valid_to": None, "is_current": False},         # closed without valid_to
    {"valid_from": "not-a-date"},
])
def test_scd2_row_rejects_inconsistent_dates(kwargs):
    base = {"employee_id": "E1", "department": "Eng",
            "valid_from": "2024-01-01"}
    base.update(kwargs)
    with pytest.raises(ValidationError):
        SCD2Row(**base)


def test_scd2_row_round_trips_through_dict():
    row = SCD2Row("E1", "Eng", "2024-01-01", manager_id="Eng-MGR-1")
    assert SCD2Row.from_dict(row.to_dict()) == row


def test_validation_result_counts():
    result = ValidationResult(
        valid=[EmployeeRecord("E1", "Eng", 1, 0)],
        quarantined=[])
    assert result.rows_in == 1 and result.rows_out == 1 and result.rejected == 0
