# PyShop 🛒

Uma loja virtual moderna construída com **Python puro** — FastAPI no backend, NiceGUI no frontend e PostgreSQL como banco de dados. Tudo containerizado com Docker Compose.

## 🖥️ Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | FastAPI + SQLAlchemy + Alembic |
| **Frontend** | NiceGUI (Python → WebUI) |
| **Banco de Dados** | PostgreSQL 16 |
| **Infra** | Docker + Docker Compose |

## ✨ Funcionalidades

- 🏠 **Catálogo de Produtos** — grid responsivo com filtro por categoria
- 🛒 **Carrinho de Compras** — adicionar, remover, alterar quantidades
- ✅ **Checkout** — formulário completo com confirmação de pedido
- 🌙 **Dark Mode** — design premium em modo escuro com gradientes e animações
- 📦 **8 Produtos** pré-cadastrados com imagens geradas por IA

## 🚀 Como rodar

### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando

### Iniciando

```bash
# Clone o repositório
git clone https://github.com/gusstavocardoso/PyShop.git
cd PyShop

# Suba todos os containers
docker compose up --build
```

Aguarde o build (primeira vez ~2-3 min). Quando aparecer:
```
pyshop_frontend | NiceGUI ready to go on http://localhost:3000
```

Acesse: **http://localhost:3000** 🎉

## 📁 Estrutura do Projeto

```
pyshop/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py          # FastAPI app + rotas
│   ├── models.py        # Modelos SQLAlchemy
│   ├── schemas.py       # Schemas Pydantic
│   ├── database.py      # Conexão DB
│   ├── seed.py          # Dados iniciais
│   ├── routers/
│   │   ├── products.py  # CRUD de produtos
│   │   └── orders.py    # Criação de pedidos
│   └── static/
│       └── images/      # Imagens dos produtos
└── frontend/
    ├── Dockerfile
    ├── requirements.txt
    └── main.py          # App NiceGUI completo
```

## 🔗 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/products/` | Listar produtos |
| `GET` | `/products/categories` | Listar categorias |
| `POST` | `/orders/` | Criar pedido |
| `GET` | `/docs` | Swagger UI |

Acesse a documentação interativa em: **http://localhost:8000/docs**

## 🛠️ Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql://pyshop:pyshop_secret@db:5432/pyshop_db` |
| `IMAGE_BASE_URL` | URL pública das imagens | `http://localhost:8000` |
| `BACKEND_URL` | URL do backend (usada pelo frontend) | `http://backend:8000` |

## 📸 Screenshots

### Catálogo de Produtos
Dark mode com cards de produto, filtro por categoria e badge do carrinho reativo.

### Carrinho
Controle de quantidade, subtotais por item e resumo do pedido.

### Checkout
Formulário de dados pessoais e endereço, com tela de confirmação animada.
