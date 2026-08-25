from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoriaAtualizar, CategoriaCriar, CategoriaLer
from app.services import category as servico

router = APIRouter(prefix="/categories", tags=["categorias"])


@router.get("", response_model=list[CategoriaLer])
def listar_categorias(db: Session = Depends(get_db)) -> list[CategoriaLer]:
    """Lista todas as categorias em ordem alfabética."""
    return servico.listar(db)


@router.post("", response_model=CategoriaLer, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaCriar, db: Session = Depends(get_db)) -> CategoriaLer:
    """Cria uma categoria. O slug é gerado a partir do nome."""
    return servico.criar(db, dados)


@router.patch("/{categoria_id}", response_model=CategoriaLer)
def atualizar_categoria(
    categoria_id: int, dados: CategoriaAtualizar, db: Session = Depends(get_db)
) -> CategoriaLer:
    """Atualiza o nome de uma categoria e regenera o slug."""
    return servico.atualizar(db, categoria_id, dados)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_categoria(categoria_id: int, db: Session = Depends(get_db)) -> Response:
    """Remove uma categoria sem produtos vinculados."""
    servico.remover(db, categoria_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
