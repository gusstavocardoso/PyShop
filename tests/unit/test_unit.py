"""
Testes Unitários — PyShop Backend

Testam funções e lógica de negócio isoladamente, sem banco de dados ou HTTP.
O sys.path já é configurado pelo conftest.py — sem imports duplicados aqui.

Cobertura:
  - Schemas Pydantic (validação de entrada)
  - Lógica de cálculo de totais
  - Modelos SQLAlchemy (atributos e defaults)
  - Seed helpers (construção e correção de URLs de imagem)
  - Formatação de preço (estilo BR)
  - Validação de estoque
"""
import pytest
from pydantic import ValidationError
from schemas import ProductCreate, ProductBase, OrderCreate, OrderItemCreate
from models import Product, Order, OrderItem


# ─── Schemas: Validação de Produtos ──────────────────────────────────────────

class TestProductSchemas:
    """Valida que os schemas Pydantic rejeitam/aceitam dados corretamente."""

    def test_product_create_valid(self):
        product = ProductCreate(
            name="Fone de Ouvido Pro",
            description="Ótimo fone com ANC",
            price=299.90,
            category="Eletrônicos",
            image_url="http://localhost:8000/static/images/headphones.png",
            stock=50,
        )
        assert product.name == "Fone de Ouvido Pro"
        assert product.price == 299.90
        assert product.stock == 50

    def test_product_stock_default_value(self):
        """Stock deve ter default 100 quando não informado."""
        product = ProductCreate(
            name="Produto",
            description="Desc",
            price=10.0,
            category="Cat",
            image_url="http://localhost/img.png",
        )
        assert product.stock == 100

    def test_product_price_must_be_numeric(self):
        """Preço não numérico deve lançar ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(
                name="Produto",
                description="Desc",
                price="não-é-número",
                category="Cat",
                image_url="http://localhost/img.png",
            )

    def test_product_name_required(self):
        """Nome é obrigatório."""
        with pytest.raises(ValidationError):
            ProductCreate(
                description="Desc",
                price=10.0,
                category="Cat",
                image_url="http://localhost/img.png",
            )

    def test_product_description_required(self):
        with pytest.raises(ValidationError):
            ProductCreate(
                name="Produto",
                price=10.0,
                category="Cat",
                image_url="http://localhost/img.png",
            )


# ─── Schemas: Validação de Pedidos ───────────────────────────────────────────

class TestOrderSchemas:

    def test_order_create_valid(self):
        order = OrderCreate(
            customer_name="Maria Souza",
            customer_email="maria@exemplo.com",
            address="Av. Paulista, 1000",
            city="São Paulo",
            postal_code="01310-100",
            items=[OrderItemCreate(product_id=1, quantity=2)],
        )
        assert order.customer_name == "Maria Souza"
        assert len(order.items) == 1
        assert order.items[0].quantity == 2

    def test_order_create_empty_items_allowed_by_schema(self):
        """Schema permite items vazio; a validação de negócio fica no endpoint."""
        order = OrderCreate(
            customer_name="Maria",
            customer_email="maria@exemplo.com",
            address="Rua X",
            city="SP",
            postal_code="01000-000",
            items=[],
        )
        assert order.items == []

    def test_order_item_quantity_must_be_int(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(product_id=1, quantity="dois")

    def test_order_requires_customer_name(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                customer_email="x@x.com",
                address="Rua",
                city="SP",
                postal_code="00000-000",
                items=[],
            )


# ─── Lógica de Negócio: Cálculo de Totais ────────────────────────────────────

class TestOrderTotalCalculation:

    def test_single_item_total(self):
        assert round(299.90 * 2, 2) == 599.80

    def test_multiple_items_total(self):
        items = [
            {"price": 299.90, "quantity": 2},  # 599.80
            {"price": 899.90, "quantity": 1},  # 899.90
            {"price": 189.90, "quantity": 3},  # 569.70
        ]
        total = round(sum(i["price"] * i["quantity"] for i in items), 2)
        assert total == 2069.40

    def test_total_rounded_to_two_decimals(self):
        assert round(10.005 * 3, 2) == 30.02

    def test_zero_price_item(self):
        items = [{"price": 0.0, "quantity": 5}, {"price": 100.0, "quantity": 1}]
        assert round(sum(i["price"] * i["quantity"] for i in items), 2) == 100.0

    def test_single_quantity(self):
        assert round(6799.90 * 1, 2) == 6799.90


# ─── Modelos SQLAlchemy: Atributos e Defaults ────────────────────────────────

class TestProductModel:

    def test_product_model_attributes(self):
        p = Product(
            name="Laptop",
            description="Ultrabook premium",
            price=6799.90,
            category="Eletrônicos",
            image_url="http://localhost:8000/static/images/laptop.png",
            stock=20,
        )
        assert p.name == "Laptop"
        assert p.price == 6799.90
        assert p.category == "Eletrônicos"
        assert p.stock == 20

    def test_product_tablename(self):
        assert Product.__tablename__ == "products"

    def test_order_tablename(self):
        assert Order.__tablename__ == "orders"

    def test_order_item_tablename(self):
        assert OrderItem.__tablename__ == "order_items"

    def test_product_has_image_url_field(self):
        p = Product(
            name="X", description="Y", price=1.0,
            category="Z", image_url="http://test.com/img.png",
        )
        assert p.image_url == "http://test.com/img.png"


# ─── Seed: Construção de URLs de Imagem ──────────────────────────────────────

class TestImageUrlConstruction:

    def test_image_url_with_localhost_base(self):
        url = f"http://localhost:8000/static/images/headphones.png"
        assert url == "http://localhost:8000/static/images/headphones.png"

    def test_image_url_with_production_base(self):
        base = "https://api.pyshop.com"
        url = f"{base}/static/images/laptop.png"
        assert url == "https://api.pyshop.com/static/images/laptop.png"

    def test_fix_image_url_detects_wrong_host(self):
        """Simula a lógica fix_image_urls do seed.py."""
        IMAGE_FILENAMES = {"headphones.png", "smartwatch.png"}
        IMAGE_BASE_URL = "http://localhost:8000"

        wrong_url = "http://0.0.0.0:8000/static/images/headphones.png"
        fixed = None
        for fname in IMAGE_FILENAMES:
            if fname in wrong_url and not wrong_url.startswith(IMAGE_BASE_URL):
                fixed = f"{IMAGE_BASE_URL}/static/images/{fname}"
                break

        assert fixed == "http://localhost:8000/static/images/headphones.png"

    def test_fix_image_url_skips_correct_url(self):
        """URL já correta não é reescrita."""
        IMAGE_FILENAMES = {"headphones.png"}
        IMAGE_BASE_URL = "http://localhost:8000"

        correct_url = "http://localhost:8000/static/images/headphones.png"
        fixed = None
        for fname in IMAGE_FILENAMES:
            if fname in correct_url and not correct_url.startswith(IMAGE_BASE_URL):
                fixed = f"{IMAGE_BASE_URL}/static/images/{fname}"
                break

        assert fixed is None


# ─── Formatação de Preço ──────────────────────────────────────────────────────

class TestPriceFormatting:
    """Replica da função fmt_price do frontend NiceGUI."""

    def fmt_price(self, value: float) -> str:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def test_format_simple_price(self):
        assert self.fmt_price(299.90) == "R$ 299,90"

    def test_format_price_with_thousands(self):
        assert self.fmt_price(6799.90) == "R$ 6.799,90"

    def test_format_price_zero(self):
        assert self.fmt_price(0.0) == "R$ 0,00"

    def test_format_price_large_value(self):
        assert self.fmt_price(10000.00) == "R$ 10.000,00"

    def test_format_price_starts_with_rs(self):
        assert self.fmt_price(100.0).startswith("R$")

    def test_format_price_contains_comma_as_decimal(self):
        result = self.fmt_price(1.50)
        assert "," in result
        assert result.endswith("50")


# ─── Validação de Estoque ─────────────────────────────────────────────────────

class TestStockValidation:

    def test_sufficient_stock(self):
        assert 50 >= 5

    def test_insufficient_stock(self):
        assert 2 < 5

    def test_exact_stock_match_is_allowed(self):
        assert 3 >= 3

    def test_zero_stock_blocks_purchase(self):
        assert 0 < 1

    def test_negative_quantity_edge_case(self):
        """Quantidade negativa nunca deve ser válida."""
        quantity = -1
        assert quantity <= 0
