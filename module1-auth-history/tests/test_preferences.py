from tests.conftest import auth_headers, make_user


def two_users(client):
    make_user(client)
    make_user(client, email="bob@example.com", username="bob")
    return auth_headers(client, "alice"), auth_headers(client, "bob")


def test_preferences_require_auth(client):
    assert client.get("/preferences").status_code == 401
    assert client.put(
        "/preferences", json={"preferred_market": "NSE", "analysis_period": "1Y"}
    ).status_code == 401
    assert client.delete("/preferences").status_code == 401


def test_new_user_gets_defaults(client):
    make_user(client)
    r = client.get("/preferences", headers=auth_headers(client))
    assert r.status_code == 200
    body = r.json()
    assert body["preferred_market"] == "NSE"
    assert body["analysis_period"] == "1Y"
    assert body["is_default"] is True


def test_save_and_read_back(client):
    make_user(client)
    h = auth_headers(client)
    r = client.put(
        "/preferences", json={"preferred_market": "NASDAQ", "analysis_period": "6M"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["is_default"] is False
    got = client.get("/preferences", headers=h).json()
    assert got["preferred_market"] == "NASDAQ"
    assert got["analysis_period"] == "6M"
    assert got["is_default"] is False


def test_update_overwrites_not_duplicates(client):
    make_user(client)
    h = auth_headers(client)
    client.put("/preferences", json={"preferred_market": "NSE", "analysis_period": "1M"}, headers=h)
    client.put("/preferences", json={"preferred_market": "BSE", "analysis_period": "5Y"}, headers=h)
    got = client.get("/preferences", headers=h).json()
    assert (got["preferred_market"], got["analysis_period"]) == ("BSE", "5Y")


def test_case_insensitive_input_is_normalised(client):
    make_user(client)
    h = auth_headers(client)
    r = client.put(
        "/preferences", json={"preferred_market": " nyse ", "analysis_period": "3m"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["preferred_market"] == "NYSE"
    assert r.json()["analysis_period"] == "3M"


def test_invalid_values_rejected(client):
    make_user(client)
    h = auth_headers(client)
    bad = [
        {"preferred_market": "LSE", "analysis_period": "1Y"},
        {"preferred_market": "NSE", "analysis_period": "10Y"},
        {"preferred_market": "NSE"},
        {"analysis_period": "1Y"},
        {},
    ]
    for payload in bad:
        assert client.put("/preferences", json=payload, headers=h).status_code == 422


def test_users_have_separate_preferences(client):
    alice, bob = two_users(client)
    client.put("/preferences", json={"preferred_market": "NYSE", "analysis_period": "3Y"}, headers=alice)
    b = client.get("/preferences", headers=bob).json()
    assert b["is_default"] is True and b["preferred_market"] == "NSE"
    a = client.get("/preferences", headers=alice).json()
    assert a["preferred_market"] == "NYSE"


def test_reset_returns_defaults(client):
    make_user(client)
    h = auth_headers(client)
    client.put("/preferences", json={"preferred_market": "BSE", "analysis_period": "3M"}, headers=h)
    assert client.delete("/preferences", headers=h).status_code == 204
    assert client.get("/preferences", headers=h).json()["is_default"] is True
    assert client.delete("/preferences", headers=h).status_code == 204  # idempotent


def test_history_uses_saved_preferences_when_omitted(client):
    make_user(client)
    h = auth_headers(client)
    client.put("/preferences", json={"preferred_market": "NASDAQ", "analysis_period": "6M"}, headers=h)
    r = client.post("/history", json={"query": "Analyze Apple"}, headers=h)
    assert r.status_code == 201
    assert r.json()["market"] == "NASDAQ"
    assert r.json()["analysis_period"] == "6M"


def test_history_explicit_values_win_over_preferences(client):
    make_user(client)
    h = auth_headers(client)
    client.put("/preferences", json={"preferred_market": "NASDAQ", "analysis_period": "6M"}, headers=h)
    r = client.post(
        "/history", json={"query": "Analyze TCS", "market": "NSE", "analysis_period": "1Y"}, headers=h
    )
    assert r.json()["market"] == "NSE" and r.json()["analysis_period"] == "1Y"


def test_history_without_preferences_stays_empty(client):
    make_user(client)
    h = auth_headers(client)
    r = client.post("/history", json={"query": "Analyze Infosys"}, headers=h)
    assert r.json()["market"] is None and r.json()["analysis_period"] is None
