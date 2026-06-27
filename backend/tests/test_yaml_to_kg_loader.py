from app.config import settings
from app.services import yaml_to_kg_loader


def test_resolve_db_url_preserves_compose_postgres_host():
    original_url = settings.database_url
    object.__setattr__(
        settings,
        "database_url",
        "postgresql://aquant:changeme@postgres:5432/aquant",
    )

    try:
        assert (
            yaml_to_kg_loader._resolve_db_url()
            == "postgresql://aquant:changeme@postgres:5432/aquant"
        )
    finally:
        object.__setattr__(settings, "database_url", original_url)
