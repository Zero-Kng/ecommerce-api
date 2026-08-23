from fastapi import FastAPI

app = FastAPI(
    title="E-commerce API",
    version="0.1.0",
    description="API REST de e-commerce com catálogo, autenticação e pedidos.",
)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    """Confirma que a aplicação está de pé."""
    return {"status": "ok"}
