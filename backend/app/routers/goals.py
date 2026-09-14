from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import SavingsGoal, User
from app.schemas import GoalContribution, GoalIn, GoalOut

router = APIRouter(prefix="/goals", tags=["goals"])


def _serialize(goal: SavingsGoal) -> dict:
    progress = round(min(100, (goal.current_amount / goal.target_amount) * 100), 1) if goal.target_amount else 0
    required_monthly = None
    if goal.deadline:
        months_left = max(1, (goal.deadline.year - datetime.utcnow().year) * 12 + (goal.deadline.month - datetime.utcnow().month))
        remaining = max(0, goal.target_amount - goal.current_amount)
        required_monthly = round(remaining / months_left, 2)
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "deadline": goal.deadline,
        "progress_percent": progress,
        "required_monthly_saving": required_monthly,
    }


@router.get("", response_model=list[GoalOut])
def list_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()
    return [_serialize(g) for g in goals]


@router.post("", response_model=GoalOut, status_code=201)
def create_goal(payload: GoalIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = SavingsGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _serialize(goal)


@router.post("/{goal_id}/contribute", response_model=GoalOut)
def contribute_to_goal(goal_id: str, payload: GoalContribution, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.current_amount += payload.amount
    db.commit()
    db.refresh(goal)
    return _serialize(goal)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return None
