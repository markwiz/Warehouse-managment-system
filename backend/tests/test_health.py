from fastapi.testclient import TestClient

from app.agents.graph import build_graph
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_graph_compiles() -> None:
    assert build_graph().invoke({"messages": []}) == {"messages": []}
