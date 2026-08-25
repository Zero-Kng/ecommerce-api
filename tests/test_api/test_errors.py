import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import registrar_handlers
from app.core.exceptions import (
    CategoryInUseError,
    DomainError,
    DuplicateResourceError,
    NotFoundError,
    PermissionDeniedError,
)

CASOS = [
    (NotFoundError, 404, "NOT_FOUND"),
    (CategoryInUseError, 409, "CATEGORY_IN_USE"),
    (DuplicateResourceError, 409, "DUPLICATE_RESOURCE"),
    (PermissionDeniedError, 403, "PERMISSION_DENIED"),
    (DomainError, 400, "DOMAIN_ERROR"),
]


@pytest.mark.parametrize(("excecao", "status", "code"), CASOS)
def test_traduz_excecao_para_status_e_code(
    excecao: type[DomainError], status: int, code: str
) -> None:
    aplicacao = FastAPI()
    registrar_handlers(aplicacao)

    @aplicacao.get("/estoura")
    def estoura() -> None:
        raise excecao("mensagem de teste")

    resposta = TestClient(aplicacao).get("/estoura")

    assert resposta.status_code == status
    assert resposta.json() == {"detail": "mensagem de teste", "code": code}
