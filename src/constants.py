"""Shared constants for the people-analytics warehouse.

Nothing here is environment- or deployment-specific: paths and tunable
values live in :mod:`src.config` / ``config.yaml``. These are the stable
names the code and the SQL agree on.
"""

from __future__ import annotations

# Table names (must match sql/*.sql).
TABLE_BRONZE_EMPLOYEES = "bronze_employees"
TABLE_QUARANTINE_EMPLOYEES = "quarantine_employees"
TABLE_DIM_EMPLOYEE = "dim_employee"
TABLE_FACT_EMPLOYEE_MONTH = "fact_employee_month"

# SCD2 convention used by src/scd2.py and sql/dim_employee.sql:
# valid_from is inclusive, valid_to is the change date (the first day the
# new row is valid). A current row always has valid_to IS NULL and
# is_current = 1.
SCD2_CURRENT_FLAG = 1
SCD2_CLOSED_FLAG = 0

# Sentinel for an open-ended validity period in display/exports only.
# The database stores NULL for a current row, never this string.
OPEN_ENDED_LABEL = "9999-12-31"

# Mask shown by src/access.py for fields a role may not see.
MASKED_VALUE = "***"

# Validation bounds for synthetic employee records.
MIN_TENURE_MONTHS = 0
MAX_TENURE_MONTHS = 480  # 40 years; config.yaml uses a lower demo cap.
EXITED_VALUES = (0, 1)

# Exit probability used only when no config value is supplied.
DEFAULT_EXIT_PROBABILITY = 0.14
