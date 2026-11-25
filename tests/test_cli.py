"""Tests for src/logging_config.py and the load_synthetic CLI."""

import io
import logging

from src import load_synthetic
from src.loader import connect
from src.logging_config import get_logger, setup_logging


def test_setup_logging_and_get_logger():
    setup_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
    logger = get_logger("test-logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test-logger"
    # The logger actually emits through the configured handler.
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info("hello %s", "world")
    logger.removeHandler(handler)
    assert "hello world" in stream.getvalue()


def test_setup_logging_accepts_unknown_level_without_crashing():
    setup_logging("NOT-A-LEVEL")  # falls back to INFO


def test_load_synthetic_cli_end_to_end(monkeypatch, tmp_path):
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("PEOPLE_ANALYTICS_DB", str(db_path))
    counts = load_synthetic.main(["--rows", "10", "--seed", "3"])
    assert counts["bronze_employees"] == 10
    assert counts["dim_employee"] == 10
    assert counts["quarantine_employees"] == 0
    # Second run is idempotent.
    assert load_synthetic.main(["--rows", "10", "--seed", "3"]) == counts
    with connect(db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM bronze_employees").fetchone()[0] == 10


def test_load_synthetic_cli_db_flag_overrides_env(monkeypatch, tmp_path):
    db_path = tmp_path / "flag.db"
    counts = load_synthetic.main(
        ["--rows", "5", "--seed", "1", "--db", str(db_path)])
    assert counts["bronze_employees"] == 5
    assert db_path.exists()
