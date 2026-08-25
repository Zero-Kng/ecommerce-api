from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import CategoryInUseError, DuplicateResourceError, NotFoundError
from app.core.slug import gerar_slug
from app.models import Category, Product
from app.schemas.category import CategoriaAtualizar, CategoriaCriar


def listar(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def buscar_por_id(db: Session, categoria_id: int) -> Category:
    categoria = db.get(Category, categoria_id)
    if categoria is None:
        raise NotFoundError(f"Categoria {categoria_id} não encontrada")
    return categoria


def criar(db: Session, dados: CategoriaCriar) -> Category:
    slug = gerar_slug(dados.name)
    _recusar_duplicata(db, dados.name, slug)

    categoria = Category(name=dados.name, slug=slug)
    db.add(categoria)
    db.flush()
    return categoria


def atualizar(db: Session, categoria_id: int, dados: CategoriaAtualizar) -> Category:
    categoria = buscar_por_id(db, categoria_id)

    if dados.name is not None:
        slug = gerar_slug(dados.name)
        _recusar_duplicata(db, dados.name, slug, ignorar_id=categoria.id)
        categoria.name = dados.name
        categoria.slug = slug

    db.flush()
    return categoria


def remover(db: Session, categoria_id: int) -> None:
    categoria = buscar_por_id(db, categoria_id)

    vinculados = db.scalar(
        select(func.count()).select_from(Product).where(Product.category_id == categoria.id)
    )
    if vinculados:
        raise CategoryInUseError(
            f"Categoria {categoria.name} tem {vinculados} produto(s) e não pode ser removida"
        )

    db.delete(categoria)
    db.flush()


def _recusar_duplicata(db: Session, nome: str, slug: str, ignorar_id: int | None = None) -> None:
    consulta = select(Category).where((Category.name == nome) | (Category.slug == slug))
    if ignorar_id is not None:
        consulta = consulta.where(Category.id != ignorar_id)

    if db.scalar(consulta) is not None:
        raise DuplicateResourceError(f"Já existe uma categoria chamada {nome}")
