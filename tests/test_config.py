"""Tests for src/config.py."""

import pytest

from src.config import WarehouseConfig, load_config
from src.errors import ConfigurationError


def test_load_config_defaults_match_config_yaml():
    config = load_config()
    assert config.seed == 3
    assert config.employee_count == 500
    assert config.departments == ("Eng", "Sales", "Ops", "Finance")
    assert config.exit_probability == 0.14
    assert config.max_tenure_months == 120
    assert config.db_filename == "people.db"
    assert config.scd2_tracked_attributes == ("department", "manager_id")


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "nope.yaml")


def test_load_config_invalid_yaml_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("seed: [unclosed\n")
    with pytest.raises(ConfigurationError, match="not valid YAML"):
        load_config(bad)


def test_load_config_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("PEOPLE_ANALYTICS_SEED", "42")
    monkeypatch.setenv("PEOPLE_ANALYTICS_ROWS", "7")
    monkeypatch.setenv("PEOPLE_ANALYTICS_DB", str(tmp_path / "env.db"))
    config = load_config()
    assert config.seed == 42
    assert config.employee_count == 7
    assert config.resolved_db_path == tmp_path / "env.db"


def test_load_config_bad_env_int_raises(monkeypatch):
    monkeypatch.setenv("PEOPLE_ANALYTICS_SEED", "not-a-number")
    with pytest.raises(ConfigurationError, match="must be an integer"):
        load_config()


def test_config_rejects_bad_values():
    with pytest.raises(ConfigurationError):
        WarehouseConfig(employee_count=-1)
    with pytest.raises(ConfigurationError):
        WarehouseConfig(departments=())
    with pytest.raises(ConfigurationError):
        WarehouseConfig(exit_probability=1.5)


def test_resolved_db_path_defaults_to_repo_root():
    config = WarehouseConfig()
    assert config.resolved_db_path.name == "people.db"
    assert config.resolved_db_path.is_absolute()
    assert config.sql_dir.name == "sql"
    assert config.sql_dir.is_dir()
