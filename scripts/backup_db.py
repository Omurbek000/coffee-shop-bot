import sqlite3
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

BACKUP_DIR = config.BASE_DIR / "backups"
KEEP = 7


def main():
    if not Path(config.DB_FILE).exists():
        print("База не найдена:", config.DB_FILE)
        return

    BACKUP_DIR.mkdir(exist_ok=True)
    target = BACKUP_DIR / f"coffee_shop_{datetime.now():%Y-%m-%d_%H-%M-%S}.db"

    source = sqlite3.connect(config.DB_FILE)
    destination = sqlite3.connect(target)
    try:
        with destination:
            source.backup(destination)
    finally:
        destination.close()
        source.close()

    print("Бэкап создан:", target)

    backups = sorted(BACKUP_DIR.glob("coffee_shop_*.db"))
    for old in backups[:-KEEP]:
        old.unlink()
        print("Удалён старый бэкап:", old)


if __name__ == "__main__":
    main()
