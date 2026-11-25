"""Tests for src/validation.py."""

import pytest

from src.errors import ValidationError
from src.validation import validate_record, validate_records


def test_validate_record_happy_path():
    record = validate_record(
        {"employee_id": "E0001", "department": "Eng",
         "tenure_months": "12", "exited": "0"}, ("Eng", "Sales"))
    assert record.employee_id == "E0001"
    assert record.tenure_months == 12 and record.exited == 0


@pytest.mark.parametrize("raw,reason", [
    ({"department": "Eng", "tenure_months": 12, "exited": 0},
     "missing or null field: employee_id"),
    ({"employee_id": "E1", "department": "Eng", "tenure_months": 12,
      "exited": 0, "manager_id": ""}, "manager_id"),
    ({"employee_id": "E1", "department": "Legal", "tenure_months": 12,
      "exited": 0}, "unknown department"),
    ({"employee_id": "E1", "department": "Eng", "tenure_months": "abc",
      "exited": 0}, "must be an integer"),
    ({"employee_id": "E1", "department": "Eng", "tenure_months": True,
      "exited": 0}, "must be an integer"),
    ({"employee_id": "E1", "department": "Eng", "tenure_months": 12,
      "exited": 3}, "must be 0 or 1"),
])
def test_validate_record_rejects_with_reason(raw, reason):
    with pytest.raises(ValidationError, match=reason):
        validate_record(raw, ("Eng", "Sales"))


def test_validate_records_quarantines_every_bad_row(sample_raw_rows):
    result = validate_records(sample_raw_rows, ("Eng", "Sales"))
    assert result.rows_in == 8
    assert result.rows_out == 2
    assert result.rejected == 6
    reasons = " | ".join(q.reason for q in result.quarantined)
    assert "duplicate employee_id: E0001" in reasons
    assert "unknown department" in reasons
    assert "missing or null field: tenure_months" in reasons
    assert "outside 0..480" in reasons
    assert "must be 0 or 1" in reasons
    assert "non-empty string" in reasons


def test_validate_records_first_duplicate_wins():
    rows = [
        {"employee_id": "E1", "department": "Eng", "tenure_months": 1, "exited": 0},
        {"employee_id": "E1", "department": "Sales", "tenure_months": 2, "exited": 0},
    ]
    result = validate_records(rows, ("Eng", "Sales"))
    assert len(result.valid) == 1
    assert result.valid[0].department == "Eng"
    assert result.rejected == 1


def test_validate_records_empty_batch():
    result = validate_records([], ("Eng",))
    assert result.rows_in == 0 and result.rows_out == 0 and result.rejected == 0
