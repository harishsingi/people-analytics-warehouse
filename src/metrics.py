"""Attrition and headcount metrics over validated employee records.

Rates are computed, never asserted: headcount is the number of records
in scope, exits the number with ``exited == 1``, and the attrition rate
is exits / headcount. A department with no employees has a rate of
``None`` (not zero), so an empty slice cannot be mistaken for no attrition.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from .models import EmployeeRecord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AttritionMetrics:
    """Headcount, exits and attrition rate for one slice (dept or total)."""

    scope: str
    headcount: int
    exits: int

    @property
    def attrition_rate(self) -> float | None:
        """Exits / headcount, or None when headcount is zero."""
        if self.headcount == 0:
            return None
        return self.exits / self.headcount


def attrition_by_department(
        records: Iterable[EmployeeRecord]) -> dict[str, AttritionMetrics]:
    """Compute headcount / exits / rate per department, plus an OVERALL row."""
    by_dept: dict[str, list[int]] = {}  # dept -> [headcount, exits]
    total_headcount = total_exits = 0
    for record in records:
        headcount, exits = by_dept.setdefault(record.department, [0, 0])
        by_dept[record.department] = [headcount + 1, exits + record.exited]
        total_headcount += 1
        total_exits += record.exited

    result = {
        dept: AttritionMetrics(scope=dept, headcount=counts[0], exits=counts[1])
        for dept, counts in sorted(by_dept.items())
    }
    result["OVERALL"] = AttritionMetrics(scope="OVERALL",
                                         headcount=total_headcount,
                                         exits=total_exits)
    logger.info("attrition computed for %d departments, %d employees, "
                "%d exits", len(by_dept), total_headcount, total_exits)
    return result
