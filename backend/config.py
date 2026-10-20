"""Application configuration.

Secrets and connection strings are read from environment variables.
A .env file (see .env.example) can be used for local development.
"""

import os
from datetime import timedelta


def _get_env(key: str, default: str) -> str:
    return os.environ.get(key, default)


class Config:
    # Core
    SECRET_KEY = _get_env("SECRET_KEY", "dev-secret-change-me")
    DEBUG = _get_env("FLASK_DEBUG", "False").lower() == "true"

    # Database: defaults to SQLite so the project runs without a MySQL server.
    # For MySQL, set DATABASE_URL to e.g.
    #   mysql+pymysql://securepay:securepay@localhost:3306/securepay
    SQLALCHEMY_DATABASE_URI = _get_env(
        "DATABASE_URL", "sqlite:///securepay.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = _get_env("JWT_SECRET_KEY", "dev-jwt-secret-key-securepay-auth-token-32bytes")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # CORS
    CORS_ORIGINS = _get_env("CORS_ORIGINS", "*")

    # Fraud detection business threshold (risk_score >= threshold => Suspicious)
    FRAUD_THRESHOLD = float(_get_env("FRAUD_THRESHOLD", "0.5"))


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key-securepay-auth-token-32bytes"
    SECRET_KEY = "test-secret-key-securepay-32bytes"
    FRAUD_THRESHOLD = 0.5
    DEBUG = False
