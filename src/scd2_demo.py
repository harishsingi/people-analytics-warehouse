"""SCD2 demo: close the current row and open a new one on a change.

Thin demo over :mod:`src.scd2`. Run from the repo root::

    python -m src.scd2_demo
"""

from __future__ import annotations

import logging

from .logging_config import get_logger, setup_logging
from .models import SCD2Row
from .scd2 import apply_change

logger = get_logger(__name__)


def demo() -> list[SCD2Row]:
    """Run the canonical example: E1 moves Eng -> Data on 2025-03-01."""
    current = SCD2Row(employee_id="E1", department="Eng",
                      valid_from="2024-01-01")
    result = apply_change(current, new_department="Data",
                          change_date="2025-03-01")
    for row in result:
        logger.info("%s", row.to_dict())
    return result


if __name__ == "__main__":
    setup_logging()
    demo()
