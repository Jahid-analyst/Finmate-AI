import enum
import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                         Integer, String, Text)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserType(str, enum.Enum):
    student = "student"
    employee = "employee"
    household = "household"
    freelancer = "freelancer"
    business_owner = "business_owner"


class TxnType(str, enum.Enum):
    income = "income"
    expense = "expense"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    bank = "bank"
    card = "card"
    mfs = "mfs"  # mobile financial service (bKash, Nagad, etc.)
    other = "other"


class BudgetPeriod(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("FinancialInsight", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    recurring = relationship("RecurringTransaction", back_populates="user", cascade="all, delete-orphan")
    scores = relationship("FinancialScore", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    user_type = Column(Enum(UserType), default=UserType.student)
    age_range = Column(String, nullable=True)
    monthly_income = Column(Float, default=0.0)
    income_frequency = Column(String, default="monthly")
    preferred_language = Column(String, default="en")  # 'en' or 'bn'
    preferred_currency = Column(String, default="BDT")
    savings_target = Column(Float, default=0.0)
    financial_goal_text = Column(String, nullable=True)
    onboarding_complete = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    txn_type = Column(Enum(TxnType), nullable=False)
    icon = Column(String, default="tag")
    is_default = Column(Boolean, default=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # null = global default category


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    txn_type = Column(Enum(TxnType), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    category_name = Column(String, nullable=False)  # denormalized for simple querying
    description = Column(String, default="")
    notes = Column(Text, default="")
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.cash)
    occurred_on = Column(DateTime, default=datetime.utcnow, index=True)
    is_recurring = Column(Boolean, default=False)
    source = Column(String, default="manual")  # 'manual' | 'ai_nl' | 'seed'
    ai_flagged_anomaly = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    period = Column(Enum(BudgetPeriod), default=BudgetPeriod.monthly)
    month = Column(String, nullable=False)  # 'YYYY-MM'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="budgets")
    categories = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(String, primary_key=True, default=gen_uuid)
    budget_id = Column(String, ForeignKey("budgets.id"), nullable=False)
    category_name = Column(String, nullable=False)
    allocated_amount = Column(Float, nullable=False)

    budget = relationship("Budget", back_populates="categories")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    category = Column(String, default="general")  # budget, goal, anomaly, system
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class FinancialInsight(Base):
    __tablename__ = "financial_insights"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    insight_type = Column(String, nullable=False)  # spending_increase, savings_opportunity, etc.
    message = Column(String, nullable=False)
    severity = Column(String, default="info")  # info, warning, positive
    data_snapshot = Column(Text, default="{}")  # JSON string of the numbers behind the insight
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="insights")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    txn_type = Column(Enum(TxnType), nullable=False)
    category_name = Column(String, nullable=False)
    description = Column(String, default="")
    frequency = Column(String, default="monthly")  # weekly | monthly
    next_due = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="recurring")


class FinancialScore(Base):
    __tablename__ = "financial_scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    month = Column(String, nullable=False)  # 'YYYY-MM'
    total_score = Column(Integer, nullable=False)
    savings_score = Column(Integer, nullable=False)
    budget_score = Column(Integer, nullable=False)
    cashflow_score = Column(Integer, nullable=False)
    goals_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scores")
