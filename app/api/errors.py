from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)

STATUS_POR_EXCECAO: list[tuple[type[DomainError], int]] = [
    (NotFoundError, 404),
    (ConflictError, 409),
    (PermissionDeniedError, 403),
]

STATUS_PADRAO = 400


def registrar_handlers(app: FastAPI) -> None:
    """Registra a tradução de exceções de domínio para respostas HTTP."""

    @app.exception_handler(DomainError)
    async def tratar_erro_de_dominio(_: Request, erro: DomainError) -> JSONResponse:
        status = next(
            (codigo for tipo, codigo in STATUS_POR_EXCECAO if isinstance(erro, tipo)),
            STATUS_PADRAO,
        )
        return JSONResponse(
            status_code=status,
            content={"detail": erro.detail, "code": erro.code},
        )
