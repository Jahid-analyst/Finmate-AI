def test_create_and_list_transaction(auth_client):
    client, headers = auth_client
    resp = client.post("/transactions", headers=headers, json={
        "amount": 250, "txn_type": "expense", "category_name": "Food",
        "description": "Lunch", "payment_method": "cash",
    })
    assert resp.status_code == 201
    txn = resp.json()
    assert txn["amount"] == 250
    assert txn["source"] == "manual"

    resp = client.get("/transactions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_and_delete_transaction(auth_client):
    client, headers = auth_client
    create = client.post("/transactions", headers=headers, json={
        "amount": 100, "txn_type": "expense", "category_name": "Food", "payment_method": "cash",
    })
    txn_id = create.json()["id"]

    update = client.put(f"/transactions/{txn_id}", headers=headers, json={
        "amount": 150, "txn_type": "expense", "category_name": "Transportation", "payment_method": "mfs",
    })
    assert update.status_code == 200
    assert update.json()["amount"] == 150
    assert update.json()["category_name"] == "Transportation"

    delete = client.delete(f"/transactions/{txn_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/transactions", headers=headers)
    assert len(listing.json()) == 0


def test_users_cannot_see_each_others_transactions(client):
    client.post("/auth/register", json={"email": "u1@x.com", "password": "password1", "full_name": "U1"})
    t1 = client.post("/auth/login", data={"username": "u1@x.com", "password": "password1"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    client.post("/auth/register", json={"email": "u2@x.com", "password": "password2", "full_name": "U2"})
    t2 = client.post("/auth/login", data={"username": "u2@x.com", "password": "password2"}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    client.post("/transactions", headers=h1, json={
        "amount": 500, "txn_type": "expense", "category_name": "Food", "payment_method": "cash",
    })

    resp = client.get("/transactions", headers=h2)
    assert resp.status_code == 200
    assert resp.json() == []


def test_nl_transaction_parse_fallback_english(auth_client):
    """No LLM_API_KEY is set in the test env, so this exercises the rule-based fallback."""
    client, headers = auth_client
    resp = client.post("/transactions/parse", headers=headers, json={
        "text": "I spent 250 taka on lunch at a restaurant today"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 250
    assert body["txn_type"] == "expense"
    assert body["category_name"] == "Food"
    assert body["used_ai"] is False


def test_nl_transaction_parse_bengali(auth_client):
    client, headers = auth_client
    resp = client.post("/transactions/parse", headers=headers, json={
        "text": "আজকে রিকশায় ১২০ টাকা খরচ হয়েছে"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 120
    assert body["category_name"] == "Transportation"


def test_invalid_txn_type_rejected(auth_client):
    client, headers = auth_client
    resp = client.post("/transactions", headers=headers, json={
        "amount": 100, "txn_type": "not_a_type", "category_name": "Food", "payment_method": "cash",
    })
    assert resp.status_code == 400
