from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.errors import registrar_handlers
from app.api.routes import categories, products
from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="API REST de e-commerce com catálogo, autenticação e pedidos.",
)

registrar_handlers(app)

app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")


@app.get("/health", tags=["sistema"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Confirma que a aplicação está de pé e alcança o banco de dados."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
