import calendar as calendar_module
import os
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session

from expenses import (
    create_expenses_table, add_expense, view_expenses, get_expense,
    edit_expense, delete_expense, get_total_expenses,
    get_total_by_category as get_expense_by_category,
    get_total_by_method as get_expense_by_method,
)
from earnings import (
    create_earnings_table, add_earning, view_earnings, get_earning,
    edit_earning, delete_earning, get_total_earnings,
    get_total_by_category as get_earning_by_category,
    get_total_by_method as get_earning_by_method,
)
from labels import (
    create_labels_table, view_categories, view_methods,
    add_category, add_method, get_label, edit_label, delete_label,
    CATEGORY_COLORS, METHOD_COLORS, get_category_colors, get_method_colors,
)
from budget import (
    create_budget_tables, get_all_periods,
    get_period, add_period, edit_period, delete_period,
    get_allocations, set_allocation, get_allocation_progress, delete_allocation,
    get_remaining_for_period, get_current_period, find_period_by_dates,
)
from settings import (
    create_settings_table, get_currency_code, get_currency_symbol,
    set_currency, CURRENCY_SYMBOLS,
)
from accounts import (
    create_accounts_table, set_account_balance, get_account,
    get_all_accounts, get_balance, get_total_balance,
    get_account_dates, get_account_activity_for_date, get_balance_as_of,
)
from transfers import (
    create_transfers_table, add_transfer, view_transfers, get_transfer,
    edit_transfer, delete_transfer,
)
from recurring import (
    create_recurring_table, add_recurring, view_recurring, get_recurring,
    edit_recurring, delete_recurring, set_active, generate_due,
)
from trends import get_monthly_totals
from search import search_expenses, search_earnings
from dateutils import week_range, week_days, month_calendar, month_range
from events import (
    create_events_table, add_event, edit_event, delete_event,
    get_event, get_all_events, get_band_map, get_tag_map,
    get_transactions_for_event, get_event_totals, get_event_for_date,
    get_band_total, get_tag_totals_for_range,
    get_daily_tag_totals, get_band_total_earnings, get_daily_tag_totals_earnings,
    get_tag_totals_for_range_earnings, EVENT_COLORS,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

create_expenses_table()
create_earnings_table()
create_labels_table()
create_budget_tables()
create_settings_table()
create_accounts_table()
create_transfers_table()
create_recurring_table()
create_events_table()


@app.before_request
def _generate_due_recurring():
    generate_due()


@app.context_processor
def inject_currency():
    return dict(currency_symbol=get_currency_symbol())


def format_transfer(row):
    """Turns a raw transfer row into a display-ready dict:
    '2 July 2026' style date, from/to, note, amount."""
    id, date_str, from_m, to_m, amount, note = row
    d = date.fromisoformat(date_str)
    return {
        "id": id, "date_display": f"{d.day} {d.strftime('%B')} {d.year}",
        "from_method": from_m, "to_method": to_m, "amount": amount, "note": note,
    }


# ---------- Home ----------

@app.route("/")
def home():
    total_balance = get_total_balance()
    current_period = get_current_period()
    current_period_remaining = get_remaining_for_period(current_period["id"]) if current_period else None

    total_expenses = get_total_expenses()
    total_earnings = get_total_earnings()
    expense_by_category = get_expense_by_category()
    expense_by_method = get_expense_by_method()
    earning_by_category = get_earning_by_category()
    earning_by_method = get_earning_by_method()
    monthly_trends = get_monthly_totals(6)

    return render_template(
        "home.html",
        total_balance=total_balance,
        current_period=current_period,
        current_period_remaining=current_period_remaining,
        total_expenses=total_expenses,
        total_earnings=total_earnings,
        expense_by_category=expense_by_category,
        expense_by_method=expense_by_method,
        earning_by_category=earning_by_category,
        earning_by_method=earning_by_method,
        monthly_trends=monthly_trends,
        category_colors=get_category_colors(),
        method_colors=get_method_colors(),
    )


# ---------- Expenses ----------

@app.route("/expenses")
def expenses_view():
    view = request.args.get("view", "day")
    date_str = request.args.get("date")
    if date_str:
        session[f"expenses_{view}_date"] = date_str
    else:
        date_str = session.get(f"expenses_{view}_date", str(date.today()))

    if view == "month":
        month_str = date_str[:7]
        year, month = map(int, month_str.split("-"))
        grid = month_calendar(year, month)
        start, end = month_range(month_str)
        rows = view_expenses(start, end)
        totals_by_day = {}
        for r in rows:
            totals_by_day[r[1]] = totals_by_day.get(r[1], 0) + r[3]
        total = get_total_expenses(start, end)
        by_category = get_expense_by_category(start, end)
        by_method = get_expense_by_method(start, end)
        prev_month_str = f"{year-1}-12" if month == 1 else f"{year}-{month-1:02d}"
        next_month_str = f"{year+1}-01" if month == 12 else f"{year}-{month+1:02d}"
        month_display = date(year, month, 1).strftime("%B %Y")
        return render_template(
            "expenses_month.html", month_str=month_str, month_display=month_display,
            year=year, month=month, grid=grid, totals_by_day=totals_by_day, total=total,
            by_category=by_category, by_method=by_method,
            prev_month_str=prev_month_str, next_month_str=next_month_str,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_map=get_band_map(start, end), tag_map=get_tag_map(start, end),
            band_totals={eid: get_band_total(eid) for eid in {e["id"] for e in get_band_map(start, end).values()}},
            daily_tag_totals=get_daily_tag_totals(start, end),
            month_tag_totals=get_tag_totals_for_range(start, end),
        )

    elif view == "week":
        start, end = week_range(date_str)
        days = week_days(date_str)
        rows = view_expenses(start, end)
        totals_by_day = {}
        for r in rows:
            totals_by_day[r[1]] = totals_by_day.get(r[1], 0) + r[3]
        total = get_total_expenses(start, end)
        by_category = get_expense_by_category(start, end)
        by_method = get_expense_by_method(start, end)
        prev_week_date = str(date.fromisoformat(days[0]) - timedelta(days=7))
        next_week_date = str(date.fromisoformat(days[0]) + timedelta(days=7))
        day_labels = [{"date": d, "display": date.fromisoformat(d).strftime("%A, %d %B")} for d in days]
        monday = date.fromisoformat(days[0])
        week_label = f"{monday.strftime('%B')}, Week {((monday.day - 1) // 7) + 1}"
        return render_template(
            "expenses_week.html", days=days, day_labels=day_labels, totals_by_day=totals_by_day,
            total=total, by_category=by_category, by_method=by_method, week_label=week_label,
            prev_week_date=prev_week_date, next_week_date=next_week_date,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_map=get_band_map(start, end), tag_map=get_tag_map(start, end),
            daily_tag_totals=get_daily_tag_totals(start, end),
            week_tag_totals=get_tag_totals_for_range(start, end),
        )

    else:  # day
        rows = view_expenses(date_str, date_str)
        total = get_total_expenses(date_str, date_str)
        by_category = get_expense_by_category(date_str, date_str)
        by_method = get_expense_by_method(date_str, date_str)
        date_display = date.fromisoformat(date_str).strftime("%A, %d %B %Y")
        prev_date = str(date.fromisoformat(date_str) - timedelta(days=1))
        next_date = str(date.fromisoformat(date_str) + timedelta(days=1))
        return render_template(
            "expenses_day.html", date_str=date_str, date_display=date_display,
            rows=rows, total=total, prev_date=prev_date, next_date=next_date,
            by_category=by_category, by_method=by_method,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_event=get_band_map(date_str, date_str).get(date_str),
            event_lookup={e["id"]: e for e in get_all_events()},
            day_tag_totals=get_tag_totals_for_range(date_str, date_str),
        )


@app.route("/expenses/add", methods=["GET", "POST"])
def expenses_add():
    if request.method == "POST":
        entry_date = request.form["date"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        method = request.form["method"]
        note = request.form.get("note", "")
        reimbursed = float(request.form.get("reimbursed") or 0)
        event_id = request.form.get("event_id") or None
        if not event_id:
            band_event = get_event_for_date(entry_date)
            event_id = band_event["id"] if band_event else None

        if request.form.get("is_recurring"):
            day_of_month = int(entry_date.split("-")[2])
            add_recurring("expense", category, amount, method, note, day_of_month, entry_date)
            generate_due()
        else:
            add_expense(entry_date, category, amount, method, note, reimbursed, event_id)

        return redirect(url_for("expenses_view", view="day", date=entry_date))

    default_date = request.args.get("date", str(date.today()))
    return render_template(
        "expense_form.html", entry=None, default_date=default_date,
        categories=view_categories(), methods=view_methods(), all_events=get_all_events(),
    )


@app.route("/expenses/edit/<int:expense_id>", methods=["GET", "POST"])
def expenses_edit(expense_id):
    if request.method == "POST":
        reimbursed = float(request.form.get("reimbursed") or 0)
        event_id = request.form.get("event_id") or None
        edit_expense(
            expense_id, request.form["date"], request.form["category"],
            float(request.form["amount"]), request.form["method"],
            request.form.get("note", ""), reimbursed, event_id
        )
        return redirect(url_for("expenses_view", view="day", date=request.form["date"]))

    entry = get_expense(expense_id)
    return render_template(
        "expense_form.html", entry=entry, default_date=entry[1],
        categories=view_categories(), methods=view_methods(), all_events=get_all_events(),
    )


@app.route("/expenses/delete/<int:expense_id>", methods=["POST"])
def expenses_delete(expense_id):
    delete_expense(expense_id)
    return redirect(url_for("expenses_view"))


# ---------- Earnings ----------

@app.route("/earnings")
def earnings_view():
    view = request.args.get("view", "day")
    date_str = request.args.get("date")
    if date_str:
        session[f"earnings_{view}_date"] = date_str
    else:
        date_str = session.get(f"earnings_{view}_date", str(date.today()))

    if view == "month":
        month_str = date_str[:7]
        year, month = map(int, month_str.split("-"))
        grid = month_calendar(year, month)
        start, end = month_range(month_str)
        rows = view_earnings(start, end)
        totals_by_day = {}
        for r in rows:
            totals_by_day[r[1]] = totals_by_day.get(r[1], 0) + r[3]
        total = get_total_earnings(start, end)
        by_category = get_earning_by_category(start, end)
        by_method = get_earning_by_method(start, end)
        prev_month_str = f"{year-1}-12" if month == 1 else f"{year}-{month-1:02d}"
        next_month_str = f"{year+1}-01" if month == 12 else f"{year}-{month+1:02d}"
        month_display = date(year, month, 1).strftime("%B %Y")
        return render_template(
            "earnings_month.html", month_str=month_str, month_display=month_display,
            year=year, month=month, grid=grid, totals_by_day=totals_by_day, total=total,
            by_category=by_category, by_method=by_method,
            prev_month_str=prev_month_str, next_month_str=next_month_str,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_map=get_band_map(start, end), tag_map=get_tag_map(start, end),
            band_totals={eid: get_band_total_earnings(eid) for eid in {e["id"] for e in get_band_map(start, end).values()}},
            daily_tag_totals=get_daily_tag_totals_earnings(start, end),
            month_tag_totals=get_tag_totals_for_range_earnings(start, end),
        )

    elif view == "week":
        start, end = week_range(date_str)
        days = week_days(date_str)
        rows = view_earnings(start, end)
        totals_by_day = {}
        for r in rows:
            totals_by_day[r[1]] = totals_by_day.get(r[1], 0) + r[3]
        total = get_total_earnings(start, end)
        by_category = get_earning_by_category(start, end)
        by_method = get_earning_by_method(start, end)
        prev_week_date = str(date.fromisoformat(days[0]) - timedelta(days=7))
        next_week_date = str(date.fromisoformat(days[0]) + timedelta(days=7))
        day_labels = [{"date": d, "display": date.fromisoformat(d).strftime("%A, %d %B")} for d in days]
        monday = date.fromisoformat(days[0])
        week_label = f"{monday.strftime('%B')}, Week {((monday.day - 1) // 7) + 1}"
        return render_template(
            "earnings_week.html", days=days, day_labels=day_labels, totals_by_day=totals_by_day,
            total=total, by_category=by_category, by_method=by_method, week_label=week_label,
            prev_week_date=prev_week_date, next_week_date=next_week_date,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_map=get_band_map(start, end), tag_map=get_tag_map(start, end),
            daily_tag_totals=get_daily_tag_totals_earnings(start, end),
            week_tag_totals=get_tag_totals_for_range_earnings(start, end),
        )

    else:  # day
        rows = view_earnings(date_str, date_str)
        total = get_total_earnings(date_str, date_str)
        by_category = get_earning_by_category(date_str, date_str)
        by_method = get_earning_by_method(date_str, date_str)
        date_display = date.fromisoformat(date_str).strftime("%A, %d %B %Y")
        prev_date = str(date.fromisoformat(date_str) - timedelta(days=1))
        next_date = str(date.fromisoformat(date_str) + timedelta(days=1))
        return render_template(
            "earnings_day.html", date_str=date_str, date_display=date_display,
            rows=rows, total=total, prev_date=prev_date, next_date=next_date,
            by_category=by_category, by_method=by_method,
            category_colors=get_category_colors(), method_colors=get_method_colors(),
            band_event=get_band_map(date_str, date_str).get(date_str),
            event_lookup={e["id"]: e for e in get_all_events()},
            day_tag_totals=get_tag_totals_for_range_earnings(date_str, date_str),
        )


@app.route("/earnings/add", methods=["GET", "POST"])
def earnings_add():
    if request.method == "POST":
        entry_date = request.form["date"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        method = request.form["method"]
        note = request.form.get("note", "")
        event_id = request.form.get("event_id") or None
        if not event_id:
            band_event = get_event_for_date(entry_date)
            event_id = band_event["id"] if band_event else None

        if request.form.get("is_recurring"):
            day_of_month = int(entry_date.split("-")[2])
            add_recurring("earning", category, amount, method, note, day_of_month, entry_date)
            generate_due()
        else:
            add_earning(entry_date, category, amount, method, note, event_id)

        return redirect(url_for("earnings_view", view="day", date=entry_date))

    default_date = request.args.get("date", str(date.today()))
    prefill_amount = request.args.get("amount", "")
    prefill_note = request.args.get("note", "")
    return render_template(
        "earning_form.html", entry=None, default_date=default_date,
        prefill_amount=prefill_amount, prefill_note=prefill_note,
        categories=view_categories(), methods=view_methods(), all_events=get_all_events(),
    )


@app.route("/earnings/edit/<int:earning_id>", methods=["GET", "POST"])
def earnings_edit(earning_id):
    if request.method == "POST":
        event_id = request.form.get("event_id") or None
        edit_earning(
            earning_id, request.form["date"], request.form["category"],
            float(request.form["amount"]), request.form["method"],
            request.form.get("note", ""), event_id
        )
        return redirect(url_for("earnings_view", view="day", date=request.form["date"]))

    entry = get_earning(earning_id)
    return render_template(
        "earning_form.html", entry=entry, default_date=entry[1],
        categories=view_categories(), methods=view_methods(), all_events=get_all_events(),
    )


@app.route("/earnings/delete/<int:earning_id>", methods=["POST"])
def earnings_delete(earning_id):
    delete_earning(earning_id)
    return redirect(url_for("earnings_view"))


# ---------- Budget ----------

@app.route("/budget")
def budget_view():
    periods = get_all_periods()

    period_id = request.args.get("period_id", type=int)
    selected_period = get_period(period_id) if period_id else (periods[0] if periods else None)

    category_progress = []
    method_progress = []
    remaining_for_period = None
    if selected_period:
        category_progress = get_allocation_progress(selected_period["id"], "category")
        method_progress = get_allocation_progress(selected_period["id"], "method")
        remaining_for_period = get_remaining_for_period(selected_period["id"])

    return render_template(
        "budget.html", periods=periods,
        selected_period=selected_period, category_progress=category_progress,
        method_progress=method_progress, remaining_for_period=remaining_for_period,
    )


@app.route("/budget/edit", methods=["GET", "POST"])
@app.route("/budget/edit/<int:period_id>", methods=["GET", "POST"])
def budget_edit(period_id=None):
    if request.method == "POST":
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        amount = float(request.form["amount"])
        rollover = "rollover" in request.form
        label = request.form.get("label", "")

        if period_id:
            edit_period(period_id, start_date, end_date, amount, rollover, label)
        else:
            period_id = add_period(start_date, end_date, amount, rollover, label)

        categories = request.form.getlist("alloc_category_name")
        category_amounts = request.form.getlist("alloc_category_amount")
        for name, amt in zip(categories, category_amounts):
            if name and amt:
                set_allocation(period_id, "category", name, float(amt))

        methods = request.form.getlist("alloc_method_name")
        method_amounts = request.form.getlist("alloc_method_amount")
        for name, amt in zip(methods, method_amounts):
            if name and amt:
                set_allocation(period_id, "method", name, float(amt))

        return redirect(url_for("budget_view", period_id=period_id))

    period = get_period(period_id) if period_id else None
    category_allocs = get_allocations(period_id, "category") if period_id else []
    method_allocs = get_allocations(period_id, "method") if period_id else []
    return render_template(
        "budget_form.html", period=period, categories=view_categories(),
        methods=view_methods(), category_allocs=category_allocs, method_allocs=method_allocs,
        default_start=str(date.today())[:8] + "01",
    )


@app.route("/budget/delete/<int:period_id>", methods=["POST"])
def budget_delete(period_id):
    delete_period(period_id)
    return redirect(url_for("budget_view"))


@app.route("/budget/allocation/delete/<int:allocation_id>", methods=["POST"])
def budget_allocation_delete(allocation_id):
    delete_allocation(allocation_id)
    return ("", 204)


# ---------- Accounts ----------

@app.route("/accounts")
def accounts_view():
    methods = view_methods()
    account_rows = []
    for id, name, color in methods:
        account = get_account(name)
        balance = get_balance(name) if account else None
        account_rows.append({"id": id, "name": name, "color": color, "account": account, "balance": balance})

    all_transfers = [format_transfer(t) for t in view_transfers()]
    recent_transfers = all_transfers[:3]
    total_balance = get_total_balance()

    return render_template(
        "accounts.html", account_rows=account_rows, transfers=recent_transfers,
        has_more_transfers=len(all_transfers) > 3, total_balance=total_balance,
        method_colors=get_method_colors(),
    )


@app.route("/accounts/transfers")
def transfers_all():
    all_transfers = [format_transfer(t) for t in view_transfers()]
    return render_template("accounts_transfers.html", transfers=all_transfers, method_colors=get_method_colors())


@app.route("/accounts/add", methods=["GET", "POST"])
def accounts_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        color = request.form.get("color")
        if name:
            add_method(name, color)
            starting_balance = request.form.get("starting_balance")
            if starting_balance:
                start_date = request.form.get("start_date") or str(date.today())
                set_account_balance(name, float(starting_balance), start_date)
        return redirect(url_for("accounts_view"))

    return render_template(
        "account_add.html", method_colors=METHOD_COLORS, default_date=str(date.today()),
    )


@app.route("/accounts/set/<method_name>", methods=["GET", "POST"])
def accounts_set(method_name):
    if request.method == "POST":
        starting_balance = float(request.form["starting_balance"])
        start_date = request.form["start_date"]
        set_account_balance(method_name, starting_balance, start_date)
        return redirect(url_for("accounts_view"))

    account = get_account(method_name)
    return render_template(
        "account_form.html", method_name=method_name, account=account,
        default_date=str(date.today()),
    )


@app.route("/accounts/<method_name>")
def account_detail(method_name):
    account = get_account(method_name)
    if not account:
        return redirect(url_for("accounts_set", method_name=method_name))

    page = request.args.get("page", 0, type=int)
    per_page = 5
    all_dates = get_account_dates(method_name, account["start_date"])
    page_dates = all_dates[page * per_page: (page + 1) * per_page]

    days = []
    for d in page_dates:
        days.append({
            "date": d,
            "date_display": date.fromisoformat(d).strftime("%A, %d %B %Y"),
            "activity": get_account_activity_for_date(method_name, d),
            "balance_after": get_balance_as_of(method_name, d),
        })

    return render_template(
        "account_detail.html", method_name=method_name, account=account, days=days,
        page=page, has_prev=page > 0, has_next=(page + 1) * per_page < len(all_dates),
        current_balance=get_balance(method_name),
        color=get_method_colors().get(method_name, "#ccc"),
        category_colors=get_category_colors(), method_colors=get_method_colors(),
    )


@app.route("/accounts/transfer/add", methods=["GET", "POST"])
def transfer_add():
    if request.method == "POST":
        add_transfer(
            request.form["date"], request.form["from_method"],
            request.form["to_method"], float(request.form["amount"]),
            request.form.get("note", "")
        )
        return redirect(url_for("accounts_view"))

    return render_template(
        "transfer_form.html", entry=None, default_date=str(date.today()),
        methods=view_methods(),
    )


@app.route("/accounts/transfer/edit/<int:transfer_id>", methods=["GET", "POST"])
def transfer_edit(transfer_id):
    if request.method == "POST":
        edit_transfer(
            transfer_id, request.form["date"], request.form["from_method"],
            request.form["to_method"], float(request.form["amount"]),
            request.form.get("note", "")
        )
        return redirect(url_for("accounts_view"))

    entry = get_transfer(transfer_id)
    return render_template(
        "transfer_form.html", entry=entry, default_date=entry[1],
        methods=view_methods(),
    )


@app.route("/accounts/transfer/delete/<int:transfer_id>", methods=["POST"])
def transfer_delete(transfer_id):
    delete_transfer(transfer_id)
    return redirect(url_for("accounts_view"))


# ---------- Search ----------

@app.route("/expenses/search")
def expenses_search():
    query = request.args.get("q", "").strip()
    results = search_expenses(query) if query else []
    return render_template(
        "expenses_search.html", query=query, results=results,
        category_colors=get_category_colors(), method_colors=get_method_colors(),
    )


@app.route("/earnings/search")
def earnings_search():
    query = request.args.get("q", "").strip()
    results = search_earnings(query) if query else []
    return render_template(
        "earnings_search.html", query=query, results=results,
        category_colors=get_category_colors(), method_colors=get_method_colors(),
    )


# ---------- Recurring transactions ----------

@app.route("/recurring")
def recurring_view():
    return render_template("recurring.html", items=view_recurring())


@app.route("/recurring/add", methods=["GET", "POST"])
def recurring_add():
    if request.method == "POST":
        add_recurring(
            request.form["type"], request.form["category"],
            float(request.form["amount"]), request.form["method"],
            request.form.get("note", ""), int(request.form["day_of_month"]),
            request.form["start_date"],
        )
        return redirect(url_for("recurring_view"))

    return render_template(
        "recurring_form.html", entry=None, default_date=str(date.today()),
        categories=view_categories(), methods=view_methods(),
    )


@app.route("/recurring/edit/<int:recurring_id>", methods=["GET", "POST"])
def recurring_edit(recurring_id):
    if request.method == "POST":
        edit_recurring(
            recurring_id, request.form["category"], float(request.form["amount"]),
            request.form["method"], request.form.get("note", ""),
            int(request.form["day_of_month"]),
        )
        return redirect(url_for("recurring_view"))

    entry = get_recurring(recurring_id)
    return render_template(
        "recurring_form.html", entry=entry, default_date=entry["start_date"],
        categories=view_categories(), methods=view_methods(),
    )


@app.route("/recurring/toggle/<int:recurring_id>", methods=["POST"])
def recurring_toggle(recurring_id):
    entry = get_recurring(recurring_id)
    set_active(recurring_id, not entry["active"])
    return redirect(url_for("recurring_view"))


@app.route("/recurring/delete/<int:recurring_id>", methods=["POST"])
def recurring_delete(recurring_id):
    delete_recurring(recurring_id)
    return redirect(url_for("recurring_view"))


# ---------- Events ----------

@app.route("/events")
def events_view():
    all_events = get_all_events()
    event_id = request.args.get("event_id", type=int)
    selected_event = get_event(event_id) if event_id else (all_events[0] if all_events else None)

    days = []
    totals = None
    if selected_event:
        transactions = get_transactions_for_event(selected_event["id"])
        totals = get_event_totals(selected_event["id"])
        seen_dates = []
        for t in transactions:
            if t["date"] not in seen_dates:
                seen_dates.append(t["date"])
                days.append({
                    "date": t["date"],
                    "date_display": date.fromisoformat(t["date"]).strftime("%A, %-d %B %Y"),
                    "entries": [], "day_total": 0,
                })
            for d in days:
                if d["date"] == t["date"]:
                    d["entries"].append(t)
                    d["day_total"] += t["amount"] if t["kind"] == "expense" else -t["amount"]

    return render_template(
        "event_list.html", events=all_events, selected_event=selected_event,
        days=days, totals=totals,
        category_colors=get_category_colors(), method_colors=get_method_colors(),
    )


@app.route("/events/add", methods=["GET", "POST"])
def events_add():
    if request.method == "POST":
        budget_val = request.form.get("budget")
        new_id = add_event(
            request.form["name"], request.form["color"],
            request.form.get("start_date") or None,
            request.form.get("end_date") or None,
            float(budget_val) if budget_val else None,
        )
        return redirect(url_for("events_view", event_id=new_id))
    prefill_date = request.args.get("start_date", "")
    return render_template("event_add.html", entry=None, event_colors=EVENT_COLORS, prefill_date=prefill_date)


@app.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
def events_edit(event_id):
    if request.method == "POST":
        budget_val = request.form.get("budget")
        edit_event(
            event_id, request.form["name"], request.form["color"],
            request.form.get("start_date") or None,
            request.form.get("end_date") or None,
            float(budget_val) if budget_val else None,
        )
        return redirect(url_for("events_view", event_id=event_id))
    entry = get_event(event_id)
    return render_template("event_add.html", entry=entry, event_colors=EVENT_COLORS, prefill_date="")


@app.route("/events/delete/<int:event_id>", methods=["POST"])
def events_delete(event_id):
    delete_event(event_id)
    return redirect(url_for("events_view"))


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    return redirect(url_for("events_view", event_id=event_id))


# ---------- Settings ----------

@app.route("/settings")
def settings_view():
    return render_template(
        "settings.html",
        categories=view_categories(),
        currency_code=get_currency_code(), currencies=CURRENCY_SYMBOLS,
        category_colors=CATEGORY_COLORS,
    )


@app.route("/settings/currency", methods=["POST"])
def settings_currency():
    code = request.form.get("currency")
    if code in CURRENCY_SYMBOLS:
        set_currency(code)
    return redirect(url_for("settings_view"))


@app.route("/settings/categories/add")
def category_add_page():
    return render_template("category_add.html", category_colors=CATEGORY_COLORS)


@app.route("/labels/add/category", methods=["POST"])
def labels_add_category():
    name = request.form.get("name", "").strip()
    color = request.form.get("color")
    if name:
        add_category(name, color)
    return redirect(url_for("settings_view"))


@app.route("/labels/add/method", methods=["POST"])
def labels_add_method():
    name = request.form.get("name", "").strip()
    color = request.form.get("color")
    if name:
        add_method(name, color)
    return redirect(url_for("accounts_view"))


@app.route("/labels/edit/<int:label_id>", methods=["GET", "POST"])
def labels_edit(label_id):
    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_color = request.form.get("color")
        label_type = request.form.get("type")
        if new_name:
            edit_label(label_id, new_name, new_color)
        return redirect(url_for("accounts_view") if label_type == "method" else url_for("settings_view"))

    label = get_label(label_id)
    colors = CATEGORY_COLORS if label[1] == "category" else METHOD_COLORS
    return render_template("label_edit.html", label=label, colors=colors)


@app.route("/labels/delete/<int:label_id>", methods=["POST"])
def labels_delete(label_id):
    label = get_label(label_id)
    label_type = label[1] if label else "category"
    delete_label(label_id)
    return redirect(url_for("accounts_view") if label_type == "method" else url_for("settings_view"))


if __name__ == "__main__":
    app.run(debug=False, port=5002)