from contextlib import closing

from db import connect


def _upsert_user(conn, user_id, username, first_name, last_name):
    conn.execute(
        """
        INSERT INTO users (id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            updated_at = datetime('now')
        """,
        (user_id, username, first_name, last_name),
    )


def _cart_rows(conn, user_id):
    return conn.execute(
        """
        SELECT p.id AS product_id, p.slug, p.name, p.price, p.emoji,
               ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = ?
        ORDER BY ci.added_at, p.name
        """,
        (user_id,),
    ).fetchall()


def add_item(user_id, username, first_name, last_name, product_slug):
    with closing(connect()) as conn:
        with conn:
            _upsert_user(conn, user_id, username, first_name, last_name)
            product = conn.execute(
                "SELECT id FROM products WHERE slug = ? AND is_available = 1",
                (product_slug,),
            ).fetchone()
            if product is None:
                return False
            conn.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, product_id)
                DO UPDATE SET quantity = quantity + 1
                """,
                (user_id, product["id"]),
            )
    return True


def get_items(user_id):
    with closing(connect()) as conn:
        rows = _cart_rows(conn, user_id)
    return [dict(row) for row in rows]


def total(user_id):
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(p.price * ci.quantity), 0) AS total
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return row["total"]


def clear(user_id):
    with closing(connect()) as conn:
        with conn:
            conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))


def checkout(user_id, username, first_name, last_name):
    with closing(connect()) as conn:
        with conn:
            _upsert_user(conn, user_id, username, first_name, last_name)
            rows = _cart_rows(conn, user_id)
            if not rows:
                return None

            total_sum = sum(row["price"] * row["quantity"] for row in rows)
            cursor = conn.execute(
                "INSERT INTO orders (user_id, total) VALUES (?, ?)",
                (user_id, total_sum),
            )
            order_id = cursor.lastrowid

            for row in rows:
                conn.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, name, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        row["product_id"],
                        row["name"],
                        row["price"],
                        row["quantity"],
                    ),
                )

            conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

    return {
        "order_id": order_id,
        "total": total_sum,
        "items": [dict(row) for row in rows],
    }
