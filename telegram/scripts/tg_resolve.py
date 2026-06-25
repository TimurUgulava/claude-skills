#!/usr/bin/env python3
"""
Поиск чатов по подстроке названия. READ-ONLY — ничего не отправляет и не меняет.

Usage:
    python3 tg_resolve.py "<запрос>" [--limit 300]

Печатает JSON со списком совпавших диалогов: id, title, type, username.
Если запрос пустой — ошибка (не вываливаем весь список диалогов: приватность).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tg_common import get_client, dialog_type  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Поиск чатов по названию (read-only)")
    ap.add_argument("query", help="подстрока названия чата (регистронезависимо)")
    ap.add_argument("--limit", type=int, default=300, help="сколько диалогов просмотреть")
    args = ap.parse_args()

    q = (args.query or "").strip().lower()
    if not q:
        sys.exit("[tg_resolve] Пустой запрос. Укажи подстроку названия чата.")

    matches = []
    with get_client() as client:
        for d in client.iter_dialogs(limit=args.limit):
            name = d.name or ""
            if q in name.lower():
                ent = d.entity
                matches.append({
                    "id": d.id,
                    "title": name,
                    "type": dialog_type(ent),
                    "username": getattr(ent, "username", None),
                })

    print(json.dumps(matches, ensure_ascii=False, indent=2))
    print(f"[tg_resolve] совпадений: {len(matches)}", file=sys.stderr)


if __name__ == "__main__":
    main()
