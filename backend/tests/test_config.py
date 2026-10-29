import pytest
from pydantic import ValidationError

from app.config import Settings


def test_development_defaults_remain_usable():
    settings = Settings(_env_file=None)
    assert settings.ENVIRONMENT == "development"


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="production")


def test_production_rejects_placeholder_neo4j_password():
    with pytest.raises(ValidationError, match="NEO4J_PASSWORD"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="a-unique-production-secret-key-that-is-long-enough",
        )


def test_production_accepts_configured_secrets():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        SECRET_KEY="a-unique-production-secret-key-that-is-long-enough",
        NEO4J_PASSWORD="a-strong-database-password",
    )
    assert settings.ENVIRONMENT == "production"


def test_production_rejects_example_secret_placeholder():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            SECRET_KEY="change-this-in-production",
            NEO4J_PASSWORD="a-strong-database-password",
        )
