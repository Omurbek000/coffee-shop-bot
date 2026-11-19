# ☕ Coffee Shop Bot

Telegram-бот для кофейни: меню, корзина, оформление заказа с доставкой или самовывозом, админ-панель и статистика.

## Возможности

- Меню по категориям с ценами (хранится в SQLite, засев из `data/menu.json`)
- Корзина с количеством товаров
- Оформление заказа: телефон (кнопкой «отправить контакт») → самовывоз/доставка + адрес → комментарий → подтверждение
- Проверка часов приёма заказов (`WORK_START` / `WORK_END`)
- Админ получает карточку заказа с кнопками статусов, клиент — уведомления о смене статуса
- Админ-команды `/orders` и `/stats`
- Отзывы (пересылаются админу), `/wifi`, контакты, о нас

## Структура

```
coffee-shop-bot/
├── bot.py                  # точка входа
├── config.py               # настройки из .env
├── db.py                   # схема SQLite и миграции
├── data/
│   ├── menu.json           # исходное меню для засева
│   └── coffee_shop.db      # база (создаётся автоматически)
├── handlers/
│   ├── menu.py             # меню и карточки товаров
│   ├── cart.py             # корзина
│   ├── order.py            # оформление заказа (FSM)
│   ├── order_views.py      # карточка заказа и клавиатура статусов
│   ├── admin.py            # /orders, /stats, смена статусов
│   └── info.py             # о нас, контакты, Wi-Fi, отзывы
├── services/
│   ├── menu_service.py     # работа с каталогом
│   ├── cart_service.py     # корзина и создание заказа
│   └── order_service.py    # заказы, статусы, статистика
├── scripts/
│   ├── seed_db.py          # перезаливка меню в БД
│   └── backup_db.py        # бэкап базы
├── Dockerfile
└── docker-compose.yml
```

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env        # Linux/macOS: cp .env.example .env
# заполните BOT_TOKEN и ADMIN_CHAT_ID

python bot.py
```

- `BOT_TOKEN` — у [@BotFather](https://t.me/BotFather) (`/newbot`).
- `ADMIN_CHAT_ID` — свой ID можно узнать у [@userinfobot](https://t.me/userinfobot). Без него бот работает, но заказы и отзывы никуда не приходят (только в лог).

При первом запуске база создаётся автоматически и меню засевается из `data/menu.json`. Принудительная перезаливка меню:

```bash
python scripts/seed_db.py
```

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | токен бота (обязательно) | — |
| `ADMIN_CHAT_ID` | Telegram ID админа | пусто |
| `LOG_LEVEL` | уровень логов | `INFO` |
| `WORK_START` | начало приёма заказов | `07:30` |
| `WORK_END` | конец приёма заказов | `23:00` |
| `WIFI_LOGIN` | логин Wi-Fi | пусто |
| `WIFI_PASSWORD` | пароль Wi-Fi | пусто |

## Команды

- `/start` — главное меню
- `/menu` — меню кофейни
- `/wifi` — данные Wi-Fi
- `/orders` — заказы за сегодня (админ)
- `/stats` — выручка и топ товаров (админ)

## Статусы заказа

```
new → accepted → ready → done
new / accepted → rejected
```

Клиент получает сообщение при каждой смене статуса.

## Docker

```bash
docker compose up -d --build
docker compose logs -f
```

База и меню монтируются из `./data`, бэкапы — в `./backups`, настройки берутся из `.env`.

## Бэкапы

```bash
python scripts/backup_db.py
```

Скрипт создаёт `backups/coffee_shop_<дата>.db` и хранит 7 последних копий. Пример cron на VPS:

```
0 3 * * * cd /opt/coffee-shop-bot && python scripts/backup_db.py
```

## Лицензия

MIT
