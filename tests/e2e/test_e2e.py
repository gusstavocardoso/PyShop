"""
Testes E2E — PyShop Frontend

Testam o fluxo completo da aplicação no browser usando Playwright.
Requerem que os containers Docker estejam rodando:
  - Frontend: http://localhost:3000
  - Backend:  http://localhost:8000

Execute com:
  pytest tests/e2e/ -v --headed        # visível no browser
  pytest tests/e2e/ -v                 # headless (CI)
"""
import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"
TIMEOUT = 15_000  # 15 segundos por asserção


# ─── Fixtures E2E ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def navigate_to_home(page: Page):
    """
    Antes de cada teste E2E:
    1. Limpa o carrinho via /clear-cart (garante isolamento de estado)
    2. Navega para home e aguarda carregamento completo
    """
    page.goto(f"{BASE_URL}/clear-cart", timeout=30_000)
    # Espera a grid de produtos carregar (confirma que o redirect para / ocorreu)
    page.wait_for_selector(".products-grid", timeout=15_000)
    page.wait_for_load_state("networkidle")


# ─── Home Page ────────────────────────────────────────────────────────────────

class TestHomePage:

    def test_page_title(self, page: Page):
        """Título da aba deve conter PyShop."""
        expect(page).to_have_title(re.compile("PyShop"), timeout=TIMEOUT)

    def test_navbar_logo_visible(self, page: Page):
        logo = page.locator("text=PyShop").first
        expect(logo).to_be_visible(timeout=TIMEOUT)

    def test_hero_heading_visible(self, page: Page):
        heading = page.locator("text=Tecnologia").first
        expect(heading).to_be_visible(timeout=TIMEOUT)

    def test_products_grid_visible(self, page: Page):
        grid = page.locator(".products-grid")
        expect(grid).to_be_visible(timeout=TIMEOUT)

    def test_at_least_one_product_card_visible(self, page: Page):
        cards = page.locator(".product-card")
        expect(cards.first).to_be_visible(timeout=TIMEOUT)
        assert cards.count() >= 1

    def test_product_has_name(self, page: Page):
        name = page.locator(".product-name").first
        expect(name).to_be_visible(timeout=TIMEOUT)
        assert name.inner_text().strip() != ""

    def test_product_has_price(self, page: Page):
        price = page.locator(".product-price").first
        expect(price).to_be_visible(timeout=TIMEOUT)
        assert "R$" in price.inner_text()

    def test_product_has_category_badge(self, page: Page):
        badge = page.locator(".product-badge").first
        expect(badge).to_be_visible(timeout=TIMEOUT)

    def test_product_images_loaded(self, page: Page):
        """Imagens dos produtos devem carregar (não quebradas)."""
        page.wait_for_timeout(2000)
        images = page.locator(".product-img-wrap img")
        count = images.count()
        assert count > 0
        for i in range(min(count, 4)):
            natural_width = images.nth(i).evaluate("el => el.naturalWidth")
            assert natural_width > 0, f"Imagem {i} não carregou (naturalWidth=0)"

    def test_add_to_cart_button_visible(self, page: Page):
        btn = page.locator("button", has_text="Adicionar").first
        expect(btn).to_be_visible(timeout=TIMEOUT)

    def test_cart_icon_in_navbar(self, page: Page):
        """Ícone do carrinho deve estar na navbar (via id)."""
        cart_btn = page.locator("#navbar-cart-btn")
        expect(cart_btn).to_be_visible(timeout=TIMEOUT)

    def test_footer_visible(self, page: Page):
        footer = page.locator("footer")
        expect(footer).to_be_visible(timeout=TIMEOUT)


# ─── Filtro de Categorias ─────────────────────────────────────────────────────

class TestCategoryFilter:

    def test_category_pills_visible(self, page: Page):
        """Pills de categoria devem estar visíveis após carregamento."""
        page.wait_for_selector(".cat-pill", timeout=TIMEOUT)
        pills = page.locator(".cat-pill")
        expect(pills.first).to_be_visible(timeout=TIMEOUT)
        assert pills.count() >= 2

    def test_todos_pill_exists(self, page: Page):
        """Pill 'Todos' deve existir na lista de categorias."""
        page.wait_for_selector(".cat-pill", timeout=TIMEOUT)
        todos = page.locator(".cat-pill", has_text="Todos")
        expect(todos).to_be_visible(timeout=TIMEOUT)

    def test_filter_by_eletronicos(self, page: Page):
        """Filtrar por Eletrônicos deve mostrar apenas produtos dessa categoria."""
        page.wait_for_selector(".cat-pill", timeout=TIMEOUT)
        pill = page.locator(".cat-pill", has_text="Eletrônicos")
        if pill.count() == 0:
            pytest.skip("Categoria Eletrônicos não encontrada")
        pill.click()
        
        # O filtro via websocket pode demorar uns ms para remover os itens antigos.
        # Polling até que todos os emblemas visíveis sejam apenas "Eletrônicos"
        badges = page.locator(".product-badge")
        for _ in range(20):  # tenta por até 10 segundos
            count = badges.count()
            if count > 0:
                all_match = True
                for i in range(count):
                    if badges.nth(i).inner_text() != "Eletrônicos":
                        all_match = False
                        break
                if all_match:
                    break
            page.wait_for_timeout(500)
        
        count = badges.count()
        assert count > 0, "Nenhum produto encontrado após o filtro"
        for i in range(count):
            assert badges.nth(i).inner_text() == "Eletrônicos"

    def test_filter_todos_shows_all_products(self, page: Page):
        """Clicar em 'Todos' após filtrar deve mostrar todos os produtos."""
        page.wait_for_selector(".cat-pill", timeout=TIMEOUT)
        pills = page.locator(".cat-pill")
        if pills.count() >= 2:
            pills.nth(1).click()
            page.wait_for_timeout(1000)
            count_filtered = page.locator(".product-card").count()

            page.locator(".cat-pill", has_text="Todos").click()
            page.wait_for_timeout(1500)
            count_all = page.locator(".product-card").count()
            assert count_all >= count_filtered


# ─── Adicionar ao Carrinho ────────────────────────────────────────────────────

class TestAddToCart:

    def test_add_product_shows_toast(self, page: Page):
        """Adicionar produto deve exibir notificação toast."""
        btn = page.locator("button", has_text="Adicionar").first
        btn.click()
        toast = page.locator(".q-notification")
        expect(toast.first).to_be_visible(timeout=TIMEOUT)

    def test_cart_badge_appears_after_add(self, page: Page):
        """Badge numérico deve aparecer na navbar após adicionar produto."""
        btn = page.locator("button", has_text="Adicionar").first
        btn.click()
        page.wait_for_timeout(600)
        badge = page.locator(".cart-badge")
        expect(badge).to_be_visible(timeout=TIMEOUT)
        assert badge.inner_text().strip() == "1"

    def test_cart_badge_increments_on_second_add(self, page: Page):
        """Badge deve incrementar ao adicionar mais produtos."""
        btn = page.locator("button", has_text="Adicionar").first
        btn.click()
        page.wait_for_timeout(400)
        btn.click()
        page.wait_for_timeout(600)
        badge = page.locator(".cart-badge")
        expect(badge).to_be_visible(timeout=TIMEOUT)
        assert int(badge.inner_text().strip()) >= 2

    def test_add_multiple_different_products(self, page: Page):
        """Adicionar produtos diferentes deve refletir no badge."""
        buttons = page.locator("button", has_text="Adicionar")
        count = buttons.count()
        if count >= 2:
            buttons.nth(0).click()
            page.wait_for_timeout(400)
            buttons.nth(1).click()
            page.wait_for_timeout(600)
            badge = page.locator(".cart-badge")
            expect(badge).to_be_visible(timeout=TIMEOUT)
            assert int(badge.inner_text().strip()) >= 2


# ─── Página do Carrinho ───────────────────────────────────────────────────────

class TestCartPage:

    def test_empty_cart_message(self, page: Page):
        """Carrinho vazio deve mostrar mensagem 'Seu carrinho está vazio'."""
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        # Texto exato do frontend: "Seu carrinho está vazio"
        empty_msg = page.locator("text=Seu carrinho está vazio")
        expect(empty_msg).to_be_visible(timeout=TIMEOUT)

    def test_cart_with_product_shows_item(self, page: Page):
        """Produto adicionado deve aparecer no carrinho."""
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        item = page.locator(".cart-item")
        expect(item.first).to_be_visible(timeout=TIMEOUT)

    def test_cart_shows_subtotal(self, page: Page):
        """Carrinho deve exibir subtotal em R$."""
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        price_elements = page.locator("text=R$")
        assert price_elements.count() >= 1

    def test_cart_has_checkout_button(self, page: Page):
        """Carrinho com item deve ter botão de finalizar pedido."""
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        checkout_btn = page.locator("button", has_text="Finalizar Pedido")
        expect(checkout_btn).to_be_visible(timeout=TIMEOUT)

    def test_cart_increase_quantity(self, page: Page):
        """Botão + deve aumentar a quantidade do item."""
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")

        plus_btn = page.locator(".qty-btn", has_text="+").first
        plus_btn.click()
        page.wait_for_load_state("networkidle")
        qty = page.locator("text=2").first
        expect(qty).to_be_visible(timeout=TIMEOUT)

    def test_cart_remove_item(self, page: Page):
        """Remover o único item deve exibir carrinho vazio."""
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")

        # Botão remove é o emoji 🗑
        remove_btn = page.locator("button", has_text="🗑").first
        remove_btn.click()
        page.wait_for_load_state("networkidle")

        empty_msg = page.locator("text=Seu carrinho está vazio")
        expect(empty_msg).to_be_visible(timeout=TIMEOUT)

    def test_empty_cart_has_explore_button(self, page: Page):
        """Carrinho vazio deve ter botão para explorar produtos."""
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        explore_btn = page.locator("button", has_text="Explorar Produtos")
        expect(explore_btn).to_be_visible(timeout=TIMEOUT)

    def test_explore_button_navigates_home(self, page: Page):
        """Botão 'Explorar Produtos' deve navegar para a home."""
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        page.locator("button", has_text="Explorar Produtos").click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{BASE_URL}/", timeout=TIMEOUT)


# ─── Checkout ─────────────────────────────────────────────────────────────────

class TestCheckoutPage:

    def _add_product_and_go_to_checkout(self, page: Page):
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/checkout")
        page.wait_for_load_state("networkidle")

    def test_checkout_empty_cart_shows_message(self, page: Page):
        """Checkout sem produto deve mostrar 'carrinho está vazio'."""
        page.goto(f"{BASE_URL}/checkout")
        page.wait_for_load_state("networkidle")
        # Texto exato do frontend: "Seu carrinho está vazio."
        empty = page.locator("text=Seu carrinho está vazio")
        expect(empty).to_be_visible(timeout=TIMEOUT)

    def test_checkout_form_visible(self, page: Page):
        self._add_product_and_go_to_checkout(page)
        form_section = page.locator(".form-section").first
        expect(form_section).to_be_visible(timeout=TIMEOUT)

    def test_checkout_has_name_field(self, page: Page):
        self._add_product_and_go_to_checkout(page)
        name_field = page.locator("input").first
        expect(name_field).to_be_visible(timeout=TIMEOUT)

    def test_checkout_shows_order_summary(self, page: Page):
        self._add_product_and_go_to_checkout(page)
        summary = page.locator(".summary-card")
        expect(summary).to_be_visible(timeout=TIMEOUT)
        total = page.locator("text=Total")
        expect(total.first).to_be_visible(timeout=TIMEOUT)

    def test_checkout_submit_without_fields_shows_warning(self, page: Page):
        """Submeter sem preencher campos deve mostrar aviso."""
        self._add_product_and_go_to_checkout(page)
        page.locator("button", has_text="Confirmar Pedido").click()
        page.wait_for_timeout(500)
        warning = page.locator(".q-notification")
        expect(warning.first).to_be_visible(timeout=TIMEOUT)

    def test_checkout_complete_flow(self, page: Page):
        """Fluxo completo: produto → formulário → confirmar → sucesso."""
        self._add_product_and_go_to_checkout(page)

        inputs = page.locator("input")
        inputs.nth(0).fill("João Silva")
        inputs.nth(1).fill("joao@exemplo.com")
        inputs.nth(2).fill("Rua das Flores, 123")
        inputs.nth(3).fill("São Paulo")
        inputs.nth(4).fill("01310-100")

        page.locator("button", has_text="Confirmar Pedido").click()
        page.wait_for_url(f"{BASE_URL}/success/**", timeout=15_000)
        page.wait_for_load_state("networkidle")

        success = page.locator("text=Pedido Confirmado")
        expect(success.first).to_be_visible(timeout=TIMEOUT)

    def test_success_page_shows_order_id(self, page: Page):
        self._add_product_and_go_to_checkout(page)

        inputs = page.locator("input")
        inputs.nth(0).fill("Maria Souza")
        inputs.nth(1).fill("maria@exemplo.com")
        inputs.nth(2).fill("Av. Paulista, 1000")
        inputs.nth(3).fill("São Paulo")
        inputs.nth(4).fill("01310-000")

        page.locator("button", has_text="Confirmar Pedido").click()
        page.wait_for_url(f"{BASE_URL}/success/**", timeout=15_000)
        page.wait_for_load_state("networkidle")

        order_badge = page.locator(".order-badge")
        expect(order_badge).to_be_visible(timeout=TIMEOUT)

    def test_success_page_has_continue_shopping_button(self, page: Page):
        self._add_product_and_go_to_checkout(page)

        inputs = page.locator("input")
        inputs.nth(0).fill("Carlos")
        inputs.nth(1).fill("carlos@exemplo.com")
        inputs.nth(2).fill("Rua Y, 42")
        inputs.nth(3).fill("Curitiba")
        inputs.nth(4).fill("80000-000")

        page.locator("button", has_text="Confirmar Pedido").click()
        page.wait_for_url(f"{BASE_URL}/success/**", timeout=15_000)
        page.wait_for_load_state("networkidle")

        continue_btn = page.locator("button", has_text="Continuar Comprando")
        expect(continue_btn).to_be_visible(timeout=TIMEOUT)
        continue_btn.click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{BASE_URL}/", timeout=TIMEOUT)


# ─── Navegação ────────────────────────────────────────────────────────────────

class TestNavigation:

    def test_logo_click_goes_home(self, page: Page):
        """Clicar no logo deve navegar para a home."""
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        page.locator("text=PyShop").first.click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{BASE_URL}/", timeout=TIMEOUT)

    def test_cart_icon_navigates_to_cart(self, page: Page):
        """Ícone do carrinho (via id #navbar-cart-btn) deve navegar para /cart."""
        cart_btn = page.locator("#navbar-cart-btn")
        expect(cart_btn).to_be_visible(timeout=TIMEOUT)
        cart_btn.click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{BASE_URL}/cart", timeout=TIMEOUT)

    def test_produtos_link_goes_home(self, page: Page):
        """Link 'Produtos' na navbar deve ir para a home."""
        page.goto(f"{BASE_URL}/cart")
        page.wait_for_load_state("networkidle")
        page.locator(".nav-link", has_text="Produtos").click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(f"{BASE_URL}/", timeout=TIMEOUT)
