"""
conftest.py — Fixtures compartidas para todos los tests
Provee: cliente HTTP async, DB de test en memoria, PC de ejemplo
"""

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_PATH"] = ":memory:"
os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-real")
os.environ.setdefault("ENVIRONMENT", "development")

import servidor.config as config_module

config_module.settings.secret_key = "test-secret-key-not-real"
import servidor.database as db_module
from servidor.database import Base

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

db_module.engine = TEST_ENGINE
db_module.SessionLocal = TestSessionLocal

from servidor.main import app, get_db  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db():
    """Crea tablas frescas antes de cada test y las elimina después."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP síncrono para tests simples."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """Cliente HTTP async para tests más complejos."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def sample_pc_data() -> dict:
    """Datos de PC de ejemplo para tests."""
    return {"ip": "192.168.1.100", "name": "PC-Test-01"}
