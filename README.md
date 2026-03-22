# Kanban Project Manager — Back-end

API REST do sistema de gerenciamento de projetos no estilo Kanban. Desenvolvida em Python com FastAPI + PostgreSQL.

---

## Stack

| Camada         | Tecnologia                    |
|----------------|-------------------------------|
| Framework      | FastAPI                       |
| Banco de dados | PostgreSQL                    |
| ORM            | SQLAlchemy (assíncrono)       |
| Autenticação   | JWT (`python-jose`)           |
| Hash de senha  | Bcrypt (`passlib`)            |
| Servidor       | Uvicorn (porta 8000)          |
| E-mail         | SMTP                          |

---

## Ambientes

| Ambiente | Banco | Como rodar |
|----------|-------|------------|
| **Local** | PostgreSQL via Docker | Siga os passos abaixo |
| **Produção** | Supabase (PostgreSQL) | Deploy no Render via GitHub |

---

## Como Rodar Localmente

### 1. Navegue até o diretório do projeto

```bash
cd Back-end
```

### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` dentro de `Back-end/app/`:

```env
SECRET_KEY=qualquer_chave_secreta_local
ALGORITHM=HS256
TEST_MODE=True
DB_URL_TEST=postgresql+asyncpg://postgres:admin@localhost:5432/faculdade-test
DB_URL=postgresql+asyncpg://postgres:admin@localhost:5432/faculdade-test
EMAIL=seu@email.com
EMAIL_PASSWORD=sua_senha_de_app
FRONT_URL=http://localhost:3000
```

> **TEST_MODE=True** faz a aplicação usar `DB_URL_TEST` (banco local via Docker).
> Em produção no Render, `TEST_MODE=False` e `DB_URL` aponta para o Supabase.

### 3. Crie e ative o ambiente virtual

```bash
# Criar
python -m venv .venv

# Ativar — Windows PowerShell
.\.venv\Scripts\Activate

# Ativar — Windows Command Prompt
.venv\Scripts\activate

# Ativar — macOS/Linux
source .venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install --no-cache-dir -r requirements.txt
```

### 5. Suba o banco de dados local

Certifique-se de que o Docker Desktop está aberto. Depois execute:

```bash
docker compose up -d
```

Isso sobe um container PostgreSQL na porta `5432` com as credenciais configuradas no `.env`.

### 6. Crie as tabelas e roles no banco local

> **ATENÇÃO:** Este script apaga e recria todo o banco. Use **somente** com `TEST_MODE=True` apontando para o banco local.

```bash
python -m app.generate_table
```

### 7. Suba o servidor

```bash
uvicorn app.main:app --reload --port 8000
```

A aplicação estará disponível em: `http://localhost:8000`

**Swagger UI (documentação interativa):** `http://localhost:8000/docs`

> O Swagger só aparece em ambiente local. Em produção ele é desabilitado por segurança.

---

## Arquitetura

```
Rotas (api/routes/)
    └── Regras de negócio (rules/)
            └── Banco de dados (db/models/)
```

- **Routes** — recebem requisições HTTP e delegam para as Rules
- **Rules** — lógica de negócio; acessam os Models
- **Schemas** (Pydantic) — validação de entrada e saída
- **Core** — JWT, bcrypt, dependências, e-mail, configurações

---

## Estrutura de Arquivos

```
Back-end/
├── run.py                        # Ponto de entrada (inicia Uvicorn)
├── requirements.txt
├── docker-compose.yml            # Container PostgreSQL local
└── app/
    ├── .env                      # Variáveis de ambiente (não vai ao Git)
    ├── main.py                   # Instância FastAPI, CORS, routers
    ├── generate_table.py         # Reset e seed do banco LOCAL
    ├── api/
    │   ├── api.py                # Agrega todos os routers em /api
    │   └── routes/
    │       ├── user_router.py        # /api/users
    │       ├── project_router.py     # /api/projects
    │       ├── list_router.py        # /api/projects/{id}/lists
    │       ├── card_router.py        # /api/cards
    │       └── comments_router.py    # /api/comments
    ├── core/
    │   ├── configs.py            # Settings via variáveis de ambiente
    │   ├── auth.py               # Geração e validação de JWT
    │   ├── security.py           # Hash de senha (bcrypt)
    │   ├── deps.py               # get_session, get_current_user
    │   └── email.py              # Envio de e-mails SMTP
    ├── db/
    │   ├── conection.py          # Engine assíncrona SQLAlchemy
    │   └── models/               # ORM models (um por tabela)
    ├── rules/                    # Lógica de negócio por domínio
    └── schemas/                  # Pydantic schemas (validação I/O)
```

---

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/users/login` | Login (retorna JWT) |
| POST | `/api/users/` | Cadastro |
| GET | `/api/projects/` | Lista projetos do usuário |
| POST | `/api/projects/` | Cria projeto |
| GET | `/api/projects/{id}/lists/` | Lista colunas do kanban |
| POST | `/api/cards/{list_id}` | Cria card |
| PUT | `/api/cards/{card_id}` | Atualiza card |
| POST | `/api/users/forgot-password` | Solicitar redefinição de senha |

Documentação completa no Swagger (apenas local): `http://localhost:8000/docs`
