from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str

    class Config:
        from_attributes = True


# ---------- Onboarding / Profile ----------
class ProfileIn(BaseModel):
    user_type: str
    age_range: Optional[str] = None
    monthly_income: float = 0
    income_frequency: str = "monthly"
    preferred_language: str = "en"
    preferred_currency: str = "BDT"
    savings_target: float = 0
    financial_goal_text: Optional[str] = None


class ProfileOut(ProfileIn):
    onboarding_complete: bool

    class Config:
        from_attributes = True


# ---------- Transactions ----------
class TransactionIn(BaseModel):
    amount: float = Field(gt=0)
    txn_type: str  # income | expense
    category_name: str
    description: str = ""
    notes: str = ""
    payment_method: str = "cash"
    occurred_on: Optional[datetime] = None
    is_recurring: bool = False


class TransactionOut(BaseModel):
    id: str
    amount: float
    txn_type: str
    category_name: str
    description: str
    notes: str
    payment_method: str
    occurred_on: datetime
    is_recurring: bool
    source: str
    ai_flagged_anomaly: bool

    class Config:
        from_attributes = True


class NLParseRequest(BaseModel):
    text: str


class NLParseResult(BaseModel):
    amount: Optional[float] = None
    txn_type: str = "expense"
    category_name: Optional[str] = None
    description: Optional[str] = None
    occurred_on: Optional[datetime] = None
    payment_method: Optional[str] = None
    confidence: str = "low"  # low | medium | high
    used_ai: bool = False
    raw_text: str = ""


# ---------- Budgets ----------
class BudgetCategoryIn(BaseModel):
    category_name: str
    allocated_amount: float = Field(ge=0)


class BudgetIn(BaseModel):
    month: str  # 'YYYY-MM'
    period: str = "monthly"
    categories: list[BudgetCategoryIn]


class BudgetCategoryOut(BudgetCategoryIn):
    spent: float = 0
    percent_used: float = 0
    status: str = "ok"  # ok | warning | high_warning | overspent

    class Config:
        from_attributes = True


class BudgetOut(BaseModel):
    id: str
    month: str
    period: str
    categories: list[BudgetCategoryOut]

    class Config:
        from_attributes = True


# ---------- Savings Goals ----------
class GoalIn(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    current_amount: float = 0
    deadline: Optional[datetime] = None


class GoalOut(BaseModel):
    id: str
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[datetime]
    progress_percent: float
    required_monthly_saving: Optional[float] = None

    class Config:
        from_attributes = True


class GoalContribution(BaseModel):
    amount: float = Field(gt=0)


# ---------- AI Assistant ----------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    used_ai: bool


# ---------- Analytics ----------
class SummaryOut(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    savings_rate: float
    budget_usage_percent: Optional[float]
    top_categories: list[dict]
