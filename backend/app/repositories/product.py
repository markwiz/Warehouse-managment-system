"""Database operations for products."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Product


def get(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_by_sku(db: Session, sku: str) -> Product | None:
    return db.scalar(select(Product).where(Product.sku == sku))


def list_(db: Session, *, offset: int, limit: int) -> Sequence[Product]:
    return db.scalars(select(Product).order_by(Product.id).offset(offset).limit(limit)).all()


def add(db: Session, product: Product) -> Product:
    db.add(product)
    db.flush()
    return product


def update(db: Session, product: Product, fields: dict[str, Any]) -> Product:
    for key, value in fields.items():
        setattr(product, key, value)
    db.flush()
    return product
