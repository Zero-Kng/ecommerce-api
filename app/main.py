from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="API REST de e-commerce com catálogo, autenticação e pedidos.",
)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Confirma que a aplicação está de pé."""
    return {"status": "ok"}
