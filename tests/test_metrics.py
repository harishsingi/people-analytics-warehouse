"""Tests for src/metrics.py."""

import pytest

from src.metrics import attrition_by_department
from src.models import EmployeeRecord


def _records():
    return [
        EmployeeRecord("E1", "Eng", 12, 0),
        EmployeeRecord("E2", "Eng", 24, 1),
        EmployeeRecord("E3", "Eng", 36, 1),
        EmployeeRecord("E4", "Sales", 6, 0),
    ]


def test_attrition_by_department():
    metrics = attrition_by_department(_records())
    eng = metrics["Eng"]
    assert (eng.headcount, eng.exits) == (3, 2)
    assert eng.attrition_rate == pytest.approx(2 / 3)
    sales = metrics["Sales"]
    assert (sales.headcount, sales.exits) == (1, 0)
    assert sales.attrition_rate == 0.0
    overall = metrics["OVERALL"]
    assert (overall.headcount, overall.exits) == (4, 2)
    assert overall.attrition_rate == 0.5


def test_attrition_empty_input_has_none_rate():
    metrics = attrition_by_department([])
    assert metrics["OVERALL"].headcount == 0
    assert metrics["OVERALL"].attrition_rate is None


def test_attrition_all_exited_is_one():
    metrics = attrition_by_department(
        [EmployeeRecord("E1", "Eng", 1, 1), EmployeeRecord("E2", "Eng", 1, 1)])
    assert metrics["Eng"].attrition_rate == 1.0
