from datetime import date

from expenses import get_total_expenses
from earnings import get_total_earnings
from budget import calendar_month_range, find_period_by_dates


def get_last_n_months(n=6):
    today = date.today()
    months = []
    y, m = today.year, today.month
    for _ in range(n):
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def get_monthly_totals(n=6):
    """Returns a list of {month, expenses, earnings, budget} dicts for the
    last n months (oldest first) - ready to feed straight into a chart.
    budget is 0 for a month if no budget period exactly matches that
    calendar month."""
    months = get_last_n_months(n)
    data = []
    for month_str in months:
        start, end = calendar_month_range(month_str)
        period = find_period_by_dates(start, end)
        data.append({
            "month": month_str,
            "expenses": get_total_expenses(start, end),
            "earnings": get_total_earnings(start, end),
            "budget": period["amount"] if period else 0,
        })
    return data
