#!/usr/bin/env python3
"""
Общий модуль для telegram-скилла: достаёт ключи и сессию, отдаёт TelegramClient.

Ключи (api_id/api_hash) и путь к сессии НЕ хардкодятся как секреты:
- api_id/api_hash: из переменных окружения TG_API_ID/TG_API_HASH, иначе из macOS Keychain
  (services: tg-api-id / tg-api-hash).
- сессия: из TG_SESSION, иначе дефолтный путь к уже авторизованной сессии.

Сессия одна на аккаунт намеренно — это одна пройденная авторизация,
дублировать секрет нельзя. См. references/setup.md.
"""
import os
import subprocess
import sys

# Дефолтный путь к авторизованной Telethon-сессии (без расширения .session).
DEFAULT_SESSION = "~/.tg/tg_session"
KEYCHAIN_ID_SERVICE = "tg-api-id"
KEYCHAIN_HASH_SERVICE = "tg-api-hash"


def _keychain(service):
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", service,
             "-a", os.environ.get("USER", ""), "-w"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return None


def get_credentials():
    api_id = os.environ.get("TG_API_ID") or _keychain(KEYCHAIN_ID_SERVICE)
    api_hash = os.environ.get("TG_API_HASH") or _keychain(KEYCHAIN_HASH_SERVICE)
    if not api_id or not api_hash:
        sys.exit(
            "[telegram] Нет ключей API. Ожидаю TG_API_ID/TG_API_HASH в окружении "
            "или в Keychain (tg-api-id / tg-api-hash). См. references/setup.md"
        )
    try:
        api_id = int(api_id)
    except ValueError:
        sys.exit("[telegram] TG_API_ID должен быть числом.")
    return api_id, api_hash


def get_session():
    return os.environ.get("TG_SESSION", DEFAULT_SESSION)


def get_client():
    try:
        from telethon.sync import TelegramClient
    except ImportError:
        sys.exit("[telegram] Не установлен telethon. Поставь: pip3 install telethon")
    api_id, api_hash = get_credentials()
    return TelegramClient(get_session(), api_id, api_hash)


def dialog_type(entity):
    cls = entity.__class__.__name__
    if cls == "User":
        return "личка"
    if cls == "Chat":
        return "группа"
    if cls == "Channel":
        return "канал" if getattr(entity, "broadcast", False) else "супергруппа"
    return cls
