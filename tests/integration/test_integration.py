"""
Testes de Integração — PyShop Backend API

Testam os endpoints FastAPI contra um banco SQLite em memória (via conftest.py).
Usam o TestClient do FastAPI + httpx para simular requests HTTP reais.

Cobertura:
  - GET /                    (health check raiz)
  - GET /health
  - GET /products/           (listagem, filtro por categoria)
  - GET /products/categories
  - GET /products/{id}       (produto existente e 404)
  - POST /orders/            (criação válida, carrinho vazio, produto inexistente, estoque insuficiente)
  - GET  /orders/{id}        (pedido existente e 404)
"""
import pytest


# ─── API Root & Health ────────────────────────────────────────────────────────

class TestRootEndpoints:

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_message(self, client):
        data = client.get("/").json()
        assert "message" in data
        assert "PyShop" in data["message"]

    def test_root_contains_docs_url(self, client):
        data = client.get("/").json()
        assert "docs" in data

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ─── Products: Listagem ───────────────────────────────────────────────────────

class TestProductsListEndpoint:

    def test_list_products_empty_db(self, client):
        """Banco sem produtos retorna lista vazia."""
        response = client.get("/products/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_products_returns_all(self, client, multiple_products):
        response = client.get("/products/")
        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_list_products_response_fields(self, client, sample_product):
        """Cada produto deve conter todos os campos necessários."""
        products = client.get("/products/").json()
        assert len(products) == 1
        p = products[0]
        assert "id" in p
        assert "name" in p
        assert "description" in p
        assert "price" in p
        assert "category" in p
        assert "image_url" in p
        assert "stock" in p
        assert "created_at" in p

    def test_list_products_correct_data(self, client, sample_product):
        products = client.get("/products/").json()
        p = products[0]
        assert p["name"] == "Fone de Ouvido Pro"
        assert p["price"] == 299.90
        assert p["category"] == "Eletrônicos"

    def test_filter_by_category(self, client, multiple_products):
        """Filtro por categoria deve retornar apenas produtos dessa categoria."""
        response = client.get("/products/?category=Eletrônicos")
        assert response.status_code == 200
        products = response.json()
        assert len(products) == 2
        for p in products:
            assert p["category"] == "Eletrônicos"

    def test_filter_by_acessorios(self, client, multiple_products):
        response = client.get("/products/?category=Acessórios")
        assert response.status_code == 200
        products = response.json()
        assert len(products) == 1
        assert products[0]["name"] == "Mochila Urban"

    def test_filter_todos_returns_all(self, client, multiple_products):
        """Filtro 'Todos' deve ignorar o filtro e retornar tudo."""
        response = client.get("/products/?category=Todos")
        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_filter_nonexistent_category(self, client, multiple_products):
        """Categoria inexistente retorna lista vazia."""
        response = client.get("/products/?category=Inexistente")
        assert response.status_code == 200
        assert response.json() == []


# ─── Products: Categorias ─────────────────────────────────────────────────────

class TestCategoriesEndpoint:

    def test_categories_empty_db(self, client):
        response = client.get("/products/categories")
        assert response.status_code == 200
        assert response.json() == []

    def test_categories_no_duplicates(self, client, multiple_products):
        """Categorias devem ser únicas mesmo com múltiplos produtos."""
        categories = client.get("/products/categories").json()
        assert len(categories) == len(set(categories))

    def test_categories_contains_expected(self, client, multiple_products):
        categories = client.get("/products/categories").json()
        assert "Eletrônicos" in categories
        assert "Acessórios" in categories
        assert "Calçados" in categories

    def test_categories_returns_list_of_strings(self, client, multiple_products):
        categories = client.get("/products/categories").json()
        assert isinstance(categories, list)
        for c in categories:
            assert isinstance(c, str)


# ─── Products: Por ID ─────────────────────────────────────────────────────────

class TestGetProductByIdEndpoint:

    def test_get_existing_product(self, client, sample_product):
        response = client.get(f"/products/{sample_product.id}")
        assert response.status_code == 200
        p = response.json()
        assert p["id"] == sample_product.id
        assert p["name"] == sample_product.name

    def test_get_nonexistent_product_returns_404(self, client):
        response = client.get("/products/99999")
        assert response.status_code == 404

    def test_get_product_404_message(self, client):
        response = client.get("/products/99999")
        assert "não encontrado" in response.json()["detail"].lower()

    def test_get_product_invalid_id_type(self, client):
        """ID não-inteiro deve retornar 422."""
        response = client.get("/products/abc")
        assert response.status_code == 422


# ─── Orders: Criação de Pedidos ───────────────────────────────────────────────

class TestCreateOrderEndpoint:

    def test_create_order_success(self, client, valid_order_payload):
        response = client.post("/orders/", json=valid_order_payload)
        assert response.status_code == 201

    def test_create_order_response_fields(self, client, valid_order_payload):
        order = client.post("/orders/", json=valid_order_payload).json()
        assert "id" in order
        assert "customer_name" in order
        assert "customer_email" in order
        assert "total" in order
        assert "status" in order
        assert "items" in order
        assert "created_at" in order

    def test_create_order_correct_customer(self, client, valid_order_payload):
        order = client.post("/orders/", json=valid_order_payload).json()
        assert order["customer_name"] == "João Silva"
        assert order["customer_email"] == "joao@exemplo.com"

    def test_create_order_total_calculated_correctly(self, client, valid_order_payload, sample_product):
        """Total deve ser preço × quantidade."""
        order = client.post("/orders/", json=valid_order_payload).json()
        expected_total = round(sample_product.price * 2, 2)  # quantity=2
        assert order["total"] == expected_total

    def test_create_order_status_confirmed(self, client, valid_order_payload):
        order = client.post("/orders/", json=valid_order_payload).json()
        assert order["status"] == "confirmed"

    def test_create_order_contains_items(self, client, valid_order_payload):
        order = client.post("/orders/", json=valid_order_payload).json()
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 2

    def test_create_order_empty_cart_returns_400(self, client, sample_product):
        """Carrinho vazio deve retornar 400."""
        payload = {
            "customer_name": "João",
            "customer_email": "joao@exemplo.com",
            "address": "Rua X",
            "city": "SP",
            "postal_code": "01000-000",
            "items": [],
        }
        response = client.post("/orders/", json=payload)
        assert response.status_code == 400
        assert "vazio" in response.json()["detail"].lower()

    def test_create_order_nonexistent_product_returns_404(self, client):
        """Produto inexistente no item deve retornar 404."""
        payload = {
            "customer_name": "João",
            "customer_email": "joao@exemplo.com",
            "address": "Rua X",
            "city": "SP",
            "postal_code": "01000-000",
            "items": [{"product_id": 99999, "quantity": 1}],
        }
        response = client.post("/orders/", json=payload)
        assert response.status_code == 404

    def test_create_order_insufficient_stock_returns_400(self, client, sample_product_low_stock):
        """Estoque insuficiente deve retornar 400."""
        payload = {
            "customer_name": "João",
            "customer_email": "joao@exemplo.com",
            "address": "Rua X",
            "city": "SP",
            "postal_code": "01000-000",
            "items": [{"product_id": sample_product_low_stock.id, "quantity": 10}],
        }
        response = client.post("/orders/", json=payload)
        assert response.status_code == 400
        assert "estoque" in response.json()["detail"].lower()

    def test_create_order_multiple_items(self, client, multiple_products):
        """Pedido com vários produtos deve calcular total corretamente."""
        products = multiple_products
        payload = {
            "customer_name": "Maria",
            "customer_email": "maria@exemplo.com",
            "address": "Av. Brasil, 500",
            "city": "Rio de Janeiro",
            "postal_code": "20040-020",
            "items": [
                {"product_id": products[0].id, "quantity": 1},
                {"product_id": products[2].id, "quantity": 2},
            ],
        }
        response = client.post("/orders/", json=payload)
        assert response.status_code == 201
        order = response.json()
        expected_total = round(products[0].price * 1 + products[2].price * 2, 2)
        assert order["total"] == expected_total
        assert len(order["items"]) == 2

    def test_create_order_missing_required_fields_returns_422(self, client):
        """Campos obrigatórios ausentes devem retornar 422."""
        payload = {"customer_name": "João"}  # faltam campos
        response = client.post("/orders/", json=payload)
        assert response.status_code == 422


# ─── Orders: Consulta por ID ──────────────────────────────────────────────────

class TestGetOrderEndpoint:

    def test_get_existing_order(self, client, valid_order_payload):
        created = client.post("/orders/", json=valid_order_payload).json()
        response = client.get(f"/orders/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_order_correct_data(self, client, valid_order_payload):
        created = client.post("/orders/", json=valid_order_payload).json()
        order = client.get(f"/orders/{created['id']}").json()
        assert order["customer_name"] == "João Silva"
        assert order["status"] == "confirmed"

    def test_get_nonexistent_order_returns_404(self, client):
        response = client.get("/orders/99999")
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()

    def test_get_order_invalid_id_returns_422(self, client):
        response = client.get("/orders/abc")
        assert response.status_code == 422
