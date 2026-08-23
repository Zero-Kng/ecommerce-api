import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP que fala com a aplicação sem subir um servidor de verdade."""
    return TestClient(app)
