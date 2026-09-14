"""
Automatic transaction categorization (spec section 13).

Strategy: keyword rules first (fast, free, deterministic, works offline).
If no rule matches and an LLM is configured, ask the LLM to pick from the
user's allowed category list. Otherwise fall back to "Other".
"""
from app.ai.llm_client import chat_completion

EXPENSE_KEYWORDS: dict[str, list[str]] = {
    "Food": ["lunch", "dinner", "breakfast", "restaurant", "biryani", "food", "snack",
             "coffee", "tea", "cafe", "khabar", "নাস্তা", "খাবার", "রেস্টুরেন্ট", "চা"],
    "Transportation": ["uber", "rickshaw", "rikshaw", "bus", "cng", "taxi", "fuel",
                        "petrol", "train", "ride", "রিকশা", "বাস", "সিএনজি", "ভাড়া"],
    "Education": ["tuition", "book", "course", "exam fee", "textbook", "coaching",
                  "বই", "কোচিং", "টিউশন"],
    "Utilities": ["electricity", "gas bill", "water bill", "internet", "wifi", "broadband",
                  "বিদ্যুৎ", "গ্যাস", "পানি", "ইন্টারনেট"],
    "Entertainment": ["netflix", "movie", "cinema", "spotify", "game", "subscription",
                       "সিনেমা"],
    "Rent": ["rent", "hostel", "ভাড়া বাসা", "বাসা ভাড়া"],
    "Healthcare": ["medicine", "doctor", "hospital", "pharmacy", "ডাক্তার", "ওষুধ"],
    "Shopping": ["shopping", "clothes", "shirt", "shoes", "amazon", "daraz"],
    "Mobile Recharge": ["recharge", "flexiload", "মোবাইল রিচার্জ", "রিচার্জ"],
    "Family Support": ["family", "parents", "পরিবার"],
}

INCOME_KEYWORDS: dict[str, list[str]] = {
    "Salary": ["salary", "beton", "বেতন"],
    "Freelancing": ["freelance", "client payment", "upwork", "fiverr"],
    "Tuition Income": ["tuition income", "tutoring"],
    "Business": ["business", "sales", "profit"],
    "Allowance": ["allowance", "pocket money", "হাত খরচ"],
    "Bonus": ["bonus", "eid bonus", "bonus payment"],
    "Investment Income": ["dividend", "interest income", "investment return"],
}

DEFAULT_EXPENSE_CATEGORY = "Other"
DEFAULT_INCOME_CATEGORY = "Other Income"


def _rule_based(text: str, keyword_map: dict[str, list[str]]) -> str | None:
    lowered = text.lower()
    for category, keywords in keyword_map.items():
        for kw in keywords:
            if kw.lower() in lowered:
                return category
    return None


def categorize(text: str, txn_type: str, allowed_categories: list[str]) -> tuple[str, bool]:
    """
    Returns (category_name, used_ai).
    txn_type: 'income' | 'expense'
    """
    keyword_map = INCOME_KEYWORDS if txn_type == "income" else EXPENSE_KEYWORDS
    default = DEFAULT_INCOME_CATEGORY if txn_type == "income" else DEFAULT_EXPENSE_CATEGORY

    rule_result = _rule_based(text, keyword_map)
    if rule_result:
        return rule_result, False

    # AI fallback: ask the LLM to pick from the user's actual category list only.
    system = (
        "You categorize a single personal-finance transaction description into "
        "exactly one category from the provided list. Reply with ONLY the category "
        "name, nothing else. If nothing fits well, reply with 'Other'."
    )
    user = f"Transaction: \"{text}\"\nAllowed categories: {', '.join(allowed_categories)}"
    ai_result = chat_completion(system, user)
    if ai_result:
        cleaned = ai_result.strip().strip('"').strip(".")
        if cleaned in allowed_categories:
            return cleaned, True

    return default, False
