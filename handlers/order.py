import logging
import re
from datetime import datetime

from telebot import types

import config
from handlers import order_views
from services import cart_service, order_service

logger = logging.getLogger(__name__)

_pending = {}


def _normalize_phone(text):
    digits = re.sub(r"\D", "", text or "")
    if 10 <= len(digits) <= 15:
        return text.strip()
    return None


def _is_working_now():
    now = datetime.now()
    current = now.hour * 60 + now.minute
    start = config.WORK_START.hour * 60 + config.WORK_START.minute
    end = config.WORK_END.hour * 60 + config.WORK_END.minute

    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def register(bot):
    def ask_comment(chat_id):
        bot.send_message(
            chat_id,
            "Последний шаг. Комментарий к заказу (или «-», чтобы пропустить):",
        )
        bot.register_next_step_handler_by_chat_id(chat_id, process_comment)

    def send_summary(chat_id, user_id):
        items = cart_service.get_items(user_id)
        if not items:
            _pending.pop(user_id, None)
            bot.send_message(chat_id, "Корзина пуста, оформление отменено.")
            return

        state = _pending[user_id]
        total = sum(item["price"] * item["quantity"] for item in items)

        if state["method"] == "pickup":
            delivery = "🏃 Самовывоз"
        else:
            delivery = f"🛵 Доставка: {state.get('address')}"

        lines = ["📝 Проверьте заказ:", ""]
        for item in items:
            line_total = item["price"] * item["quantity"]
            lines.append(
                f"{item['emoji']} {item['name']} x{item['quantity']} — {line_total}₸"
            )
        lines += [
            "",
            f"💰 Итого: {total}₸",
            f"📞 Телефон: {state['phone']}",
            delivery,
        ]
        if state.get("comment"):
            lines.append(f"💬 Комментарий: {state['comment']}")

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_order"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_order"),
        )
        bot.send_message(chat_id, "\n".join(lines), reply_markup=markup)

    def process_phone(message):
        user = message.from_user
        state = _pending.get(user.id)
        if not state or state.get("step") != "phone":
            return

        phone = None
        if message.content_type == "contact" and message.contact:
            if message.contact.user_id == user.id:
                phone = message.contact.phone_number
        elif message.content_type == "text":
            text = message.text.strip()
            if text.startswith("/"):
                _pending.pop(user.id, None)
                bot.send_message(
                    message.chat.id,
                    "Оформление отменено.",
                    reply_markup=types.ReplyKeyboardRemove(),
                )
                return
            phone = _normalize_phone(text)

        if not phone:
            bot.send_message(
                message.chat.id,
                "Не увидел номер. Отправьте телефон кнопкой ниже.",
            )
            bot.register_next_step_handler(message, process_phone)
            return

        state["phone"] = phone
        state["step"] = "method"
        bot.send_message(
            message.chat.id,
            "Шаг 2/4. Как вам удобнее получить заказ?",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏃 Самовывоз", callback_data="delivery_pickup"),
            types.InlineKeyboardButton("🛵 Доставка", callback_data="delivery_delivery"),
        )
        bot.send_message(
            message.chat.id, "Выберите способ получения:", reply_markup=markup
        )

    def process_address(message):
        state = _pending.get(message.from_user.id)
        if not state or state.get("step") != "address":
            return
        if message.content_type != "text":
            bot.send_message(message.chat.id, "Напишите адрес текстом:")
            bot.register_next_step_handler(message, process_address)
            return

        address = message.text.strip()
        if not 5 <= len(address) <= 200:
            bot.send_message(
                message.chat.id,
                "Адрес слишком короткий или длинный. Напишите подробнее:",
            )
            bot.register_next_step_handler(message, process_address)
            return

        state["address"] = address
        state["step"] = "comment"
        ask_comment(message.chat.id)

    def process_comment(message):
        state = _pending.get(message.from_user.id)
        if not state or state.get("step") != "comment":
            return

        text = message.text.strip() if message.content_type == "text" else ""
        if not text:
            bot.send_message(message.chat.id, "Напишите комментарий текстом или «-»:")
            bot.register_next_step_handler(message, process_comment)
            return

        state["comment"] = "" if text == "-" else text[:300]
        state["step"] = "confirm"
        send_summary(message.chat.id, message.from_user.id)

    @bot.callback_query_handler(func=lambda call: call.data == "checkout")
    def start_checkout(call):
        user = call.from_user

        if call.message.chat.type != "private":
            bot.answer_callback_query(
                call.id, "Оформить заказ можно в личных сообщениях с ботом."
            )
            return

        if not _is_working_now():
            bot.answer_callback_query(
                call.id,
                "Принимаем заказы с "
                f"{config.WORK_START.strftime('%H:%M')} до "
                f"{config.WORK_END.strftime('%H:%M')}.",
                show_alert=True,
            )
            return

        if not cart_service.get_items(user.id):
            bot.answer_callback_query(call.id, "Корзина пуста")
            return

        _pending[user.id] = {"step": "phone"}
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup.add(types.KeyboardButton("📱 Отправить телефон", request_contact=True))
        bot.send_message(
            call.message.chat.id,
            "Шаг 1/4. Отправьте номер телефона кнопкой ниже:",
            reply_markup=markup,
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_phone)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(
        func=lambda call: call.data in ("delivery_pickup", "delivery_delivery")
    )
    def choose_delivery(call):
        state = _pending.get(call.from_user.id)
        if not state or state.get("step") != "method":
            bot.answer_callback_query(
                call.id, "Начните оформление заново из корзины."
            )
            return

        if call.data == "delivery_pickup":
            state["method"] = "pickup"
            state["address"] = None
            state["step"] = "comment"
            bot.answer_callback_query(call.id, "Самовывоз")
            ask_comment(call.message.chat.id)
        else:
            state["method"] = "delivery"
            state["step"] = "address"
            bot.answer_callback_query(call.id, "Доставка")
            bot.send_message(
                call.message.chat.id, "Шаг 3/4. Напишите адрес доставки:"
            )
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id, process_address
            )

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_order")
    def confirm_order(call):
        user = call.from_user
        state = _pending.get(user.id)
        if not state or state.get("step") != "confirm":
            bot.answer_callback_query(call.id, "Сессия оформления устарела.")
            return

        order = cart_service.checkout(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            state["phone"],
            state["method"],
            state.get("address"),
            state.get("comment") or None,
        )
        _pending.pop(user.id, None)

        if not order:
            bot.answer_callback_query(call.id, "Корзина пуста")
            return

        full_order = order_service.get_order(order["order_id"])

        if config.ADMIN_CHAT_ID:
            try:
                bot.send_message(
                    config.ADMIN_CHAT_ID,
                    order_views.build_order_text(full_order),
                    reply_markup=order_views.build_status_keyboard(full_order),
                )
            except Exception:
                logger.exception("Не удалось отправить заказ админу")
        else:
            logger.warning(
                "ADMIN_CHAT_ID не задан: заказ №%s не отправлен",
                order["order_id"],
            )

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "📞 Связаться с нами", url="https://wa.me/77002478746"
            ),
            types.InlineKeyboardButton("🔙 В меню", callback_data="menu"),
        )
        bot.send_message(
            call.message.chat.id,
            f"✅ Заказ №{order['order_id']} принят!\n\n"
            f"Сумма: {order['total']}₸\n"
            "Мы свяжемся с вами для подтверждения.",
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
    def cancel_order(call):
        _pending.pop(call.from_user.id, None)
        bot.answer_callback_query(call.id, "Отменено")
        bot.send_message(call.message.chat.id, "Оформление отменено.")
