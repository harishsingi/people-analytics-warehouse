"""Tests for src/synthetic.py."""

from dataclasses import replace

from src.synthetic import generate_employees


def test_generate_is_deterministic(config):
    first = generate_employees(config)
    second = generate_employees(config)
    assert first == second


def test_generate_different_seed_differs(config):
    assert generate_employees(config, seed=3) != generate_employees(config, seed=4)


def test_generate_respects_count_and_departments(config):
    employees = generate_employees(config)
    assert len(employees) == 10
    assert {e.employee_id for e in employees} == {f"E{i:04d}" for i in range(1, 11)}
    assert all(e.department in ("Eng", "Sales") for e in employees)
    assert all(1 <= e.tenure_months <= 120 for e in employees)
    assert all(e.exited in (0, 1) for e in employees)
    assert all(e.manager_id.startswith(e.department) for e in employees)


def test_generate_zero_rows(config):
    assert generate_employees(replace(config, employee_count=0)) == []
