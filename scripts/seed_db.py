import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db
from services import menu_service


def main():
    db.init_db()
    menu_service.reseed_from_json()
    categories = menu_service.get_categories()
    print(
        f"Готово: {len(categories)} категорий, {menu_service.count_products()} товаров"
    )


if __name__ == "__main__":
    main()
