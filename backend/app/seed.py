"""
Seeds realistic demo data (spec sections 33-34) so charts, budgets, goals,
and AI insights work immediately without manual data entry.

Run with:  python -m app.seed
"""
import random
from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import (Budget, BudgetCategory, Profile, SavingsGoal,
                         Transaction, User)
from app.security import hash_password

random.seed(42)

DEMO_USERS = [
    {
        "email": "student@demo.finmate.ai", "password": "demo1234", "full_name": "Rafiul Islam (Demo Student)",
        "user_type": "student", "monthly_income": 12000, "savings_target": 15000,
        "income_source": ("Tuition Income", 8000), "extra_income": ("Allowance", 4000),
        "expense_profile": {
            "Food": (150, 400), "Transportation": (30, 120), "Mobile Recharge": (50, 150),
            "Education": (200, 1500), "Entertainment": (100, 500), "Rent": (2500, 2500),
        },
    },
    {
        "email": "employee@demo.finmate.ai", "password": "demo1234", "full_name": "Nusrat Jahan (Demo Employee)",
        "user_type": "employee", "monthly_income": 45000, "savings_target": 100000,
        "income_source": ("Salary", 45000), "extra_income": None,
        "expense_profile": {
            "Food": (300, 900), "Transportation": (80, 300), "Rent": (12000, 12000),
            "Utilities": (500, 2000), "Shopping": (200, 3000), "Entertainment": (200, 1500),
            "Family Support": (1000, 5000),
        },
    },
    {
        "email": "household@demo.finmate.ai", "password": "demo1234", "full_name": "Karim Family (Demo Household)",
        "user_type": "household", "monthly_income": 80000, "savings_target": 200000,
        "income_source": ("Salary", 70000), "extra_income": ("Business", 10000),
        "expense_profile": {
            "Food": (500, 1500), "Rent": (20000, 20000), "Utilities": (1500, 4000),
            "Education": (1000, 5000), "Healthcare": (300, 3000), "Transportation": (200, 800),
            "Family Support": (1000, 4000),
        },
    },
]


def seed_user(db, spec: dict):
    existing = db.query(User).filter(User.email == spec["email"]).first()
    if existing:
        print(f"  - {spec['email']} already exists, skipping")
        return

    user = User(email=spec["email"], hashed_password=hash_password(spec["password"]), full_name=spec["full_name"])
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id, user_type=spec["user_type"], monthly_income=spec["monthly_income"],
        preferred_language="en", preferred_currency="BDT", savings_target=spec["savings_target"],
        onboarding_complete=True,
    )
    db.add(profile)

    now = datetime.utcnow()
    # Generate 3 months of transaction history so month-over-month insights have data.
    for month_offset in range(2, -1, -1):
        month_date = (now.replace(day=1) - timedelta(days=1)) if month_offset else now
        for _ in range(month_offset):
            month_date = (month_date.replace(day=1) - timedelta(days=1))
        year, month = month_date.year, month_date.month

        # Income
        cat, amount = spec["income_source"]
        db.add(Transaction(
            user_id=user.id, amount=amount, txn_type="income", category_name=cat,
            description=f"{cat} for {year}-{month:02d}", payment_method="bank",
            occurred_on=datetime(year, month, 3), source="seed",
        ))
        if spec["extra_income"]:
            cat2, amount2 = spec["extra_income"]
            db.add(Transaction(
                user_id=user.id, amount=amount2, txn_type="income", category_name=cat2,
                description=f"{cat2}", payment_method="mfs",
                occurred_on=datetime(year, month, 5), source="seed",
            ))

        # Expenses: several transactions per category per month, with a slight
        # upward trend in the most recent month to make insights interesting.
        for category, (low, high) in spec["expense_profile"].items():
            num_txns = random.randint(2, 5)
            trend_multiplier = 1.2 if month_offset == 0 and category in ("Food", "Entertainment") else 1.0
            for _ in range(num_txns):
                amount = round(random.uniform(low, high) * trend_multiplier / num_txns, 2)
                day = random.randint(1, 27)
                db.add(Transaction(
                    user_id=user.id, amount=amount, txn_type="expense", category_name=category,
                    description=f"{category} expense", payment_method=random.choice(["cash", "mfs", "card", "bank"]),
                    occurred_on=datetime(year, month, day), source="seed",
                ))

    # One larger, deliberately anomalous transaction in the current month for anomaly detection demo.
    main_cat = list(spec["expense_profile"].keys())[0]
    low, high = spec["expense_profile"][main_cat]
    db.add(Transaction(
        user_id=user.id, amount=round(high * 4, 2), txn_type="expense", category_name=main_cat,
        description=f"Unusually large {main_cat} expense", payment_method="card",
        occurred_on=now - timedelta(days=1), source="seed",
    ))

    # A monthly budget for the current month.
    month_str = f"{now.year}-{now.month:02d}"
    budget = Budget(user_id=user.id, month=month_str, period="monthly")
    db.add(budget)
    db.flush()
    for category, (low, high) in spec["expense_profile"].items():
        db.add(BudgetCategory(budget_id=budget.id, category_name=category, allocated_amount=round((low + high) * 2.2, -2)))

    # A savings goal.
    db.add(SavingsGoal(
        user_id=user.id, name="Emergency Fund", target_amount=spec["savings_target"],
        current_amount=round(spec["savings_target"] * random.uniform(0.15, 0.4), 2),
        deadline=now + timedelta(days=240),
    ))

    db.commit()
    print(f"  - Seeded {spec['email']} (password: {spec['password']})")


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("Seeding FinMate AI demo data...")
    try:
        for spec in DEMO_USERS:
            seed_user(db, spec)
    finally:
        db.close()
    print("Done. Demo accounts:")
    for spec in DEMO_USERS:
        print(f"  {spec['email']} / {spec['password']}")


if __name__ == "__main__":
    run()
