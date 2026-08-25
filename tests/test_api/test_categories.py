from fastapi.testclient import TestClient


def test_criar_categoria_devolve_201_e_slug(client: TestClient) -> None:
    resposta = client.post("/api/v1/categories", json={"name": "Monitores Gamer"})

    assert resposta.status_code == 201
    assert resposta.json()["slug"] == "monitores-gamer"


def test_criar_categoria_duplicada_devolve_409(client: TestClient) -> None:
    client.post("/api/v1/categories", json={"name": "Cadeiras"})

    resposta = client.post("/api/v1/categories", json={"name": "Cadeiras"})

    assert resposta.status_code == 409
    assert resposta.json()["code"] == "DUPLICATE_RESOURCE"


def test_atualizar_categoria_inexistente_devolve_404(client: TestClient) -> None:
    resposta = client.patch("/api/v1/categories/9999", json={"name": "Qualquer"})

    assert resposta.status_code == 404
    assert resposta.json()["code"] == "NOT_FOUND"


def test_nome_vazio_devolve_422(client: TestClient) -> None:
    resposta = client.post("/api/v1/categories", json={"name": ""})

    assert resposta.status_code == 422
