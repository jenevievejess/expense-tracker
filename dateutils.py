from datetime import date, timedelta
import calendar


def week_range(any_date_str):
    """Given any date string, returns (monday, sunday) of that week."""
    d = date.fromisoformat(any_date_str)
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return str(start), str(end)


def week_days(any_date_str):
    """Returns a list of 7 date strings, Monday through Sunday, for the week
    containing any_date_str."""
    d = date.fromisoformat(any_date_str)
    start = d - timedelta(days=d.weekday())
    return [str(start + timedelta(days=i)) for i in range(7)]


def month_calendar(year, month):
    """Returns a list of weeks (list of lists), each inner list has 7 day
    numbers (0 = blank/not in this month), Monday-first - ready to render
    as a calendar grid."""
    cal = calendar.Calendar(firstweekday=0)
    return cal.monthdayscalendar(year, month)


def month_range(period_str):
    """'2026-08' -> ('2026-08-01', '2026-08-31')"""
    year, month = map(int, period_str.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return f"{period_str}-01", f"{period_str}-{last_day:02d}"
