"""SQLite loading: bronze, quarantine, and the initial dim_employee.

Idempotency: every load runs inside one transaction and first clears
the target table, so re-running the same (deterministic, seeded) load
produces the same rows instead of duplicating them. The DDL lives in
``sql/*.sql`` and is the single source of truth; this module reads those
files rather than duplicating their statements.

No network calls happen here, so there is nothing to retry. A database
failure is wrapped in :class:`LoadError` with the original error chained.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from .config import WarehouseConfig
from .constants import (
    TABLE_BRONZE_EMPLOYEES,
    TABLE_DIM_EMPLOYEE,
    TABLE_QUARANTINE_EMPLOYEES,
)
from .errors import LoadError
from .models import EmployeeRecord, QuarantinedRecord, SCD2Row

logger = logging.getLogger(__name__)


@contextmanager
def connect(db_path: Path | str):
    """Yield a SQLite connection; commit on success, roll back on error."""
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _read_sql(sql_dir: Path, filename: str) -> str:
    path = sql_dir / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LoadError(f"SQL file not found: {path}") from exc


def init_schema(conn: sqlite3.Connection, sql_dir: Path) -> None:
    """Create bronze, quarantine, dim and fact tables from sql/*.sql."""
    for filename in ("bronze_employees.sql", "dim_employee.sql",
                     "fact_employee_month.sql"):
        try:
            conn.executescript(_read_sql(sql_dir, filename))
        except sqlite3.Error as exc:
            raise LoadError(f"failed applying {filename}: {exc}") from exc
    logger.info("schema initialised from %s", sql_dir)


def load_employees(conn: sqlite3.Connection,
                   records: Iterable[EmployeeRecord]) -> int:
    """Replace the bronze table contents with ``records`` (idempotent).

    Returns the number of rows inserted.
    """
    rows = [r.to_row() for r in records]
    try:
        conn.execute(f"DELETE FROM {TABLE_BRONZE_EMPLOYEES}")
        conn.executemany(
            f"INSERT INTO {TABLE_BRONZE_EMPLOYEES} "
            "(employee_id, department, tenure_months, exited, manager_id) "
            "VALUES (?, ?, ?, ?, ?)", rows)
    except sqlite3.Error as exc:
        raise LoadError(f"failed loading {TABLE_BRONZE_EMPLOYEES}: {exc}") from exc
    logger.info("bronze load: %d rows inserted into %s",
                len(rows), TABLE_BRONZE_EMPLOYEES)
    return len(rows)


def load_quarantine(conn: sqlite3.Connection,
                    quarantined: Iterable[QuarantinedRecord]) -> int:
    """Store rejected records for audit. Returns rows inserted."""
    rows = [q.to_row() for q in quarantined]
    try:
        conn.execute(f"DELETE FROM {TABLE_QUARANTINE_EMPLOYEES}")
        conn.executemany(
            f"INSERT INTO {TABLE_QUARANTINE_EMPLOYEES} (raw_json, reason) "
            "VALUES (?, ?)", rows)
    except sqlite3.Error as exc:
        raise LoadError(f"failed loading {TABLE_QUARANTINE_EMPLOYEES}: {exc}") from exc
    if rows:
        logger.warning("quarantine load: %d rejected records stored", len(rows))
    return len(rows)


def build_dim_employee(conn: sqlite3.Connection,
                       effective_date: date | None = None) -> int:
    """Build the initial dim_employee: one current SCD2 row per employee.

    Idempotent (clears dim_employee first). The initial row's valid_from
    is the load date; later changes go through :mod:`src.scd2`.
    """
    effective = effective_date or date.today()
    try:
        conn.execute(f"DELETE FROM {TABLE_DIM_EMPLOYEE}")
        conn.execute(
            f"INSERT INTO {TABLE_DIM_EMPLOYEE} "
            "(employee_id, department, manager_id, valid_from, valid_to, is_current) "
            f"SELECT employee_id, department, manager_id, ?, NULL, 1 "
            f"FROM {TABLE_BRONZE_EMPLOYEES}",
            (effective.isoformat(),))
        count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_DIM_EMPLOYEE}").fetchone()[0]
    except sqlite3.Error as exc:
        raise LoadError(f"failed building {TABLE_DIM_EMPLOYEE}: {exc}") from exc
    logger.info("dim_employee built: %d current rows (valid_from=%s)",
                count, effective)
    return count


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Row counts per table, for load metrics / reconciliation."""
    counts = {}
    for table in (TABLE_BRONZE_EMPLOYEES, TABLE_QUARANTINE_EMPLOYEES,
                  TABLE_DIM_EMPLOYEE):
        counts[table] = conn.execute(
            f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def load_warehouse(config: WarehouseConfig,
                   records: list[EmployeeRecord],
                   quarantined: list[QuarantinedRecord] | None = None,
                   effective_date: date | None = None) -> dict[str, int]:
    """Full load: schema + bronze + quarantine + dim. Returns row counts.

    This is the function the CLI calls; it is also the seam tests use to
    verify an end-to-end load against a temporary database.
    """
    with connect(config.resolved_db_path) as conn:
        init_schema(conn, config.sql_dir)
        inserted = load_employees(conn, records)
        rejected = load_quarantine(conn, quarantined or [])
        dim_rows = build_dim_employee(conn, effective_date)
        counts = row_counts(conn)
    logger.info("load complete: bronze=%d quarantined=%d dim=%d "
                "(inserted=%d rejected=%d)",
                counts[TABLE_BRONZE_EMPLOYEES],
                counts[TABLE_QUARANTINE_EMPLOYEES],
                counts[TABLE_DIM_EMPLOYEE], inserted, rejected)
    return counts


def fetch_scd2_rows(conn: sqlite3.Connection) -> list[SCD2Row]:
    """Read dim_employee back as validated SCD2Row objects."""
    cursor = conn.execute(
        f"SELECT employee_id, department, manager_id, valid_from, valid_to, "
        f"is_current FROM {TABLE_DIM_EMPLOYEE} ORDER BY employee_id, valid_from")
    return [SCD2Row(employee_id=row[0], department=row[1], manager_id=row[2],
                    valid_from=row[3], valid_to=row[4],
                    is_current=bool(row[5])) for row in cursor]
