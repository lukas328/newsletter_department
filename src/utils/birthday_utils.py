from __future__ import annotations

from datetime import date
from typing import List, Optional

from src.models.data_models import Birthday


def get_upcoming_birthdays(
    birthdays: List[Birthday],
    count: int = 3,
    reference_date: Optional[date] = None,
) -> List[Birthday]:
    """Return the next ``count`` upcoming birthdays sorted by soonest.

    Args:
        birthdays: List of Birthday objects.
        count: How many upcoming birthdays to return.
        reference_date: Date used as "today" for calculations. Defaults to
            ``date.today()``.
    """
    ref = reference_date or date.today()

    def days_until(b: Birthday) -> int:
        try:
            upcoming = date(ref.year, b.date_month, b.date_day)
        except ValueError:
            return 999999  # invalid date
        if upcoming < ref:
            upcoming = date(ref.year + 1, b.date_month, b.date_day)
        return (upcoming - ref).days

    sorted_birthdays = sorted(birthdays, key=days_until)
    return sorted_birthdays[:count]

