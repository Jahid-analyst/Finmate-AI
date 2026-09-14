"""
AI financial assistant (spec section 17).

Architecture (spec section 30): the assistant NEVER gets raw DB access or
the whole database. It only receives a small, structured JSON snapshot of
THIS user's current data, built server-side. This keeps answers grounded in
real numbers and keeps other users' data completely out of reach.
"""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.llm_client import chat_completion
from app.analytics import (budget_status, financial_health_score,
                            forecast_end_of_month, summary_for_month)

SYSTEM_PROMPT = """You are FinMate AI, a friendly personal-finance assistant for users in
Bangladesh (amounts are in BDT / Taka, symbol ৳). You are given a JSON snapshot of the
user's OWN financial data for the current month - never assume any data beyond what is
given. Answer their question using ONLY these numbers. Be concise, warm, and practical.

Hard rules:
- You are not a licensed financial advisor; do not present suggestions as guarantees.
- Never claim access to bank accounts, investments, or data not present in the snapshot.
- If the snapshot doesn't contain what's needed to answer, say so honestly.
- Keep responses under ~120 words unless the user asks for detail.
- Respond in the same language the user asked in (Bengali or English)."""


def build_context(db: Session, user_id: str) -> dict:
    now = datetime.utcnow()
    month_str = f"{now.year}-{now.month:02d}"
    return {
        "current_month": month_str,
        "summary": summary_for_month(db, user_id, now.year, now.month),
        "budgets": budget_status(db, user_id, month_str),
        "financial_health": financial_health_score(db, user_id),
        "forecast": forecast_end_of_month(db, user_id),
    }


def _rule_based_answer(message: str, context: dict) -> str:
    """Simple template answers so the assistant still works with zero AI config."""
    lowered = message.lower()
    summary = context["summary"]

    if "save" in lowered or "সেভ" in message or "সঞ্চয়" in message:
        rate = summary["savings_rate"]
        return (
            f"This month your income is ৳{summary['total_income']:.0f} and expenses are "
            f"৳{summary['total_expense']:.0f}, giving you a savings rate of {rate}%. "
            f"Your current balance is ৳{summary['balance']:.0f}."
        )
    if "most" in lowered or "কোন খাতে" in message or "top" in lowered or "কোথায়" in message:
        if summary["top_categories"]:
            top = summary["top_categories"][0]
            return f"Your top spending category this month is {top['category']} at ৳{top['amount']:.0f}."
        return "You don't have any recorded expenses this month yet."
    if "overspend" in lowered or "budget" in lowered:
        overspent = [b for b in context["budgets"] if b["status"] in ("overspent", "high_warning")]
        if overspent:
            names = ", ".join(b["category_name"] for b in overspent)
            return f"You're close to or over budget in: {names}. Consider slowing spending there this month."
        return "You're currently within budget in all categories you've set a budget for."
    if "health" in lowered or "score" in lowered:
        score = context["financial_health"]
        return f"Your financial health score is {score['total_score']}/100 this month."
    if "forecast" in lowered or "predict" in lowered:
        return context["forecast"]["message"]

    return (
        f"This month: income ৳{summary['total_income']:.0f}, expenses ৳{summary['total_expense']:.0f}, "
        f"balance ৳{summary['balance']:.0f}. Ask me about your top spending category, budget status, "
        f"savings rate, or financial health score for more detail."
    )


def answer(db: Session, user_id: str, message: str) -> tuple[str, bool]:
    """Returns (reply_text, used_ai)."""
    context = build_context(db, user_id)
    user_prompt = f"User's data snapshot:\n{json.dumps(context, default=str)}\n\nUser question: {message}"

    ai_reply = chat_completion(SYSTEM_PROMPT, user_prompt)
    if ai_reply:
        return ai_reply.strip(), True

    return _rule_based_answer(message, context), False
