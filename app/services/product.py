from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError, NotFoundError
from app.models import Category, Product
from app.schemas.product import ProdutoAtualizar, ProdutoCriar


def listar(db: Session) -> list[Product]:
    consulta = select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    return list(db.scalars(consulta))


def buscar_por_id(db: Session, produto_id: int) -> Product:
    produto = db.get(Product, produto_id)
    if produto is None:
        raise NotFoundError(f"Produto {produto_id} não encontrado")
    return produto


def criar(db: Session, dados: ProdutoCriar) -> Product:
    _exigir_categoria(db, dados.category_id)
    _recusar_sku_duplicado(db, dados.sku)

    produto = Product(**dados.model_dump())
    db.add(produto)
    db.flush()
    return produto


def atualizar(db: Session, produto_id: int, dados: ProdutoAtualizar) -> Product:
    produto = buscar_por_id(db, produto_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "category_id" in alteracoes:
        _exigir_categoria(db, alteracoes["category_id"])
    if "sku" in alteracoes:
        _recusar_sku_duplicado(db, alteracoes["sku"], ignorar_id=produto.id)

    for campo, valor in alteracoes.items():
        setattr(produto, campo, valor)

    db.flush()
    return produto


def remover(db: Session, produto_id: int) -> None:
    produto = buscar_por_id(db, produto_id)
    produto.is_active = False
    db.flush()


def _exigir_categoria(db: Session, categoria_id: int) -> None:
    if db.get(Category, categoria_id) is None:
        raise NotFoundError(f"Categoria {categoria_id} não encontrada")


def _recusar_sku_duplicado(db: Session, sku: str, ignorar_id: int | None = None) -> None:
    consulta = select(Product).where(Product.sku == sku)
    if ignorar_id is not None:
        consulta = consulta.where(Product.id != ignorar_id)

    if db.scalar(consulta) is not None:
        raise DuplicateResourceError(f"Já existe um produto com o SKU {sku}")
