"""Pytest configuration and shared helpers for SecurePay backend tests."""

import os
import sys

import pytest

# Ensure the backend package is importable when running from tests/.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app_for_testing  # noqa: E402


@pytest.fixture
def app():
    app = create_app_for_testing()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, email, password, role="customer", **extra):
    payload = {"email": email, "password": password, "role": role}
    payload.update(extra)
    return client.post("/api/auth/register", json=payload)


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(client, email, password):
    r = login(client, email, password)
    token = r.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
