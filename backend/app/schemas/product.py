"""Request/response schemas for products. All input validation lives here."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

SKU_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{0,63}$")


def _normalize_sku(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value


def _check_sku(value: str) -> str:
    if not SKU_PATTERN.fullmatch(value):
        raise ValueError(
            "SKU must be 1-64 characters of A-Z, 0-9, '-' or '_', starting with a letter or digit"
        )
    return value


Sku = Annotated[str, BeforeValidator(_normalize_sku), AfterValidator(_check_sku)]
Name = Annotated[str, Field(min_length=1, max_length=255)]
Description = Annotated[str, Field(max_length=2000)]
Price = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class _Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ProductCreate(_Input):
    sku: Sku
    name: Name
    description: Description | None = None
    unit_price: Price


class ProductUpdate(_Input):
    """Partial update. SKU is immutable, so it is not accepted here."""

    name: Name | None = None
    description: Description | None = None
    unit_price: Price | None = None

    @model_validator(mode="after")
    def _check_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in ("name", "unit_price"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime
