import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """
    Cliente de teste do FastAPI
    """
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """
    Faz login e retorna headers com JWT
    """
    login = client.post(
        "/auth/login",
        data={
            "username": "dala@example.com",
            "password": "dala123"
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
