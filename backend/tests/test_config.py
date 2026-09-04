import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_unsafe_defaults():
    with pytest.raises(ValidationError):
        Settings(environment="production", database_url="postgresql+psycopg://u:p@db/teamflow", seed_demo=False, demo_enabled=False)


def test_production_accepts_explicit_configuration():
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://u:p@db/teamflow",
        secret_key="a" * 48,
        seed_demo=False,
        demo_enabled=False,
    )
    assert settings.environment == "production"
