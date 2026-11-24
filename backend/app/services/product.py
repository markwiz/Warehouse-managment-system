"""Business rules for products."""

from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Product
from app.repositories import product as product_repo
from app.schemas.product import ProductCreate, ProductUpdate


class ProductNotFoundError(Exception):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} not found")


class DuplicateSkuError(Exception):
    def __init__(self, sku: str) -> None:
        super().__init__(f"A product with SKU '{sku}' already exists")


def create_product(db: Session, data: ProductCreate) -> Product:
    if product_repo.get_by_sku(db, data.sku) is not None:
        raise DuplicateSkuError(data.sku)
    try:
        product = product_repo.add(db, Product(**data.model_dump()))
        db.commit()
    except IntegrityError as exc:
        # Lost a race with a concurrent insert of the same SKU.
        db.rollback()
        raise DuplicateSkuError(data.sku) from exc
    db.refresh(product)
    return product


def get_product(db: Session, product_id: int) -> Product:
    product = product_repo.get(db, product_id)
    if product is None:
        raise ProductNotFoundError(product_id)
    return product


def list_products(db: Session, *, offset: int, limit: int) -> Sequence[Product]:
    return product_repo.list_(db, offset=offset, limit=limit)


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    product_repo.update(db, product, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(product)
    return product
