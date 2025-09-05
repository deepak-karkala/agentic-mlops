from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Agentic MLOps API"}


def test_thin_slice_workflow() -> None:
    payload = {"messages": [{"role": "user", "content": "Hello"}]}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)
    assert data["messages"][-1]["role"] == "assistant"
