import logging

from telebot import TeleBot

from config import BOT_TOKEN, LOG_LEVEL
from handlers import register_handlers


def main():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Скопируйте .env.example в .env и заполните BOT_TOKEN.")

    bot = TeleBot(BOT_TOKEN)
    register_handlers(bot)

    logger.info("Bot started")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


if __name__ == "__main__":
    main()
