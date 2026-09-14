from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.categorizer import EXPENSE_KEYWORDS, INCOME_KEYWORDS, categorize
from app.ai.parser import parse_transaction_text
from app.database import get_db
from app.deps import get_current_user
from app.models import PaymentMethod, Transaction, TxnType, User
from app.schemas import (NLParseRequest, NLParseResult, TransactionIn,
                          TransactionOut)

router = APIRouter(prefix="/transactions", tags=["transactions"])

EXPENSE_CATEGORIES = list(EXPENSE_KEYWORDS.keys()) + ["Other"]
INCOME_CATEGORIES = list(INCOME_KEYWORDS.keys()) + ["Other Income"]


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    txn_type: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    q: Optional[str] = Query(None, description="free-text search over description/category"),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if txn_type:
        query = query.filter(Transaction.txn_type == txn_type)
    if category:
        query = query.filter(Transaction.category_name == category)
    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if date_from:
        query = query.filter(Transaction.occurred_on >= date_from)
    if date_to:
        query = query.filter(Transaction.occurred_on <= date_to)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Transaction.description.ilike(like)) | (Transaction.category_name.ilike(like))
        )
    return query.order_by(Transaction.occurred_on.desc()).all()


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.txn_type not in (TxnType.income.value, TxnType.expense.value):
        raise HTTPException(status_code=400, detail="txn_type must be 'income' or 'expense'")
    if payload.payment_method not in [m.value for m in PaymentMethod]:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    txn = Transaction(
        user_id=current_user.id,
        amount=payload.amount,
        txn_type=payload.txn_type,
        category_name=payload.category_name,
        description=payload.description,
        notes=payload.notes,
        payment_method=payload.payment_method,
        occurred_on=payload.occurred_on or datetime.utcnow(),
        is_recurring=payload.is_recurring,
        source="manual",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.put("/{txn_id}", response_model=TransactionOut)
def update_transaction(txn_id: str, payload: TransactionIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(txn_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return None


@router.post("/parse", response_model=NLParseResult)
def parse_nl_transaction(payload: NLParseRequest, current_user: User = Depends(get_current_user)):
    """Natural-language entry (spec section 11): extracts a draft transaction
    for the user to confirm before saving - never auto-saves."""
    result = parse_transaction_text(payload.text, EXPENSE_CATEGORIES, INCOME_CATEGORIES)
    result["raw_text"] = payload.text
    return result


@router.post("/categorize-preview")
def categorize_preview(payload: NLParseRequest, txn_type: str = "expense", current_user: User = Depends(get_current_user)):
    """Lets the frontend show a suggested category as the user types, before saving."""
    allowed = INCOME_CATEGORIES if txn_type == "income" else EXPENSE_CATEGORIES
    category, used_ai = categorize(payload.text, txn_type, allowed)
    return {"category_name": category, "used_ai": used_ai}


@router.get("/categories/list")
def list_categories():
    return {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORIES}
