"""Shared fixtures for the people-analytics warehouse tests."""

import pytest

from src.config import WarehouseConfig


@pytest.fixture
def config(tmp_path):
    """Small deterministic config writing to a temp database."""
    return WarehouseConfig(seed=3, employee_count=10,
                           departments=("Eng", "Sales"),
                           exit_probability=0.25, max_tenure_months=120,
                           db_path=tmp_path / "test.db")


@pytest.fixture
def sample_raw_rows():
    """Raw rows covering the happy path plus each quarantine reason."""
    return [
        {"employee_id": "E0001", "department": "Eng",
         "tenure_months": 12, "exited": 0, "manager_id": "Eng-MGR-1"},
        {"employee_id": "E0002", "department": "Sales",
         "tenure_months": 60, "exited": 1},
        {"employee_id": "E0001", "department": "Eng",
         "tenure_months": 12, "exited": 0},          # duplicate
        {"employee_id": "E0003", "department": "Legal",
         "tenure_months": 12, "exited": 0},          # unknown department
        {"employee_id": "E0004", "department": "Eng",
         "tenure_months": None, "exited": 0},        # null tenure
        {"employee_id": "E0005", "department": "Eng",
         "tenure_months": -1, "exited": 0},          # out of range
        {"employee_id": "E0006", "department": "Eng",
         "tenure_months": 12, "exited": 2},          # bad exited flag
        {"employee_id": "", "department": "Eng",
         "tenure_months": 12, "exited": 0},          # empty id
    ]
