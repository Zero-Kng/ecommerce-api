from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError, NotFoundError
from app.models import Product
from app.schemas.category import CategoriaCriar
from app.schemas.product import ProdutoAtualizar, ProdutoCriar
from app.services import category as servico_categoria
from app.services import product as servico


def _categoria(db: Session) -> int:
    return servico_categoria.criar(db, CategoriaCriar(name="Notebooks")).id


def test_criar_produto_guarda_preco_como_decimal(db_session: Session) -> None:
    criado = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-001",
            name="Notebook Pro",
            price=Decimal("4599.90"),
            stock_quantity=3,
            category_id=_categoria(db_session),
        ),
    )

    assert criado.price == Decimal("4599.90")
    assert isinstance(criado.price, Decimal)


def test_criar_com_categoria_inexistente_levanta_not_found(db_session: Session) -> None:
    with pytest.raises(NotFoundError):
        servico.criar(
            db_session,
            ProdutoCriar(
                sku="NB-002",
                name="Notebook Air",
                price=Decimal("3299.00"),
                stock_quantity=1,
                category_id=9999,
            ),
        )


def test_sku_duplicado_e_recusado(db_session: Session) -> None:
    dados = ProdutoCriar(
        sku="NB-003",
        name="Notebook Slim",
        price=Decimal("2899.00"),
        stock_quantity=2,
        category_id=_categoria(db_session),
    )
    servico.criar(db_session, dados)

    with pytest.raises(DuplicateResourceError):
        servico.criar(db_session, dados)


def test_remover_faz_soft_delete(db_session: Session) -> None:
    criado = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-004",
            name="Notebook Básico",
            price=Decimal("1999.00"),
            stock_quantity=10,
            category_id=_categoria(db_session),
        ),
    )

    servico.remover(db_session, criado.id)

    assert criado.is_active is False
    assert db_session.get(Product, criado.id) is not None


def test_listar_ignora_produtos_inativos(db_session: Session) -> None:
    criado = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-005",
            name="Notebook Antigo",
            price=Decimal("999.00"),
            stock_quantity=1,
            category_id=_categoria(db_session),
        ),
    )
    servico.remover(db_session, criado.id)

    assert servico.listar(db_session) == []


def test_buscar_produto_inexistente_levanta_not_found(db_session: Session) -> None:
    with pytest.raises(NotFoundError):
        servico.buscar_por_id(db_session, 9999)


def test_atualizar_para_categoria_inexistente_levanta_not_found(db_session: Session) -> None:
    criado = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-006",
            name="Notebook Alvo",
            price=Decimal("1500.00"),
            stock_quantity=1,
            category_id=_categoria(db_session),
        ),
    )

    with pytest.raises(NotFoundError):
        servico.atualizar(db_session, criado.id, ProdutoAtualizar(category_id=9999))


def test_atualizar_sku_para_um_ja_existente_e_recusado(db_session: Session) -> None:
    categoria_id = _categoria(db_session)
    servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-007",
            name="Notebook Um",
            price=Decimal("1000.00"),
            stock_quantity=1,
            category_id=categoria_id,
        ),
    )
    segundo = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-008",
            name="Notebook Dois",
            price=Decimal("2000.00"),
            stock_quantity=1,
            category_id=categoria_id,
        ),
    )

    with pytest.raises(DuplicateResourceError):
        servico.atualizar(db_session, segundo.id, ProdutoAtualizar(sku="NB-007"))
