from telebot import types

from services import order_service

STATUS_LABELS = {
    "new": "🆕 Новый",
    "accepted": "✅ Принят",
    "ready": "✔️ Готов",
    "done": "📦 Завершён",
    "rejected": "❌ Отклонён",
}


def customer_name(order):
    if order.get("username"):
        return f"@{order['username']}"
    return order.get("first_name") or f"ID {order['user_id']}"


def build_order_text(order):
    if order["delivery_method"] == "pickup":
        delivery = "🏃 Самовывоз"
    else:
        delivery = f"🛵 Доставка — {order.get('address') or 'адрес не указан'}"

    lines = [
        f"Заказ №{order['id']} — {STATUS_LABELS.get(order['status'], order['status'])}",
        f"🕒 {order['created_at']}",
        f"👤 {customer_name(order)}",
        f"📞 {order['phone'] or 'не указан'}",
        delivery,
    ]
    if order.get("comment"):
        lines.append(f"💬 {order['comment']}")
    lines.append("")
    for item in order["items"]:
        line_total = item["price"] * item["quantity"]
        lines.append(f"{item['name']} x{item['quantity']} — {line_total}₸")
    lines += ["", f"💰 Итого: {order['total']}₸"]
    return "\n".join(lines)


def build_status_keyboard(order):
    transitions = order_service.ALLOWED_TRANSITIONS.get(order["status"], ())
    if not transitions:
        return None

    markup = types.InlineKeyboardMarkup(row_width=2)
    for status in transitions:
        markup.add(
            types.InlineKeyboardButton(
                STATUS_LABELS[status],
                callback_data=f"ostatus_{order['id']}_{status}",
            )
        )
    return markup


def client_status_text(order):
    status = order["status"]
    if status == "accepted":
        return f"✅ Заказ №{order['id']} принят. Уже готовим!"
    if status == "ready":
        return f"✔️ Заказ №{order['id']} готов!"
    if status == "done":
        return f"🙏 Заказ №{order['id']} завершён. Спасибо, что выбрали нас!"
    if status == "rejected":
        return (
            f"❌ Заказ №{order['id']} отклонён. "
            "Свяжитесь с нами: https://wa.me/77002478746"
        )
    return f"Заказ №{order['id']}: {STATUS_LABELS.get(status, status)}"
