
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_invalid_request():
    response = client.post(
        "/api/technical-analysis",
        json={}
    )

    assert response.status_code == 422


def test_successful_technical_analysis():
    response = client.post(
        "/api/technical-analysis",
        json={
            "symbol": "INFY",
            "market": "NSE",
            "period": "1Y"
        }
    )

    assert response.status_code == 200

    result = response.json()

    # Basic response checks
    assert result["symbol"] == "INFY"
    assert result["analysis_status"] == "completed"

    # Analysis sections
    assert "indicators" in result
    assert "signals" in result
    assert "technical_conditions" in result

    assert result["records_analyzed"] > 0

    # Data quality checks
    assert "data_quality" in result

    assert result["data_quality"]["validation_status"] == "clean"

    assert result["data_quality"]["rows_received"] > 0

    assert result["data_quality"]["data_source"] != "unknown"
