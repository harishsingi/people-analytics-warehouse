"""Tests for src/loader.py (SQLite, temp databases only)."""

import sqlite3
from datetime import date

import pytest

from src.errors import LoadError
from src.loader import (
    build_dim_employee,
    connect,
    fetch_scd2_rows,
    init_schema,
    load_employees,
    load_quarantine,
    load_warehouse,
    row_counts,
)
from src.models import EmployeeRecord, QuarantinedRecord
from src.synthetic import generate_employees
from src.validation import validate_records


@pytest.fixture
def conn(config):
    with connect(config.resolved_db_path) as connection:
        init_schema(connection, config.sql_dir)
        yield connection


def test_init_schema_creates_all_tables(conn):
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"bronze_employees", "quarantine_employees", "dim_employee",
            "fact_employee_month"} <= tables


def test_load_employees_is_idempotent(conn, config):
    employees = generate_employees(config)
    assert load_employees(conn, employees) == 10
    assert load_employees(conn, employees) == 10  # re-run: no duplicates
    assert conn.execute("SELECT COUNT(*) FROM bronze_employees").fetchone()[0] == 10


def test_load_quarantine_stores_reasons(conn):
    quarantined = [QuarantinedRecord(raw={"employee_id": "E9"}, reason="bad id")]
    assert load_quarantine(conn, quarantined) == 1
    row = conn.execute(
        "SELECT raw_json, reason FROM quarantine_employees").fetchone()
    assert row[1] == "bad id" and "E9" in row[0]


def test_build_dim_employee_one_current_row_each(conn, config):
    load_employees(conn, generate_employees(config))
    assert build_dim_employee(conn, effective_date=date(2026, 11, 24)) == 10
    rows = fetch_scd2_rows(conn)
    assert len(rows) == 10
    assert all(r.is_current and r.valid_from.isoformat() == "2026-11-24"
               for r in rows)


def test_load_warehouse_end_to_end(config, sample_raw_rows):
    result = validate_records(sample_raw_rows, config.departments)
    counts = load_warehouse(config, result.valid, result.quarantined)
    assert counts["bronze_employees"] == 2
    assert counts["quarantine_employees"] == 6
    assert counts["dim_employee"] == 2
    # Idempotent: a second full load yields the same counts.
    assert load_warehouse(config, result.valid, result.quarantined) == counts


def test_row_counts_matches_tables(config):
    with connect(config.resolved_db_path) as connection:
        init_schema(connection, config.sql_dir)
        load_employees(connection, [EmployeeRecord("E1", "Eng", 5, 0)])
        assert row_counts(connection)["bronze_employees"] == 1


def test_init_schema_missing_sql_dir_raises(config, tmp_path):
    with connect(config.resolved_db_path) as connection:
        with pytest.raises(LoadError, match="SQL file not found"):
            init_schema(connection, tmp_path / "no-sql-here")


def test_connect_rolls_back_on_error(config):
    # Note: Python's sqlite3 implicitly commits DDL, so rollback is
    # verified with DML (an INSERT), not CREATE TABLE.
    with connect(config.resolved_db_path) as connection:
        init_schema(connection, config.sql_dir)
    with pytest.raises(RuntimeError):
        with connect(config.resolved_db_path) as connection:
            connection.execute(
                "INSERT INTO bronze_employees VALUES ('E1','Eng',5,0,NULL)")
            raise RuntimeError("boom")
    with sqlite3.connect(str(config.resolved_db_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM bronze_employees").fetchone()[0]
    assert count == 0
