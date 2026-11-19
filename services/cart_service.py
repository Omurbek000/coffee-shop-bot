import json
import logging
import threading

import config

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _load():
    try:
        with open(config.CART_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(key): items for key, items in data.items()}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Файл корзины повреждён, создаю новый")
        return {}


_cart = _load()


def _save():
    with open(config.CART_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {str(key): items for key, items in _cart.items()},
            f,
            ensure_ascii=False,
            indent=2,
        )


def get_items(user_id):
    with _lock:
        return list(_cart.get(user_id, []))


def add_item(user_id, product):
    with _lock:
        _cart.setdefault(user_id, []).append(product)
        _save()


def clear(user_id):
    with _lock:
        _cart[user_id] = []
        _save()


def total(user_id):
    with _lock:
        return sum(item["price"] for item in _cart.get(user_id, []))
