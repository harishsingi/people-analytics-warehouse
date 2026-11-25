"""Deterministic synthetic employee generator.

All data is invented for this portfolio demo: employee ids, departments,
tenure and exit flags are drawn from a seeded ``random.Random`` instance,
so the same seed always produces the same dataset. There is no real
employee data, no company data, and no external source to call, so there
is no network access, no retry logic and no credential to manage here.
"""

from __future__ import annotations

import logging
import random

from .config import WarehouseConfig
from .models import EmployeeRecord

logger = logging.getLogger(__name__)


def generate_employees(config: WarehouseConfig,
                       seed: int | None = None) -> list[EmployeeRecord]:
    """Generate ``config.employee_count`` synthetic employees.

    Deterministic: two calls with the same seed return identical lists,
    which is what makes loads idempotent and tests reproducible.
    """
    rng = random.Random(config.seed if seed is None else seed)
    employees: list[EmployeeRecord] = []
    for index in range(1, config.employee_count + 1):
        department = rng.choice(list(config.departments))
        employees.append(EmployeeRecord(
            employee_id=f"E{index:04d}",
            department=department,
            tenure_months=rng.randint(1, config.max_tenure_months),
            exited=1 if rng.random() < config.exit_probability else 0,
            # One synthetic manager per department, rotating 1..3.
            manager_id=f"{department}-MGR-{(index % 3) + 1}",
        ))
    logger.info("generated %d synthetic employees (seed=%d)",
                len(employees), config.seed if seed is None else seed)
    return employees
