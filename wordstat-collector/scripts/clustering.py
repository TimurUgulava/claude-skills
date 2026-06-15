#!/usr/bin/env python3
"""
Кластеризация ключей по топу Яндекса через Pixel Tools /api/gruppirovka.

Группирует ключи по SERP-сходству: если у двух запросов достаточно общих URL в
топ-10 Яндекса — они попадают в один кластер. Это стандартный для рунета способ
понять, какие запросы поисковик считает одной темой (и, значит, ждёт одну страницу).

Каждый кластер = потенциально одна страница / один крупный раздел.

Usage:
    python scripts/clustering.py <keys_enriched.json> <input-brief.md> <output_clusters.json>
        [--method 3] [--degree 3] [--lr 213] [--min-overall 10]

method: 0=soft, 1=middle, 2=hard, 3=pixeltools (default)
degree: 1-10, глубина кластеризации (default 3)
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
MAX_WAIT_SEC = 1800


def extract_lr_from_brief(brief_path: Path) -> int:
    text = brief_path.read_text(encoding="utf-8")
    m = re.search(r"[Кк]од\s*lr[^\d]*(\d+)", text) or re.search(r"lr\s*[=:]\s*(\d+)", text)
    return int(m.group(1)) if m else 213


def collect_queries(keys_data: dict, min_overall: int = 0) -> list[str]:
    queries: list[str] = []
    for cat_id, cat in keys_data.items():
        if not isinstance(cat, dict) or "keys" not in cat:
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            if not q or q in queries:
                continue
            ws = k.get("wordstat", {})
            if min_overall > 0 and ws.get("overall", 0) < min_overall:
                continue
            queries.append(q)
    return queries


def submit_clustering(queries: list[str], lr: int, method: int, degree: int, rel_url: str | None) -> str:
    from urllib.parse import urlencode
    body_pairs = [("lr", str(lr)), ("method", str(method)), ("degree_group", str(degree)), ("home_pages", "true")]
    if rel_url:
        body_pairs.append(("rel_url", rel_url))
    body_pairs.extend(("requests[]", q) for q in queries)
    body = urlencode(body_pairs)
    r = httpx.post(
        f"{API_BASE}/gruppirovka?key={API_KEY}",
        content=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()
    resp = r.json()
    if isinstance(resp, list) and resp and "report_id" in resp[0]:
        return str(resp[0]["report_id"])
    if isinstance(resp, dict) and "report_id" in resp:
        return str(resp["report_id"])
    raise RuntimeError(f"Неожиданный ответ: {resp}")


def poll_clustering(report_id: str) -> dict:
    # Pixel Tools возвращает "In progress" и как list, и как dict — обрабатываем оба формата.
    # Без dict-проверки скрипт выходил до завершения задачи с пустым результатом.
    waited = 0
    while waited < MAX_WAIT_SEC:
        r = httpx.get(f"{API_BASE}/gruppirovka?key={API_KEY}&report_id={report_id}", timeout=60)
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
            print(f"  кластеризация в процессе: {progress}% (прошло {waited}с)", file=sys.stderr)
            time.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            continue

        return data[0] if isinstance(data, list) and len(data) == 1 else {"result": data}

    raise TimeoutError(f"Кластеризация не завершилась за {MAX_WAIT_SEC}с")


def parse_clusters(raw: dict) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = {}
    result_data = raw.get("result", raw)
    if isinstance(result_data, list):
        source = result_data
    elif isinstance(result_data, dict):
        source = [v for k, v in result_data.items() if str(k).isdigit()]
        if not source:
            source = [result_data]
    else:
        source = []

    for item in source:
        if not isinstance(item, dict):
            continue
        query = item.get("request") or item.get("query")
        group = item.get("group") or item.get("cluster")
        if query and group:
            clusters.setdefault(str(group), []).append(query)
    return clusters


def build_frequency_lookup(keys_data: dict) -> dict[str, int]:
    """Build {query: overall_frequency} lookup from keys_enriched.json."""
    freq: dict[str, int] = {}
    for cat_id, cat in keys_data.items():
        if not isinstance(cat, dict) or "keys" not in cat:
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            if not q:
                continue
            ws = k.get("wordstat", {})
            overall = ws.get("overall", 0) or 0
            freq[q] = max(freq.get(q, 0), overall)
    return freq


def enrich_clusters_list(clusters: dict[str, list[str]], freq_lookup: dict[str, int]) -> list[dict]:
    """Convert clusters dict to enriched list with representative_keyword and total_frequency."""
    result = []
    for cluster_id, queries in clusters.items():
        # Sort queries by frequency descending
        sorted_queries = sorted(queries, key=lambda q: freq_lookup.get(q, 0), reverse=True)
        rep_keyword = sorted_queries[0] if sorted_queries else ""
        total_freq = sum(freq_lookup.get(q, 0) for q in queries)
        result.append({
            "id": cluster_id,
            "representative_keyword": rep_keyword,
            "size": len(queries),
            "total_frequency": total_freq,
            "keywords": sorted_queries
        })
    result.sort(key=lambda c: c["total_frequency"], reverse=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys_path")
    parser.add_argument("brief_path")
    parser.add_argument("output_path")
    parser.add_argument("--method", type=int, default=3)
    parser.add_argument("--degree", type=int, default=3)
    parser.add_argument("--lr", type=int)
    parser.add_argument("--min-overall", type=int, default=0, help="Минимальная Wordstat-частотность, ниже — не включаем")
    parser.add_argument("--rel-url", help="Фильтр по домену (site:domain) — для проверки каннибализации")
    args = parser.parse_args()

    if not API_KEY:
        print("ОШИБКА: PIXELTOOLS_API_KEY не задан", file=sys.stderr)
        return 1

    keys_data = json.loads(Path(args.keys_path).read_text(encoding="utf-8"))
    lr = args.lr or extract_lr_from_brief(Path(args.brief_path))
    queries = collect_queries(keys_data, min_overall=args.min_overall)

    if len(queries) < 2:
        print(f"ОШИБКА: нужно минимум 2 ключа для кластеризации, найдено {len(queries)}", file=sys.stderr)
        return 1

    print(f"Кластеризация: {len(queries)} ключей, lr={lr}, method={args.method}, degree={args.degree}", file=sys.stderr)
    report_id = submit_clustering(queries, lr, args.method, args.degree, args.rel_url)
    print(f"  report_id={report_id}, ждём (обычно до 3 мин)...", file=sys.stderr)

    raw = poll_clustering(report_id)
    clusters_dict = parse_clusters(raw)

    freq_lookup = build_frequency_lookup(keys_data)
    enriched_list = enrich_clusters_list(clusters_dict, freq_lookup)

    output = {
        "lr": lr,
        "method": args.method,
        "degree": args.degree,
        "total_queries": len(queries),
        "total_clusters": len(enriched_list),
        "clusters": enriched_list,
        "clusters_raw_dict": clusters_dict,
    }
    Path(args.output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nКластеризация сохранена: {args.output_path}", file=sys.stderr)
    print(f"   Кластеров: {len(enriched_list)}", file=sys.stderr)
    print(f"   Топ-5 по объёму запросов:", file=sys.stderr)
    for c in enriched_list[:5]:
        print(f"     • '{c['representative_keyword']}' — {c['size']} запросов, частотность {c['total_frequency']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
