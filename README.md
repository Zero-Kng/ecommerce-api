# E-commerce API

[![CI](https://github.com/Zero-Kng/ecommerce-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Zero-Kng/ecommerce-api/actions/workflows/ci.yml)

API REST de e-commerce construída com FastAPI e PostgreSQL, com catálogo de produtos,
autenticação e gestão de pedidos com controle de estoque transacional.

> **Status:** em desenvolvimento. Fase 1 de 6 concluída — infraestrutura e fatia vertical.

## Stack

Python 3.14 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · pytest · Docker · GitHub Actions

Alembic entra na Fase 2, junto com as primeiras migrations.

## Como rodar

Pré-requisitos: [Docker](https://www.docker.com/products/docker-desktop) e [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Zero-Kng/ecommerce-api.git
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
