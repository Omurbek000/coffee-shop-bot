import logging

from telebot import types

import config

logger = logging.getLogger(__name__)


def register(bot):
    def send_wifi(chat_id):
        if config.WIFI_LOGIN and config.WIFI_PASSWORD:
            text = (
                "📶 *Wi-Fi кофейни*\n\n"
                f"Логин: `{config.WIFI_LOGIN}`\n"
                f"Пароль: `{config.WIFI_PASSWORD}`"
            )
        else:
            text = "📶 Wi-Fi: уточните логин и пароль у бариста."
        bot.send_message(chat_id, text, parse_mode="Markdown")

    @bot.message_handler(commands=["wifi"])
    def wifi_command(message):
        send_wifi(message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "wifi")
    def wifi_callback(call):
        send_wifi(call.message.chat.id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "feedback")
    def feedback_start(call):
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "✍️ Напишите отзыв или предложение одним сообщением:",
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, save_feedback)

    def save_feedback(message):
        text = message.text.strip() if message.content_type == "text" else ""
        if not text:
            bot.send_message(message.chat.id, "Пришлите текст сообщением:")
            bot.register_next_step_handler(message, save_feedback)
            return

        if config.ADMIN_CHAT_ID:
            user = message.from_user
            customer = f"@{user.username}" if user.username else user.full_name
            try:
                bot.send_message(
                    config.ADMIN_CHAT_ID,
                    f"✍️ Отзыв от {customer} (ID: {user.id}):\n\n{text}",
                )
            except Exception:
                logger.exception("Не удалось отправить отзыв админу")
        bot.send_message(message.chat.id, "🙏 Спасибо за отзыв!")

    @bot.callback_query_handler(func=lambda call: call.data == "contacts")
    def show_contacts(call):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📍 2GIS", url="https://go.2gis.com/sans3"),
            types.InlineKeyboardButton(
                "🗺️ Yandex", url="https://yandex.kz/maps/ru/-/CDuOU4M0"
            ),
        )
        markup.add(
            types.InlineKeyboardButton(
                "📞 WhatsApp", url="https://wa.me/77002478746"
            ),
            types.InlineKeyboardButton("📸 Instagram", url="https://instagram.com"),
        )
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))

        bot.send_message(
            call.message.chat.id,
            "📍 *Наши контакты*\n\n"
            "📞 Телефон: +7 747 838 2703\n"
            "🏠 Адрес: Кунаева 130\n"
            "⏰ Часы работы: 07:30 - 23:00",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def show_about(call):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))

        bot.send_message(
            call.message.chat.id,
            "☕ *О нашей кофейне*\n\n"
            "Мы - уютная кофейня в центре города, "
            "где каждый гость может насладиться "
            "ароматным кофе и вкусными завтраками.\n\n"
            "✅ Свежая обжарка кофе\n"
            "✅ Домашняя выпечка\n"
            "✅ Бесплатный Wi-Fi\n"
            "✅ Комфортная атмосфера",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id)
