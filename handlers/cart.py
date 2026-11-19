from telebot import types

from services import cart_service


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
            line_total = item["price"] * item["quantity"]
            text += (
                f"{index}. {item['emoji']} {item['name']}"
                f" x{item['quantity']} — {line_total}₸\n"
            )
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
