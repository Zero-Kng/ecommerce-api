import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_le_database_url_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://usuario:senha@localhost:5432/teste")

    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://usuario:senha@localhost:5432/teste"


def test_settings_falha_quando_database_url_esta_ausente(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)  # sai da pasta do projeto para não achar o .env

    with pytest.raises(ValidationError):
        Settings()
