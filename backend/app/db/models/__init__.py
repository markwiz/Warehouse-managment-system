"""ORM model registry.

Every model module must be imported here so that `Base.metadata` is complete
wherever this package is imported (Alembic autogenerate and tests rely on it).
"""

from app.db.base import Base
from app.db.models.product import Product

__all__ = ["Base", "Product"]
