"""
PyShop Frontend — NiceGUI
A premium dark-mode e-commerce store built in pure Python.
Pages: Home (catalog), Cart, Checkout
"""
import os
import httpx
from nicegui import ui, app

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── Global State ─────────────────────────────────────────────────────────────
cart: dict[int, dict] = {}   # product_id -> {product, quantity}


def fmt_price(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cart_total() -> float:
    return sum(item["product"]["price"] * item["quantity"] for item in cart.values())


def cart_count() -> int:
    return sum(item["quantity"] for item in cart.values())


# ─── Common Styles ────────────────────────────────────────────────────────────
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { width: 100%; height: 100%; overflow-x: hidden; }

body {
    background: #08060f !important;
    color: white;
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    width: 100%;
    overflow-x: hidden;
}

/* ── NiceGUI / Quasar full-width overrides ── */
.q-layout, .q-layout__shadow, .q-page-container, .q-page, .nicegui-content {
    background: #08060f !important;
    min-width: 100% !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #08060f; }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.4); border-radius: 3px; }

/* Navbar */
.navbar {
    background: rgba(10,10,20,0.92);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(124,58,237,0.2);
    padding: 0.85rem 2rem;
    position: sticky;
    top: 0;
    z-index: 100;
    width: 100%;
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}

.logo-py { color: #7C3AED; font-weight: 900; font-size: 1.5rem; line-height: 1; }
.logo-shop { color: white; font-weight: 900; font-size: 1.5rem; line-height: 1; }

/* Cart badge */
.cart-badge {
    background: #7C3AED;
    color: white;
    border-radius: 50%;
    width: 20px; height: 20px;
    font-size: 0.7rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    position: absolute; top: -8px; right: -8px;
}

/* Nav links */
.nav-link {
    color: rgba(255,255,255,0.7);
    font-weight: 500;
    font-size: 0.95rem;
    text-decoration: none;
    transition: color 0.2s;
    cursor: pointer;
}
.nav-link:hover { color: white; }

/* Hero */
.hero {
    text-align: center;
    padding: 3.5rem 1rem 2rem;
    position: relative;
}
.hero::before {
    content: "";
    position: absolute; top: 0; left: 50%; transform: translateX(-50%);
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero-badge {
    display: inline-block;
    background: rgba(124,58,237,0.15);
    color: #A78BFA;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 999px;
    font-size: 0.8rem; font-weight: 600;
    padding: 0.3rem 0.9rem;
    margin-bottom: 1rem;
}
.hero h1 {
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 900; line-height: 1.15; color: white;
    margin-bottom: 1rem;
}
.hero-accent {
    background: linear-gradient(135deg, #7C3AED, #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p { color: rgba(255,255,255,0.55); font-size: 1.05rem; max-width: 480px; margin: 0 auto; }

/* Category pills */
.cat-pill {
    border-radius: 999px;
    font-size: 0.85rem; font-weight: 600;
    padding: 0.45rem 1.1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.6);
}
.cat-pill:hover { background: rgba(124,58,237,0.2); color: white; border-color: rgba(124,58,237,0.4); }
.cat-pill.active { background: linear-gradient(135deg,#7C3AED,#5B21B6); color: white; border-color: transparent; }

/* Product grid */
.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1.5rem;
    width: 100%;
    padding: 1.5rem 0;
}

/* Product card */
.product-card {
    background: rgba(18,16,36,0.8);
    border: 1px solid rgba(124,58,237,0.15);
    border-radius: 14px;
    overflow: hidden;
    transition: all 0.3s ease;
    cursor: pointer;
}
.product-card:hover {
    border-color: rgba(124,58,237,0.5);
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(124,58,237,0.2);
}
.product-img-wrap {
    background: rgba(255,255,255,0.04);
    height: 200px;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
}
.product-img-wrap img {
    width: 100%; height: 100%; object-fit: contain;
    padding: 1rem;
    transition: transform 0.4s ease;
}
.product-card:hover .product-img-wrap img { transform: scale(1.08); }
.product-info { padding: 1rem 1.25rem 1.25rem; }
.product-badge {
    display: inline-block;
    background: rgba(124,58,237,0.15);
    color: #A78BFA;
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 999px;
    font-size: 0.7rem; font-weight: 600;
    padding: 0.15rem 0.6rem;
    margin-bottom: 0.5rem;
}
.product-name {
    font-size: 1rem; font-weight: 700; color: white;
    line-height: 1.3; margin-bottom: 0.35rem;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.product-desc {
    font-size: 0.8rem; color: rgba(255,255,255,0.45);
    line-height: 1.5; margin-bottom: 0.75rem;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.product-price {
    font-size: 1.3rem; font-weight: 800; color: #A78BFA;
}

/* Buttons */
.btn-primary {
    background: linear-gradient(135deg,#7C3AED,#5B21B6) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}
.btn-primary:hover {
    background: linear-gradient(135deg,#8B5CF6,#6D28D9) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
}
.btn-large {
    background: linear-gradient(135deg,#7C3AED,#5B21B6) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 1rem !important; padding: 0.85rem 1.5rem !important;
    transition: all 0.2s !important; cursor: pointer !important;
    width: 100% !important;
}
.btn-large:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(124,58,237,0.4) !important; }
.btn-ghost {
    background: transparent !important;
    color: rgba(239,68,68,0.7) !important;
    border: 1px solid rgba(239,68,68,0.25) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
.btn-ghost:hover { color: #EF4444 !important; border-color: rgba(239,68,68,0.5) !important; background: rgba(239,68,68,0.05) !important; }

/* Cart page */
.cart-item {
    background: rgba(18,16,36,0.7);
    border: 1px solid rgba(124,58,237,0.12);
    border-radius: 14px; padding: 1.25rem;
    transition: border-color 0.2s;
    margin-bottom: 0.75rem;
}
.cart-item:hover { border-color: rgba(124,58,237,0.3); }

/* Summary card */
.summary-card {
    background: rgba(18,16,36,0.8);
    border: 1px solid rgba(124,58,237,0.15);
    border-radius: 16px; padding: 1.5rem;
    position: sticky; top: 90px;
    min-width: 280px;
}
.summary-total { color: #A78BFA; font-size: 1.3rem; font-weight: 800; }

/* Quantity controls */
.qty-btn {
    background: rgba(124,58,237,0.15) !important;
    color: white !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: 8px !important;
    width: 32px !important; height: 32px !important;
    font-size: 1rem !important;
    padding: 0 !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    cursor: pointer !important; transition: background 0.2s !important;
    min-width: unset !important;
}
.qty-btn:hover { background: rgba(124,58,237,0.35) !important; }

/* Form */
.form-input .q-field__control { background: rgba(255,255,255,0.05) !important; border-radius: 10px !important; }
.form-input .q-field__native { color: white !important; }
.form-input .q-field__label { color: rgba(255,255,255,0.6) !important; }
.form-input .q-field__bottom { display: none; }
.form-section {
    background: rgba(18,16,36,0.7);
    border: 1px solid rgba(124,58,237,0.12);
    border-radius: 16px; padding: 1.5rem;
}
.section-title { color: white; font-size: 1.05rem; font-weight: 700; margin-bottom: 1rem; }

/* Success */
.success-icon {
    background: rgba(74,222,128,0.1);
    border: 2px solid rgba(74,222,128,0.3);
    border-radius: 50%; padding: 2rem;
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0%,100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.3); }
    50% { box-shadow: 0 0 0 16px rgba(74,222,128,0); }
}
.order-badge {
    background: rgba(124,58,237,0.1);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 16px; padding: 1.25rem 3rem;
    text-align: center;
}

/* Toast */
.toast {
    background: rgba(18,16,36,0.95) !important;
    border: 1px solid rgba(74,222,128,0.3) !important;
    border-radius: 12px !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
}

/* Empty state */
.empty-icon {
    background: rgba(124,58,237,0.08);
    border-radius: 50%; padding: 2rem;
    display: inline-flex;
}

/* Footer */
.footer {
    background: rgba(8,6,18,0.95);
    border-top: 1px solid rgba(124,58,237,0.15);
    padding: 2rem;
    margin-top: 4rem;
    width: 100%;
}
.footer-copy { color: rgba(255,255,255,0.35); font-size: 0.8rem; }

/* Page container */
.page-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
    width: 100%;
}

/* Divider */
.divider { border-color: rgba(124,58,237,0.15) !important; margin: 0.75rem 0; }

/* Free shipping */
.free-ship { color: #4ADE80; font-weight: 600; font-size: 0.9rem; }

/* Headings on pages */
.page-heading { font-size: 2rem; font-weight: 800; color: white; margin-bottom: 1.5rem; }

@media (max-width: 768px) {
    .products-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; }
    .cart-row { flex-direction: column; }
}
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────
async def fetch_products(category: str = "Todos") -> list[dict]:
    try:
        async with httpx.AsyncClient() as client:
            params = {} if category == "Todos" else {"category": category}
            r = await client.get(f"{BACKEND_URL}/products/", params=params, timeout=10)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


async def fetch_categories() -> list[str]:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BACKEND_URL}/products/categories", timeout=10)
            r.raise_for_status()
            return ["Todos"] + r.json()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return ["Todos"]


async def post_order(payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{BACKEND_URL}/orders/", json=payload, timeout=15)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"Error placing order: {e}")
        return None


# ─── Cart Badge (refreshable so it updates live without page reload) ──────────
@ui.refreshable
def render_cart_badge():
    count = cart_count()
    if count > 0:
        ui.html(f'<span class="cart-badge">{count}</span>')


# ─── Navbar ───────────────────────────────────────────────────────────────────
def render_navbar():
    with ui.element("nav").classes("navbar"):
        with ui.row().classes("items-center w-full gap-6"):
            # Logo
            with ui.row().classes("items-center gap-0 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
                ui.html('<span class="logo-py">Py</span><span class="logo-shop">Shop</span>')

            ui.space()

            # Nav links
            ui.html('<span class="nav-link" onclick="window.location=\'/\'">Produtos</span>')

            # Cart icon with reactive badge — id for E2E testing
            with ui.element("div").props('id="navbar-cart-btn"').style("position:relative; cursor:pointer").on("click", lambda: ui.navigate.to("/cart")):
                ui.icon("shopping_cart", size="1.4rem").style("color:white")
                render_cart_badge()


# ─── Footer ───────────────────────────────────────────────────────────────────
def render_footer():
    with ui.element("footer").classes("footer"):
        with ui.row().classes("items-center w-full"):
            ui.html('<span class="logo-py">Py</span><span class="logo-shop">Shop</span>')
            ui.space()
            ui.html('<span class="footer-copy">© 2024 PyShop · Feito com ❤️ em Python + NiceGUI</span>')


# ─── Home Page ────────────────────────────────────────────────────────────────
@ui.page("/")
async def home():
    ui.add_css(GLOBAL_CSS)
    products = await fetch_products()
    categories = await fetch_categories()

    render_navbar()

    with ui.element("div").style("background:#08060f;min-height:100vh;width:100%;"):
        with ui.element("div").classes("page-container"):

            # Hero
            with ui.element("div").classes("hero"):
                ui.html('<div class="hero-badge">✨ Nova Coleção 2024</div>')
                ui.html('''
                    <h1>Descubra o Melhor<br>
                    <span class="hero-accent">da Tecnologia</span></h1>
                    <p>Os melhores produtos de eletrônicos, moda e acessórios com entrega rápida</p>
                ''')

            # Category pills container
            cat_container = ui.row().classes("gap-2 flex-wrap justify-center py-4")

            # Products container
            grid_container = ui.element("div").classes("products-grid")

            # Mutable state dict to avoid nonlocal issues in nested async functions
            state = {"active_category": "Todos", "products": products}

            def filter_by(cat_name):
                state["active_category"] = cat_name
                if cat_name == "Todos":
                    state["products"] = products
                else:
                    state["products"] = [p for p in products if p["category"] == cat_name]
                render_pills()
                render_products(state["products"])

            def render_products(prods: list[dict]):
                grid_container.clear()
                with grid_container:
                    if not prods:
                        with ui.column().classes("items-center py-16 w-full"):
                            ui.icon("search_off", size="4rem").style("color:rgba(124,58,237,0.4)")
                            ui.label("Nenhum produto encontrado nesta categoria.").style("color:rgba(255,255,255,0.4)")
                        return
                    for p in prods:
                        render_product_card(p)

            def render_product_card(p: dict):
                with ui.element("div").classes("product-card"):
                    with ui.element("div").classes("product-img-wrap"):
                        ui.image(p["image_url"]).style("width:100%;height:100%;object-fit:contain;padding:1rem")
                    with ui.element("div").classes("product-info"):
                        ui.html(f'<span class="product-badge">{p["category"]}</span>')
                        ui.html(f'<div class="product-name">{p["name"]}</div>')
                        ui.html(f'<div class="product-desc">{p["description"]}</div>')
                        with ui.row().classes("items-center justify-between w-full mt-2"):
                            ui.html(f'<span class="product-price">{fmt_price(p["price"])}</span>')
                            btn = ui.button("+ Adicionar", on_click=lambda _, prod=p: add_to_cart(prod))
                            btn.classes("btn-primary").style("padding:0.5rem 0.9rem")

            def render_pills():
                cat_container.clear()
                with cat_container:
                    for c in categories:
                        is_active = "active" if c == state["active_category"] else ""
                        ui.button(c, on_click=lambda _, cat_=c: filter_by(cat_)).classes(f"cat-pill {is_active}")

            # Initial render of products and category pills
            render_pills()
            render_products(products)

        render_footer()


# ─── Test Helper: limpa o carrinho (usado nos testes E2E) ─────────────────────
@ui.page("/clear-cart")
def clear_cart_route():
    """Rota auxiliar para testes E2E — reseta o estado do carrinho."""
    cart.clear()
    ui.navigate.to("/")


def add_to_cart(prod: dict):
    pid = prod["id"]
    if pid in cart:
        cart[pid]["quantity"] += 1
    else:
        cart[pid] = {"product": prod, "quantity": 1}
    # Refresh the navbar badge immediately — no page reload needed
    render_cart_badge.refresh()
    ui.notify(
        f'✅ "{prod["name"]}" adicionado ao carrinho!',
        type="positive",
        classes="toast",
        position="bottom-right",
        timeout=2500,
    )


# ─── Cart Page ────────────────────────────────────────────────────────────────
@ui.page("/cart")
def cart_page():
    ui.add_css(GLOBAL_CSS)

    render_navbar()

    with ui.element("div").style("background:#08060f;min-height:100vh;width:100%;"):
        with ui.element("div").classes("page-container"):
            with ui.row().classes("items-center gap-3 mb-6"):
                ui.icon("shopping_cart", size="1.8rem").style("color:#7C3AED")
                ui.html('<span class="page-heading" style="margin:0">Meu Carrinho</span>')
                if cart_count() > 0:
                    ui.html(f'<span class="product-badge" style="font-size:0.9rem;padding:0.3rem 0.75rem">{cart_count()} itens</span>')

            if not cart:
                # Empty state
                with ui.column().classes("items-center py-20 w-full gap-4"):
                    with ui.element("div").classes("empty-icon"):
                        ui.icon("shopping_cart", size="4rem").style("color:rgba(124,58,237,0.4)")
                    ui.html('<div style="font-size:1.5rem;font-weight:700;color:white">Seu carrinho está vazio</div>')
                    ui.html('<p style="color:rgba(255,255,255,0.5)">Adicione produtos incríveis para começar a comprar!</p>')
                    ui.button("← Explorar Produtos", on_click=lambda: ui.navigate.to("/")).classes("btn-large").style("max-width:220px;margin-top:0.5rem")
            else:
                with ui.row().classes("gap-6 w-full items-start").style("flex-wrap:wrap"):
                    # Items list
                    items_col = ui.column().classes("flex-1").style("min-width:300px")
                    with items_col:
                        render_cart_items()

                    # Summary sidebar
                    with ui.element("div").classes("summary-card").style("width:300px"):
                        render_cart_summary()

        render_footer()


def render_cart_items():
    for pid, entry in list(cart.items()):
        p = entry["product"]
        qty = entry["quantity"]
        with ui.element("div").classes("cart-item"):
            with ui.row().classes("items-center gap-4 w-full").style("flex-wrap:wrap"):
                ui.image(p["image_url"]).style(
                    "width:80px;height:80px;object-fit:contain;border-radius:10px;"
                    "background:rgba(255,255,255,0.05);padding:0.4rem;flex-shrink:0"
                )
                with ui.column().classes("flex-1 gap-1"):
                    ui.html(f'<div style="font-weight:700;color:white;font-size:1rem">{p["name"]}</div>')
                    ui.html(f'<div style="color:#A78BFA;font-weight:600">{fmt_price(p["price"])}</div>')
                ui.space()
                # Qty controls
                with ui.row().classes("items-center gap-2"):
                    ui.button("-", on_click=lambda _, pid_=pid: change_qty(pid_, -1)).classes("qty-btn")
                    ui.html(f'<span style="color:white;font-weight:700;min-width:24px;text-align:center">{qty}</span>')
                    ui.button("+", on_click=lambda _, pid_=pid: change_qty(pid_, 1)).classes("qty-btn")
                # Subtotal
                ui.html(f'<span style="color:white;font-weight:700;min-width:90px;text-align:right">{fmt_price(p["price"] * qty)}</span>')
                # Remove
                ui.button("🗑", on_click=lambda _, pid_=pid: remove_item(pid_)).classes("btn-ghost").style("padding:0.3rem 0.5rem")


def render_cart_summary():
    ui.html('<div style="font-size:1.05rem;font-weight:700;color:white;margin-bottom:0.75rem">Resumo do Pedido</div>')
    ui.separator().classes("divider")
    with ui.row().classes("justify-between items-center w-full"):
        ui.html('<span style="color:rgba(255,255,255,0.6);font-size:0.9rem">Subtotal</span>')
        ui.html(f'<span style="color:white;font-weight:600">{fmt_price(cart_total())}</span>')
    with ui.row().classes("justify-between items-center w-full"):
        ui.html('<span style="color:rgba(255,255,255,0.6);font-size:0.9rem">Frete</span>')
        ui.html('<span class="free-ship">Grátis</span>')
    ui.separator().classes("divider")
    with ui.row().classes("justify-between items-center w-full"):
        ui.html('<span style="color:white;font-weight:700;font-size:1.05rem">Total</span>')
        ui.html(f'<span class="summary-total">{fmt_price(cart_total())}</span>')
    ui.button("Finalizar Pedido →", on_click=lambda: ui.navigate.to("/checkout")).classes("btn-large").style("margin-top:0.5rem")
    ui.button("🗑 Limpar Carrinho", on_click=clear_cart).classes("btn-ghost").style("width:100%;margin-top:0.5rem;padding:0.5rem")


def change_qty(pid: int, delta: int):
    if pid in cart:
        cart[pid]["quantity"] += delta
        if cart[pid]["quantity"] <= 0:
            del cart[pid]
    ui.navigate.to("/cart")


def remove_item(pid: int):
    if pid in cart:
        del cart[pid]
    ui.navigate.to("/cart")


def clear_cart():
    cart.clear()
    ui.navigate.to("/cart")


# ─── Checkout Page ────────────────────────────────────────────────────────────
@ui.page("/checkout")
def checkout_page():
    ui.add_css(GLOBAL_CSS)

    render_navbar()

    order_result: dict = {}

    with ui.element("div").style("background:#08060f;min-height:100vh;width:100%;"):
        main_area = ui.element("div").classes("page-container")
        with main_area:
            render_checkout_content(order_result)

        render_footer()


def render_checkout_content(order_result: dict):
    if order_result.get("placed"):
        render_success(order_result["order_id"])
        return

    with ui.row().classes("items-center gap-3 mb-6"):
        ui.icon("credit_card", size="1.8rem").style("color:#7C3AED")
        ui.html('<span class="page-heading" style="margin:0">Finalizar Pedido</span>')

    if not cart:
        with ui.column().classes("items-center gap-4 py-16 w-full"):
            ui.html('<p style="color:rgba(255,255,255,0.5)">Seu carrinho está vazio.</p>')
            ui.button("← Voltar à Loja", on_click=lambda: ui.navigate.to("/")).classes("btn-large").style("max-width:200px")
        return

    with ui.row().classes("gap-6 w-full items-start").style("flex-wrap:wrap"):
        # Form
        form_col = ui.column().classes("flex-1 gap-4").style("min-width:300px")
        with form_col:
            # Personal data
            with ui.element("div").classes("form-section"):
                ui.html('<div class="section-title">👤 Dados Pessoais</div>')
                name_input = ui.input("Nome Completo", placeholder="João Silva").classes("form-input w-full")
                name_input.props('outlined dark color="deep-purple-4"')
                email_input = ui.input("E-mail", placeholder="joao@email.com").classes("form-input w-full mt-3")
                email_input.props('outlined dark color="deep-purple-4" type="email"')

            # Address
            with ui.element("div").classes("form-section"):
                ui.html('<div class="section-title">📦 Endereço de Entrega</div>')
                addr_input = ui.input("Endereço Completo", placeholder="Rua das Flores, 123").classes("form-input w-full")
                addr_input.props('outlined dark color="deep-purple-4"')
                with ui.row().classes("gap-3 w-full mt-3"):
                    city_input = ui.input("Cidade", placeholder="São Paulo").classes("form-input flex-1")
                    city_input.props('outlined dark color="deep-purple-4"')
                    postal_input = ui.input("CEP", placeholder="01310-100").classes("form-input").style("width:140px")
                    postal_input.props('outlined dark color="deep-purple-4"')

            # Error area
            error_label = ui.html("").style("display:none")

        # Summary sidebar
        with ui.element("div").classes("summary-card").style("width:300px"):
            ui.html('<div style="font-size:1.05rem;font-weight:700;color:white;margin-bottom:0.75rem">🛒 Resumo</div>')
            ui.separator().classes("divider")

            for entry in cart.values():
                p = entry["product"]
                qty = entry["quantity"]
                with ui.row().classes("justify-between items-center w-full"):
                    ui.html(f'<span style="color:rgba(255,255,255,0.8);font-size:0.85rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{p["name"]} ×{qty}</span>')
                    ui.html(f'<span style="color:#A78BFA;font-weight:600;font-size:0.85rem;margin-left:0.5rem">{fmt_price(p["price"] * qty)}</span>')

            ui.separator().classes("divider")
            with ui.row().classes("justify-between items-center w-full"):
                ui.html('<span style="color:rgba(255,255,255,0.5);font-size:0.85rem">Frete</span>')
                ui.html('<span class="free-ship" style="font-size:0.85rem">Grátis</span>')
            with ui.row().classes("justify-between items-center w-full"):
                ui.html('<span style="color:white;font-weight:700;font-size:1.05rem">Total</span>')
                ui.html(f'<span class="summary-total">{fmt_price(cart_total())}</span>')

            ui.separator().classes("divider")

            confirm_btn = ui.button("🛡 Confirmar Pedido", on_click=lambda: place_order())
            confirm_btn.classes("btn-large")

            ui.html('<div style="text-align:center;margin-top:0.5rem"><span style="color:rgba(255,255,255,0.35);font-size:0.78rem">🔒 Pagamento 100% seguro</span></div>')

    async def place_order():
        # Validate
        if not all([name_input.value, email_input.value, addr_input.value, city_input.value, postal_input.value]):
            ui.notify("Por favor, preencha todos os campos!", type="warning", position="bottom-right")
            return

        confirm_btn.text = "Processando..."
        confirm_btn.props("loading")

        payload = {
            "customer_name": name_input.value,
            "customer_email": email_input.value,
            "address": addr_input.value,
            "city": city_input.value,
            "postal_code": postal_input.value,
            "items": [{"product_id": e["product"]["id"], "quantity": e["quantity"]} for e in cart.values()],
        }

        result = await post_order(payload)
        confirm_btn.props(remove="loading")
        confirm_btn.text = "🛡 Confirmar Pedido"

        if result:
            cart.clear()
            order_result["placed"] = True
            order_result["order_id"] = result["id"]
            ui.navigate.to(f"/success/{result['id']}")
        else:
            ui.notify("Erro ao processar pedido. Tente novamente.", type="negative", position="bottom-right")


def render_success(order_id: int):
    with ui.column().classes("items-center gap-6 py-16 w-full"):
        with ui.element("div").classes("success-icon"):
            ui.icon("check_circle", size="4rem").style("color:#4ADE80")
        ui.html('<div style="font-size:2rem;font-weight:900;color:white;text-align:center">Pedido Confirmado! 🎉</div>')
        ui.html('<p style="color:rgba(255,255,255,0.6);font-size:1.05rem;text-align:center">Seu pedido foi recebido com sucesso.</p>')
        with ui.element("div").classes("order-badge"):
            ui.html('<div style="color:rgba(255,255,255,0.5);font-size:0.85rem;margin-bottom:0.25rem">Número do Pedido</div>')
            ui.html(f'<div style="color:white;font-size:1.2rem;font-weight:700"># <span style="color:#A78BFA;font-size:2rem;font-weight:900">{order_id}</span></div>')
        ui.button("← Continuar Comprando", on_click=lambda: ui.navigate.to("/")).classes("btn-large").style("max-width:260px")


# ─── Success redirect page ────────────────────────────────────────────────────
@ui.page("/success/{order_id}")
def success_page(order_id: int):
    ui.add_css(GLOBAL_CSS)
    render_navbar()
    with ui.element("div").style("background:#08060f;min-height:100vh;width:100%;"):
        with ui.element("div").classes("page-container"):
            render_success(order_id)
        render_footer()


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=3000,
        title="PyShop — Loja Virtual",
        favicon="🛒",
        dark=True,
        reload=False,
    )
