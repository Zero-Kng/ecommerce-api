from fastapi.testclient import TestClient


def _criar_categoria(client: TestClient) -> int:
    return client.post("/api/v1/categories", json={"name": "Placas de Vídeo"}).json()["id"]


def test_criar_produto_devolve_201(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-001",
            "name": "Placa de Vídeo 8GB",
            "price": "2799.90",
            "stock_quantity": 4,
            "category_id": _criar_categoria(client),
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["price"] == "2799.90"


def test_preco_negativo_devolve_422(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-002",
            "name": "Placa Inválida",
            "price": "-10.00",
            "stock_quantity": 1,
            "category_id": _criar_categoria(client),
        },
    )

    assert resposta.status_code == 422


def test_categoria_inexistente_devolve_404(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-003",
            "name": "Placa Órfã",
            "price": "1500.00",
            "stock_quantity": 1,
            "category_id": 9999,
        },
    )

    assert resposta.status_code == 404


def test_patch_altera_so_o_campo_enviado(client: TestClient) -> None:
    criado = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-004",
            "name": "Placa Original",
            "price": "1000.00",
            "stock_quantity": 7,
            "category_id": _criar_categoria(client),
        },
    ).json()

    resposta = client.patch(f"/api/v1/products/{criado['id']}", json={"price": "1200.00"})

    assert resposta.status_code == 200
    assert resposta.json()["price"] == "1200.00"
    assert resposta.json()["name"] == "Placa Original"
    assert resposta.json()["stock_quantity"] == 7


def test_delete_some_da_listagem_mas_detalhe_continua(client: TestClient) -> None:
    criado = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-005",
            "name": "Placa Descontinuada",
            "price": "800.00",
            "stock_quantity": 2,
            "category_id": _criar_categoria(client),
        },
    ).json()

    assert client.delete(f"/api/v1/products/{criado['id']}").status_code == 204
    assert client.get("/api/v1/products").json() == []
    assert client.get(f"/api/v1/products/{criado['id']}").status_code == 200
