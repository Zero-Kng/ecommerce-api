from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app

RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine]:
    url = get_settings().database_url_test
    servidor, banco = url.rsplit("/", 1)

    administrador = create_engine(f"{servidor}/postgres", isolation_level="AUTOCOMMIT")
    with administrador.connect() as conexao:
        existe = conexao.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": banco}
        ).scalar()
        if not existe:
            conexao.execute(text(f'CREATE DATABASE "{banco}"'))
    administrador.dispose()

    configuracao = Config(str(RAIZ_DO_PROJETO / "alembic.ini"))
    configuracao.set_main_option("script_location", str(RAIZ_DO_PROJETO / "alembic"))
    configuracao.attributes["sqlalchemy.url"] = url
    command.upgrade(configuracao, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    conexao = test_engine.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, expire_on_commit=False)

    yield sessao

    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def sessao_de_teste() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = sessao_de_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
