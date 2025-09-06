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
    # Should return a thread_id
    assert "thread_id" in data
    assert isinstance(data["thread_id"], str)


def test_thread_id_generation() -> None:
    """Test that thread_id is auto-generated when not provided."""
    payload = {"messages": [{"role": "user", "content": "Test message"}]}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Should auto-generate thread_id
    assert "thread_id" in data
    thread_id = data["thread_id"]
    assert isinstance(thread_id, str)
    assert len(thread_id) > 0


def test_thread_id_persistence() -> None:
    """Test that providing a thread_id returns the same thread_id."""
    custom_thread_id = "test-thread-123"
    payload = {
        "messages": [{"role": "user", "content": "Hello with custom thread"}],
        "thread_id": custom_thread_id,
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Should return the same thread_id
    assert data["thread_id"] == custom_thread_id


def test_conversation_continuity() -> None:
    """Test that conversations can continue with the same thread_id."""
    thread_id = "continuity-test"

    # First message
    payload1 = {
        "messages": [{"role": "user", "content": "Hello"}],
        "thread_id": thread_id,
    }
    response1 = client.post("/api/chat", json=payload1)
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["thread_id"] == thread_id

    # Second message with same thread_id should work
    payload2 = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": data1["messages"][-1]["content"]},
            {"role": "user", "content": "Follow up message"},
        ],
        "thread_id": thread_id,
    }
    response2 = client.post("/api/chat", json=payload2)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["thread_id"] == thread_id

    # Should have processed the follow-up message
    assert len(data2["messages"]) > 0
    assert data2["messages"][-1]["role"] == "assistant"
