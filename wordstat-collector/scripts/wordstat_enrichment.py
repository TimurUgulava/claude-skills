#!/usr/bin/env python3
"""
Обогащение семантического ядра частотностью Wordstat через Pixel Tools API.

Для каждого ключа из keys.json получает:
- overall — общая частотность (широкое соответствие)
- exact — точная "!слово" частотность
- quoted — частотность в кавычках "..."

Частотность — по конкретному региону из input-brief.md (lr).

Ключи с overall < порога помечаются как low_freq и могут быть исключены.

Usage:
    python scripts/wordstat_enrichment.py <keys.json> <input-brief.md> <output_enriched.json> [--lr 213] [--min-freq 10]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("ОШИБКА: pip install httpx python-dotenv", file=sys.stderr)
    sys.exit(1)


SKILL_DIR = Path(__file__).parent.parent
load_dotenv(SKILL_DIR / ".env", override=True)

API_BASE = "https://tools.pixelplus.ru/api"
API_KEY = os.getenv("PIXELTOOLS_API_KEY")

POLL_INTERVAL = 20
MAX_WAIT_SEC = 600
BATCH_SIZE = 1000


def extract_lr_from_brief(brief_path: Path) -> int:
    text = brief_path.read_text(encoding="utf-8")
    m = re.search(r"[Кк]од\s*lr[^\d]*(\d+)", text) or re.search(r"lr\s*[=:]\s*(\d+)", text)
    if m:
        return int(m.group(1))
    return 213


def collect_all_queries(keys_data: dict, skip_enriched: bool = True) -> list[str]:
    """Собрать запросы для Wordstat-обогащения.

    Если skip_enriched=True (по умолчанию) — пропустить ключи, у которых уже
    есть поле `wordstat` с ненулевой `overall` (значит, обогащались ранее,
    например через wordstat_expansion). Это экономит лимиты API при повторных
    прогонах пайплайна.
    """
    queries: list[str] = []
    for cat in keys_data.values():
        if not isinstance(cat, dict):
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            if not q or q in queries:
                continue
            if skip_enriched:
                ws = k.get("wordstat")
                if isinstance(ws, dict) and (int(ws.get("overall") or 0) > 0 or k.get("source") == "wordstat_expansion"):
                    continue
            queries.append(q)
    return queries


def submit_wordstat(queries: list[str], lr: int) -> str:
    from urllib.parse import urlencode
    body_pairs = [("lr", str(lr)), ("overall", "1"), ("exact", "1"), ("quoted", "1"), ("delete_special_characters", "1")]
    body_pairs.extend(("requests[]", q) for q in queries)
    body = urlencode(body_pairs)
    r = httpx.post(
        f"{API_BASE}/wordstatapi?key={API_KEY}",
        content=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()
    resp = r.json()
    if isinstance(resp, dict) and "report_id" in resp:
        return str(resp["report_id"])
    if isinstance(resp, list) and resp and "report_id" in resp[0]:
        return str(resp[0]["report_id"])
    raise RuntimeError(f"Неожиданный ответ при создании задачи: {resp}")


def poll_result(report_id: str) -> dict:
    waited = 0
    while waited < MAX_WAIT_SEC:
        r = httpx.get(f"{API_BASE}/wordstatapi?key={API_KEY}&report_id={report_id}", timeout=60)
        r.raise_for_status()
        data = r.json()

        in_progress = False
        progress = 0
        if isinstance(data, dict) and data.get("error") == "In progress":
            in_progress = True
            progress = data.get("progress", 0)
        elif isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("error") == "In progress":
            in_progress = True
            progress = data[0].get("progress", 0)

        if in_progress:
            print(f"  в процессе: {progress}% (прошло {waited}с)", file=sys.stderr)
            time.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            continue

        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return data

    raise TimeoutError(f"Wordstat не ответил за {MAX_WAIT_SEC}с (report_id={report_id})")


def parse_result(result: dict, lr: int) -> dict[str, dict]:
    parsed: dict[str, dict] = {}
    for query, regions in result.items():
        if query == "periods":
            continue
        if not isinstance(regions, dict):
            continue
        lr_data = regions.get(str(lr)) or regions.get(lr)
        if not isinstance(lr_data, dict):
            continue
        parsed[query] = {
            "overall": lr_data.get("overall", 0),
            "exact": lr_data.get("exact", 0),
            "quoted": lr_data.get("quoted", 0),
        }
    return parsed


def enrich_keys(keys_data: dict, freq_map: dict[str, dict], min_freq: int) -> dict:
    total_enriched = 0
    total_zero = 0
    total_preserved = 0
    for cat_id, cat in keys_data.items():
        if not isinstance(cat, dict):
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            existing = k.get("wordstat") if isinstance(k.get("wordstat"), dict) else None
            if existing and (int(existing.get("overall") or 0) > 0 or k.get("source") == "wordstat_expansion"):
                # уже обогащён ранее — не трогаем
                k["low_freq"] = int(existing.get("overall") or 0) < min_freq
                total_preserved += 1
                continue
            freq = freq_map.get(q, {"overall": 0, "exact": 0, "quoted": 0})
            k["wordstat"] = freq
            k["low_freq"] = freq["overall"] < min_freq
            total_enriched += 1
            if freq["overall"] == 0:
                total_zero += 1
    keys_data["_wordstat_meta"] = {
        "enriched": total_enriched,
        "preserved_already_enriched": total_preserved,
        "zero_frequency": total_zero,
        "min_freq_threshold": min_freq,
    }
    return keys_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys_path")
    parser.add_argument("brief_path")
    parser.add_argument("output_path")
    parser.add_argument("--lr", type=int, help="Yandex region code (default: из brief)")
    parser.add_argument("--min-freq", type=int, default=10, help="Минимальная overall-частотность (default: 10)")
    args = parser.parse_args()

    if not API_KEY:
        print("ОШИБКА: PIXELTOOLS_API_KEY не задан в .env", file=sys.stderr)
        return 1

    keys_path = Path(args.keys_path)
    brief_path = Path(args.brief_path)
    output_path = Path(args.output_path)

    keys_data = json.loads(keys_path.read_text(encoding="utf-8"))
    lr = args.lr or extract_lr_from_brief(brief_path)

    queries = collect_all_queries(keys_data)
    print(f"Всего ключей: {len(queries)}, регион lr={lr}, порог low_freq={args.min_freq}", file=sys.stderr)

    freq_map: dict[str, dict] = {}
    for i in range(0, len(queries), BATCH_SIZE):
        batch = queries[i : i + BATCH_SIZE]
        print(f"\nBatch {i // BATCH_SIZE + 1}: отправка {len(batch)} ключей...", file=sys.stderr)
        report_id = submit_wordstat(batch, lr)
        print(f"  report_id={report_id}, ждём...", file=sys.stderr)
        result = poll_result(report_id)
        parsed = parse_result(result, lr)
        freq_map.update(parsed)
        print(f"  получено {len(parsed)} частотностей", file=sys.stderr)

    enriched = enrich_keys(keys_data, freq_map, args.min_freq)
    output_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = enriched["_wordstat_meta"]
    print(f"\n✅ Сохранено: {output_path}", file=sys.stderr)
    print(f"   Обогащено: {meta['enriched']}", file=sys.stderr)
    print(f"   С нулевой частотностью: {meta['zero_frequency']}", file=sys.stderr)
    print(f"   Ниже порога {args.min_freq}: {sum(1 for c in enriched.values() if isinstance(c, dict) for k in c.get('keys', []) if k.get('low_freq'))}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
