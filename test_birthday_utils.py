from datetime import date
from src.models.data_models import Birthday
from src.utils.birthday_utils import get_upcoming_birthdays


def test_get_upcoming_birthdays():
    birthdays = [
        Birthday(name="A", date_month=1, date_day=1, source="s"),
        Birthday(name="B", date_month=12, date_day=31, source="s"),
        Birthday(name="C", date_month=6, date_day=15, source="s"),
    ]
    ref = date(2024, 6, 10)
    upcoming = get_upcoming_birthdays(birthdays, 2, reference_date=ref)
    assert [b.name for b in upcoming] == ["C", "B"]
