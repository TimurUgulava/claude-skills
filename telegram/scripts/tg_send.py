#!/usr/bin/env python3
"""
Отправка сообщения в чат Telegram. ⚠️ ЕДИНСТВЕННЫЙ скрипт скилла, который пишет.

ПРЕДОХРАНИТЕЛЬ: без флага --yes скрипт работает в режиме СУХОГО ПРОГОНА —
резолвит чат и печатает, что было бы отправлено, но НИЧЕГО НЕ ШЛЁТ.
Реальная отправка только с --yes. Это страховка: нет --yes -> нет сообщения.

Флаг --yes по протоколу скилла ставится ТОЛЬКО после явного согласия пользователя.

Usage:
    # сухой прогон (безопасно, ничего не уходит):
    python3 tg_send.py --chat <id|@username> --text "сообщение"
    # реальная отправка (после согласования):
    python3 tg_send.py --chat <id|@username> --text "сообщение" --yes
    # длинный текст из файла:
    python3 tg_send.py --chat <id|@username> --file path/to/message.txt --yes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tg_common import get_client, dialog_type  # noqa: E402


def parse_chat(value):
    v = value.strip()
    if v.startswith("@") or not (v.lstrip("-").isdigit()):
        return v
    return int(v)


def peer_id(entity, fallback):
    """Тот же маркированный id, что отдаёт tg_resolve.py (-100… для каналов)."""
    try:
        from telethon import utils
        return utils.get_peer_id(entity)
    except Exception:
        return getattr(entity, "id", fallback)


def main():
    ap = argparse.ArgumentParser(description="Отправка сообщения (по умолчанию — сухой прогон)")
    ap.add_argument("--chat", required=True, help="id чата или @username")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="текст сообщения")
    g.add_argument("--file", help="путь к файлу с текстом сообщения")
    ap.add_argument("--yes", action="store_true",
                    help="РЕАЛЬНО отправить. Без него — только сухой прогон.")
    args = ap.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            sys.exit(f"[tg_send] Не удалось прочитать файл: {e}")
    else:
        text = args.text
    if not text or not text.strip():
        sys.exit("[tg_send] Пустой текст — отправлять нечего.")

    chat = parse_chat(args.chat)
    with get_client() as client:
        entity = client.get_entity(chat)
        title = getattr(entity, "title", None) or \
            (" ".join(filter(None, [getattr(entity, "first_name", None),
                                    getattr(entity, "last_name", None)])) or str(chat))
        ctype = dialog_type(entity)
        pid = peer_id(entity, chat)

        if not args.yes:
            # Карточка согласования в формате протокола SKILL.md — показывай пользователю 1:1.
            print("📤 Готов отправить:")
            print(f"Чат:  «{title}»  (тип: {ctype}, id: {pid})")
            print("Текст:")
            print(text)
            print()
            print("⚠️ Сухой прогон — сообщение НЕ отправлено. После явного «да» от пользователя — повтори с --yes.")
            return

        msg = client.send_message(entity, text)
        print(f"[tg_send] ОТПРАВЛЕНО в «{title}» (id: {pid}), message_id = {msg.id}")


if __name__ == "__main__":
    main()
