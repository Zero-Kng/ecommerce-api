# Documento de Design de Software (SDD)
## API de E-commerce

| | |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-08-23 |
| **Autor** | José Henrique |
| **Status** | Em andamento |

---

## Sumário

1. [Objetivo e contexto](#1-objetivo-e-contexto)
2. [Decisões de projeto](#2-decisões-de-projeto)
3. [Arquitetura e stack](#3-arquitetura-e-stack)
4. [Modelo de dados](#4-modelo-de-dados)
5. [Regras de negócio](#5-regras-de-negócio)
6. [Contratos da API](#6-contratos-da-api)
7. [Tratamento de erros](#7-tratamento-de-erros)
8. [Segurança](#8-segurança)
9. [Estratégia de testes](#9-estratégia-de-testes)
10. [Roadmap de implementação](#10-roadmap-de-implementação)
11. [Fora de escopo](#11-fora-de-escopo)
12. [Alternativas consideradas](#12-alternativas-consideradas)

---

## 1. Objetivo e contexto

Construir uma API REST de e-commerce em Python, com qualidade de produção, para sustentar candidaturas a vagas de **estágio ou desenvolvedor júnior de backend**.

O critério de sucesso não é "ter um projeto no GitHub". É que um revisor técnico abra o repositório e encontre, em menos de dois minutos:

- testes automatizados executando;
- integração contínua verde;
- um comando único que sobe o projeto inteiro;
- um README que explica **decisões**, não só instalação;
- uma URL pública funcionando.

**Prazo realista:** 2 a 3 meses em ritmo de meio período.

### Por que e-commerce

O domínio tem regras de negócio genuínas, estoque não pode ficar negativo, um pedido é uma transação atômica, preço praticado precisa ser preservado. Isso rende conversa técnica de verdade em entrevista, ao contrário de um CRUD que apenas salva e lê.

---

## 2. Decisões de projeto

| Decisão | Escolha | Justificativa |
|---|---|---|
| Vaga alvo | Backend Python | Mercado maior e mais previsível para júnior |
| Domínio | Catálogo / e-commerce | Regras de negócio reais |
| Escopo funcional | Catálogo rico | Produtos, categorias, busca, filtros, paginação, usuários e pedidos |
| Estratégia de construção | Stack profissional desde o início | Repositório nasce pronto; sem refatoração de infraestrutura depois |
| Nível do autor | Python básico | Primeira API, primeiro banco, primeiro Docker |

### Mitigação de risco: fatia vertical

Montar o stack completo antes da primeira funcionalidade tem um risco conhecido: travar em erro de configuração antes de escrever qualquer lógica.

A mitigação é construir primeiro uma **fatia vertical** — um endpoint trivial (`/health`)
que atravessa a pilha inteira:

```
Docker sobe → FastAPI responde → PostgreSQL conecta → teste passa → CI fica verde
```

Se algo estiver mal configurado, o erro aparece num endpoint bobo, não no meio da lógica
de pedidos. Depois disso a configuração está resolvida em definitivo.

---

## 3. Arquitetura e stack

### Stack técnico

| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.12+ | — |
| Framework | FastAPI + Uvicorn | Swagger automático, validação embutida, framework Python mais pedido hoje |
| Banco de dados | PostgreSQL 16 | Padrão de mercado; roda em container, sem instalação na máquina |
| ORM | SQLAlchemy 2.0 | O que as empresas usam de verdade |
| Migrations | Alembic | Versiona o schema do banco — poucos júniors sabem, pega bem |
| Validação | Pydantic v2 | Contratos de entrada e saída |
| Testes | pytest + httpx + coverage | — |
| Qualidade | Ruff | Lint e formatação numa ferramenta só |
| Containerização | Docker + Docker Compose | Um comando sobe API e banco |
| CI | GitHub Actions | Testes e lint a cada push |
| Deploy | Render (free tier) | URL pública para o currículo |

### Estrutura de pastas

```
app/
  main.py              # ponto de entrada, registra rotas e handlers
  core/
    config.py          # configuração via variáveis de ambiente
    security.py        # hash de senha, geração e leitura de JWT
    exceptions.py      # exceções de domínio
  db/
    session.py         # engine e sessão do SQLAlchemy
    base.py            # classe base declarativa
  models/              # tabelas do banco (SQLAlchemy)
  schemas/             # contratos da API (Pydantic)
  services/            # regras de negócio
  api/
    deps.py            # dependências (sessão, usuário atual)
    routes/            # endpoints HTTP
tests/
  conftest.py          # fixtures compartilhadas
  test_services/       # testes das regras de negócio
  test_api/            # testes dos endpoints
alembic/               # histórico de migrations
docker-compose.yml
Dockerfile
.github/workflows/ci.yml
.env.example
README.md
```

### Princípio de organização

A separação que importa é **rota ≠ regra de negócio**. O endpoint recebe a requisição,
valida o formato e delega. Quem decide "tem estoque suficiente?" é a camada `services/`.

Consequência prática: os `services/` não sabem o que é HTTP. Não importam `fastapi`, não
levantam `HTTPException`, não conhecem códigos de status. Eles levantam exceções de
domínio, e a camada HTTP as traduz.

É a primeira coisa que um revisor experiente procura, e a razão pela qual um projeto
parece sênior mesmo sendo de júnior.

---

## 4. Modelo de dados

### Diagrama de relacionamentos

```
categories 1 ──── N products
                     │ 1
                     │
                     N
users 1 ──── N orders 1 ──── N order_items
```

### Tabelas

#### `users`

| Coluna | Tipo | Restrições |
|---|---|---|
| id | Integer | PK |
| email | String(255) | único, obrigatório, indexado |
| hashed_password | String(255) | obrigatório |
| full_name | String(255) | obrigatório |
| role | Enum(`admin`, `customer`) | obrigatório, padrão `customer` |
| is_active | Boolean | padrão `true` |
| created_at | DateTime(tz) | padrão agora |

#### `categories`

| Coluna | Tipo | Restrições |
|---|---|---|
| id | Integer | PK |
| name | String(100) | único, obrigatório |
| slug | String(120) | único, obrigatório, indexado |
| created_at | DateTime(tz) | padrão agora |

#### `products`

| Coluna | Tipo | Restrições |
|---|---|---|
| id | Integer | PK |
| sku | String(50) | único, obrigatório, indexado |
| name | String(255) | obrigatório, indexado (busca) |
| description | Text | opcional |
| price | **Numeric(10,2)** | obrigatório, `CHECK (price > 0)` |
| stock_quantity | Integer | obrigatório, padrão 0, `CHECK (stock_quantity >= 0)` |
| category_id | Integer | FK → categories.id |
| is_active | Boolean | padrão `true` |
| created_at | DateTime(tz) | padrão agora |
| updated_at | DateTime(tz) | atualizado automaticamente |

#### `orders`

| Coluna | Tipo | Restrições |
|---|---|---|
| id | Integer | PK |
| user_id | Integer | FK → users.id, obrigatório, indexado |
| status | Enum(`confirmed`, `cancelled`) | obrigatório, padrão `confirmed` |
| total_amount | Numeric(10,2) | obrigatório, calculado no servidor |
| created_at | DateTime(tz) | padrão agora |
| updated_at | DateTime(tz) | atualizado automaticamente |

#### `order_items`

| Coluna | Tipo | Restrições |
|---|---|---|
| id | Integer | PK |
| order_id | Integer | FK → orders.id, obrigatório |
| product_id | Integer | FK → products.id, obrigatório |
| quantity | Integer | obrigatório, `CHECK (quantity > 0)` |
| **unit_price** | Numeric(10,2) | obrigatório — cópia do preço no momento da compra |

### Três decisões que merecem explicação

Estas são as decisões a destacar no README e a defender numa entrevista.

**1. Dinheiro é `Numeric`, nunca `Float`.**
`Float` é binário e não representa decimais exatamente — `0.1 + 0.2` não dá `0.3`. Em
valores monetários isso vira centavo errado acumulado. `Numeric(10,2)` é decimal exato.
No Python, os valores chegam como `Decimal`.

**2. `order_items.unit_price` é uma cópia, não uma referência.**
O preço de um produto muda com o tempo. Se o item do pedido apenas apontasse para
`products.price`, o histórico de pedidos mudaria sozinho toda vez que um preço fosse
reajustado — e o total gravado deixaria de bater com a soma dos itens. Copiar o preço no
momento da compra é um *snapshot* de dados. É um erro que quase todo júnior comete.

**3. Produto não é apagado, é desativado (`is_active`).**
Apagar um produto que já apareceu em pedidos quebraria a integridade referencial e
destruiria o histórico. `DELETE /products/{id}` faz *soft delete*.

---

## 5. Regras de negócio

Todas implementadas em `services/`, todas cobertas por teste.

| # | Regra |
|---|---|
| R1 | Criar pedido é **atômico**: valida estoque de todos os itens, debita estoque, grava pedido e itens. Se qualquer etapa falhar, nada é gravado (rollback). |
| R2 | Estoque **nunca** fica negativo. Validado no service **e** garantido por `CHECK` no banco. |
| R3 | O preço unitário é congelado no momento do pedido. |
| R4 | Cancelar um pedido **devolve** o estoque. Só pedidos `confirmed` podem ser cancelados. |
| R5 | Produto inativo ou inexistente não pode entrar em pedido novo. |
| R6 | O total do pedido é **calculado no servidor**. O cliente envia apenas produto e quantidade. |
| R7 | Só `admin` cria, edita ou remove produtos e categorias. `customer` apenas lê o catálogo. |
| R8 | Um `customer` só enxerga os **próprios** pedidos. `admin` enxerga todos. |
| R9 | Categoria com produtos vinculados não pode ser removida. |

### Por que R6 é uma regra de segurança

Se a API aceitasse o total vindo do cliente, qualquer pessoa poderia enviar uma requisição
com `total_amount: 0.01` e comprar de graça. O servidor recalcula a partir do preço em
banco. É a categoria de falha mais comum em e-commerce amador.

### Por que R8 é uma regra de segurança

Sem essa verificação, trocar o ID na URL (`/orders/1`, `/orders/2`, `/orders/3`) exporia
os pedidos de outros clientes. A falha se chama **IDOR** (*Insecure Direct Object
Reference*) e está no OWASP Top 10. Não basta exigir login: é preciso checar se o usuário
logado é o dono do recurso.

### Concorrência: a última unidade em estoque

Se dois clientes pedirem a última unidade no mesmo instante, ambas as requisições podem
ler `stock_quantity = 1`, ambas validar com sucesso, e ambas debitar — deixando o estoque
em `-1`.

A solução é travar a linha do produto durante a transação:

```python
stmt = select(Product).where(Product.id == product_id).with_for_update()
```

O segundo pedido espera o primeiro terminar e então lê o valor já atualizado. O `CHECK`
no banco é a segunda linha de defesa, caso a trava falhe.

Este é um detalhe de nível sênior. Vale implementar e vale escrever sobre ele no README.

---

## 6. Contratos da API

Prefixo de todas as rotas de negócio: `/api/v1`

### Sistema

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/health` | público | Verifica aplicação e conexão com o banco |

### Autenticação

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/auth/register` | público | Cria conta de `customer` |
| POST | `/auth/login` | público | Retorna token JWT |
| GET | `/auth/me` | autenticado | Dados do usuário logado |

### Categorias

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/categories` | público | Lista categorias |
| POST | `/categories` | admin | Cria categoria |
| PATCH | `/categories/{id}` | admin | Atualiza categoria |
| DELETE | `/categories/{id}` | admin | Remove (bloqueado se houver produtos — R9) |

### Produtos

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/products` | público | Lista com busca, filtros, ordenação e paginação |
| GET | `/products/{id}` | público | Detalhe do produto |
| POST | `/products` | admin | Cria produto |
| PATCH | `/products/{id}` | admin | Atualiza produto |
| DELETE | `/products/{id}` | admin | Soft delete (`is_active = false`) |

**Parâmetros de `GET /products`:**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `search` | string | — | Busca parcial no nome, sem diferenciar maiúsculas |
| `category_id` | int | — | Filtra por categoria |
| `min_price` | decimal | — | Preço mínimo |
| `max_price` | decimal | — | Preço máximo |
| `sort` | enum | `name` | `name`, `-name`, `price`, `-price`, `-created_at` |
| `page` | int | 1 | Página, começando em 1 |
| `size` | int | 20 | Itens por página, máximo 100 |

**Formato de resposta paginada:**

```json
{
  "items": [ ... ],
  "total": 137,
  "page": 1,
  "size": 20,
  "pages": 7
}
```

### Pedidos

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/orders` | customer | Cria pedido |
| GET | `/orders` | autenticado | Próprios pedidos; admin vê todos |
| GET | `/orders/{id}` | dono ou admin | Detalhe do pedido |
| POST | `/orders/{id}/cancel` | dono ou admin | Cancela e devolve estoque |

**Requisição de `POST /orders`:**

```json
{
  "items": [
    { "product_id": 12, "quantity": 2 },
    { "product_id": 45, "quantity": 1 }
  ]
}
```

Observe que não há campo de preço nem de total. O servidor os determina (R6).

---

## 7. Tratamento de erros

### Formato padronizado

Toda resposta de erro segue a mesma forma:

```json
{
  "detail": "Estoque insuficiente para o produto Teclado Mecânico",
  "code": "INSUFFICIENT_STOCK"
}
```

O campo `code` é legível por máquina e estável; `detail` é legível por humano e pode mudar.

### Códigos HTTP

| Código | Quando |
|---|---|
| 400 | Requisição malformada em termos de negócio |
| 401 | Token ausente, inválido ou expirado |
| 403 | Autenticado, mas sem permissão (customer tentando rota de admin) |
| 404 | Recurso não existe |
| 409 | Conflito de estado: estoque insuficiente, e-mail já cadastrado, categoria em uso |
| 422 | Validação de formato (gerado automaticamente pelo Pydantic) |
| 500 | Erro não previsto |

### Exceções de domínio

Os `services/` levantam exceções próprias, definidas em `core/exceptions.py`:

```
DomainError
├── NotFoundError            → 404
├── ConflictError            → 409
│   ├── InsufficientStockError
│   ├── EmailAlreadyExistsError
│   └── CategoryInUseError
└── PermissionDeniedError    → 403
```

Um *exception handler* registrado em `main.py` traduz cada uma para a resposta HTTP
correspondente. Assim a regra de negócio permanece independente do protocolo — o mesmo
service funcionaria numa fila ou numa CLI sem alteração.

### Regra de vazamento

Nenhuma resposta de erro expõe stack trace, SQL ou mensagem interna de banco. Erros 500
registram o detalhe no log do servidor e devolvem mensagem genérica ao cliente.

---

## 8. Segurança

| Item | Decisão |
|---|---|
| Senhas | Hash com **bcrypt** via `passlib`. Nunca armazenadas em texto puro. |
| Tokens | JWT assinado com `SECRET_KEY` vinda de variável de ambiente. Expiração de 30 minutos. |
| Segredos | Nunca no código. `.env` no `.gitignore`; `.env.example` commitado com valores fictícios. |
| Autorização | Verificada por dependência do FastAPI (`get_current_user`, `require_admin`). |
| Posse de recurso | Checada explicitamente em pedidos (R8). |
| Injeção de SQL | Prevenida pelo uso do ORM com parâmetros vinculados. Sem concatenação de strings em query. |
| CORS | Configurável por variável de ambiente; restritivo por padrão. |

---

## 9. Estratégia de testes

### Distribuição

| Camada | Volume | O que verifica |
|---|---|---|
| Testes de service | maioria | Regras de negócio isoladas |
| Testes de API | médio | Endpoints ponta a ponta via `httpx` |
| Testes de modelo | poucos | Constraints do banco |

### Isolamento

Banco de testes separado. Cada teste roda dentro de uma transação revertida ao final,
via fixture no `conftest.py`. Nenhum teste enxerga dados de outro, e a ordem de execução
não importa.

### Casos obrigatórios

Estes não são opcionais — são a prova de que as regras funcionam:

- [ ] Pedido com estoque suficiente debita a quantidade correta
- [ ] Pedido com estoque insuficiente retorna 409 e **não grava nada**
- [ ] Pedido com múltiplos itens, um deles sem estoque, não grava nenhum item (atomicidade)
- [ ] Cancelamento devolve exatamente a quantidade debitada
- [ ] Cancelar pedido já cancelado retorna erro
- [ ] Alterar o preço de um produto não altera pedidos anteriores
- [ ] Total do pedido é calculado no servidor, ignorando qualquer valor enviado pelo cliente
- [ ] `customer` recebe 403 ao tentar criar produto
- [ ] `customer` recebe 404 ao pedir um pedido de outro usuário
- [ ] Requisição sem token recebe 401
- [ ] Paginação devolve a contagem total correta
- [ ] Busca por nome não diferencia maiúsculas de minúsculas

### Meta de cobertura

**80% em `services/`.** Não perseguir 100% global — cobertura alta em código trivial é
métrica vazia. O que importa é que toda regra de negócio tenha teste.

### Integração contínua

O workflow do GitHub Actions roda a cada push e pull request:

1. `ruff check` — lint
2. `ruff format --check` — formatação
3. `pytest --cov` — testes com cobertura

Build vermelho não é mesclado.

---

## 10. Roadmap de implementação

Cada fase termina com código rodando, testes passando, CI verde e commit feito.

### Fase 0 — Repositório e ambiente
Repositório Git local e no GitHub, `.gitignore`, ambiente virtual, `pyproject.toml`,
Ruff configurado, estrutura de pastas criada.
**Entregável:** repositório público com estrutura visível.

### Fase 1 — Fatia vertical
`Dockerfile`, `docker-compose.yml` com API e PostgreSQL, `GET /health` verificando a
conexão com o banco, primeiro teste, workflow do GitHub Actions verde.
**Entregável:** `docker compose up` sobe tudo; CI verde no GitHub.
**Marco crítico** — a partir daqui a infraestrutura não atrapalha mais.

### Fase 2 — Catálogo
Models de `categories` e `products`, primeira migration com Alembic, schemas Pydantic,
CRUD completo dos dois recursos, testes.
**Entregável:** catálogo funcional documentado no Swagger.

### Fase 3 — Busca, filtros e paginação
Parâmetros de `GET /products`, resposta paginada, índices no banco, testes.
**Entregável:** listagem de nível profissional.

### Fase 4 — Usuários e autenticação
Model `users`, hash de senha, registro, login com JWT, dependências de autorização,
proteção das rotas de admin, testes de permissão.
**Entregável:** API com controle de acesso funcionando.

### Fase 5 — Pedidos e estoque
Models `orders` e `order_items`, service de criação com transação atômica e trava de
linha, cancelamento com devolução, todos os casos obrigatórios de teste.
**Entregável:** o coração do projeto — a parte que rende entrevista.

### Fase 6 — Acabamento e deploy
README com decisões técnicas e diagrama, seed de dados de exemplo, relatório de
cobertura, deploy no Render, URL pública no currículo e no LinkedIn.
**Entregável:** projeto no ar, pronto para ser mostrado.

---

## 11. Fora de escopo

Excluídos deliberadamente. Enfeite desnecessário conta **contra** o candidato numa
entrevista, porque sugere incapacidade de avaliar proporção entre problema e solução.

- Carrinho persistente
- Pagamento, mesmo simulado
- Cálculo de frete
- Avaliações e comentários de produtos
- Upload de imagens
- Cache com Redis
- Filas e processamento assíncrono
- Microserviços
- Camada de repositório separada dos services
- Interface web (a documentação Swagger cumpre o papel de demonstração)

---

## 12. Alternativas consideradas

### Outros projetos avaliados

| Alternativa | Motivo da recusa |
|---|---|
| Pipeline de dados + dashboard Streamlit | Menos aderente a vagas de backend puro |
| Aplicação full-stack com front-end | Dobra o escopo; risco de entregar as duas metades pela metade |
| Aplicação com IA/LLM (RAG sobre documentos) | Forte candidata a **segundo projeto** — assunto quente e raro em portfólio júnior |

### Outras estratégias de construção

| Alternativa | Motivo da recusa |
|---|---|
| Escada (uma camada por vez, SQLite primeiro) | Exigiria migrar de SQLite para PostgreSQL depois; preferimos nascer no formato final |
| Escopo mínimo com acabamento máximo | Pouca substância técnica; entrevistador esgota as perguntas em cinco minutos |

### Decisões técnicas alternativas

| Alternativa | Motivo da recusa |
|---|---|
| Flask no lugar de FastAPI | Sem validação nem documentação automáticas; menos pedido em vagas novas |
| SQLModel no lugar de SQLAlchemy | Mais simples de aprender, mas mistura o modelo de banco com o contrato da API — justamente a separação que queremos demonstrar |
| MySQL no lugar de PostgreSQL | PostgreSQL é mais comum em vagas Python e tem recursos melhores |
