from tests.conftest import auth_headers, make_user


def add(client, headers, query="Analyze Tesla", **extra):
    r = client.post("/history", json={"query": query, **extra}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def two_users(client):
    make_user(client)
    make_user(client, email="bob@example.com", username="bob")
    return auth_headers(client, "alice"), auth_headers(client, "bob")


def test_history_requires_auth(client):
    assert client.get("/history").status_code == 401
    assert client.post("/history", json={"query": "x"}).status_code == 401


def test_create_and_get_entry(client):
    make_user(client)
    h = auth_headers(client)
    item = add(
        client, h, market="US", analysis_period="1Y",
        result_summary="Bullish", result_data={"score": 0.8},
    )
    r = client.get(f"/history/{item['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["result_data"] == {"score": 0.8}
    assert r.json()["market"] == "US"


def test_empty_query_rejected(client):
    make_user(client)
    r = client.post("/history", json={"query": ""}, headers=auth_headers(client))
    assert r.status_code == 422


def test_users_only_see_their_own_history(client):
    alice, bob = two_users(client)
    add(client, alice, "Alice query")
    add(client, bob, "Bob query")
    a = client.get("/history", headers=alice).json()
    b = client.get("/history", headers=bob).json()
    assert a["total"] == 1 and a["items"][0]["query"] == "Alice query"
    assert b["total"] == 1 and b["items"][0]["query"] == "Bob query"


def test_cannot_read_or_delete_other_users_entry(client):
    alice, bob = two_users(client)
    item = add(client, alice, "Private research")
    assert client.get(f"/history/{item['id']}", headers=bob).status_code == 404
    assert client.delete(f"/history/{item['id']}", headers=bob).status_code == 404
    assert client.get(f"/history/{item['id']}", headers=alice).status_code == 200


def test_delete_entry(client):
    make_user(client)
    h = auth_headers(client)
    item = add(client, h)
    assert client.delete(f"/history/{item['id']}", headers=h).status_code == 204
    assert client.get(f"/history/{item['id']}", headers=h).status_code == 404


def test_clear_history_only_affects_current_user(client):
    alice, bob = two_users(client)
    add(client, alice, "a1")
    add(client, alice, "a2")
    add(client, bob, "b1")
    assert client.delete("/history", headers=alice).status_code == 204
    assert client.get("/history", headers=alice).json()["total"] == 0
    assert client.get("/history", headers=bob).json()["total"] == 1


def test_pagination_and_newest_first(client):
    make_user(client)
    h = auth_headers(client)
    for i in range(5):
        add(client, h, f"query {i}")
    r = client.get("/history?page=1&page_size=2", headers=h).json()
    assert r["total"] == 5 and len(r["items"]) == 2
    assert r["items"][0]["query"] == "query 4"
    last = client.get("/history?page=3&page_size=2", headers=h).json()
    assert len(last["items"]) == 1


def test_search_and_market_filter(client):
    make_user(client)
    h = auth_headers(client)
    add(client, h, "Tesla outlook", market="US")
    add(client, h, "Tata Motors outlook", market="India")
    assert client.get("/history?q=tesla", headers=h).json()["total"] == 1
    assert client.get("/history?market=india", headers=h).json()["total"] == 1
