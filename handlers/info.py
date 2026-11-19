from telebot import types


def register(bot):
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
