from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from database import Base, engine
from routers import products, orders

app = FastAPI(
    title="PyShop API",
    description="API da loja virtual PyShop",
    version="1.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files (product images) ───────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(products.router)
app.include_router(orders.router)


# ─── Events ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "PyShop API is running 🚀", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
