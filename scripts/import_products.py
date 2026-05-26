import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database.session import SessionLocal

BASE_DIR = Path(__file__).resolve().parent.parent

JSON_FILES = [
    "products_perfumaria.json",
    "products_bodysplash.json",
    "products_kits_bodysplash.json",
    "products_creme_desodorante.json",
]


def load_products_from_file(file_name: str):
    file_path = BASE_DIR / file_name

    if not file_path.exists():
        print(f"⚠️ Arquivo não encontrado: {file_name}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"⚠️ Arquivo inválido: {file_name}")
        return []

    print(f"📦 {file_name}: {len(data)} produto(s) carregado(s)")
    return data


def ensure_product_columns(db):
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS subcategory VARCHAR"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_wholesale BOOLEAN DEFAULT FALSE"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS wholesale_price NUMERIC(10,2)"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_kit BOOLEAN DEFAULT FALSE"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSONB DEFAULT '[]'::jsonb"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSONB DEFAULT '[]'::jsonb"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS images JSONB DEFAULT '[]'::jsonb"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS video_url VARCHAR"))
    db.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))


def main():
    db = SessionLocal()

    created = 0
    updated = 0

    try:
        ensure_product_columns(db)

        all_products = []
        for json_file in JSON_FILES:
            all_products.extend(load_products_from_file(json_file))

        print(f"🚀 Total consolidado para importar: {len(all_products)} produto(s)")

        for data in all_products:
            existing = db.execute(
                text("SELECT id FROM products WHERE name = :name LIMIT 1"),
                {"name": data["name"]},
            ).fetchone()

            payload = {
                "name": data["name"],
                "description": data.get("description"),
                "price": Decimal(str(data["price"])),
                "stock": int(data.get("stock", 0)),
                "category": data.get("category"),
                "subcategory": data.get("subcategory"),
                "is_wholesale": bool(data.get("is_wholesale", False)),
                "wholesale_price": (
                    Decimal(str(data["wholesale_price"]))
                    if data.get("wholesale_price") is not None
                    else None
                ),
                "is_kit": bool(data.get("is_kit", False)),
                "sizes": json.dumps(data.get("sizes", []), ensure_ascii=False),
                "colors": json.dumps(data.get("colors", []), ensure_ascii=False),
                "images": json.dumps(data.get("images", []), ensure_ascii=False),
                "video_url": data.get("video_url"),
                "is_active": bool(data.get("is_active", True)),
            }

            if existing:
                db.execute(
                    text(
                        """
                        UPDATE products SET
                            description = :description,
                            price = :price,
                            stock = :stock,
                            category = :category,
                            subcategory = :subcategory,
                            is_wholesale = :is_wholesale,
                            wholesale_price = :wholesale_price,
                            is_kit = :is_kit,
                            sizes = CAST(:sizes AS JSONB),
                            colors = CAST(:colors AS JSONB),
                            images = CAST(:images AS JSONB),
                            video_url = :video_url,
                            is_active = :is_active
                        WHERE name = :name
                        """
                    ),
                    payload,
                )
                updated += 1
                print(f"🔁 Atualizado: {data['name']}")
            else:
                db.execute(
                    text(
                        """
                        INSERT INTO products (
                            name, description, price, stock, category, subcategory,
                            is_wholesale, wholesale_price, is_kit,
                            sizes, colors, images, video_url, is_active
                        )
                        VALUES (
                            :name, :description, :price, :stock, :category, :subcategory,
                            :is_wholesale, :wholesale_price, :is_kit,
                            CAST(:sizes AS JSONB),
                            CAST(:colors AS JSONB),
                            CAST(:images AS JSONB),
                            :video_url,
                            :is_active
                        )
                        """
                    ),
                    payload,
                )
                created += 1
                print(f"✅ Criado: {data['name']}")

        db.commit()
        print(f"\n🎉 Importação concluída. Criados: {created} | Atualizados: {updated}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro durante a importação: {repr(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()