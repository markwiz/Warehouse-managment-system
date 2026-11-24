"""Validation rules for product input (no database needed)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductUpdate

VALID = {"sku": "ABC-123", "name": "Pallet jack", "unit_price": "199.99"}


def make(**overrides: object) -> ProductCreate:
    return ProductCreate.model_validate(VALID | overrides)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(" ab-12 ", "AB-12"), ("x", "X"), ("A_B-9", "A_B-9"), ("9" * 64, "9" * 64)],
)
def test_sku_is_normalized(raw: str, expected: str) -> None:
    assert make(sku=raw).sku == expected


@pytest.mark.parametrize("sku", ["", "   ", "-ABC", "_ABC", "AB C", "AB/1", "ÄB", "9" * 65])
def test_invalid_sku_rejected(sku: str) -> None:
    with pytest.raises(ValidationError):
        make(sku=sku)


def test_name_is_trimmed() -> None:
    assert make(name="  Shelf  ").name == "Shelf"


@pytest.mark.parametrize("name", ["", "   ", "x" * 256])
def test_invalid_name_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        make(name=name)


def test_description_length_limit() -> None:
    assert make(description="d" * 2000).description == "d" * 2000
    with pytest.raises(ValidationError):
        make(description="d" * 2001)


def test_price_parsed_as_decimal() -> None:
    assert make(unit_price="0").unit_price == Decimal("0")
    assert make(unit_price="9999999999.99").unit_price == Decimal("9999999999.99")


@pytest.mark.parametrize("price", ["-0.01", "1.999", "10000000000.00", "abc"])
def test_invalid_price_rejected(price: str) -> None:
    with pytest.raises(ValidationError):
        make(unit_price=price)


@pytest.mark.parametrize("field", ["sku", "name", "unit_price"])
def test_required_fields(field: str) -> None:
    data = dict(VALID)
    del data[field]
    with pytest.raises(ValidationError):
        ProductCreate.model_validate(data)


@pytest.mark.parametrize("field", ["id", "created_at", "updated_at", "unknown"])
def test_create_rejects_server_and_unknown_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        make(**{field: 1})


def test_update_tracks_only_sent_fields() -> None:
    update = ProductUpdate.model_validate({"name": "New name"})
    assert update.model_dump(exclude_unset=True) == {"name": "New name"}


def test_update_allows_clearing_description() -> None:
    update = ProductUpdate.model_validate({"description": None})
    assert update.model_dump(exclude_unset=True) == {"description": None}


@pytest.mark.parametrize(
    "payload",
    [{}, {"sku": "NEW-1"}, {"name": None}, {"unit_price": None}, {"unknown": 1}],
)
def test_invalid_update_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ProductUpdate.model_validate(payload)
