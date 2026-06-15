#!/usr/bin/env python3
"""
Проверяет доступность Pixel Tools API и наличие лимитов.
Запускается один раз после установки ключа.

Usage:
    python scripts/smoke_test.py

Exit codes:
    0 — PIXELTOOLS_API_KEY работает
    1 — ключа нет или не работает
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("ОШИБКА: pip install httpx python-dotenv")
    sys.exit(1)


SKILL_DIR = Path(__file__).parent.parent
load_dotenv(SKILL_DIR / ".env")

API_BASE = "https://tools.pixelplus.ru/api"


def check_pixeltools_main() -> tuple[bool, str]:
    """Проверка Pixel Tools через метод getlimits."""
    key = os.getenv("PIXELTOOLS_API_KEY")
    if not key or key in ("...", ""):
        return False, "не задан или placeholder"

    try:
        resp = httpx.get(f"{API_BASE}/getlimits?key={key}", timeout=15)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

        data = resp.json()
        if isinstance(data, list):
            data = data[0] if data else {}
        if "error" in data:
            return False, f"API ошибка: {data['error']}"

        left = data.get("limits_left") or data.get("left") or data.get("available")
        total = data.get("limits_total") or data.get("total")
        if left is not None:
            return True, f"работает. Лимитов осталось: {left}" + (f"/{total}" if total else "")
        return True, f"работает. Ответ: {str(data)[:100]}"
    except httpx.HTTPError as e:
        return False, f"ошибка запроса: {e}"


def check_deps() -> list[tuple[str, bool]]:
    deps = []
    for mod in ("httpx", "dotenv", "rapidfuzz", "openpyxl"):
        try:
            __import__(mod)
            deps.append((mod, True))
        except ImportError:
            deps.append((mod, False))
    return deps


def main() -> int:
    print("=" * 60)
    print("wordstat-collector — smoke test")
    print("=" * 60)

    ok, msg = check_pixeltools_main()
    symbol = "OK" if ok else "FAIL"
    print(f"[{symbol}] PIXELTOOLS_API_KEY (tools.pixelplus.ru): {msg}")

    print()
    print("Python-зависимости:")
    for mod, present in check_deps():
        print(f"[{'OK' if present else 'FAIL'}] {mod}")

    print()
    if ok:
        print("Готово к работе.")
        return 0
    else:
        print("Сбор не пойдёт без рабочего PIXELTOOLS_API_KEY.")
        print("Положи ключ в файл:", SKILL_DIR / ".env")
        return 1


if __name__ == "__main__":
    sys.exit(main())
