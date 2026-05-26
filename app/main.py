import html
import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.api import api_router
from app.models.product import Product

# Pastas necessárias para uploads e arquivos estáticos.
# Mantém o backend estável tanto no Windows/local quanto em produção.
os.makedirs("uploads/produtos", exist_ok=True)
os.makedirs("uploads/users", exist_ok=True)
os.makedirs("uploads/home/banners", exist_ok=True)
os.makedirs("uploads/home/sections", exist_ok=True)
os.makedirs("app/static/generated", exist_ok=True)
os.makedirs("app/static/templates", exist_ok=True)

app = FastAPI(title="Paixão API")

# CORS liberado para desenvolvimento local e produção.
# Em local: frontend Vite normalmente roda em http://localhost:5173.
# Em produção: mantém os domínios oficiais da Paixão Angola.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "https://paixaoangola.com",
    "https://www.paixaoangola.com",
    "https://api.paixaoangola.com",

    "https://paixao-backend.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/images", StaticFiles(directory="uploads"), name="images")
app.mount("/generated", StaticFiles(directory="app/static/generated"), name="generated")
app.mount("/templates", StaticFiles(directory="app/static/templates"), name="templates")

# Defaults locais para desenvolvimento.
# Em produção, basta definir essas variáveis no servidor:
# FRONTEND_BASE_URL=https://www.paixaoangola.com
# API_BASE_URL=https://api.paixaoangola.com
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _normalize_media_url(value: str | None) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    if not raw:
        return ""

    # Não forçar http -> https aqui.
    # Em desenvolvimento local isso quebraria URLs como http://localhost:8000.
    # Em produção, use API_BASE_URL/FRONTEND_BASE_URL com https no .env do servidor.
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    if "/uploads/" in raw:
        return f"{API_BASE_URL}{raw[raw.index('/uploads/'):]}"
    if raw.startswith("uploads/"):
        return f"{API_BASE_URL}/{raw}"
    if raw.startswith("/uploads/"):
        return f"{API_BASE_URL}{raw}"

    if "/imagem/" in raw:
        return f"{FRONTEND_BASE_URL}{raw[raw.index('/imagem/'):]}"
    if raw.startswith("imagem/"):
        return f"{FRONTEND_BASE_URL}/{raw}"
    if raw.startswith("/imagem/"):
        return f"{FRONTEND_BASE_URL}{raw}"

    if "/video/" in raw:
        return f"{FRONTEND_BASE_URL}{raw[raw.index('/video/'):]}"
    if raw.startswith("video/"):
        return f"{FRONTEND_BASE_URL}/{raw}"
    if raw.startswith("/video/"):
        return f"{FRONTEND_BASE_URL}{raw}"

    if raw.startswith("/"):
        return f"{API_BASE_URL}{raw}"

    return f"{API_BASE_URL}/{raw}"


def _first_product_image(product: Product) -> str:
    images = getattr(product, "images", None) or []

    if isinstance(images, list):
        for item in images:
            normalized = _normalize_media_url(item)
            if normalized:
                return normalized

    return f"{FRONTEND_BASE_URL}/imagem/produtos/logo_1024.png"


@app.get("/")
def root():
    return {"message": "Paixão API está funcionando 🚀"}


@app.get("/share/product/{product_id}", response_class=HTMLResponse)
def share_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )

    if not product:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="pt">
              <head>
                <meta charset="utf-8" />
                <title>Produto não encontrado | Paixão Angola</title>
                <meta name="robots" content="noindex,nofollow" />
              </head>
              <body>
                <h1>Produto não encontrado</h1>
              </body>
            </html>
            """,
            status_code=404,
        )

    title = html.escape(str(product.name or "Produto Paixão Angola"), quote=True)
    description = html.escape(
        str(product.description or "Confira este produto na Paixão Angola."),
        quote=True,
    )
    image_url = html.escape(_first_product_image(product), quote=True)
    frontend_url = html.escape(f"{FRONTEND_BASE_URL}/products/{product.id}", quote=True)

    price_value = getattr(product, "price", None)
    price_display = str(price_value) if price_value is not None else ""

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="pt">
          <head>
            <meta charset="utf-8" />
            <title>{title}</title>

            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <meta name="robots" content="index,follow" />

            <meta property="og:site_name" content="Paixão Angola" />
            <meta property="og:title" content="{title}" />
            <meta property="og:description" content="{description}" />
            <meta property="og:image" content="{image_url}" />
            <meta property="og:image:secure_url" content="{image_url}" />
            <meta property="og:url" content="{frontend_url}" />
            <meta property="og:type" content="product" />
            <meta property="product:price:amount" content="{html.escape(price_display, quote=True)}" />
            <meta property="product:price:currency" content="AOA" />

            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="{title}" />
            <meta name="twitter:description" content="{description}" />
            <meta name="twitter:image" content="{image_url}" />

            <meta http-equiv="refresh" content="0;url={frontend_url}" />
            <link rel="canonical" href="{frontend_url}" />
          </head>
          <body>
            <script>
              window.location.replace("{frontend_url}");
            </script>
            <p>A redirecionar para <a href="{frontend_url}">o produto</a>...</p>
          </body>
        </html>
        """
    )


app.include_router(api_router)
