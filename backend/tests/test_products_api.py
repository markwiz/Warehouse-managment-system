"""Product endpoints and persistence, against a real PostgreSQL test database."""

from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Product
from app.repositories import product as product_repo
from app.schemas.product import ProductCreate
from app.services import product as product_service
from app.services.product import DuplicateSkuError


def create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"sku": "SKU-1", "name": "Pallet jack", "unit_price": "199.99"} | overrides
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_product(db_client: TestClient) -> None:
    body = create(db_client, sku=" ab-12 ", description="Manual, 2.5t")
    assert body["id"] > 0
    assert body["sku"] == "AB-12"
    assert body["name"] == "Pallet jack"
    assert body["description"] == "Manual, 2.5t"
    assert Decimal(body["unit_price"]) == Decimal("199.99")
    assert body["created_at"] and body["updated_at"]


@pytest.mark.parametrize("duplicate", ["SKU-1", "sku-1", "  Sku-1 "])
def test_duplicate_sku_conflict(db_client: TestClient, duplicate: str) -> None:
    create(db_client, sku="SKU-1")
    response = db_client.post(
        "/api/products", json={"sku": duplicate, "name": "Other", "unit_price": "1"}
    )
    assert response.status_code == 409
    assert "SKU-1" in response.json()["detail"]


def test_create_invalid_payload(db_client: TestClient) -> None:
    response = db_client.post("/api/products", json={"sku": "-bad", "name": "", "unit_price": -1})
    assert response.status_code == 422
    assert db_client.get("/api/products").json() == []


def test_get_product(db_client: TestClient) -> None:
    created = create(db_client)
    response = db_client.get(f"/api/products/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_product(db_client: TestClient) -> None:
    response = db_client.get("/api/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product 999 not found"}


def test_list_products_ordered_and_paginated(db_client: TestClient) -> None:
    ids = [create(db_client, sku=f"SKU-{i}")["id"] for i in range(5)]
    assert [p["id"] for p in db_client.get("/api/products").json()] == ids
    page = db_client.get("/api/products", params={"offset": 1, "limit": 2}).json()
    assert [p["id"] for p in page] == ids[1:3]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 201}, {"offset": -1}])
def test_list_products_invalid_query(db_client: TestClient, params: dict[str, int]) -> None:
    assert db_client.get("/api/products", params=params).status_code == 422


def test_update_product_partially(db_client: TestClient) -> None:
    created = create(db_client, description="Old")
    response = db_client.patch(f"/api/products/{created['id']}", json={"unit_price": "149.50"})
    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["unit_price"]) == Decimal("149.50")
    assert body["name"] == created["name"]
    assert body["description"] == "Old"
    assert body["sku"] == created["sku"]
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > created["updated_at"]


def test_update_clears_description(db_client: TestClient) -> None:
    created = create(db_client, description="Old")
    response = db_client.patch(f"/api/products/{created['id']}", json={"description": None})
    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_missing_product(db_client: TestClient) -> None:
    response = db_client.patch("/api/products/999", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload", [{}, {"sku": "NEW-1"}, {"name": None}, {"unit_price": "-1"}, {"id": 5}]
)
def test_update_invalid_payload(db_client: TestClient, payload: dict[str, Any]) -> None:
    created = create(db_client)
    response = db_client.patch(f"/api/products/{created['id']}", json=payload)
    assert response.status_code == 422
    assert db_client.get(f"/api/products/{created['id']}").json() == created


def test_unique_constraint_enforced_without_precheck(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulates two concurrent inserts: the DB constraint still yields DuplicateSkuError."""
    data = ProductCreate(sku="RACE-1", name="A", unit_price=Decimal("1"))
    product_service.create_product(db_session, data)
    monkeypatch.setattr(product_repo, "get_by_sku", lambda db, sku: None)
    with pytest.raises(DuplicateSkuError):
        product_service.create_product(db_session, data)


def test_negative_price_rejected_by_database(db_session: Session) -> None:
    db_session.add(Product(sku="NEG-1", name="A", unit_price=Decimal("-1")))
    with pytest.raises(IntegrityError):
        db_session.flush()
