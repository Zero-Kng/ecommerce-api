from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import CategoryInUseError, DuplicateResourceError, NotFoundError
from app.models import Product
from app.schemas.category import CategoriaAtualizar, CategoriaCriar
from app.services import category as servico


def test_criar_gera_slug_a_partir_do_nome(db_session: Session) -> None:
    criada = servico.criar(db_session, CategoriaCriar(name="Eletrônicos de Áudio"))

    assert criada.slug == "eletronicos-de-audio"


def test_criar_recusa_nome_duplicado(db_session: Session) -> None:
    servico.criar(db_session, CategoriaCriar(name="Periféricos"))

    with pytest.raises(DuplicateResourceError):
        servico.criar(db_session, CategoriaCriar(name="Periféricos"))


def test_buscar_inexistente_levanta_not_found(db_session: Session) -> None:
    with pytest.raises(NotFoundError):
        servico.buscar_por_id(db_session, 9999)


def test_remover_categoria_com_produto_e_bloqueado(db_session: Session) -> None:
    categoria = servico.criar(db_session, CategoriaCriar(name="Teclados"))
    db_session.add(
        Product(
            sku="TEC-001",
            name="Teclado Mecânico",
            price=Decimal("399.90"),
            stock_quantity=5,
            category_id=categoria.id,
        )
    )
    db_session.flush()

    with pytest.raises(CategoryInUseError):
        servico.remover(db_session, categoria.id)


def test_remover_categoria_sem_produtos_funciona(db_session: Session) -> None:
    categoria = servico.criar(db_session, CategoriaCriar(name="Categoria Vazia"))

    servico.remover(db_session, categoria.id)

    with pytest.raises(NotFoundError):
        servico.buscar_por_id(db_session, categoria.id)


def test_listar_devolve_em_ordem_alfabetica(db_session: Session) -> None:
    servico.criar(db_session, CategoriaCriar(name="Zebra"))
    servico.criar(db_session, CategoriaCriar(name="Abacaxi"))

    assert [c.name for c in servico.listar(db_session)] == ["Abacaxi", "Zebra"]


def test_atualizar_regenera_o_slug(db_session: Session) -> None:
    categoria = servico.criar(db_session, CategoriaCriar(name="Fones"))

    atualizada = servico.atualizar(
        db_session, categoria.id, CategoriaAtualizar(name="Fones de Ouvido")
    )

    assert atualizada.name == "Fones de Ouvido"
    assert atualizada.slug == "fones-de-ouvido"


def test_atualizar_mantendo_o_proprio_nome_nao_acusa_duplicata(db_session: Session) -> None:
    categoria = servico.criar(db_session, CategoriaCriar(name="Mouses"))

    atualizada = servico.atualizar(db_session, categoria.id, CategoriaAtualizar(name="Mouses"))

    assert atualizada.slug == "mouses"
