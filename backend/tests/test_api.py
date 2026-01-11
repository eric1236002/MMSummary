# tests/test_api.py
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to MMSummary API"}

def test_DB_health():
    response = client.get("/DB_health")
    assert response.status_code == 200, f"Detail: {response.json()}"
    assert response.json() == {"status": "ok"}


def test_split_endpoint():
    payload = {
        "text": "Hello mapping test.",
        "chunk_size": 100,
        "chunk_overlap": 0
    }
    response = client.post("/split", json=payload)
    assert response.status_code == 200, f"Detail: {response.json()}"
    assert "chunks" in response.json()


def test_summarize_endpoint():
    payload = {
        "text": "Hello mapping test.",
        "model": "google/gemma-3-27b-it:free",
        "chunk_size_1": 100,
        "chunk_overlap_1": 0,
        "chunk_size_2": 100,
        "chunk_overlap_2": 0,
        "token_max": 4000,
        "use_map": False,
        "test_mode": True
    }
    response = client.post("/summarize", json=payload)
    assert response.status_code == 200, f"Detail: {response.json()}"
    assert "summary" in response.json()


def test_history_endpoint():
    response = client.get("/history")
    assert response.status_code == 200, f"Detail: {response.json()}"
    assert isinstance(response.json(), list)

