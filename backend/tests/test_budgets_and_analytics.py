from datetime import datetime


def _current_month_str():
    now = datetime.utcnow()
    return f"{now.year}-{now.month:02d}"


def test_budget_creation_and_usage_percent(auth_client):
    client, headers = auth_client
    month = _current_month_str()

    client.post("/budgets", headers=headers, json={
        "month": month, "period": "monthly",
        "categories": [{"category_name": "Food", "allocated_amount": 1000}],
    })

    client.post("/transactions", headers=headers, json={
        "amount": 750, "txn_type": "expense", "category_name": "Food", "payment_method": "cash",
    })

    resp = client.get(f"/budgets/{month}", headers=headers)
    assert resp.status_code == 200
    cat = resp.json()["categories"][0]
    assert cat["spent"] == 750
    assert cat["percent_used"] == 75.0
    assert cat["status"] == "warning"


def test_budget_overspent_status(auth_client):
    client, headers = auth_client
    month = _current_month_str()
    client.post("/budgets", headers=headers, json={
        "month": month, "period": "monthly",
        "categories": [{"category_name": "Entertainment", "allocated_amount": 500}],
    })
    client.post("/transactions", headers=headers, json={
        "amount": 600, "txn_type": "expense", "category_name": "Entertainment", "payment_method": "card",
    })
    resp = client.get(f"/budgets/{month}", headers=headers)
    cat = resp.json()["categories"][0]
    assert cat["status"] == "overspent"


def test_savings_goal_progress_calculation(auth_client):
    client, headers = auth_client
    resp = client.post("/goals", headers=headers, json={
        "name": "Laptop", "target_amount": 80000, "current_amount": 20000,
    })
    assert resp.status_code == 201
    assert resp.json()["progress_percent"] == 25.0

    contrib = client.post(f"/goals/{resp.json()['id']}/contribute", headers=headers, json={"amount": 10000})
    assert contrib.json()["current_amount"] == 30000
    assert contrib.json()["progress_percent"] == 37.5


def test_analytics_summary_reflects_real_transactions(auth_client):
    client, headers = auth_client
    client.post("/transactions", headers=headers, json={
        "amount": 30000, "txn_type": "income", "category_name": "Salary", "payment_method": "bank",
    })
    client.post("/transactions", headers=headers, json={
        "amount": 10000, "txn_type": "expense", "category_name": "Food", "payment_method": "cash",
    })

    resp = client.get("/analytics/summary", headers=headers)
    body = resp.json()
    assert body["total_income"] == 30000
    assert body["total_expense"] == 10000
    assert body["balance"] == 20000
    assert body["savings_rate"] > 0


def test_ai_chat_fallback_works_without_api_key(auth_client):
    """No LLM key configured in test env -> rule-based assistant must still answer."""
    client, headers = auth_client
    client.post("/transactions", headers=headers, json={
        "amount": 30000, "txn_type": "income", "category_name": "Salary", "payment_method": "bank",
    })
    resp = client.post("/ai/chat", headers=headers, json={"message": "How much can I save this month?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["used_ai"] is False
    assert "৳" in body["reply"] or "savings" in body["reply"].lower()


def test_financial_health_score_returns_explainable_breakdown(auth_client):
    client, headers = auth_client
    client.post("/transactions", headers=headers, json={
        "amount": 30000, "txn_type": "income", "category_name": "Salary", "payment_method": "bank",
    })
    resp = client.get("/analytics/health-score", headers=headers)
    body = resp.json()
    assert 0 <= body["total_score"] <= 100
    assert body["savings_score"] + body["budget_score"] + body["cashflow_score"] + body["goals_score"] == body["total_score"]
