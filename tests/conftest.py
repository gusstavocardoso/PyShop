"""
conftest.py — Fixtures compartilhadas entre todos os testes.

Estratégia de isolamento:
  1. Define DATABASE_URL=sqlite ANTES de importar qualquer módulo do backend
  2. O database.py lê a env var e cria engine SQLite (sem precisar do PostgreSQL)
  3. O startup event do FastAPI roda create_all no SQLite em vez do PostgreSQL
  4. Cada teste faz rollback automático via fixture `db`
"""
import os
import sys

# ── IMPORTANTE: definir DATABASE_URL ANTES de qualquer import do backend ─────
# Isso garante que database.py crie a engine SQLite (não PostgreSQL)
SQLITE_URL = "sqlite:///./test_pyshop.db"
os.environ["DATABASE_URL"] = SQLITE_URL

# ── Adiciona o diretório backend/ ao Python path ──────────────────────────────
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Agora os imports do backend usarão SQLite automaticamente
import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import Base, engine, get_db
from main import app

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Setup / Teardown do banco ─────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Cria todas as tabelas SQLite antes da session e derruba depois."""
    import models  # Garante que as tabelas estão registradas no Base.metadata
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Remove arquivo de banco gerado
    db_file = os.path.join(BACKEND_DIR, "test_pyshop.db")
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(autouse=True)
def clean_tables(request, setup_database):
    """
    Limpa todas as tabelas ANTES de cada teste.
    Ignorado nos testes E2E, que rodam contra o Docker.
    """
    if "e2e" in request.node.nodeid:
        yield
        return

    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture()
def db():
    """
    Sessão de banco isolada por teste.
    Faz rollback automático ao final para não contaminar outros testes.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ── FastAPI TestClient com banco de teste injetado ───────────────────────────
@pytest.fixture()
def client(db):
    """
    Cliente HTTP para testar a API.
    Injeta a sessão SQLite via dependency_override —
    a API nunca conecta ao PostgreSQL real.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Fixtures de dados ─────────────────────────────────────────────────────────
@pytest.fixture()
def sample_product(db):
    """Produto de exemplo inserido no banco de teste."""
    from models import Product
    product = Product(
        name="Fone de Ouvido Pro",
        description="Fone over-ear sem fio com cancelamento de ruído ativo",
        price=299.90,
        category="Eletrônicos",
        image_url="http://localhost:8000/static/images/headphones.png",
        stock=50,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture()
def sample_product_low_stock(db):
    """Produto com estoque baixo para testar validação."""
    from models import Product
    product = Product(
        name="Item Raro",
        description="Produto com estoque limitado",
        price=100.00,
        category="Eletrônicos",
        image_url="http://localhost:8000/static/images/headphones.png",
        stock=2,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture()
def multiple_products(db):
    """Vários produtos de categorias diferentes."""
    from models import Product
    products_data = [
        Product(name="Fone Pro", description="Fone premium", price=299.90,
                category="Eletrônicos", image_url="http://localhost:8000/static/images/headphones.png", stock=50),
        Product(name="Smartwatch Elite", description="Relógio inteligente", price=899.90,
                category="Eletrônicos", image_url="http://localhost:8000/static/images/smartwatch.png", stock=30),
        Product(name="Mochila Urban", description="Mochila urbana", price=189.90,
                category="Acessórios", image_url="http://localhost:8000/static/images/backpack.png", stock=80),
        Product(name="Tênis Runner", description="Tênis de corrida", price=349.90,
                category="Calçados", image_url="http://localhost:8000/static/images/shoes.png", stock=60),
    ]
    for p in products_data:
        db.add(p)
    db.commit()
    return products_data


@pytest.fixture()
def valid_order_payload(sample_product):
    """Payload válido para criação de pedido."""
    return {
        "customer_name": "João Silva",
        "customer_email": "joao@exemplo.com",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "postal_code": "01310-100",
        "items": [
            {"product_id": sample_product.id, "quantity": 2}
        ],
    }
