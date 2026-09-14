from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import analytics as engine
from app.database import get_db
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(year: int | None = None, month: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    return engine.summary_for_month(db, current_user.id, year or now.year, month or now.month)


@router.get("/categories")
def categories(year: int | None = None, month: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    breakdown = engine.category_breakdown(db, current_user.id, year or now.year, month or now.month)
    return [{"category": k, "amount": round(v, 2)} for k, v in sorted(breakdown.items(), key=lambda x: -x[1])]


@router.get("/insights")
def insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engine.generate_insights(db, current_user.id)


@router.get("/health-score")
def health_score(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engine.financial_health_score(db, current_user.id)


@router.get("/forecast")
def forecast(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engine.forecast_end_of_month(db, current_user.id)


@router.get("/monthly-report")
def monthly_report(year: int | None = None, month: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    y, m = year or now.year, month or now.month
    return {
        "summary": engine.summary_for_month(db, current_user.id, y, m),
        "categories": engine.category_breakdown(db, current_user.id, y, m),
        "insights": engine.generate_insights(db, current_user.id),
        "health_score": engine.financial_health_score(db, current_user.id),
    }
