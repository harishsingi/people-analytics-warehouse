"""Configuration: typed settings loaded from config.yaml + env overrides.

No paths are hardcoded. ``db_path`` and ``repo_root`` resolve relative to
the repository root (the parent of ``src/``) unless an absolute path or
an environment variable is given.

Environment overrides (all optional):
    PEOPLE_ANALYTICS_DB     path to the SQLite database file
    PEOPLE_ANALYTICS_SEED   synthetic-data seed (int)
    PEOPLE_ANALYTICS_ROWS   number of synthetic employees (int)
    PEOPLE_ANALYTICS_CONFIG path to an alternate config.yaml
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .errors import ConfigurationError

DEFAULT_SEED = 3
DEFAULT_EMPLOYEE_COUNT = 500
DEFAULT_DEPARTMENTS = ("Eng", "Sales", "Ops", "Finance")
DEFAULT_EXIT_PROBABILITY = 0.14
DEFAULT_MAX_TENURE_MONTHS = 120
DEFAULT_DB_FILENAME = "people.db"
DEFAULT_SCD2_TRACKED_ATTRIBUTES = ("department", "manager_id")

ENV_CONFIG = "PEOPLE_ANALYTICS_CONFIG"
ENV_DB = "PEOPLE_ANALYTICS_DB"
ENV_SEED = "PEOPLE_ANALYTICS_SEED"
ENV_ROWS = "PEOPLE_ANALYTICS_ROWS"


def repo_root() -> Path:
    """Repository root: the parent directory of the ``src`` package."""
    return Path(__file__).resolve().parent.parent


def default_config_path() -> Path:
    """Path to the bundled ``config.yaml`` (repo root)."""
    return repo_root() / "config.yaml"


@dataclass(frozen=True)
class WarehouseConfig:
    """Validated, immutable warehouse settings."""

    seed: int = DEFAULT_SEED
    employee_count: int = DEFAULT_EMPLOYEE_COUNT
    departments: tuple[str, ...] = DEFAULT_DEPARTMENTS
    exit_probability: float = DEFAULT_EXIT_PROBABILITY
    max_tenure_months: int = DEFAULT_MAX_TENURE_MONTHS
    db_filename: str = DEFAULT_DB_FILENAME
    scd2_tracked_attributes: tuple[str, ...] = DEFAULT_SCD2_TRACKED_ATTRIBUTES
    db_path: Path | None = None  # explicit override; else repo_root/db_filename

    def __post_init__(self) -> None:
        if self.employee_count < 0:
            raise ConfigurationError("employee_count must be >= 0")
        if not self.departments:
            raise ConfigurationError("departments must not be empty")
        if not 0.0 <= self.exit_probability <= 1.0:
            raise ConfigurationError("exit_probability must be between 0 and 1")
        if self.max_tenure_months < 0:
            raise ConfigurationError("max_tenure_months must be >= 0")

    @property
    def resolved_db_path(self) -> Path:
        """Absolute database path, resolved against the repo root."""
        path = self.db_path or Path(self.db_filename)
        return path if path.is_absolute() else repo_root() / path

    @property
    def sql_dir(self) -> Path:
        """Directory holding the sql/*.sql DDL and metric queries."""
        return repo_root() / "sql"


def _read_yaml(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except FileNotFoundError as exc:
        raise ConfigurationError(f"config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"config file is not valid YAML: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"config file must contain a mapping: {path}")
    return data


def _env_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from exc


def load_config(path: Path | str | None = None) -> WarehouseConfig:
    """Load settings from config.yaml, with env overrides applied last.

    Args:
        path: explicit config file; defaults to ``$PEOPLE_ANALYTICS_CONFIG``
            or the bundled ``config.yaml`` next to the repo root.
    """
    config_path = Path(path) if path is not None else Path(
        os.environ.get(ENV_CONFIG, default_config_path()))
    data = _read_yaml(config_path)

    departments = data.get("departments", list(DEFAULT_DEPARTMENTS))
    tracked = data.get("scd2_tracked_attributes",
                       list(DEFAULT_SCD2_TRACKED_ATTRIBUTES))
    db_override = os.environ.get(ENV_DB)
    seed_override = _env_int(ENV_SEED)
    rows_override = _env_int(ENV_ROWS)

    return WarehouseConfig(
        seed=seed_override if seed_override is not None
        else int(data.get("seed", DEFAULT_SEED)),
        employee_count=rows_override if rows_override is not None
        else int(data.get("employee_count", DEFAULT_EMPLOYEE_COUNT)),
        departments=tuple(str(d) for d in departments),
        exit_probability=float(data.get("exit_probability",
                                        DEFAULT_EXIT_PROBABILITY)),
        max_tenure_months=int(data.get("max_tenure_months",
                                       DEFAULT_MAX_TENURE_MONTHS)),
        db_filename=str(data.get("db_filename", DEFAULT_DB_FILENAME)),
        scd2_tracked_attributes=tuple(str(a) for a in tracked),
        db_path=Path(db_override) if db_override else None,
    )
