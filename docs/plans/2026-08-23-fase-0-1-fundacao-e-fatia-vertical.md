# Fases 0 e 1 — Fundação e Fatia Vertical — Plano de Implementação

> **Para executores agênticos:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para implementar este plano tarefa a tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para acompanhamento.

**Objetivo:** Entregar um repositório profissional no GitHub onde `docker compose up` sobe API e PostgreSQL juntos, o endpoint `GET /health` confirma que a aplicação alcança o banco, e o GitHub Actions roda lint e testes em verde a cada push.

**Arquitetura:** Aplicação FastAPI síncrona em container, conversando com PostgreSQL em container irmão, orquestrados por Docker Compose. A configuração vem de variáveis de ambiente via Pydantic Settings. Nenhuma tabela de negócio é criada nesta fase — o objetivo é exclusivamente provar que a pilha inteira se comunica ponta a ponta antes de qualquer lógica de domínio existir.

**Stack:** Python 3.14, FastAPI, Uvicorn, SQLAlchemy 2.0 (síncrono), psycopg 3, Pydantic Settings, PostgreSQL 16, pytest, httpx, Ruff, Docker Compose, GitHub Actions, uv.

**Spec:** [`docs/sdd.md`](../sdd.md) — Seções 3 (Arquitetura e stack) e 10 (Roadmap, Fases 0 e 1).

---

## Restrições globais

Estas valem para **todas** as tarefas deste plano.

- Python **3.14**, fixado com `.python-version`. A mesma versão localmente, no Docker e no CI.
- SQLAlchemy **2.0+**, em modo **síncrono** (ver "Decisões novas" abaixo).
- Driver PostgreSQL: **psycopg 3** (`psycopg[binary]`), nunca `psycopg2`.
- PostgreSQL **16**.
- Gerenciador de dependências: **uv**. Todo comando Python roda via `uv run`.
- Ruff com `line-length = 100`, alvo `py314`.
- Nenhum segredo em código. Toda configuração vem de variável de ambiente.
- `.env` **nunca** é commitado. `.env.example` **sempre** é.
- Nenhum model de negócio, migration ou tabela nesta fase. Isso é a Fase 2.
- Toda tarefa termina com commit. Mensagens em português, prefixo Conventional Commits (`feat:`, `chore:`, `test:`, `docs:`, `ci:`).
- Testes rodam **na máquina host**, conectando em `localhost:5432`. O container da API conecta em `db:5432`. Essa diferença é intencional e está explicada na Tarefa 5.

---

## Decisões novas tomadas neste plano

O SDD não especificava estes três pontos. Cada um é defensável em entrevista.

**1. `uv` como gerenciador de dependências.** Substitui pip + venv + requirements.txt. Instala dependências em segundos, gera arquivo de lock automaticamente e elimina o passo de "ativar o ambiente virtual" — a fonte número um de confusão de quem está começando. É o padrão do ecossistema Python hoje.

**2. SQLAlchemy síncrono, não assíncrono.** A versão async exige sessões assíncronas, driver assíncrono, fixtures de teste assíncronas e cuidados com greenlet. É complexidade real em troca de ganho que este projeto não colhe — o gargalo aqui não é concorrência de I/O. O FastAPI executa endpoints síncronos num pool de threads sem bloquear o servidor. Resposta pronta para entrevista: *"escolhi síncrono porque o custo de complexidade do async não se pagava neste projeto; sei quando ele se paga."*

**3. `get_settings()` com cache, em vez de um objeto global.** Permite substituir a configuração nos testes e é o padrão idiomático do FastAPI.

---

## Mapa de arquivos

Ao final deste plano, o repositório terá exatamente esta estrutura:

| Arquivo | Responsabilidade |
|---|---|
| `.gitignore` | Impede que ambiente virtual, cache e segredos entrem no repositório |
| `.gitattributes` | Normaliza fim de linha entre Windows e Linux |
| `.python-version` | Fixa a versão do Python usada pelo uv |
| `pyproject.toml` | Dependências, configuração do Ruff e do pytest |
| `uv.lock` | Versões exatas resolvidas (gerado, mas commitado) |
| `.env.example` | Modelo de configuração, com valores fictícios |
| `.env` | Configuração local real — **não commitado** |
| `Dockerfile` | Imagem da API |
| `docker-compose.yml` | Orquestra API e PostgreSQL |
| `README.md` | Como rodar, o que é, quais decisões foram tomadas |
| `app/__init__.py` | Marca `app` como pacote |
| `app/main.py` | Cria a aplicação FastAPI e registra o `/health` |
| `app/core/__init__.py` | Marca `app.core` como pacote |
| `app/core/config.py` | Lê configuração de variáveis de ambiente |
| `app/db/__init__.py` | Marca `app.db` como pacote |
| `app/db/session.py` | Engine, fábrica de sessões e dependência `get_db` |
| `tests/__init__.py` | Marca `tests` como pacote |
| `tests/conftest.py` | Fixture do cliente de teste |
| `tests/test_config.py` | Testa a leitura de configuração |
| `tests/test_health.py` | Testa o endpoint `/health` |
| `.github/workflows/ci.yml` | Lint, formatação e testes automáticos |

**Ausente de propósito:** `app/models/`, `app/schemas/`, `app/services/`, `app/api/`, `alembic/`. Criar pastas vazias que ninguém usa é ruído. Elas nascem na Fase 2, quando houver o que colocar dentro.

---

## Tarefa 1: Repositório, ferramental e qualidade

Entregável: repositório Git publicado no GitHub, dependências instaladas, Ruff funcionando.

**Arquivos:**
- Criar: `.gitignore`
- Criar: `pyproject.toml`
- Criar: `app/__init__.py`, `app/core/__init__.py`, `app/db/__init__.py`, `tests/__init__.py`
- Gerado: `uv.lock`

**Interfaces:**
- Consome: nada (primeira tarefa)
- Produz: comandos `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` funcionando a partir da raiz do projeto

---

- [x] **Passo 1: Instalar o uv**

No PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Feche e reabra o terminal. Confirme:

```bash
uv --version
```

Esperado: uma versão é impressa. Se o comando não for encontrado, o terminal não foi reaberto.

- [x] **Passo 2: Inicializar o repositório Git**

Na raiz do projeto (`E:\Dev\Projetos\Projeto Full-Stack 1`):

```bash
git init -b main
```

Esperado: `Initialized empty Git repository`.

- [x] **Passo 3: Criar o `.gitignore`**

Crie `.gitignore` com este conteúdo:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/

# Ambiente virtual
.venv/

# Segredos
.env

# Cache de ferramentas
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# Editores
.vscode/
.idea/
```

A linha `.env` é a mais importante do arquivo. Ela é o que impede sua senha de banco de virar pública.

- [x] **Passo 4: Criar o `pyproject.toml`**

Crie `pyproject.toml` com este conteúdo:

```toml
[project]
name = "ecommerce-api"
version = "0.1.0"
description = "API REST de e-commerce"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.2",
    "pydantic-settings>=2.6",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "httpx>=0.28",
    "ruff>=0.8",
]

[tool.uv]
package = false

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "fastapi.Depends",
    "fastapi.Query",
    "fastapi.Path",
    "fastapi.Body",
    "fastapi.Header",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

O que cada bloco faz:

- `dependencies` — o que a aplicação precisa para rodar em produção.
- `dependency-groups.dev` — o que só você precisa para desenvolver. Não vai para a imagem final.
- `tool.uv.package = false` — diz ao uv que isto é uma aplicação, não uma biblioteca a ser publicada.
- `tool.ruff.lint.select` — quais famílias de regra ativar: `E`/`F` erros, `I` ordenação de imports, `UP` sintaxe moderna, `B` armadilhas comuns.
- `tool.ruff.lint.flake8-bugbear.extend-immutable-calls` — a regra `B008` proíbe chamar funções em valores padrão de parâmetro, porque o resultado seria calculado uma vez só e compartilhado entre chamadas. É uma boa regra, mas o `Depends()` do FastAPI é justamente uma exceção legítima: ele é um marcador, não uma chamada de verdade. Esta lista informa ao Ruff quais chamadas ignorar. Sem ela, o `ruff check` reprovaria todo endpoint que use injeção de dependência.
- `tool.pytest.pythonpath = ["."]` — permite que os testes façam `from app.main import app`.

- [x] **Passo 5: Criar os arquivos de pacote**

```bash
mkdir -p app/core app/db tests
touch app/__init__.py app/core/__init__.py app/db/__init__.py tests/__init__.py
```

No PowerShell, use:

```powershell
New-Item -ItemType Directory -Force app/core, app/db, tests
New-Item -ItemType File app/__init__.py, app/core/__init__.py, app/db/__init__.py, tests/__init__.py
```

Arquivos `__init__.py` vazios são o que transforma uma pasta num pacote Python importável.

- [x] **Passo 6: Instalar as dependências**

```bash
uv sync
```

Esperado: o uv cria `.venv/`, resolve as versões, instala tudo e grava `uv.lock`.

- [x] **Passo 7: Verificar que o Ruff funciona**

```bash
uv run ruff check .
```

Esperado: `All checks passed!`

- [x] **Passo 8: Commit**

```bash
git add .gitignore pyproject.toml uv.lock app tests docs
git commit -m "chore: estrutura inicial do projeto com uv e ruff"
```

O `docs` entra aqui: o SDD e os planos de implementação fazem parte do repositório. O README da Tarefa 7 vai linkar para `docs/sdd.md`, e um link quebrado na primeira página é pior que documentação nenhuma. Documentação de decisões versionada junto do código também é, por si só, um sinal de maturidade que poucos portfólios júnior têm.

- [x] **Passo 9: Publicar no GitHub**

Crie um repositório **público** chamado `ecommerce-api` em https://github.com/new. Não marque nenhuma opção de inicialização (sem README, sem .gitignore, sem licença) — o repositório local já tem conteúdo.

Depois, conecte e envie:

```bash
git remote add origin https://github.com/SEU-USUARIO/ecommerce-api.git
git push -u origin main
```

Esperado: o código aparece no GitHub.

---

## Tarefa 2: Aplicação FastAPI mínima com `/health`

Entregável: servidor rodando na máquina, respondendo `/health`, com teste automatizado passando. Ainda sem Docker e sem banco.

**Arquivos:**
- Criar: `app/main.py`
- Criar: `tests/conftest.py`
- Criar: `tests/test_health.py`

**Interfaces:**
- Consome: estrutura de pacotes da Tarefa 1
- Produz: `app.main.app` (instância `FastAPI`); fixture pytest `client` (`fastapi.testclient.TestClient`)

---

- [x] **Passo 1: Escrever a fixture do cliente de teste**

Crie `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP que fala com a aplicação sem subir um servidor de verdade."""
    return TestClient(app)
```

Uma *fixture* é um pedaço de preparo reaproveitável. Qualquer teste que declare um parâmetro chamado `client` recebe este objeto pronto.

- [x] **Passo 2: Escrever o teste que falha**

Crie `tests/test_health.py`:

```python
from fastapi.testclient import TestClient


def test_health_responde_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [x] **Passo 3: Rodar o teste e confirmar que falha**

```bash
uv run pytest tests/test_health.py -v
```

Esperado: **FALHA** com `ModuleNotFoundError: No module named 'app.main'`.

Este passo não é burocracia. Um teste que nunca foi visto falhando pode estar passando por engano — por exemplo, por não estar testando nada. Ver a falha é o que prova que o teste tem poder de detectar o problema.

- [x] **Passo 4: Escrever a implementação mínima**

Crie `app/main.py`:

```python
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
```

- [x] **Passo 5: Rodar o teste e confirmar que passa**

```bash
uv run pytest tests/test_health.py -v
```

Esperado: **PASSA** — `1 passed`.

- [x] **Passo 6: Ver a aplicação rodando de verdade**

```bash
uv run uvicorn app.main:app --reload
```

Abra http://localhost:8000/docs no navegador. A documentação Swagger está lá, gerada sozinha, com o `/health` clicável. Clique em *Try it out* e depois em *Execute*.

Encerre com `Ctrl+C`.

- [x] **Passo 7: Verificar lint e formatação**

```bash
uv run ruff format .
uv run ruff check .
```

Esperado: arquivos formatados e `All checks passed!`

- [x] **Passo 8: Commit**

```bash
git add app/main.py tests/conftest.py tests/test_health.py
git commit -m "feat: aplicacao FastAPI com endpoint de health check"
git push
```

---

## Tarefa 3: Containerização com Docker e PostgreSQL

Entregável: `docker compose up` sobe API e banco juntos; a API responde na porta 8000.

**Arquivos:**
- Criar: `Dockerfile`
- Criar: `docker-compose.yml`
- Criar: `.env.example`
- Criar: `.env` (local, não commitado)

**Interfaces:**
- Consome: `app.main:app` da Tarefa 2; `pyproject.toml` e `uv.lock` da Tarefa 1
- Produz: serviço `db` acessível em `localhost:5432` (host) e `db:5432` (rede interna); serviço `api` em `localhost:8000`

---

- [x] **Passo 1: Instalar o Docker Desktop**

Baixe em https://www.docker.com/products/docker-desktop e instale. Abra o Docker Desktop e espere o ícone indicar que está rodando.

```bash
docker --version
docker compose version
```

Esperado: ambas as versões são impressas.

- [x] **Passo 2: Criar o `Dockerfile`**

```dockerfile
FROM python:3.14-slim

# Copia o binário do uv de uma imagem oficial, sem precisar instalar nada
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /code

# Instala as dependências antes de copiar o código.
# Assim o Docker reaproveita esta camada enquanto as dependências não mudarem.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Deixa o ambiente virtual no PATH, para chamar "uvicorn" diretamente
ENV PATH="/code/.venv/bin:$PATH"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Dois detalhes que valem entrevista:

- **Ordem das camadas.** Dependências mudam raramente; código muda o tempo todo. Copiando as dependências primeiro, um build após uma alteração de código reaproveita o cache e leva segundos em vez de minutos.
- **`--no-dev`.** A imagem de produção não carrega pytest nem Ruff. Imagem menor, superfície de ataque menor.

- [x] **Passo 3: Criar o `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ecommerce
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@db:5432/ecommerce
    ports:
      - "8000:8000"
    volumes:
      - ./app:/code/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

O que cada parte resolve:

- **`healthcheck` + `depends_on: condition: service_healthy`** — o PostgreSQL leva alguns segundos para aceitar conexões depois que o container sobe. Sem isso, a API sobe antes e falha ao conectar. `depends_on` sozinho só espera o container *iniciar*, não ficar *pronto*.
- **`volumes: postgres_data`** — sem isso, seus dados somem toda vez que o container é removido.
- **`volumes: ./app:/code/app`** — espelha seu código dentro do container. Junto com `--reload`, você edita um arquivo no Windows e o servidor recarrega sozinho.
- **`ports: "5432:5432"`** — publica o banco na sua máquina, para que os testes rodem no host.

- [x] **Passo 4: Criar `.env.example` e `.env`**

`.env.example` (este vai para o Git):

```dotenv
# Conexão com o banco usada pelos testes rodando na máquina host
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce
```

Agora copie para `.env`, que fica só na sua máquina:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

- [x] **Passo 5: Subir tudo**

```bash
docker compose up --build
```

Esperado: o build da imagem acontece, o `db` fica saudável, e o `api` imprime `Application startup complete`.

- [x] **Passo 6: Confirmar que a API responde de dentro do container**

Em outro terminal:

```bash
curl http://localhost:8000/health
```

Esperado: `{"status":"ok"}`

Abra também http://localhost:8000/docs. Se aparecer, a API está servindo de dentro do Docker.

- [x] **Passo 7: Confirmar que o banco está de pé**

```bash
docker compose exec db psql -U postgres -d ecommerce -c "SELECT version();"
```

Esperado: a versão do PostgreSQL 16 é impressa.

Encerre com `Ctrl+C` e depois:

```bash
docker compose down
```

- [x] **Passo 8: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example
git commit -m "feat: containeriza a API com Docker Compose e PostgreSQL"
git push
```

Confirme no GitHub que o `.env` **não** aparece na listagem de arquivos. Se aparecer, o `.gitignore` está errado — corrija antes de seguir.

---

## Tarefa 4: Configuração via variáveis de ambiente

Entregável: a aplicação lê sua configuração do ambiente, com validação e mensagem de erro clara quando faltar algo.

**Arquivos:**
- Criar: `app/core/config.py`
- Criar: `tests/test_config.py`

**Interfaces:**
- Consome: nada de tarefas anteriores
- Produz:
  - `app.core.config.Settings` — classe com os campos `project_name: str` e `database_url: str`
  - `app.core.config.get_settings() -> Settings` — função com cache, usada pelo resto da aplicação

---

- [x] **Passo 1: Escrever o teste que falha**

Crie `tests/test_config.py`:

```python
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_le_database_url_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://usuario:senha@localhost:5432/teste"
    )

    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://usuario:senha@localhost:5432/teste"


def test_settings_falha_quando_database_url_esta_ausente(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)  # sai da pasta do projeto para não achar o .env

    with pytest.raises(ValidationError):
        Settings()
```

O segundo teste é o que importa de verdade: ele prova que a aplicação **quebra alto e cedo** quando falta configuração, em vez de subir e falhar de forma confusa na primeira requisição.

- [x] **Passo 2: Rodar o teste e confirmar que falha**

```bash
uv run pytest tests/test_config.py -v
```

Esperado: **FALHA** com `ModuleNotFoundError: No module named 'app.core.config'`.

- [x] **Passo 3: Escrever a implementação**

Crie `app/core/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, lida de variáveis de ambiente ou do arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "E-commerce API"
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Devolve a configuração, lendo o ambiente apenas na primeira chamada."""
    return Settings()
```

Três coisas acontecendo aqui:

- `database_url` não tem valor padrão, então é **obrigatório**. Se faltar, o Pydantic levanta erro na inicialização.
- `env_file=".env"` faz a leitura do arquivo local. Variáveis de ambiente reais têm prioridade sobre ele — é por isso que o Docker Compose consegue sobrescrever com `db:5432`.
- `@lru_cache` garante que o ambiente seja lido uma vez só; as chamadas seguintes devolvem o mesmo objeto.

- [x] **Passo 4: Rodar os testes e confirmar que passam**

```bash
uv run pytest tests/test_config.py -v
```

Esperado: **PASSA** — `2 passed`.

- [x] **Passo 5: Usar a configuração no `main.py`**

Substitua o topo de `app/main.py`:

```python
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
```

- [x] **Passo 6: Rodar a suíte inteira**

```bash
uv run pytest -v
```

Esperado: **3 passed**. Se `test_health` falhar com erro de `DATABASE_URL`, é porque o `.env` não existe — refaça o Passo 4 da Tarefa 3.

- [x] **Passo 7: Lint e commit**

```bash
uv run ruff format .
uv run ruff check .
git add app/core/config.py app/main.py tests/test_config.py
git commit -m "feat: configuracao da aplicacao via variaveis de ambiente"
git push
```

---

## Tarefa 5: Conexão com o banco no `/health`

Entregável: a fatia vertical fechada. O `/health` executa uma consulta real no PostgreSQL e reporta o resultado.

**Arquivos:**
- Criar: `app/db/session.py`
- Modificar: `app/main.py`
- Modificar: `tests/test_health.py`

**Interfaces:**
- Consome: `app.core.config.get_settings()` da Tarefa 4
- Produz:
  - `app.db.session.engine` — engine do SQLAlchemy
  - `app.db.session.SessionLocal` — fábrica de sessões
  - `app.db.session.get_db() -> Generator[Session, None, None]` — dependência do FastAPI, usada por **todos** os endpoints das fases seguintes

---

### Antes de começar: o detalhe dos dois endereços

Este é o ponto onde a maioria das pessoas perde uma tarde. Leia antes de rodar qualquer coisa.

O PostgreSQL tem **dois endereços diferentes**, dependendo de quem está chamando:

| Quem chama | Endereço | Por quê |
|---|---|---|
| Container da API | `db:5432` | Dentro da rede do Compose, `db` é o nome do serviço |
| Seus testes, na sua máquina | `localhost:5432` | O Compose publicou a porta do container para a máquina |

Por isso `.env` (usado pelos testes no host) aponta para `localhost`, enquanto o `docker-compose.yml` sobrescreve a variável para `db` dentro do container da API. Não é inconsistência — é a mesma configuração vista de dois lugares.

Consequência prática: **o banco precisa estar de pé para os testes rodarem.** Deixe `docker compose up -d db` rodando enquanto trabalha.

---

- [ ] **Passo 1: Subir apenas o banco**

```bash
docker compose up -d db
```

Confirme que ficou saudável:

```bash
docker compose ps
```

Esperado: o serviço `db` aparece com status `healthy`.

- [ ] **Passo 2: Escrever o teste que falha**

Substitua o conteúdo de `tests/test_health.py`:

```python
from fastapi.testclient import TestClient


def test_health_responde_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_confirma_conexao_com_o_banco(client: TestClient) -> None:
    response = client.get("/health")

    assert response.json() == {"status": "ok", "database": "ok"}
```

- [ ] **Passo 3: Rodar o teste e confirmar que falha**

```bash
uv run pytest tests/test_health.py -v
```

Esperado: `test_health_responde_ok` **PASSA**, e `test_health_confirma_conexao_com_o_banco` **FALHA**, porque a resposta atual é `{"status": "ok"}` — falta a chave `database`.

- [ ] **Passo 4: Escrever a camada de sessão**

Crie `app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Abre uma sessão por requisição e garante o fechamento ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Por que cada opção está aí:

- **`pool_pre_ping=True`** — o SQLAlchemy testa a conexão antes de entregá-la. Sem isso, conexões que o banco derrubou por inatividade voltam para a aplicação e estouram na primeira consulta. É o remédio para o erro intermitente clássico "server closed the connection unexpectedly".
- **`try/finally`** — a sessão fecha mesmo que o endpoint levante exceção. Sem isso, o pool de conexões vaza e a aplicação trava sob carga.
- **`expire_on_commit=False`** — depois de um commit, os objetos continuam legíveis sem uma nova ida ao banco. Isso evita erros confusos ao montar a resposta HTTP depois de gravar algo. Vai importar muito na Fase 5.

- [ ] **Passo 5: Usar a sessão no `/health`**

Substitua o conteúdo de `app/main.py`:

```python
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="API REST de e-commerce com catálogo, autenticação e pedidos.",
)


@app.get("/health", tags=["sistema"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Confirma que a aplicação está de pé e alcança o banco de dados."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
```

`Depends(get_db)` é o sistema de injeção de dependência do FastAPI. Ele chama `get_db()`, entrega a sessão ao endpoint e executa o `finally` quando a resposta termina. Você nunca abre nem fecha sessão manualmente num endpoint.

- [ ] **Passo 6: Rodar os testes e confirmar que passam**

```bash
uv run pytest -v
```

Esperado: **4 passed**.

Se aparecer `connection refused`, o banco não está de pé — volte ao Passo 1.

- [ ] **Passo 7: Confirmar a fatia vertical completa, de ponta a ponta**

```bash
docker compose up --build -d
curl http://localhost:8000/health
```

Esperado: `{"status":"ok","database":"ok"}`

Este é o marco da Fase 1. Neste momento, uma requisição HTTP entrou num container, atravessou o FastAPI, abriu uma sessão do SQLAlchemy, executou SQL num segundo container e voltou. A infraestrutura está provada.

Prove também que a detecção de falha funciona — derrube o banco e veja o `/health` reclamar:

```bash
docker compose stop db
curl http://localhost:8000/health
```

Esperado: erro 500. Isso é o correto por ora — o tratamento elegante de erros é a Fase 2, quando a hierarquia de exceções do SDD entrar.

Suba de novo:

```bash
docker compose start db
```

- [ ] **Passo 8: Lint e commit**

```bash
uv run ruff format .
uv run ruff check .
git add app/db/session.py app/main.py tests/test_health.py
git commit -m "feat: health check verifica a conexao com o PostgreSQL"
git push
```

---

## Tarefa 6: Integração contínua no GitHub Actions

Entregável: a cada push, o GitHub roda lint, checagem de formatação e testes contra um PostgreSQL de verdade.

**Arquivos:**
- Criar: `.github/workflows/ci.yml`

**Interfaces:**
- Consome: `uv.lock` da Tarefa 1; suíte de testes das Tarefas 2, 4 e 5
- Produz: verificação automática em todo push e pull request

---

- [ ] **Passo 1: Criar o arquivo de workflow**

Crie `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    name: Lint e testes
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ecommerce
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce

    steps:
      - name: Baixar o código
        uses: actions/checkout@v4

      - name: Instalar o uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Instalar dependências
        run: uv sync --frozen

      - name: Verificar lint
        run: uv run ruff check .

      - name: Verificar formatação
        run: uv run ruff format --check .

      - name: Rodar testes
        run: uv run pytest --cov=app --cov-report=term-missing
```

Note a simetria com o desenvolvimento local: aqui também o PostgreSQL sobe como serviço com `healthcheck`, e os testes conectam em `localhost:5432`. **O mesmo comando funciona nos dois lugares** — se passa na sua máquina, passa no CI. Ambiente de CI que diverge do local é fonte inesgotável de frustração.

- [ ] **Passo 2: Enviar e observar**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: roda lint e testes no GitHub Actions"
git push
```

Abra a aba **Actions** do seu repositório no GitHub. O workflow começa a rodar em segundos.

Esperado: todos os passos ficam verdes.

- [ ] **Passo 3: Provar que o CI realmente pega erro**

Um CI que nunca ficou vermelho não é prova de nada. Quebre de propósito.

Em `tests/test_health.py`, troque temporariamente:

```python
    assert response.status_code == 200
```

por:

```python
    assert response.status_code == 500
```

Depois:

```bash
git add tests/test_health.py
git commit -m "test: verifica que o CI detecta falha"
git push
```

Esperado: o workflow fica **vermelho** na aba Actions, e o GitHub envia um e-mail avisando.

Agora desfaça:

```bash
git revert HEAD --no-edit
git push
```

Esperado: o workflow volta ao verde.

Você acabou de verificar sua própria verificação. É o hábito que separa quem confia no CI de quem só tem um arquivo YAML bonito no repositório.

---

## Tarefa 7: README e fechamento da fase

Entregável: repositório apresentável a um recrutador, com instruções que funcionam e decisões explicadas.

**Arquivos:**
- Criar: `README.md`

**Interfaces:**
- Consome: tudo que foi construído nas Tarefas 1 a 6
- Produz: documentação de entrada do repositório

---

- [ ] **Passo 1: Escrever o README**

Crie `README.md`. Substitua `SEU-USUARIO` pelo seu usuário do GitHub.

````markdown
# E-commerce API

[![CI](https://github.com/SEU-USUARIO/ecommerce-api/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU-USUARIO/ecommerce-api/actions/workflows/ci.yml)

API REST de e-commerce construída com FastAPI e PostgreSQL, com catálogo de produtos,
autenticação e gestão de pedidos com controle de estoque transacional.

> **Status:** em desenvolvimento. Fase 1 de 6 concluída — infraestrutura e fatia vertical.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Alembic · pytest · Docker · GitHub Actions

## Como rodar

Pré-requisitos: [Docker](https://www.docker.com/products/docker-desktop) e [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/SEU-USUARIO/ecommerce-api.git
cd ecommerce-api
cp .env.example .env
docker compose up --build
```

A API sobe em http://localhost:8000 e a documentação interativa em http://localhost:8000/docs.

## Como rodar os testes

Os testes rodam na máquina host e precisam do banco de pé:

```bash
docker compose up -d db
uv sync
uv run pytest -v
```

## Decisões técnicas

**Fatia vertical antes de funcionalidade.** A primeira coisa construída foi um `/health`
atravessando Docker, FastAPI e PostgreSQL, antes de qualquer regra de negócio. Erros de
configuração aparecem num endpoint trivial, não no meio da lógica de pedidos.

**SQLAlchemy síncrono.** A versão assíncrona traria sessões, driver e fixtures de teste
assíncronos. O gargalo deste projeto não é concorrência de I/O, e o FastAPI executa
endpoints síncronos num pool de threads sem bloquear o servidor. A complexidade não se
pagava.

**`pool_pre_ping` habilitado.** O SQLAlchemy valida a conexão antes de entregá-la ao
código, evitando falhas intermitentes com conexões derrubadas por inatividade.

**CI espelha o ambiente local.** Nas duas situações o PostgreSQL sobe com `healthcheck` e
os testes conectam em `localhost:5432`. O mesmo comando roda nos dois lugares.

## Documentação

- [Documento de Design de Software (SDD)](docs/sdd.md) — arquitetura, modelo de dados e regras de negócio
- [Planos de implementação](docs/plans/)

## Roadmap

- [x] **Fase 0–1** — Fundação e fatia vertical
- [ ] **Fase 2** — Catálogo: produtos, categorias e migrations
- [ ] **Fase 3** — Busca, filtros e paginação
- [ ] **Fase 4** — Usuários e autenticação JWT
- [ ] **Fase 5** — Pedidos e controle transacional de estoque
- [ ] **Fase 6** — Acabamento e deploy
````

- [ ] **Passo 2: Verificar as instruções do zero**

Não confie no README — teste-o. Numa pasta diferente:

```bash
git clone https://github.com/SEU-USUARIO/ecommerce-api.git teste-clone
cd teste-clone
cp .env.example .env
docker compose up --build
```

Esperado: a API sobe e `curl http://localhost:8000/health` devolve `{"status":"ok","database":"ok"}`.

Se algum passo do README não funcionar, corrija o README. Instruções quebradas na primeira página do repositório são o pior cartão de visita possível — dizem ao revisor que você nunca conferiu o próprio trabalho.

Apague a pasta `teste-clone` depois.

- [ ] **Passo 3: Commit final da fase**

```bash
git add README.md
git commit -m "docs: README com instrucoes de execucao e decisoes tecnicas"
git push
```

- [ ] **Passo 4: Conferir a definição de pronto**

Marque cada item apenas depois de verificar:

- [ ] `docker compose up` sobe API e banco com um comando só
- [ ] `curl http://localhost:8000/health` devolve `{"status":"ok","database":"ok"}`
- [ ] http://localhost:8000/docs mostra a documentação interativa
- [ ] `uv run pytest` passa com 4 testes
- [ ] `uv run ruff check .` passa sem avisos
- [ ] O badge do CI está verde no topo do README
- [ ] O arquivo `.env` **não** aparece no GitHub
- [ ] O README foi verificado com um clone limpo

---

## O que vem depois

A Fase 2 (catálogo: models, migrations com Alembic, CRUD de produtos e categorias) ganha
seu próprio plano, escrito quando esta fase estiver concluída. Escrever agora os detalhes
de tarefas que só acontecerão em semanas significaria fixar decisões antes de existir o
código que as informa.
