"""
Seed script: populates the database with initial products.
Runs automatically on container startup (see Dockerfile CMD).
"""
import time
import os
from sqlalchemy import text
from database import engine, SessionLocal, Base
from models import Product

# Public URL the browser uses to load images (must be reachable from the user's browser)
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "http://localhost:8000")

PRODUCTS = [
    {
        "name": "Fone de Ouvido Pro",
        "description": "Fone over-ear sem fio com cancelamento de ruído ativo, bateria de 40h e áudio Hi-Res. Drivers de 40mm com graves profundos e agudos cristalinos. Design dobrável premium em alumínio e couro sintético.",
        "price": 299.90,
        "category": "Eletrônicos",
        "image_url": f"{IMAGE_BASE_URL}/static/images/headphones.png",
        "stock": 50,
    },
    {
        "name": "Smartwatch Elite",
        "description": "Relógio inteligente com tela AMOLED de 1.4\", monitor cardíaco, SpO2, GPS integrado e resistência à água 5ATM. Bateria de 7 dias. Compatível com Android e iOS.",
        "price": 899.90,
        "category": "Eletrônicos",
        "image_url": f"{IMAGE_BASE_URL}/static/images/smartwatch.png",
        "stock": 30,
    },
    {
        "name": "Câmera Mirrorless",
        "description": "Câmera mirrorless de 24MP com sensor full-frame, vídeo 4K 60fps, estabilização óptica de 5 eixos e autofoco por detecção de fase. Inclui lente 24-70mm f/2.8.",
        "price": 4999.90,
        "category": "Fotografia",
        "image_url": f"{IMAGE_BASE_URL}/static/images/camera.png",
        "stock": 15,
    },
    {
        "name": "Mochila Urban",
        "description": "Mochila urbana em tecido ripstop impermeável com compartimento para notebook de 17\", porta USB externa para carregamento, saídas para fone e capacidade de 30L.",
        "price": 189.90,
        "category": "Acessórios",
        "image_url": f"{IMAGE_BASE_URL}/static/images/backpack.png",
        "stock": 80,
    },
    {
        "name": "Tênis Runner X",
        "description": "Tênis de corrida com solado de amortecimento Boost+, cabedal em mesh respirável, palmilha ortopédica removível e tecnologia de retorno de energia. Ideal para corridas longas.",
        "price": 349.90,
        "category": "Calçados",
        "image_url": f"{IMAGE_BASE_URL}/static/images/shoes.png",
        "stock": 60,
    },
    {
        "name": "Óculos de Sol Aviator",
        "description": "Óculos aviador com armação em aço inoxidável dourado, lentes polarizadas com proteção UV400 e revestimento anti-reflexo. Acompanha estojo rígido e flanela.",
        "price": 249.90,
        "category": "Acessórios",
        "image_url": f"{IMAGE_BASE_URL}/static/images/sunglasses.png",
        "stock": 45,
    },
    {
        "name": "Laptop Ultrabook",
        "description": "Ultrabook com processador Intel Core Ultra 7, 32GB RAM LPDDR5, SSD NVMe de 1TB, tela OLED 14\" 2.8K 120Hz, bateria de 72Wh e espessura de apenas 13mm.",
        "price": 6799.90,
        "category": "Eletrônicos",
        "image_url": f"{IMAGE_BASE_URL}/static/images/laptop.png",
        "stock": 20,
    },
    {
        "name": "Camiseta Premium",
        "description": "Camiseta em algodão pima 100% penteado de altíssima qualidade, com caimento perfeito, costura reforçada e tingimento que não desbota. Disponível em várias cores.",
        "price": 89.90,
        "category": "Roupas",
        "image_url": f"{IMAGE_BASE_URL}/static/images/tshirt.png",
        "stock": 200,
    },
]

# Map of image filename → correct URL
IMAGE_FILENAMES = {
    "headphones.png", "smartwatch.png", "camera.png", "backpack.png",
    "shoes.png", "sunglasses.png", "laptop.png", "tshirt.png",
}


def wait_for_db(retries: int = 15, delay: int = 3):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready!")
            return
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("❌ Could not connect to database after retries")


def fix_image_urls(db):
    """Fix any existing product image URLs that have the wrong host (e.g. 0.0.0.0)."""
    products = db.query(Product).all()
    fixed = 0
    for p in products:
        url = p.image_url or ""
        # Extract the filename and rebuild with the correct base
        for fname in IMAGE_FILENAMES:
            if fname in url and not url.startswith(IMAGE_BASE_URL):
                p.image_url = f"{IMAGE_BASE_URL}/static/images/{fname}"
                fixed += 1
                break
    if fixed:
        db.commit()
        print(f"🔧 Fixed {fixed} product image URL(s) → {IMAGE_BASE_URL}")
    else:
        print("✅ Image URLs are correct, no fix needed.")


def seed():
    wait_for_db()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = db.query(Product).count()
        if count == 0:
            print("🌱 Seeding products...")
            for p in PRODUCTS:
                db.add(Product(**p))
            db.commit()
            print(f"✅ {len(PRODUCTS)} products created!")
        else:
            print(f"ℹ️  Database already has {count} products. Checking image URLs...")
            fix_image_urls(db)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
