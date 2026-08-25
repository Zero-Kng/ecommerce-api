from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProdutoAtualizar, ProdutoCriar, ProdutoLer
from app.services import product as servico

router = APIRouter(prefix="/products", tags=["produtos"])


@router.get("", response_model=list[ProdutoLer])
def listar_produtos(db: Session = Depends(get_db)) -> list[ProdutoLer]:
    """Lista os produtos ativos em ordem alfabética."""
    return servico.listar(db)


@router.get("/{produto_id}", response_model=ProdutoLer)
def detalhar_produto(produto_id: int, db: Session = Depends(get_db)) -> ProdutoLer:
    """Devolve um produto pelo identificador."""
    return servico.buscar_por_id(db, produto_id)


@router.post("", response_model=ProdutoLer, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoCriar, db: Session = Depends(get_db)) -> ProdutoLer:
    """Cria um produto vinculado a uma categoria existente."""
    return servico.criar(db, dados)


@router.patch("/{produto_id}", response_model=ProdutoLer)
def atualizar_produto(
    produto_id: int, dados: ProdutoAtualizar, db: Session = Depends(get_db)
) -> ProdutoLer:
    """Atualiza parcialmente um produto."""
    return servico.atualizar(db, produto_id, dados)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(produto_id: int, db: Session = Depends(get_db)) -> Response:
    """Desativa um produto sem apagar o registro."""
    servico.remover(db, produto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
