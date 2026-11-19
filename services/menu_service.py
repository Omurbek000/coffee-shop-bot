import json
from contextlib import closing
from pathlib import Path

import config
from db import connect


def _as_dict(row):
    return dict(row) if row is not None else None


def get_categories():
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT slug, title, emoji FROM categories ORDER BY sort_order, id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_category(slug):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT slug, title, emoji FROM categories WHERE slug = ?",
            (slug,),
        ).fetchone()
    return _as_dict(row)


def get_products(category_slug):
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT p.slug, p.name, p.description, p.price, p.emoji, p.image
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE c.slug = ? AND p.is_available = 1
            ORDER BY p.sort_order, p.id
            """,
            (category_slug,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_product(slug):
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT p.slug, p.name, p.description, p.price, p.emoji, p.image,
                   c.slug AS category_slug
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE p.slug = ? AND p.is_available = 1
            """,
            (slug,),
        ).fetchone()
    return _as_dict(row)


def count_products():
    with closing(connect()) as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()
    return row["count"]


def reseed_from_json():
    data = json.loads(Path(config.MENU_FILE).read_text(encoding="utf-8"))

    with closing(connect()) as conn:
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM categories")

        for category_order, (category_slug, category) in enumerate(data.items()):
            cursor = conn.execute(
                """
                INSERT INTO categories (slug, title, emoji, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (
                    category_slug,
                    category["title"],
                    category.get("emoji", ""),
                    category_order,
                ),
            )
            category_id = cursor.lastrowid

            for product_order, product in enumerate(category["items"]):
                conn.execute(
                    """
                    INSERT INTO products
                        (category_id, slug, name, description, price, emoji, image, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        category_id,
                        product["id"],
                        product["name"],
                        product.get("description", ""),
                        product["price"],
                        product.get("emoji", ""),
                        product.get("image"),
                        product_order,
                    ),
                )

        conn.commit()


def ensure_seeded():
    if count_products() > 0:
        return
    if not Path(config.MENU_FILE).exists():
        return
    reseed_from_json()
