def test_register_and_login(client):
    resp = client.post("/auth/register", json={
        "email": "alice@example.com", "password": "secret123", "full_name": "Alice"
    })
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp = client.post("/auth/login", data={"username": "alice@example.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={"email": "bob@example.com", "password": "secret123", "full_name": "Bob"})
    resp = client.post("/auth/register", json={"email": "bob@example.com", "password": "secret123", "full_name": "Bob"})
    assert resp.status_code == 400


def test_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "carl@example.com", "password": "secret123", "full_name": "Carl"})
    resp = client.post("/auth/login", data={"username": "carl@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client):
    client, headers = auth_client
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@finmate.ai"


def test_onboarding_profile_update(auth_client):
    client, headers = auth_client
    resp = client.put("/auth/profile", headers=headers, json={
        "user_type": "student", "monthly_income": 12000, "preferred_language": "en",
        "preferred_currency": "BDT", "savings_target": 5000,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarding_complete"] is True
    assert body["monthly_income"] == 12000
