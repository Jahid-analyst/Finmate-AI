"""
All numbers here come from real deterministic calculation on the user's
actual transactions - never fabricated, never randomly generated
(spec sections 6, 9, 18, 20, 21). AI is layered on TOP of these numbers
later (see app/ai/assistant.py), never used to invent the numbers themselves.
"""
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models import Budget, SavingsGoal, Transaction, TxnType


def _month_bounds(year: int, month: int):
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return start, end


def get_month_transactions(db: Session, user_id: str, year: int, month: int) -> list[Transaction]:
    start, end = _month_bounds(year, month)
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.occurred_on >= start, Transaction.occurred_on < end)
        .all()
    )


def summary_for_month(db: Session, user_id: str, year: int, month: int) -> dict:
    txns = get_month_transactions(db, user_id, year, month)
    income = sum(t.amount for t in txns if t.txn_type == TxnType.income)
    expense = sum(t.amount for t in txns if t.txn_type == TxnType.expense)
    balance = income - expense
    savings_rate = round((balance / income) * 100, 1) if income > 0 else 0.0

    by_category: dict[str, float] = defaultdict(float)
    for t in txns:
        if t.txn_type == TxnType.expense:
            by_category[t.category_name] += t.amount
    top_categories = sorted(
        [{"category": c, "amount": round(a, 2)} for c, a in by_category.items()],
        key=lambda x: x["amount"], reverse=True,
    )[:5]

    return {
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "balance": round(balance, 2),
        "savings_rate": savings_rate,
        "top_categories": top_categories,
    }


def category_breakdown(db: Session, user_id: str, year: int, month: int) -> dict[str, float]:
    txns = get_month_transactions(db, user_id, year, month)
    by_category: dict[str, float] = defaultdict(float)
    for t in txns:
        if t.txn_type == TxnType.expense:
            by_category[t.category_name] += t.amount
    return dict(by_category)


def budget_status(db: Session, user_id: str, month: str) -> list[dict]:
    """month is 'YYYY-MM'. Returns per-category budget usage."""
    budget = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).first()
    if not budget:
        return []
    year, mon = int(month[:4]), int(month[5:7])
    spent_by_cat = category_breakdown(db, user_id, year, mon)

    results = []
    for bc in budget.categories:
        spent = spent_by_cat.get(bc.category_name, 0.0)
        pct = round((spent / bc.allocated_amount) * 100, 1) if bc.allocated_amount > 0 else 0.0
        if pct >= 100:
            status = "overspent"
        elif pct >= 90:
            status = "high_warning"
        elif pct >= 75:
            status = "warning"
        else:
            status = "ok"
        results.append({
            "category_name": bc.category_name,
            "allocated_amount": bc.allocated_amount,
            "spent": round(spent, 2),
            "percent_used": pct,
            "status": status,
        })
    return results


def generate_insights(db: Session, user_id: str) -> list[dict]:
    """Rule-based / statistical insight generation. Every insight is traceable
    to a computed number, never invented (spec section 18)."""
    now = datetime.utcnow()
    this_month = summary_for_month(db, user_id, now.year, now.month)
    prev_date = (now.replace(day=1) - timedelta(days=1))
    prev_month = summary_for_month(db, user_id, prev_date.year, prev_date.month)

    insights = []

    this_cats = {c["category"]: c["amount"] for c in this_month["top_categories"]}
    prev_year, prev_mon = prev_date.year, prev_date.month
    prev_cats = category_breakdown(db, user_id, prev_year, prev_mon)

    for cat, amount in this_cats.items():
        prev_amount = prev_cats.get(cat, 0)
        if prev_amount > 0:
            change_pct = round(((amount - prev_amount) / prev_amount) * 100, 1)
            if change_pct >= 15:
                insights.append({
                    "type": "spending_increase",
                    "severity": "warning",
                    "message": f"Your {cat} expenses increased by {change_pct}% this month "
                               f"compared with last month (৳{prev_amount:.0f} → ৳{amount:.0f}).",
                    "data": {"category": cat, "this_month": amount, "last_month": prev_amount, "change_pct": change_pct},
                })

    if prev_month["savings_rate"] and this_month["savings_rate"] > prev_month["savings_rate"]:
        insights.append({
            "type": "positive_behavior",
            "severity": "positive",
            "message": f"Your savings rate improved from {prev_month['savings_rate']}% to "
                       f"{this_month['savings_rate']}% this month. Keep it up!",
            "data": {"prev": prev_month["savings_rate"], "current": this_month["savings_rate"]},
        })

    month_str = f"{now.year}-{now.month:02d}"
    for b in budget_status(db, user_id, month_str):
        if b["status"] in ("high_warning", "overspent"):
            insights.append({
                "type": "budget_warning",
                "severity": "warning" if b["status"] == "high_warning" else "critical",
                "message": (
                    f"You have already used {b['percent_used']}% of your {b['category_name']} budget."
                    if b["status"] == "high_warning"
                    else f"You have exceeded your {b['category_name']} budget by "
                         f"৳{b['spent'] - b['allocated_amount']:.0f}."
                ),
                "data": b,
            })

    anomalies = detect_anomalies(db, user_id)
    for a in anomalies:
        insights.append(a)

    return insights


def detect_anomalies(db: Session, user_id: str, lookback_days: int = 90) -> list[dict]:
    """Flags transactions that are statistical outliers vs the user's own
    history in that category (spec section 19). Explicitly labeled as
    'unusual', never as confirmed fraud."""
    since = datetime.utcnow() - timedelta(days=lookback_days)
    txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.txn_type == TxnType.expense, Transaction.occurred_on >= since)
        .order_by(Transaction.occurred_on)
        .all()
    )
    by_category: dict[str, list[Transaction]] = defaultdict(list)
    for t in txns:
        by_category[t.category_name].append(t)

    anomalies = []
    for cat, cat_txns in by_category.items():
        if len(cat_txns) < 4:
            continue  # not enough history to judge "unusual"
        amounts = [t.amount for t in cat_txns]
        mean = statistics.mean(amounts)
        stdev = statistics.pstdev(amounts) or 1.0
        latest = cat_txns[-1]
        z_score = (latest.amount - mean) / stdev
        if z_score >= 2.5 and latest.amount > mean * 1.5:
            anomalies.append({
                "type": "unusual_transaction",
                "severity": "warning",
                "message": (
                    f"An expense of ৳{latest.amount:.0f} in {cat} on "
                    f"{latest.occurred_on.strftime('%d %b')} is significantly higher than your "
                    f"typical {cat} transactions (average ৳{mean:.0f}). This is an unusual "
                    f"transaction, not a confirmed fraud alert."
                ),
                "data": {"transaction_id": latest.id, "amount": latest.amount, "category": cat, "average": round(mean, 2)},
            })
    return anomalies


def financial_health_score(db: Session, user_id: str) -> dict:
    """Transparent, explainable score out of 100 (spec section 20)."""
    now = datetime.utcnow()
    month = summary_for_month(db, user_id, now.year, now.month)
    income, expense, savings_rate = month["total_income"], month["total_expense"], month["savings_rate"]

    # Savings score (0-25): scales with savings rate, capped at 25% savings rate = full marks
    savings_score = max(0, min(25, round((savings_rate / 25) * 25))) if income > 0 else 0

    # Budget control score (0-25): based on how many budget categories are within limits
    month_str = f"{now.year}-{now.month:02d}"
    budgets = budget_status(db, user_id, month_str)
    if budgets:
        within = sum(1 for b in budgets if b["status"] in ("ok", "warning"))
        budget_score = round((within / len(budgets)) * 25)
    else:
        budget_score = 15  # neutral score if no budget set yet

    # Cash flow score (0-25): expense-to-income ratio
    if income > 0:
        ratio = expense / income
        cashflow_score = max(0, min(25, round((1 - min(ratio, 1)) * 25)))
    else:
        cashflow_score = 0

    # Goals score (0-25): average progress across active savings goals
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id).all()
    if goals:
        avg_progress = statistics.mean(
            [min(100, (g.current_amount / g.target_amount) * 100) for g in goals if g.target_amount > 0]
        )
        goals_score = round((avg_progress / 100) * 25)
    else:
        goals_score = 12  # neutral if no goals set yet

    total = savings_score + budget_score + cashflow_score + goals_score

    return {
        "total_score": total,
        "savings_score": savings_score,
        "budget_score": budget_score,
        "cashflow_score": cashflow_score,
        "goals_score": goals_score,
        "explanation": {
            "savings": f"{savings_score}/25 - based on a {savings_rate}% savings rate this month",
            "budget_control": f"{budget_score}/25 - based on how many budget categories are within limits",
            "cash_flow": f"{cashflow_score}/25 - based on your expense-to-income ratio",
            "goals": f"{goals_score}/25 - based on average progress toward your savings goals",
        },
    }


def forecast_end_of_month(db: Session, user_id: str) -> dict:
    """Simple, honest forecasting (spec section 21): projects based on the
    user's own daily average spending rate this month. Refuses to pretend
    confidence when there isn't enough data."""
    now = datetime.utcnow()
    txns = get_month_transactions(db, user_id, now.year, now.month)
    if len(txns) < 5:
        return {
            "reliable": False,
            "message": "Not enough historical data to produce a reliable forecast. "
                       "Add more transactions this month to unlock forecasting.",
        }

    days_elapsed = now.day
    days_in_month = (_month_bounds(now.year, now.month)[1] - _month_bounds(now.year, now.month)[0]).days
    expense_so_far = sum(t.amount for t in txns if t.txn_type == TxnType.expense)
    income_so_far = sum(t.amount for t in txns if t.txn_type == TxnType.income)

    daily_avg_expense = expense_so_far / days_elapsed
    projected_expense = round(daily_avg_expense * days_in_month, 2)
    projected_balance = round(income_so_far - projected_expense, 2)

    return {
        "reliable": True,
        "projected_expense": projected_expense,
        "projected_balance": projected_balance,
        "income_so_far": round(income_so_far, 2),
        "expense_so_far": round(expense_so_far, 2),
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "message": f"Based on your average daily spending of ৳{daily_avg_expense:.0f}, "
                   f"you're projected to spend about ৳{projected_expense:.0f} this month.",
    }
