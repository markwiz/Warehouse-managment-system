from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agents.graph import build_graph


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_ok(client: TestClient, healthy_db: MagicMock) -> None:
    response = client.get("/api/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    healthy_db.execute.assert_called_once()


def test_health_db_unavailable(client: TestClient, broken_db: MagicMock) -> None:
    response = client.get("/api/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_graph_compiles() -> None:
    assert build_graph().invoke({"messages": []}) == {"messages": []}
