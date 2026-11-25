"""Load synthetic employees into the warehouse (CLI entry point).

Thin wrapper: config -> generate -> validate -> load. All logic lives
in src.synthetic / src.validation / src.loader; this module only parses
arguments, wires the steps together, and logs the row counts.

Run from the repo root::

    python -m src.load_synthetic [--db PATH] [--rows N] [--seed N]

Re-running is safe (idempotent): the bronze and dim tables are rebuilt
from the same deterministic seed, so counts do not grow.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import replace
from pathlib import Path

from .config import load_config
from .loader import load_warehouse
from .logging_config import get_logger, setup_logging
from .synthetic import generate_employees
from .validation import validate_records

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> dict[str, int]:
    """Run the load and return per-table row counts."""
    setup_logging(os.environ.get("PEOPLE_ANALYTICS_LOG_LEVEL", "INFO"))
    parser = argparse.ArgumentParser(
        description="Load synthetic employees into people.db (SQLite).")
    parser.add_argument("--db", help="SQLite database path (overrides config)")
    parser.add_argument("--rows", type=int,
                        help="number of synthetic employees (overrides config)")
    parser.add_argument("--seed", type=int,
                        help="synthetic-data seed (overrides config)")
    args = parser.parse_args(argv)

    config = load_config()
    if args.db:
        config = replace(config, db_path=Path(args.db))
    if args.rows is not None:
        config = replace(config, employee_count=args.rows)
    if args.seed is not None:
        config = replace(config, seed=args.seed)

    employees = generate_employees(config)
    # Generated records are valid by construction; validation still runs
    # so a future generator regression is caught here, not downstream.
    result = validate_records(
        [dict(zip(("employee_id", "department", "tenure_months", "exited",
                   "manager_id"), record.to_row())) for record in employees],
        config.departments)
    if result.rejected:
        logger.warning("%d generated records failed validation and were "
                       "quarantined", result.rejected)
    counts = load_warehouse(config, result.valid, result.quarantined)
    logger.info("loaded %d synthetic employees into %s",
                len(result.valid), config.resolved_db_path)
    return counts


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
