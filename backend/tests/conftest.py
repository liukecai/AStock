from __future__ import annotations

import pytest
from app.config import settings


@pytest.fixture(autouse=True, scope="session")
def force_sqlite_backend():
    """Forces the SQLite backend for all unit tests to maintain isolation."""
    original_url = settings.database_url
    object.__setattr__(settings, "database_url", None)
    yield
    object.__setattr__(settings, "database_url", original_url)
