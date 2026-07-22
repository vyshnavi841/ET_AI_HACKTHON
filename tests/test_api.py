import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

from backend.sample_generator import generate_sample_banknotes

client = TestClient(app)

def setup_module():
    init_db()
    generate_sample_banknotes()

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

def test_stats_endpoint():
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "counterfeit_detection_rate_pct" in data

def test_scan_sample_endpoint():
    response = client.post(
        "/api/v1/scan",
        data={
            "sample_key": "usd_100_genuine",
            "template_key": "USD_100",
            "operator_id": "TEST_OFFICER"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["verdict"] in ["GENUINE", "SUSPECT", "COUNTERFEIT"]
    assert "visualizations" in data
    assert "annotated_scan_url" in data["visualizations"]

def test_seizures_endpoint():
    response = client.get("/api/v1/seizures")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
