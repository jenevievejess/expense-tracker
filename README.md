# Expense Tracker

A full-featured expense tracker web application built with Python, Flask, and SQLite for tracking expenses, earnings, budgets, and account balances.

Live demo: https://expense-tracker-829k.onrender.com
(hosted on Render's free tier — first load may take up to a minute)


## Features

Track expenses, earnings, budgets, and account balances.

- Add, edit, and delete expenses and earnings
- Daily, weekly, and monthly view
- Organize transactions with customizable categories and payment methods
- Search and filter transactions
- Create recurring expenses and earnings
- View summaries through charts and trends
- Create and manage budget periods with category and method allocations
- Manage different account balances with transfer support between accounts
- Configurable currency in settings


## Tech Stack

- Python, Flask, Jinja2
- SQLite
- HTML/CSS


## How to Run Locally

Requires Python 3.9+ and pip.
 
```
git clone https://github.com/jenevievejess/expense-tracker.git
cd expense-tracker
pip install -r requirements.txt
python3 app.py
```
 
Then visit http://127.0.0.1:5000
 
To try it with sample data: run `python3 seed_dummy_data.py` first.


## Project Structure
 
```
expense-tracker/
├── app.py               Flask routes
├── expenses.py          Expense CRUD + totals
├── earnings.py          Earning CRUD + totals
├── labels.py            Categories & payment methods
├── budget.py            Budget periods & allocations
├── accounts.py          Account balances
├── transfers.py         Transfers between accounts
├── recurring.py         Recurring transactions
├── trends.py            Monthly totals for charts
├── search.py            Search
├── settings.py          Currency setting
├── reports.py           Home page summary
├── dateutils.py         Date helpers
├── seed_dummy_data.py   Fills the db with sample data
├── requirements.txt     Python dependencies
├── Procfile             Render start command
├── .gitignore
├── README.md
├── static/
│   ├── style.css        All styling
│   └── pattern.svg      Background graphic
├── screenshots/
└── templates/           26 Jinja2 templates, one per page/form
```


## Screenshots

| Home | Expenses | Budget |
| ---- | -------- | ------ |
| _add screenshot_ | _add screenshot_ | _add screenshot_ |
