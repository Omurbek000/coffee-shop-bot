import logging

from telebot import types

import config
from services import cart_service

logger = logging.getLogger(__name__)


def register(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "cart")
    def show_cart(call):
        user_id = call.from_user.id
        items = cart_service.get_items(user_id)

        if not items:
            bot.answer_callback_query(call.id, "Корзина пуста")
            return

        text = "🛒 *Ваша корзина:*\n\n"
        for index, item in enumerate(items, 1):
            text += f"{index}. {item['emoji']} {item['name']} - {item['price']}₸\n"
        text += f"\n💰 *Итого: {cart_service.total(user_id)}₸*"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "🗑️ Очистить корзину", callback_data="clear_cart"
            ),
            types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"),
        )
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "clear_cart")
    def clear_cart(call):
        cart_service.clear(call.from_user.id)
        bot.answer_callback_query(call.id, "Корзина очищена")
        bot.send_message(call.message.chat.id, "🛒 Корзина очищена")

    @bot.callback_query_handler(func=lambda call: call.data == "checkout")
    def checkout(call):
        user_id = call.from_user.id
        items = cart_service.get_items(user_id)

        if not items:
            bot.answer_callback_query(call.id, "Корзина пуста")
            return

        total = cart_service.total(user_id)
        if call.from_user.username:
            customer = f"@{call.from_user.username}"
        else:
            customer = call.from_user.full_name

        order_lines = [f"🆕 Новый заказ от {customer} (ID: {user_id})", ""]
        for item in items:
            order_lines.append(f"{item['emoji']} {item['name']} - {item['price']}₸")
        order_lines += ["", f"💰 Итого: {total}₸"]
        order_text = "\n".join(order_lines)

        if config.ADMIN_CHAT_ID:
            try:
                bot.send_message(config.ADMIN_CHAT_ID, order_text)
            except Exception:
                logger.exception("Не удалось отправить заказ админу")
        else:
            logger.warning("ADMIN_CHAT_ID не задан: заказ от %s не отправлен", user_id)

        cart_service.clear(user_id)

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "📞 Связаться с нами", url="https://wa.me/77002478746"
            ),
            types.InlineKeyboardButton("🔙 В меню", callback_data="menu"),
        )
        bot.send_message(
            call.message.chat.id,
            "✅ *Заказ принят!*\n\n"
            f"Сумма заказа: {total}₸\n\n"
            "Наш менеджер свяжется с вами для подтверждения.",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id)
