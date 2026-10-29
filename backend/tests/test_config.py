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

def test_registration_schema_accepts_valid_field_lengths():
    from app.models.schemas import UserCreate

    user = UserCreate(username="student01", email="student@example.com", password="strong-pass-123")
    assert user.username == "student01"
    assert user.email == "student@example.com"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "email": "student@example.com", "password": "strong-pass-123"},
        {"username": "x" * 51, "email": "student@example.com", "password": "strong-pass-123"},
        {"username": "student01", "email": "x" * 255, "password": "strong-pass-123"},
        {"username": "student01", "email": "student@example.com", "password": "short"},
        {"username": "student01", "email": "student@example.com", "password": "x" * 73},
    ],
)
def test_registration_schema_rejects_out_of_range_fields(payload):
    from app.models.schemas import UserCreate

    with pytest.raises(ValidationError):
        UserCreate(**payload)

