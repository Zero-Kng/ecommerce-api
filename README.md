# E-commerce API

[![CI](https://github.com/Zero-Kng/ecommerce-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Zero-Kng/ecommerce-api/actions/workflows/ci.yml)

API REST de e-commerce construída com FastAPI e PostgreSQL, com catálogo de produtos,
autenticação e gestão de pedidos com controle de estoque transacional.

> **Status:** em desenvolvimento. Fase 2 de 6 concluída — infraestrutura, fatia vertical
> e catálogo de categorias e produtos.

## Stack

Python 3.14 · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 · pytest · Docker · GitHub Actions

## Como rodar

Pré-requisitos: [Docker](https://www.docker.com/products/docker-desktop) e [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Zero-Kng/ecommerce-api.git
cd ecommerce-api
cp .env.example .env
docker compose up --build -d
uv run alembic upgrade head
```

A API sobe em http://localhost:8000 e a documentação interativa em http://localhost:8000/docs.

As migrations são aplicadas à mão, e não na subida do container: é o comportamento de
produção, onde migration automática com várias instâncias pode rodar em paralelo e
corromper o histórico.

## Como rodar os testes

Os testes rodam na máquina host e precisam do banco de pé. O banco de testes
(`ecommerce_test`) é criado e migrado automaticamente na primeira execução:

```bash
docker compose up -d db
uv sync
uv run pytest -v
```

Cada teste roda dentro de uma transação revertida ao final, então nenhum enxerga dados de
outro e a ordem de execução não importa.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica aplicação e conexão com o banco |
| GET | `/api/v1/categories` | Lista categorias |
| POST | `/api/v1/categories` | Cria categoria (slug gerado do nome) |
| PATCH | `/api/v1/categories/{id}` | Atualiza categoria |
| DELETE | `/api/v1/categories/{id}` | Remove categoria sem produtos vinculados |
| GET | `/api/v1/products` | Lista produtos ativos |
| GET | `/api/v1/products/{id}` | Detalhe do produto |
| POST | `/api/v1/products` | Cria produto |
| PATCH | `/api/v1/products/{id}` | Atualiza parcialmente |
| DELETE | `/api/v1/products/{id}` | Desativa o produto |

Autenticação e autorização entram na Fase 4; por ora as rotas de escrita estão abertas.

## Decisões técnicas

**Fatia vertical antes de funcionalidade.** A primeira coisa construída foi um `/health`
atravessando Docker, FastAPI e PostgreSQL, antes de qualquer regra de negócio. Erros de
configuração aparecem num endpoint trivial, não no meio da lógica de pedidos.

**Rota não conhece regra de negócio.** Os endpoints recebem, delegam e devolvem. Quem
decide "esta categoria pode ser removida?" é a camada `services/`, que não importa
`fastapi`, não levanta `HTTPException` e não menciona código de status. Os services
levantam exceções de domínio e um handler as traduz em resposta HTTP.

**Dinheiro é `Numeric`, nunca `Float`.** `Float` é binário e não representa decimais
exatamente. Em valores monetários isso vira centavo errado acumulado. No Python os
valores chegam como `Decimal`.

**Produto é desativado, não apagado.** `DELETE /products/{id}` faz *soft delete*. Apagar
um produto que já apareceu em pedidos quebraria a integridade referencial e destruiria o
histórico.

**Regras validadas no service e no banco.** Preço positivo e estoque não negativo têm
`CHECK` no PostgreSQL além da validação no Pydantic. O service dá a mensagem clara; a
restrição garante a integridade mesmo para escritas que não passam pela API.

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
- [x] **Fase 2** — Catálogo: produtos, categorias e migrations
- [ ] **Fase 3** — Busca, filtros e paginação
- [ ] **Fase 4** — Usuários e autenticação JWT
- [ ] **Fase 5** — Pedidos e controle transacional de estoque
- [ ] **Fase 6** — Acabamento e deploy
