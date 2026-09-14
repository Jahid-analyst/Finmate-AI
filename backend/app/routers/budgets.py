from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics import budget_status
from app.database import get_db
from app.deps import get_current_user
from app.models import Budget, BudgetCategory, User
from app.schemas import BudgetIn, BudgetOut

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _serialize(db: Session, budget: Budget) -> dict:
    status_map = {b["category_name"]: b for b in budget_status(db, budget.user_id, budget.month)}
    categories = []
    for bc in budget.categories:
        s = status_map.get(bc.category_name, {})
        categories.append({
            "category_name": bc.category_name,
            "allocated_amount": bc.allocated_amount,
            "spent": s.get("spent", 0),
            "percent_used": s.get("percent_used", 0),
            "status": s.get("status", "ok"),
        })
    return {"id": budget.id, "month": budget.month, "period": budget.period, "categories": categories}


@router.get("", response_model=list[BudgetOut])
def list_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    return [_serialize(db, b) for b in budgets]


@router.get("/{month}", response_model=BudgetOut)
def get_budget(month: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.month == month).first()
    if not budget:
        raise HTTPException(status_code=404, detail="No budget set for this month")
    return _serialize(db, budget)


@router.post("", response_model=BudgetOut, status_code=201)
def create_or_replace_budget(payload: BudgetIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.month == payload.month).first()
    if existing:
        db.delete(existing)
        db.commit()

    budget = Budget(user_id=current_user.id, month=payload.month, period=payload.period)
    db.add(budget)
    db.flush()

    for cat in payload.categories:
        db.add(BudgetCategory(budget_id=budget.id, category_name=cat.category_name, allocated_amount=cat.allocated_amount))

    db.commit()
    db.refresh(budget)
    return _serialize(db, budget)
