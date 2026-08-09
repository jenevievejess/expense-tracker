"""
Run this to fill tracker.db with realistic sample data covering every
feature: colored labels, expenses/earnings (with a reimbursed example),
recurring transactions, accounts with colors + balances, transfers,
budget periods (category + method allocations), and 4-5 entries on some
days for a realistic volume. Safe to re-run - wipes and recreates the
database each time.

Usage: python3 seed_dummy_data.py
"""
import os
from labels import create_labels_table, add_category, add_method, CATEGORY_COLORS, METHOD_COLORS
from expenses import create_expenses_table, add_expense
from earnings import create_earnings_table, add_earning
from budget import create_budget_tables, add_period, set_allocation
from settings import create_settings_table
from accounts import create_accounts_table, set_account_balance
from transfers import create_transfers_table, add_transfer
from recurring import create_recurring_table, add_recurring, generate_due

DB_NAME = "tracker.db"

if os.path.exists(DB_NAME):
    os.remove(DB_NAME)
    print(f"Removed old {DB_NAME}")

create_labels_table()
create_expenses_table()
create_earnings_table()
create_budget_tables()
create_settings_table()
create_accounts_table()
create_transfers_table()
create_recurring_table()

# ---------- Categories and methods ----------
add_category("food", CATEGORY_COLORS[0])
add_category("transport", CATEGORY_COLORS[1])
add_category("rent", CATEGORY_COLORS[2])
add_category("entertainment", CATEGORY_COLORS[3])
add_category("salary", CATEGORY_COLORS[4])
add_category("freelance", CATEGORY_COLORS[5])

add_method("cash", METHOD_COLORS[0])
add_method("card", METHOD_COLORS[1])
add_method("e-wallet", METHOD_COLORS[2])
add_method("bank", METHOD_COLORS[3])

# ---------- Recurring transactions ----------
add_recurring("expense", "rent", 800.00, "bank", "Monthly rent", 1, "2026-05-01")
add_recurring("earning", "salary", 2500.00, "bank", "Monthly paycheck", 1, "2026-05-01")
add_recurring("expense", "entertainment", 15.00, "card", "Streaming subscription", 5, "2026-05-05")
generate_due()

# ---------- Recent days ----------
add_expense("2026-08-04", "food", 8.50, "cash", "coffee")
add_expense("2026-08-04", "transport", 3.50, "e-wallet", "bus to work")
add_expense("2026-08-04", "food", 22.00, "card", "lunch with coworkers")
add_expense("2026-08-04", "transport", 3.50, "e-wallet", "bus home")
add_expense("2026-08-04", "entertainment", 12.00, "cash", "bookstore")

add_expense("2026-08-05", "food", 6.00, "cash", "breakfast")
add_expense("2026-08-05", "food", 45.00, "card", "weekly groceries")
add_expense("2026-08-05", "transport", 15.00, "e-wallet", "grab ride")
add_earning("2026-08-05", "freelance", 80.00, "e-wallet", "quick logo edit")

add_expense("2026-08-05", "food", 100.00, "card", "dinner with friends, split 4 ways")
from expenses import edit_expense, view_expenses
_rows = view_expenses("2026-08-05", "2026-08-05")
_dinner = [r for r in _rows if r[5] == "dinner with friends, split 4 ways"][0]
edit_expense(_dinner[0], "2026-08-05", "food", 100.00, "card", "dinner with friends, split 4 ways", 75.00)

add_expense("2026-08-06", "food", 9.80, "cash", "coffee")
add_expense("2026-08-06", "entertainment", 25.00, "e-wallet", "movie ticket")
add_expense("2026-08-06", "transport", 4.00, "e-wallet", "bus")

add_expense("2026-08-03", "food", 12.50, "cash", "lunch")
add_expense("2026-08-02", "transport", 4.00, "e-wallet", "bus")
add_earning("2026-08-02", "freelance", 150.00, "e-wallet", "small design project")

add_expense("2026-07-10", "transport", 4.00, "e-wallet", "bus")
add_expense("2026-07-12", "food", 40.20, "card", "groceries")
add_expense("2026-07-18", "entertainment", 30.00, "cash", "concert ticket")
add_earning("2026-07-20", "freelance", 220.00, "bank", "logo design")

# ---------- Transfers between accounts ----------
add_transfer("2026-06-15", "bank", "cash", 100.00, "ATM withdrawal")
add_transfer("2026-07-05", "card", "e-wallet", 50.00, "top up")
add_transfer("2026-08-01", "bank", "e-wallet", 60.00, "e-wallet top up")
add_transfer("2026-08-10", "cash", "card", 30.00, "transfer to card for groceries")

# ---------- Account starting balances ----------
set_account_balance("bank", 500.00, "2026-05-01")
set_account_balance("cash", 50.00, "2026-05-01")
set_account_balance("card", 400.00, "2026-05-01")
set_account_balance("e-wallet", 20.00, "2026-05-01")

# ---------- Budget periods ----------
may_id = add_period("2026-05-01", "2026-05-31", 1300, rollover=False, label="May 2026")
set_allocation(may_id, "category", "food", 300)
set_allocation(may_id, "category", "transport", 60)
set_allocation(may_id, "category", "rent", 800)
set_allocation(may_id, "category", "entertainment", 100)

june_id = add_period("2026-06-01", "2026-06-30", 1300, rollover=False, label="June 2026")
set_allocation(june_id, "category", "food", 300)
set_allocation(june_id, "category", "transport", 60)
set_allocation(june_id, "category", "rent", 800)
set_allocation(june_id, "category", "entertainment", 100)
set_allocation(june_id, "method", "cash", 100)
set_allocation(june_id, "method", "card", 900)
set_allocation(june_id, "method", "e-wallet", 200)

july_id = add_period("2026-07-01", "2026-07-31", 1300, rollover=False, label="July 2026")
set_allocation(july_id, "category", "food", 300)
set_allocation(july_id, "category", "transport", 60)
set_allocation(july_id, "category", "rent", 800)
set_allocation(july_id, "category", "entertainment", 100)

aug_id = add_period("2026-08-01", "2026-08-31", 1300, rollover=False, label="August 2026")
set_allocation(aug_id, "category", "food", 300)
set_allocation(aug_id, "category", "transport", 60)
set_allocation(aug_id, "category", "rent", 800)
set_allocation(aug_id, "category", "entertainment", 100)
set_allocation(aug_id, "method", "cash", 100)
set_allocation(aug_id, "method", "card", 900)
set_allocation(aug_id, "method", "e-wallet", 200)

print("Dummy data seeded successfully - covers colored labels, recurring,")
print("accounts/balances, transfers, a reimbursed expense, and 4 months of")
print("self-contained budget periods. Busy days (Aug 4-6) show realistic volume.")
print("Run: python3 app.py, then visit http://127.0.0.1:5000")
