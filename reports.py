from expenses import get_total_expenses, get_total_by_category
from earnings import get_total_earnings, get_total_by_category as get_earning_totals_by_category
from budget import get_month_remaining


def get_summary(start_date=None, end_date=None, budget_period=None):
    """Pulls together everything for a summary page: total expenses, total
    expenses by category, total earnings, total earnings by category, and
    (if a budget_period like '2026-08' is given) remaining budget for that
    month. Nothing here is stored - it's computed fresh from the 3 tables
    every time this is called."""
    summary = {
        "total_expenses": get_total_expenses(start_date, end_date),
        "expenses_by_category": get_total_by_category(start_date, end_date),
        "total_earnings": get_total_earnings(start_date, end_date),
        "earnings_by_category": get_earning_totals_by_category(start_date, end_date),
        "remaining_budget": None,
    }
    if budget_period:
        summary["remaining_budget"] = get_month_remaining(budget_period)
    return summary
