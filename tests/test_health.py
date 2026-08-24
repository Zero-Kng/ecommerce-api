from fastapi.testclient import TestClient


def test_health_responde_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_confirma_conexao_com_o_banco(client: TestClient) -> None:
    response = client.get("/health")

    assert response.json() == {"status": "ok", "database": "ok"}
