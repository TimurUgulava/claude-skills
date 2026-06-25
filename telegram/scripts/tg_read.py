#!/usr/bin/env python3
"""
Чтение последних N сообщений чата. READ-ONLY — ничего не отправляет.

Usage:
    python3 tg_read.py <chat_id|@username> [--limit 20]

Печатает JSON: список сообщений (дата, отправитель, текст, id) от старых к новым.
chat_id для групп/каналов обычно отрицательный — передавай как есть.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tg_common import get_client  # noqa: E402


def parse_chat(value):
    v = value.strip()
    if v.startswith("@") or not (v.lstrip("-").isdigit()):
        return v
    return int(v)


def main():
    ap = argparse.ArgumentParser(description="Чтение последних сообщений чата (read-only)")
    ap.add_argument("chat", help="id чата или @username")
    ap.add_argument("--limit", type=int, default=20, help="сколько последних сообщений")
    args = ap.parse_args()

    chat = parse_chat(args.chat)
    out = []
    with get_client() as client:
        entity = client.get_entity(chat)
        title = getattr(entity, "title", None) or getattr(entity, "first_name", str(chat))
        msgs = list(client.iter_messages(entity, limit=args.limit))
        for m in reversed(msgs):  # от старых к новым
            sender = None
            try:
                s = m.sender
                if s is not None:
                    sender = getattr(s, "title", None) or \
                        (" ".join(filter(None, [getattr(s, "first_name", None),
                                                getattr(s, "last_name", None)])) or
                         getattr(s, "username", None))
            except Exception:
                pass
            out.append({
                "id": m.id,
                "date": m.date.isoformat() if m.date else None,
                "sender": sender,
                "text": m.message or "",
            })

    print(json.dumps({"chat": title, "messages": out}, ensure_ascii=False, indent=2))
    print(f"[tg_read] чат: {title} · сообщений: {len(out)}", file=sys.stderr)


if __name__ == "__main__":
    main()
