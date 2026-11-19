from contextlib import closing

from db import connect

ALLOWED_TRANSITIONS = {
    "new": ("accepted", "rejected"),
    "accepted": ("ready", "rejected"),
    "ready": ("done",),
}


def _order_items(conn, order_id):
    rows = conn.execute(
        """
        SELECT name, price, quantity
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
        """,
        (order_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_order(order_id):
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT o.id, o.user_id, o.total, o.status, o.phone,
                   o.delivery_method, o.address, o.comment,
                   strftime('%d.%m %H:%M', o.created_at, 'localtime') AS created_at,
                   u.username, u.first_name
            FROM orders o
            LEFT JOIN users u ON u.id = o.user_id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()
        if row is None:
            return None
        order = dict(row)
        order["items"] = _order_items(conn, order_id)
    return order


def set_status(order_id, new_status):
    order = get_order(order_id)
    if not order:
        return None
    if new_status not in ALLOWED_TRANSITIONS.get(order["status"], ()):
        return None

    with closing(connect()) as conn:
        with conn:
            conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id),
            )
    return get_order(order_id)


def today_orders(limit=20):
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT o.id, o.user_id, o.total, o.status,
                   strftime('%H:%M', o.created_at, 'localtime') AS time,
                   u.username, u.first_name
            FROM orders o
            LEFT JOIN users u ON u.id = o.user_id
            WHERE date(o.created_at, 'localtime') = date('now', 'localtime')
            ORDER BY o.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def stats():
    with closing(connect()) as conn:
        today = conn.execute(
            """
            SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue
            FROM orders
            WHERE date(created_at, 'localtime') = date('now', 'localtime')
              AND status != 'rejected'
            """
        ).fetchone()
        total = conn.execute(
            "SELECT COUNT(*) AS count FROM orders WHERE status != 'rejected'"
        ).fetchone()
        top = conn.execute(
            """
            SELECT oi.name, SUM(oi.quantity) AS quantity,
                   SUM(oi.price * oi.quantity) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'rejected'
            GROUP BY oi.name
            ORDER BY quantity DESC
            LIMIT 5
            """
        ).fetchall()

    return {
        "today_orders": today["orders"],
        "today_revenue": today["revenue"],
        "total_orders": total["count"],
        "top": [dict(row) for row in top],
    }
