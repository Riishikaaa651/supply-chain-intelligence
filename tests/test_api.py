from fastapi.testclient import TestClient
from src.api.main import app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_predict_delay_ok():
    r = client.post("/predict/delay", json={"order_item_id": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["shipping_mode"] == "Standard Class"
    assert body["risk_level"] == "Low"
    assert 0 <= body["delay_prob"] <= 1


def test_predict_shortage_ok():
    r = client.post("/predict/shortage", json={"order_item_id": 176147})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "High"
    assert body["product_name"] == "Adult dog supplies"


def test_unknown_order_returns_404():
    r = client.post("/predict/delay", json={"order_item_id": 99999999})
    assert r.status_code == 404


def test_invalid_order_id_returns_422():
    r = client.post("/predict/delay", json={"order_item_id": 0})
    assert r.status_code == 422


def test_short_whatif_question_returns_422():
    r = client.post("/whatif", json={"order_item_id": 2, "risk_type": "delay", "question": "hi"})
    assert r.status_code == 422


def test_summary_total_orders():
    r = client.get("/summary")
    assert r.status_code == 200
    assert r.json()["total_orders"] == 172762


def test_risky_orders_filter_by_shipping_mode():
    r = client.get("/orders/risky", params={"risk_type": "delay", "risk_level": "Medium",
                                            "shipping_mode": "Same Day", "limit": 5})
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert len(rows) > 0
    assert all(row["shipping_mode"] == "Same Day" for row in rows)