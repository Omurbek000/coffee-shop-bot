import logging

import config
from handlers import order_views
from services import order_service

logger = logging.getLogger(__name__)


def _is_admin(user_id):
    return config.ADMIN_CHAT_ID is not None and user_id == config.ADMIN_CHAT_ID


def register(bot):
    @bot.message_handler(commands=["orders"])
    def orders_command(message):
        if not _is_admin(message.from_user.id):
            return

        orders = order_service.today_orders()
        if not orders:
            bot.send_message(message.chat.id, "Заказов за сегодня нет.")
            return

        lines = ["📋 Заказы за сегодня:", ""]
        for order in orders:
            customer = (
                f"@{order['username']}"
                if order["username"]
                else order["first_name"] or f"ID {order['user_id']}"
            )
            status = order_views.STATUS_LABELS.get(order["status"], order["status"])
            lines.append(
                f"#{order['id']} {order['time']} — {order['total']}₸ — "
                f"{status} — {customer}"
            )
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.message_handler(commands=["stats"])
    def stats_command(message):
        if not _is_admin(message.from_user.id):
            return

        data = order_service.stats()
        lines = [
            "📊 Статистика",
            "",
            f"Сегодня: {data['today_orders']} заказов на {data['today_revenue']}₸",
            f"Всего заказов (без отклонённых): {data['total_orders']}",
            "",
        ]
        if data["top"]:
            lines.append("Топ товаров:")
            for index, row in enumerate(data["top"], 1):
                lines.append(
                    f"{index}. {row['name']} — {row['quantity']} шт, "
                    f"{row['revenue']}₸"
                )
        else:
            lines.append("Пока нет данных по товарам.")
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ostatus_"))
    def change_status(call):
        if not _is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Нет доступа")
            return

        parts = call.data.split("_", 2)
        if len(parts) != 3 or not parts[1].isdigit():
            bot.answer_callback_query(call.id)
            return

        order = order_service.set_status(int(parts[1]), parts[2])
        if not order:
            bot.answer_callback_query(call.id, "Смена статуса недоступна")
            return

        status_label = order_views.STATUS_LABELS.get(order["status"], order["status"])
        bot.answer_callback_query(call.id, f"Статус: {status_label}")

        try:
            bot.edit_message_text(
                order_views.build_order_text(order),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=order_views.build_status_keyboard(order),
            )
        except Exception:
            logger.exception("Не удалось обновить карточку заказа")

        try:
            bot.send_message(order["user_id"], order_views.client_status_text(order))
        except Exception:
            logger.warning(
                "Не удалось уведомить клиента заказа №%s", order["id"]
            )
