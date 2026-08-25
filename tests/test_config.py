from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

URL_BANCO = "postgresql+psycopg://usuario:senha@localhost:5432/teste"
URL_BANCO_TESTE = "postgresql+psycopg://usuario:senha@localhost:5432/teste_test"


def test_settings_le_as_urls_do_ambiente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", URL_BANCO)
    monkeypatch.setenv("DATABASE_URL_TEST", URL_BANCO_TESTE)

    settings = Settings()

    assert settings.database_url == URL_BANCO
    assert settings.database_url_test == URL_BANCO_TESTE


def test_settings_falha_quando_falta_variavel_obrigatoria(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_TEST", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError):
        Settings()
