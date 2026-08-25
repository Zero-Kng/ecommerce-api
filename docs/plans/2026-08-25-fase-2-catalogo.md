# Plano de implementação — Fase 2: Catálogo

Escrito em 25/08/2026, depois da Fase 1 concluída.

**Entregável da fase:** catálogo funcional de categorias e produtos, com migrations
versionadas, regras de negócio isoladas em `services/` e documentação automática no
Swagger.

**Referência:** `docs/sdd.md` — modelo de dados (seção 4), regras R7 e R9 (seção 5),
contratos das rotas (seção 6), tratamento de erros (seção 7), estratégia de testes
(seção 9).

---

## Restrições globais

- Python 3.14, gerenciado por `uv`.
- SQLAlchemy 2.0 **síncrono**, estilo declarativo com `Mapped` e `mapped_column`.
- Ruff com `line-length = 100`, alvo `py314`.
- Dinheiro é `Numeric(10, 2)`, nunca `Float`. No Python chega como `Decimal`.
- `services/` não conhece HTTP: não importa `fastapi`, não levanta `HTTPException`,
  não menciona código de status.
- Sem comentários explicativos no código. A explicação vive neste plano e no README.
- Cada tarefa termina com testes verdes, lint limpo e commit feito **por José**.

---

## Decisões tomadas neste plano

Quatro pontos que o SDD não fecha.

**1. O `slug` é gerado pelo servidor.** O cliente envia apenas `name`. A API deriva o
slug removendo acentos, passando para minúsculas e trocando o que não é letra ou número
por hífen. `"Eletrônicos de Áudio"` vira `"eletronicos-de-audio"`. Menos campo para o
cliente errar e formato garantido.

**2. Banco de teste separado, `ecommerce_test`.** Segunda base no mesmo container
PostgreSQL, endereçada por uma variável de ambiente nova. Os dados que você criar
brincando no Swagger nunca são vistos nem apagados por teste.

**3. Migrations rodam à mão, com `alembic upgrade head`.** É o comportamento de
produção. Migration automática na subida do container pode rodar em paralelo quando há
várias instâncias e corromper o histórico.

**4. As exceções de domínio não carregam código HTTP.** Elas expõem só `code` e
`detail`. Quem traduz tipo de exceção em status é um handler registrado no `main.py`.
É o que mantém `services/` reutilizável fora de uma API.

---

## Mapa de arquivos

Criar:

```
app/db/base.py
app/models/__init__.py
app/models/category.py
app/models/product.py
app/core/exceptions.py
app/core/slug.py
app/schemas/__init__.py
app/schemas/category.py
app/schemas/product.py
app/services/__init__.py
app/services/category.py
app/services/product.py
app/api/__init__.py
app/api/deps.py
app/api/errors.py
app/api/routes/__init__.py
app/api/routes/categories.py
app/api/routes/products.py
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/versions/<hash>_cria_categories_e_products.py
tests/test_services/__init__.py
tests/test_services/test_category_service.py
tests/test_services/test_product_service.py
tests/test_api/__init__.py
tests/test_api/test_categories.py
tests/test_api/test_products.py
```

Modificar:

```
pyproject.toml          alembic como dependência; exclusão de alembic/versions no ruff
app/core/config.py      campo database_url_test
app/main.py             registro dos routers e do handler de erros
tests/conftest.py       banco de teste, migrations e transação revertida
.env.example / .env     DATABASE_URL_TEST
docker-compose.yml      DATABASE_URL_TEST no serviço api
.github/workflows/ci.yml  DATABASE_URL_TEST e passo de migration
README.md               Alembic de volta na stack; instruções de migration
```

---

## Tarefa 1: Base declarativa e models

Entregável: as tabelas `categories` e `products` descritas em Python, prontas para o
Alembic gerar a migration.

**Arquivos:**
- Criar: `app/db/base.py`, `app/models/__init__.py`, `app/models/category.py`,
  `app/models/product.py`

**Interfaces:**
- Consome: nada
- Produz: `app.db.base.Base`, `app.models.Category`, `app.models.Product`

---

- [x] **Passo 1: A classe base declarativa**

Crie `app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Toda tabela herda dela. O `Base.metadata` acumula a descrição de todas as tabelas
registradas, e é isso que o Alembic vai comparar com o banco real para gerar migrations.

- [x] **Passo 2: O model de categoria**

Crie `app/models/category.py`:

```python
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    products: Mapped[list[Product]] = relationship(back_populates="category")
```

Três coisas para entender:

**`Mapped[int]` versus `mapped_column`.** A anotação de tipo diz ao Python e ao seu
editor o que sai da coluna; o `mapped_column` diz ao banco como a coluna é. Um tipo
`Mapped[str | None]` gera coluna que aceita nulo; `Mapped[str]` gera `NOT NULL`. A
obrigatoriedade vem do tipo, não de um argumento — mesma ideia do Pydantic na Fase 1.

**`server_default=func.now()`.** O padrão é aplicado **pelo PostgreSQL**, não pelo
Python. Se alguém inserir uma linha por `psql`, o carimbo de data continua correto.
Padrão em Python só valeria para escritas feitas pela sua aplicação.

**`TYPE_CHECKING`.** `Category` precisa mencionar `Product` e `Product` precisa
mencionar `Category`. Importar os dois de verdade criaria ciclo. O bloco
`if TYPE_CHECKING` só é lido por ferramentas de tipo, nunca em tempo de execução.

No Python 3.14 as anotações são avaliadas de forma diferida (PEP 649), então o nome
`Product` pode aparecer **sem aspas**: o SQLAlchemy lê a anotação sem executá-la e
resolve o nome pelo registro de classes dele. Em versões anteriores seria necessário
escrever `Mapped[list["Product"]]`, e o Ruff sinaliza isso com a regra `UP037`.

- [x] **Passo 3: O model de produto**

Crie `app/models/product.py`:

```python
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_quantity: Mapped[int] = mapped_column(server_default="0")
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[Category] = relationship(back_populates="products")
```

**Material de entrevista — os dois `CheckConstraint`.** A regra R2 diz que estoque nunca
fica negativo, e o SDD manda validar **no service e no banco**. Parece redundância e não
é: o service protege o caminho normal da aplicação, o `CHECK` protege contra qualquer
outro caminho — um script de manutenção, um `psql` aberto às pressas, um bug futuro.
Restrição no banco é a última linha de defesa, e é a única que ninguém consegue
contornar por descuido.

**Por que `Numeric(10, 2)` e não `Float`.** `Float` é binário e não representa decimais
exatamente; `0.1 + 0.2` não dá `0.3`. Em dinheiro isso vira centavo errado acumulado.
`Numeric` é decimal exato e chega ao Python como `Decimal`.

- [x] **Passo 4: Registrar os models**

Crie `app/models/__init__.py`:

```python
from app.models.category import Category
from app.models.product import Product

__all__ = ["Category", "Product"]
```

Isso garante que importar `app.models` registra as duas tabelas no `Base.metadata`. Sem
esse arquivo, o Alembic geraria uma migration vazia — ele só enxerga o que foi importado.

- [x] **Passo 5: Verificar que importa**

```bash
uv run python -c "from app.models import Category, Product; from app.db.base import Base; print(sorted(Base.metadata.tables))"
```

Esperado: `['categories', 'products']`.

```bash
uv run ruff check .
```

- [ ] **Passo 6: Commit**

```bash
git add app/db/base.py app/models/
```

```bash
git commit -m "feat: models de categoria e produto"
```

---

## Tarefa 2: Alembic e a primeira migration

Entregável: o esquema do banco versionado em arquivo, aplicável com um comando.

**Arquivos:**
- Criar: `alembic.ini`, `alembic/env.py`, `alembic/versions/<hash>_*.py`
- Modificar: `pyproject.toml`

**Interfaces:**
- Consome: `app.core.config.get_settings()`, `app.db.base.Base`, `app.models`
- Produz: histórico de migrations em `alembic/versions/`

---

- [x] **Passo 1: Instalar o Alembic**

```bash
uv add alembic
```

Repare que é dependência **principal**, não de desenvolvimento: em produção você precisa
aplicar migrations no servidor.

- [x] **Passo 2: Inicializar**

```bash
uv run alembic init alembic
```

Isso cria `alembic.ini`, a pasta `alembic/` com `env.py`, `script.py.mako` e
`versions/` vazia.

- [x] **Passo 3: Ligar o Alembic à sua configuração**

Abra `alembic/env.py`. Logo abaixo da linha `config = context.config`, acrescente:

```python
from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401

config.set_main_option("sqlalchemy.url", get_settings().database_url)
```

E troque a linha `target_metadata = None` por:

```python
target_metadata = Base.metadata
```

Por que cada uma:

- **`set_main_option`** faz a URL vir da sua `Settings`, e não ficar escrita no
  `alembic.ini`. O arquivo `.ini` iria para o Git com a senha dentro.
- **`import app.models`** força o registro das tabelas. O `# noqa: F401` é uma diretiva
  para o Ruff, não um comentário explicativo: sem ela o lint reclamaria de import não
  utilizado, quando o efeito colateral do import é justamente o objetivo.
- **`target_metadata`** é o que o Alembic compara com o banco para descobrir o que mudou.

- [x] **Passo 4: Tirar as migrations geradas do alcance do Ruff**

Em `pyproject.toml`, na seção `[tool.ruff]`, troque a linha de exclusão por:

```toml
exclude = ["docs", "alembic/versions"]
```

Os arquivos de migration são gerados por máquina e seguem o estilo do Alembic. Brigar
com o formatador por causa deles não agrega nada. O `alembic/env.py`, que é código seu,
continua sendo verificado.

Acrescente também uma seção nova, logo abaixo de `[tool.ruff.lint]`:

```toml
[tool.ruff.lint.isort]
known-third-party = ["alembic"]
```

Sem isso o Ruff trata `alembic` como código do próprio projeto, porque existe uma pasta
`alembic/` na raiz, e agrupa `from alembic import context` junto dos imports de `app`. O
código funciona igual — Python resolve o nome para o pacote instalado, não para a pasta
— mas a leitura fica errada, e o mesmo problema voltaria no `conftest.py` da Tarefa 3.

- [x] **Passo 5: Gerar a migration**

O banco precisa estar de pé:

```bash
docker compose up -d db
```

```bash
uv run alembic revision --autogenerate -m "cria categories e products"
```

**Abra o arquivo gerado em `alembic/versions/` e leia antes de aplicar.** O
`--autogenerate` compara os models com o banco e escreve o que achou — ele acerta quase
sempre, mas não é infalível, e aplicar migration sem ler é como dar `git push --force`
sem olhar o diff.

Confira que ele cria as duas tabelas, os índices em `slug`, `sku` e `name`, a chave
estrangeira `category_id` e os dois `CHECK`.

- [x] **Passo 6: Aplicar**

```bash
uv run alembic upgrade head
```

Confirme no banco:

```bash
docker compose exec db psql -U postgres -d ecommerce -c "\dt"
```

Esperado: `alembic_version`, `categories` e `products`.

A tabela `alembic_version` guarda uma linha só, com o identificador da última migration
aplicada. É assim que o Alembic sabe onde parou.

- [x] **Passo 7: Provar que dá para voltar**

Uma migration que não sabe descer não é migration, é caminho sem volta.

```bash
uv run alembic downgrade -1
```

```bash
docker compose exec db psql -U postgres -d ecommerce -c "\dt"
```

Esperado: as tabelas somem, sobra só `alembic_version`. Suba de novo:

```bash
uv run alembic upgrade head
```

- [ ] **Passo 8: Commit**

```bash
git add pyproject.toml uv.lock alembic.ini alembic/
```

```bash
git commit -m "feat: alembic e migration inicial do catalogo"
```

---

## Tarefa 3: Infraestrutura de testes

Entregável: cada teste roda contra um banco próprio e não deixa rastro.

**Arquivos:**
- Modificar: `app/core/config.py`, `tests/conftest.py`, `.env.example`, `.env`,
  `docker-compose.yml`, `.github/workflows/ci.yml`
- Criar: `tests/test_services/__init__.py`, `tests/test_api/__init__.py`

**Interfaces:**
- Produz: fixtures `db_session` e `client`, usadas por todos os testes das Tarefas 5 e 6

---

- [ ] **Passo 1: A variável do banco de teste**

Em `app/core/config.py`, acrescente um campo à classe `Settings`:

```python
    database_url_test: str
```

Em `.env.example` e em `.env`, acrescente a linha:

```dotenv
DATABASE_URL_TEST=postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce_test
```

Repare que é o mesmo servidor PostgreSQL, mesma porta, mesmas credenciais — muda só o
nome do banco no fim da URL. Não é outro container.

- [ ] **Passo 2: Rodar os testes e ver a falha esperada**

```bash
uv run pytest -q
```

Esperado: **falha**, porque `Settings` agora exige um campo que o teste de configuração
não fornece. Isso confirma que a obrigatoriedade funciona.

Em `tests/test_config.py`, no primeiro teste, acrescente a segunda variável junto da
primeira:

```python
    monkeypatch.setenv("DATABASE_URL_TEST", "postgresql+psycopg://u:s@localhost:5432/t")
```

E no segundo teste, apague também a nova antes de esperar o erro:

```python
    monkeypatch.delenv("DATABASE_URL_TEST", raising=False)
```

- [ ] **Passo 3: Reescrever o `conftest.py`**

Substitua o conteúdo de `tests/conftest.py`:

```python
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine]:
    url = get_settings().database_url_test
    servidor, banco = url.rsplit("/", 1)

    administrador = create_engine(f"{servidor}/postgres", isolation_level="AUTOCOMMIT")
    with administrador.connect() as conexao:
        existe = conexao.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": banco}
        ).scalar()
        if not existe:
            conexao.execute(text(f'CREATE DATABASE "{banco}"'))
    administrador.dispose()

    configuracao = Config("alembic.ini")
    configuracao.set_main_option("sqlalchemy.url", url)
    command.upgrade(configuracao, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    conexao = test_engine.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, expire_on_commit=False)

    yield sessao

    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def sessao_de_teste() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = sessao_de_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
```

Três mecanismos aqui, e todos rendem entrevista:

**Criar o banco exige `AUTOCOMMIT`.** `CREATE DATABASE` não roda dentro de transação no
PostgreSQL. Por isso a conexão administrativa aponta para o banco `postgres` — que
sempre existe — e usa `isolation_level="AUTOCOMMIT"`.

**As migrations são aplicadas no banco de teste, não `create_all`.** Seria mais rápido
pedir ao SQLAlchemy que criasse as tabelas direto dos models. Mas aí os testes rodariam
contra um esquema que **nunca passou pelas migrations**, e uma migration quebrada
passaria despercebida até o deploy. Rodando `alembic upgrade head`, cada execução da
suíte também testa o histórico de migrations.

**A transação revertida é o que dá isolamento.** Cada teste recebe uma sessão amarrada a
uma conexão com transação aberta. Tudo que o teste grava existe de verdade para ele —
inclusive depois de `commit()`, porque o commit acontece dentro da transação externa. No
final, `rollback()` desfaz tudo. Nenhum teste enxerga o que outro criou, e a ordem de
execução deixa de importar.

**`dependency_overrides`** troca o `get_db` da aplicação pela sessão do teste. É por isso
que valeu a pena, na Fase 1, `get_db` ser uma função injetável em vez de uma variável de
módulo.

- [ ] **Passo 4: Pastas dos testes**

Crie `tests/test_services/__init__.py` e `tests/test_api/__init__.py`, ambos vazios.

- [ ] **Passo 5: Confirmar que a suíte antiga continua passando**

```bash
uv run pytest -v
```

Esperado: **3 passed**. O `test_health` agora usa o banco de teste, e passa igual.

Confirme que o banco novo nasceu:

```bash
docker compose exec db psql -U postgres -c "\l"
```

Esperado: `ecommerce` e `ecommerce_test` na lista.

- [ ] **Passo 6: Ensinar o Compose e o CI sobre a variável nova**

Em `docker-compose.yml`, no serviço `api`, acrescente abaixo de `DATABASE_URL`:

```yaml
      DATABASE_URL_TEST: postgresql+psycopg://postgres:postgres@db:5432/ecommerce_test
```

Em `.github/workflows/ci.yml`, no bloco `env` do job, acrescente:

```yaml
      DATABASE_URL_TEST: postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce_test
```

Sem isso o CI fica vermelho no primeiro push desta fase, porque `Settings` exige o campo.

- [ ] **Passo 7: Commit**

```bash
git add app/core/config.py tests/ .env.example docker-compose.yml .github/workflows/ci.yml
```

```bash
git commit -m "test: banco de teste isolado com migrations e transacao revertida"
```

---

## Tarefa 4: Exceções de domínio e tradução HTTP

Entregável: os services podem recusar operações sem saber que existe HTTP.

**Arquivos:**
- Criar: `app/core/exceptions.py`, `app/api/errors.py`, `app/api/__init__.py`
- Modificar: `app/main.py`

---

- [ ] **Passo 1: A hierarquia de exceções**

Crie `app/core/exceptions.py`:

```python
class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ConflictError(DomainError):
    code = "CONFLICT"


class CategoryInUseError(ConflictError):
    code = "CATEGORY_IN_USE"


class DuplicateResourceError(ConflictError):
    code = "DUPLICATE_RESOURCE"


class PermissionDeniedError(DomainError):
    code = "PERMISSION_DENIED"
```

Repare no que **não** existe aqui: nenhum número de status HTTP, nenhum import de
`fastapi`. Este arquivo funcionaria igual dentro de uma CLI ou de um consumidor de fila.

O `code` é o campo estável que o SDD define na seção 7 — legível por máquina, e que um
front-end pode usar para decidir o que mostrar. O `detail` é a frase para humano e pode
mudar sem quebrar ninguém.

- [ ] **Passo 2: O tradutor**

Crie `app/api/errors.py`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)

STATUS_POR_EXCECAO: list[tuple[type[DomainError], int]] = [
    (NotFoundError, 404),
    (ConflictError, 409),
    (PermissionDeniedError, 403),
]


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def tratar_erro_de_dominio(_: Request, erro: DomainError) -> JSONResponse:
        status = 400
        for tipo, codigo in STATUS_POR_EXCECAO:
            if isinstance(erro, tipo):
                status = codigo
                break

        return JSONResponse(
            status_code=status,
            content={"detail": erro.detail, "code": erro.code},
        )
```

A ordem da lista importa: `CategoryInUseError` herda de `ConflictError`, então casa com
`ConflictError` e vira 409 sem precisar de entrada própria. Subclasses novas ganham o
status certo de graça — desde que herdem do lugar certo.

- [ ] **Passo 3: Registrar no `main.py`**

Em `app/main.py`, importe e chame logo depois de criar o `app`:

```python
from app.api.errors import registrar_handlers

registrar_handlers(app)
```

- [ ] **Passo 4: Verificar**

```bash
uv run pytest -q
```

```bash
uv run ruff check .
```

- [ ] **Passo 5: Commit**

```bash
git add app/core/exceptions.py app/api/ app/main.py
```

```bash
git commit -m "feat: excecoes de dominio e traducao para HTTP"
```

---

## Tarefa 5: Categorias

Entregável: CRUD de categorias funcionando, com R9 garantida.

**Arquivos:**
- Criar: `app/core/slug.py`, `app/schemas/__init__.py`, `app/schemas/category.py`,
  `app/services/__init__.py`, `app/services/category.py`, `app/api/deps.py`,
  `app/api/routes/__init__.py`, `app/api/routes/categories.py`,
  `tests/test_services/test_category_service.py`, `tests/test_api/test_categories.py`
- Modificar: `app/main.py`

---

- [ ] **Passo 1: Escrever os testes do service primeiro**

Crie `tests/test_services/test_category_service.py`:

```python
import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import CategoryInUseError, DuplicateResourceError, NotFoundError
from app.schemas.category import CategoriaCriar
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
    from decimal import Decimal

    from app.models import Product

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
```

O último teste é a regra **R9** do SDD. Ele é o mais importante dos quatro.

- [ ] **Passo 2: Rodar e confirmar a falha**

```bash
uv run pytest tests/test_services/ -v
```

Esperado: **falha** com `ModuleNotFoundError` em `app.schemas.category`.

- [ ] **Passo 3: O gerador de slug**

Crie `app/core/slug.py`:

```python
import re
import unicodedata


def gerar_slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    apenas_palavras = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento)
    return apenas_palavras.strip("-").lower()
```

`NFKD` separa a letra do acento (`á` vira `a` + acento), e o `encode("ascii", "ignore")`
descarta o que não couber em ASCII, deixando a letra limpa.

- [ ] **Passo 4: Os schemas**

Crie `app/schemas/category.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCriar(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoriaAtualizar(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class CategoriaLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: datetime
```

**Material de entrevista — por que schema e model são separados.** O model é a tabela; o
schema é o contrato da API. Mantê-los separados permite que a tabela ganhe colunas que a
API não expõe (`hashed_password` na Fase 4 é o exemplo óbvio) e que a API valide coisas
que o banco não valida. Misturar os dois é o atalho que o SDD recusa na seção 12, ao
descartar o SQLModel.

`from_attributes=True` autoriza o Pydantic a ler de um objeto do SQLAlchemy em vez de um
dicionário.

Crie também `app/schemas/__init__.py` e `app/services/__init__.py` vazios.

- [ ] **Passo 5: O service**

Crie `app/services/category.py`:

```python
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


def _recusar_duplicata(
    db: Session, nome: str, slug: str, ignorar_id: int | None = None
) -> None:
    consulta = select(Category).where((Category.name == nome) | (Category.slug == slug))
    if ignorar_id is not None:
        consulta = consulta.where(Category.id != ignorar_id)

    if db.scalar(consulta) is not None:
        raise DuplicateResourceError(f"Já existe uma categoria chamada {nome}")
```

**`flush` e não `commit`.** O `flush` manda o SQL para o banco e faz o objeto ganhar
`id`, mas **não fecha a transação**. Quem decide confirmar é a camada de cima — no caso,
a dependência `get_db`. Isso é o que vai permitir, na Fase 5, que um service componha
várias operações numa transação só e reverta tudo se alguma falhar. Service que dá
`commit` sozinho impede atomicidade.

**A contagem usa `count`, não carrega os produtos.** `select(func.count())` devolve um
número vindo do banco. Carregar a lista inteira só para perguntar "tem algum?" seria
gastar memória à toa — e numa categoria com dez mil produtos, seria desastroso.

- [ ] **Passo 6: Rodar os testes do service**

```bash
uv run pytest tests/test_services/ -v
```

Esperado: **4 passed**.

- [ ] **Passo 7: A dependência de sessão**

Crie `app/api/deps.py`:

```python
from app.db.session import get_db

__all__ = ["get_db"]
```

Um ponto único de onde as rotas importam dependências. Quando a Fase 4 acrescentar
`get_current_user` e `require_admin`, elas moram aqui e as rotas não mudam de import.

- [ ] **Passo 8: As rotas**

Crie `app/api/routes/categories.py`:

```python
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
```

Repare no tamanho de cada função: recebe, delega, devolve. Nenhuma regra de negócio
aqui. É a separação que o SDD chama de "a primeira coisa que um revisor experiente
procura".

**Sobre R7:** essas rotas ficam abertas nesta fase. A autenticação é a Fase 4, e é lá
que `require_admin` entra em `POST`, `PATCH` e `DELETE`. Nada está publicado na
internet, então o risco hoje é zero — mas não esqueça que a dívida existe.

Crie `app/api/routes/__init__.py` vazio.

- [ ] **Passo 9: Registrar o router**

Em `app/main.py`, acrescente:

```python
from app.api.routes import categories

app.include_router(categories.router, prefix="/api/v1")
```

O `/health` continua na raiz, sem prefixo, como o SDD define na seção 6.

- [ ] **Passo 10: Os testes de API**

Crie `tests/test_api/test_categories.py`:

```python
from fastapi.testclient import TestClient


def test_criar_categoria_devolve_201_e_slug(client: TestClient) -> None:
    resposta = client.post("/api/v1/categories", json={"name": "Monitores Gamer"})

    assert resposta.status_code == 201
    assert resposta.json()["slug"] == "monitores-gamer"


def test_criar_categoria_duplicada_devolve_409(client: TestClient) -> None:
    client.post("/api/v1/categories", json={"name": "Cadeiras"})

    resposta = client.post("/api/v1/categories", json={"name": "Cadeiras"})

    assert resposta.status_code == 409
    assert resposta.json()["code"] == "DUPLICATE_RESOURCE"


def test_atualizar_categoria_inexistente_devolve_404(client: TestClient) -> None:
    resposta = client.patch("/api/v1/categories/9999", json={"name": "Qualquer"})

    assert resposta.status_code == 404
    assert resposta.json()["code"] == "NOT_FOUND"


def test_nome_vazio_devolve_422(client: TestClient) -> None:
    resposta = client.post("/api/v1/categories", json={"name": ""})

    assert resposta.status_code == 422
```

Os dois do meio provam que o handler da Tarefa 4 funciona: a exceção de domínio virou
status HTTP e o `code` chegou ao cliente. O último prova que a validação do Pydantic
devolve 422 sozinha, sem código seu.

- [ ] **Passo 11: Rodar tudo**

```bash
uv run pytest -v
```

Esperado: **11 passed**.

```bash
uv run ruff format .
```

```bash
uv run ruff check .
```

- [ ] **Passo 12: Commit**

```bash
git add app/ tests/
```

```bash
git commit -m "feat: CRUD de categorias com slug automatico e regra R9"
```

---

## Tarefa 6: Produtos

Entregável: CRUD de produtos, com soft delete e validação de categoria.

**Arquivos:**
- Criar: `app/schemas/product.py`, `app/services/product.py`,
  `app/api/routes/products.py`, `tests/test_services/test_product_service.py`,
  `tests/test_api/test_products.py`
- Modificar: `app/main.py`

---

- [ ] **Passo 1: Os testes do service**

Crie `tests/test_services/test_product_service.py`:

```python
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError, NotFoundError
from app.schemas.category import CategoriaCriar
from app.schemas.product import ProdutoCriar
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
    categoria_id = _categoria(db_session)
    dados = ProdutoCriar(
        sku="NB-003",
        name="Notebook Slim",
        price=Decimal("2899.00"),
        stock_quantity=2,
        category_id=categoria_id,
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
    assert db_session.get(type(criado), criado.id) is not None


def test_listar_ignora_produtos_inativos(db_session: Session) -> None:
    categoria_id = _categoria(db_session)
    criado = servico.criar(
        db_session,
        ProdutoCriar(
            sku="NB-005",
            name="Notebook Antigo",
            price=Decimal("999.00"),
            stock_quantity=1,
            category_id=categoria_id,
        ),
    )
    servico.remover(db_session, criado.id)

    assert servico.listar(db_session) == []
```

Os dois últimos são a decisão número 3 do SDD: produto não é apagado, é desativado. O
teste prova as duas metades — a linha continua no banco, e some da listagem pública.

- [ ] **Passo 2: Confirmar a falha**

```bash
uv run pytest tests/test_services/test_product_service.py -v
```

- [ ] **Passo 3: Os schemas**

Crie `app/schemas/product.py`:

```python
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCriar(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    category_id: int


class ProdutoAtualizar(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    category_id: int | None = None
    is_active: bool | None = None


class ProdutoLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

`gt=0` e `ge=0` repetem no Pydantic o que os `CheckConstraint` já garantem no banco. De
novo, não é redundância inútil: a validação do Pydantic devolve **422 com mensagem
clara** antes de tocar o banco, enquanto o `CHECK` devolveria um erro cru de driver. Um é
experiência de quem usa a API, o outro é integridade do dado.

- [ ] **Passo 4: O service**

Crie `app/services/product.py`:

```python
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
```

**`exclude_unset=True` é o coração do PATCH.** Sem ele, um cliente que enviasse só
`{"price": 10}` receberia de volta um objeto com todos os outros campos apagados, porque
o Pydantic preencheria os ausentes com `None`. Com `exclude_unset`, só entra no
dicionário o que o cliente realmente mandou. É a diferença entre `PATCH` (atualização
parcial) e `PUT` (substituição completa), e confundir os dois é um erro comum.

- [ ] **Passo 5: Rodar os testes do service**

```bash
uv run pytest tests/test_services/ -v
```

Esperado: **9 passed**.

- [ ] **Passo 6: As rotas**

Crie `app/api/routes/products.py`:

```python
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
```

Em `app/main.py`, acrescente:

```python
from app.api.routes import products

app.include_router(products.router, prefix="/api/v1")
```

- [ ] **Passo 7: Os testes de API**

Crie `tests/test_api/test_products.py`:

```python
from fastapi.testclient import TestClient


def _criar_categoria(client: TestClient) -> int:
    return client.post("/api/v1/categories", json={"name": "Placas de Vídeo"}).json()["id"]


def test_criar_produto_devolve_201(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-001",
            "name": "Placa de Vídeo 8GB",
            "price": "2799.90",
            "stock_quantity": 4,
            "category_id": _criar_categoria(client),
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["price"] == "2799.90"


def test_preco_negativo_devolve_422(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-002",
            "name": "Placa Inválida",
            "price": "-10.00",
            "stock_quantity": 1,
            "category_id": _criar_categoria(client),
        },
    )

    assert resposta.status_code == 422


def test_categoria_inexistente_devolve_404(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-003",
            "name": "Placa Órfã",
            "price": "1500.00",
            "stock_quantity": 1,
            "category_id": 9999,
        },
    )

    assert resposta.status_code == 404


def test_patch_altera_so_o_campo_enviado(client: TestClient) -> None:
    criado = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-004",
            "name": "Placa Original",
            "price": "1000.00",
            "stock_quantity": 7,
            "category_id": _criar_categoria(client),
        },
    ).json()

    resposta = client.patch(f"/api/v1/products/{criado['id']}", json={"price": "1200.00"})

    assert resposta.status_code == 200
    assert resposta.json()["price"] == "1200.00"
    assert resposta.json()["name"] == "Placa Original"
    assert resposta.json()["stock_quantity"] == 7


def test_delete_some_da_listagem_mas_detalhe_continua(client: TestClient) -> None:
    criado = client.post(
        "/api/v1/products",
        json={
            "sku": "GPU-005",
            "name": "Placa Descontinuada",
            "price": "800.00",
            "stock_quantity": 2,
            "category_id": _criar_categoria(client),
        },
    ).json()

    assert client.delete(f"/api/v1/products/{criado['id']}").status_code == 204
    assert client.get("/api/v1/products").json() == []
    assert client.get(f"/api/v1/products/{criado['id']}").status_code == 200
```

O `test_patch_altera_so_o_campo_enviado` é o que prova o `exclude_unset`. Sem ele, `name`
e `stock_quantity` voltariam nulos e o teste falharia.

- [ ] **Passo 8: Rodar tudo**

```bash
uv run pytest -v
```

Esperado: **19 passed**.

```bash
uv run ruff format .
```

```bash
uv run ruff check .
```

- [ ] **Passo 9: Commit**

```bash
git add app/ tests/
```

```bash
git commit -m "feat: CRUD de produtos com soft delete"
```

---

## Tarefa 7: Fechamento da fase

Entregável: catálogo visível no Swagger, README atualizado, CI verde.

**Arquivos:**
- Modificar: `README.md`

---

- [ ] **Passo 1: Conferir o Swagger com os olhos**

```bash
docker compose up --build -d
```

```bash
uv run alembic upgrade head
```

Abra http://localhost:8000/docs.

Esperado: dois grupos novos, **categorias** e **produtos**, com todas as rotas, os
schemas de entrada e saída, e as descrições vindas das docstrings.

Crie uma categoria e um produto pela própria interface do Swagger. É a demonstração que
você vai fazer numa entrevista, então vale ensaiar uma vez.

- [ ] **Passo 2: Atualizar o README**

Devolva o Alembic à linha de stack e apague a frase que dizia que ele entraria na Fase 2.

Na seção **Como rodar**, acrescente o passo de migration depois do `docker compose up`:

```bash
uv run alembic upgrade head
```

Em **Decisões técnicas**, acrescente três parágrafos curtos: dinheiro em `Numeric`,
produto desativado em vez de apagado, e services sem conhecimento de HTTP.

No **Roadmap**, marque a Fase 2.

- [ ] **Passo 3: Rodar os portões antes de enviar**

Os mesmos comandos que o CI vai rodar:

```bash
uv run ruff check .
```

```bash
uv run ruff format --check .
```

```bash
uv run pytest --cov=app --cov-report=term-missing
```

- [ ] **Passo 4: Commit e observação do CI**

```bash
git add README.md
```

```bash
git commit -m "docs: README com o catalogo da Fase 2"
```

```bash
git push
```

Acompanhe a aba Actions. Se ficar vermelho, o suspeito número um é a variável
`DATABASE_URL_TEST` faltando no workflow — confira o Passo 6 da Tarefa 3.

- [ ] **Passo 5: Definição de pronto**

Marque cada item só depois de verificar:

- [ ] `alembic upgrade head` cria as duas tabelas num banco vazio
- [ ] `alembic downgrade -1` desfaz sem erro
- [ ] `POST /api/v1/categories` com `{"name": "Eletrônicos de Áudio"}` devolve slug `eletronicos-de-audio`
- [ ] Categoria com produto vinculado devolve 409 com `code: CATEGORY_IN_USE`
- [ ] `DELETE /api/v1/products/{id}` some da listagem mas responde 200 no detalhe
- [ ] `PATCH` de um campo só não apaga os outros
- [ ] Preço negativo devolve 422
- [ ] `uv run pytest` passa com 19 testes
- [ ] Cobertura de `app/services/` acima de 80%
- [ ] CI verde no GitHub
- [ ] Swagger mostra os grupos de categorias e produtos

---

## Dívidas assumidas nesta fase

Registradas aqui para não virarem esquecimento:

**As rotas de escrita estão abertas.** R7 exige `admin` para criar, editar e remover.
A autenticação é a Fase 4, e é lá que `require_admin` entra. Nada está publicado, então
o risco atual é zero.

**`GET /products` não tem busca, filtro nem paginação.** É a Fase 3 inteira. Por ora a
rota devolve todos os produtos ativos ordenados por nome.

**Não há índice composto para as consultas de listagem.** Também Fase 3, junto com os
filtros que vão justificá-los.

---

## O que vem depois

A Fase 3 acrescenta busca por nome sem diferenciar maiúsculas, filtro por categoria e
faixa de preço, ordenação, paginação e os índices que sustentam tudo isso. Ela ganha seu
próprio plano quando esta fase estiver concluída.
