from . import admin, cart, info, menu, order


def register_handlers(bot):
    menu.register(bot)
    cart.register(bot)
    order.register(bot)
    info.register(bot)
    admin.register(bot)

    @bot.callback_query_handler(func=lambda call: True)
    def answer_unknown_callback(call):
        bot.answer_callback_query(call.id)
