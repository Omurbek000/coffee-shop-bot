import logging

from telebot import types

import config
from services import cart_service, menu_service

logger = logging.getLogger(__name__)


def register(bot):
    def send_menu_categories(chat_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for category in menu_service.get_categories():
            markup.add(
                types.InlineKeyboardButton(
                    f"{category['emoji']} {category['title']}",
                    callback_data=f"category_{category['slug']}",
                )
            )
        bot.send_message(
            chat_id,
            "📋 *Выберите категорию:*",
            parse_mode="Markdown",
            reply_markup=markup,
        )

    @bot.message_handler(commands=["start"])
    def start(message):
        cart_service.clear(message.from_user.id)

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 Меню", callback_data="menu"),
            types.InlineKeyboardButton("🛒 Корзина", callback_data="cart"),
        )
        markup.add(
            types.InlineKeyboardButton("ℹ️ О нас", callback_data="about"),
            types.InlineKeyboardButton("📍 Контакты", callback_data="contacts"),
        )
        bot.send_message(
            message.chat.id,
            "☕ *Добро пожаловать в Coffee Shop Bot!*\n\n"
            "Здесь вы можете:\n"
            "📋 Просмотреть наше меню\n"
            "🛒 Добавить товары в корзину\n"
            "📞 Оставить отзыв или связаться с нами",
            parse_mode="Markdown",
            reply_markup=markup,
        )

    @bot.message_handler(commands=["menu"])
    def show_menu(message):
        send_menu_categories(message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "menu")
    def back_to_menu(call):
        send_menu_categories(call.message.chat.id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
    def show_category_products(call):
        category_slug = call.data.split("_", 1)[1]
        category = menu_service.get_category(category_slug)
        products = menu_service.get_products(category_slug)

        if not category or not products:
            bot.answer_callback_query(call.id, "Категория пуста")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        for product in products:
            markup.add(
                types.InlineKeyboardButton(
                    f"{product['emoji']} {product['name']} - {product['price']}₸",
                    callback_data=f"product_{product['slug']}",
                )
            )
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))

        text = f"📋 *{category['title']}:*"
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
    def show_product_details(call):
        product_slug = call.data.split("_", 1)[1]
        product = menu_service.get_product(product_slug)

        if not product:
            bot.answer_callback_query(call.id, "Товар не найден")
            return

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "➕ Добавить в корзину", callback_data=f"add_{product_slug}"
            ),
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"category_{product['category_slug']}",
            ),
        )

        caption_lines = [
            f"{product['emoji']} *{product['name']}*",
            "",
            f"💰 Цена: {product['price']}₸",
        ]
        if product["description"]:
            caption_lines.append(f"📝 {product['description']}")
        caption = "\n".join(caption_lines)

        image_path = config.BASE_DIR / product["image"] if product["image"] else None
        if image_path and image_path.exists():
            with open(image_path, "rb") as photo:
                bot.send_photo(
                    call.message.chat.id,
                    photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=markup,
                )
        else:
            bot.send_message(
                call.message.chat.id,
                caption,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
    def add_to_cart(call):
        product_slug = call.data.split("_", 1)[1]
        product = menu_service.get_product(product_slug)

        if not product:
            bot.answer_callback_query(call.id, "Товар не найден")
            return

        user = call.from_user
        added = cart_service.add_item(
            user.id, user.username, user.first_name, user.last_name, product_slug
        )
        if not added:
            bot.answer_callback_query(call.id, "❌ Товар недоступен")
            return

        bot.answer_callback_query(
            call.id, f"✅ {product['name']} добавлен в корзину"
        )
