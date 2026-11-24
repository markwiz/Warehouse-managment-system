"""Declarative base for all ORM models. Import models here so Alembic can see them."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
