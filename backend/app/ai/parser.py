"""
Natural-language expense/income entry (spec section 11).

e.g. "I spent 250 taka on lunch at a restaurant today"
     "আজকে রিকশায় ১২০ টাকা খরচ হয়েছে"

Approach: try the LLM first (it's genuinely better at free-form language
extraction than regex, especially mixed Bengali/English). If the LLM is not
configured or fails, fall back to a regex + keyword rule-based extractor so
the feature keeps working offline.
"""
import re
from datetime import datetime

from app.ai.categorizer import categorize
from app.ai.llm_client import chat_completion_json

BENGALI_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

INCOME_HINTS = ["salary", "পেলাম", "পেয়েছি", "income", "পাইলাম", "বেতন পেয়েছি", "earned", "got paid"]

PAYMENT_HINTS = {
    "cash": ["cash", "নগদ টাকা", "ক্যাশ"],
    "card": ["card", "কার্ড"],
    "mfs": ["bkash", "nagad", "rocket", "বিকাশ", "নগদ", "রকেট", "mfs"],
    "bank": ["bank", "ব্যাংক", "transfer"],
}


def _extract_amount(text: str) -> float | None:
    normalized = text.translate(BENGALI_DIGIT_MAP)
    # matches "250", "1,500", "1500.50", optionally followed by taka/tk/৳
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)", normalized)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_payment_method(text: str) -> str | None:
    lowered = text.lower()
    for method, hints in PAYMENT_HINTS.items():
        for hint in hints:
            if hint.lower() in lowered:
                return method
    return None


def _guess_txn_type(text: str) -> str:
    lowered = text.lower()
    for hint in INCOME_HINTS:
        if hint.lower() in lowered:
            return "income"
    return "expense"


def _rule_based_parse(text: str, allowed_expense_categories: list[str],
                       allowed_income_categories: list[str]) -> dict:
    amount = _extract_amount(text)
    txn_type = _guess_txn_type(text)
    allowed = allowed_income_categories if txn_type == "income" else allowed_expense_categories
    category, _ = categorize(text, txn_type, allowed)
    payment_method = _extract_payment_method(text)

    return {
        "amount": amount,
        "txn_type": txn_type,
        "category_name": category,
        "description": text.strip()[:200],
        "occurred_on": datetime.utcnow().isoformat(),
        "payment_method": payment_method,
        "confidence": "medium" if amount else "low",
        "used_ai": False,
    }


def parse_transaction_text(text: str, allowed_expense_categories: list[str],
                            allowed_income_categories: list[str]) -> dict:
    system = (
        "You extract a single personal finance transaction from a user's message, "
        "which may be in English, Bengali, or a mix. Amounts are in Bangladeshi Taka (BDT). "
        "Respond ONLY with a JSON object with keys: "
        "amount (number or null), txn_type ('income' or 'expense'), "
        "category_name (pick the closest match from the allowed list, or 'Other'), "
        "description (short, in the message's original language), "
        "payment_method ('cash', 'bank', 'card', 'mfs', or null if unclear). "
        "Do not include any other text."
    )
    user = (
        f"Message: \"{text}\"\n"
        f"Allowed expense categories: {', '.join(allowed_expense_categories)}\n"
        f"Allowed income categories: {', '.join(allowed_income_categories)}"
    )
    ai_result = chat_completion_json(system, user)

    if ai_result and ai_result.get("amount") is not None:
        try:
            amount = float(ai_result["amount"])
        except (TypeError, ValueError):
            amount = None
        if amount:
            return {
                "amount": amount,
                "txn_type": ai_result.get("txn_type", "expense"),
                "category_name": ai_result.get("category_name") or "Other",
                "description": (ai_result.get("description") or text)[:200],
                "occurred_on": datetime.utcnow().isoformat(),
                "payment_method": ai_result.get("payment_method"),
                "confidence": "high",
                "used_ai": True,
            }

    # Fallback: rule-based extraction keeps the feature working without AI.
    return _rule_based_parse(text, allowed_expense_categories, allowed_income_categories)
