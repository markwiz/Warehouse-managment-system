"""Shared fixtures.

Database tests run against a real PostgreSQL database that is separate from the
development one (TEST_DATABASE_URL, or "<database>_test" derived from
DATABASE_URL). It is created if missing, its schema is rebuilt from the ORM
models once per run, and all tables are truncated after every test.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import get_db
from app.main import app


def _test_database_url() -> URL:
    settings = get_settings()
    if settings.test_database_url:
        return make_url(settings.test_database_url)
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_test")


def _ensure_database_exists(url: URL) -> None:
    server = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with server.connect() as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        server.dispose()


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    url = _test_database_url()
    if url.database == make_url(get_settings().database_url).database:
        pytest.fail("Test database must differ from DATABASE_URL")
    try:
        _ensure_database_exists(url)
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL not reachable at {url.render_as_string()}: {exc.orig}")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_sessionmaker(db_engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session(db_sessionmaker: sessionmaker[Session]) -> Iterator[Session]:
    with db_sessionmaker() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_client(client: TestClient, db_sessionmaker: sessionmaker[Session]) -> TestClient:
    """Client whose requests each get a fresh session on the test database."""

    def _get_test_db() -> Iterator[Session]:
        with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    return client


@pytest.fixture
def healthy_db() -> MagicMock:
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    return db


@pytest.fixture
def broken_db() -> MagicMock:
    db = MagicMock()
    db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("connection refused"))
    app.dependency_overrides[get_db] = lambda: db
    return db
