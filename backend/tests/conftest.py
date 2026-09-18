import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Point tests at a dedicated database (caremate_test), never the dev database
# (caremate) — running tests should never create/delete real dev data.
TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/caremate_test"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Swap the real get_db dependency for our test-DB version. Every route that
# does `Depends(get_db)` will now receive a session bound to caremate_test
# whenever it runs through a TestClient built from this `app` instance.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Empty every table between tests so e.g. a duplicate-email test in one
    function can't fail because a previous test already registered that email."""
    yield
    with test_engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()


@pytest.fixture()
def client():
    return TestClient(app)


def register_and_login(client, email="patient@example.com"):
    """Shared across test files: register a fresh user and return auth
    headers ready to use, so each test doesn't repeat this boilerplate."""
    from tests.test_auth import VALID_PASSWORD, login, register

    register(client, email=email)
    token = login(client, email=email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
