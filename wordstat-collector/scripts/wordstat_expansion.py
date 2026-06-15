#!/usr/bin/env python3
"""
Расширение семантического ядра через Pixel Tools `wordstatapikeywords`.

Для каждого «живого» seed-ключа (wordstat.overall ≥ порога) через Wordstat-парсер
Pixel Tools снимаются связанные фразы из левой колонки Wordstat (до 41 страницы).
Возвращённые фразы уже идут с частотностями по заданному региону — дополнительное
обогащение для них не нужно.

Seeds выбираются автоматически из «живых» ключей входного JSON либо задаются вручную
через `--seed` (повторяется). Ручные seeds важны, когда ядро целиком состоит из
фантомных запросов и «живых» broad-ключей в нём нет — тогда можно подать пустой
`keys.json` (`{}`) и передать маркер через `--seed`.

Новые фразы (не пересекающиеся с исходным ядром по фаззи-матчу) кладутся в плоский
массив `_pending_classification` внутри keys_data — без категорий и без relevance.
Классификация в 6 категорий и оценка релевантности — работа Claude в сессии (читает
JSON, заполняет keys в нужных категориях, удаляет _pending_classification).

Usage:
    python scripts/wordstat_expansion.py <keys_enriched.json> <input-brief.md> <output_expanded.json> \
        [--lr 213] [--seed "запрос"] [--max-seeds 15] [--min-seed-freq 50] \
        [--count-pages 10] [--min-overall 10] [--max-new-keys 200]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    import httpx
    from dotenv import load_dotenv
    from rapidfuzz import fuzz
except ImportError:
    print("ОШИБКА: pip install httpx python-dotenv rapidfuzz", file=sys.stderr)
    sys.exit(1)


SKILL_DIR = Path(__file__).parent.parent
load_dotenv(SKILL_DIR / ".env", override=True)

PIXEL_API_BASE = "https://tools.pixelplus.ru/api"
PIXEL_KEY = os.getenv("PIXELTOOLS_API_KEY")

CONCURRENCY = 5          # лимит API Pixel Tools: не больше 5 активных задач
POLL_INTERVAL = 20
MAX_WAIT_SEC = 600
FUZZY_THRESHOLD = 88     # дедуп относительно существующего ядра

CATEGORY_META = {
    1: {"emoji": "🛒", "name": "Коммерческие", "description": "Запросы с коммерческим намерением, указывающие на готовность к покупке."},
    2: {"emoji": "📖", "name": "Информационные", "description": "Запросы на поиск информации: «что такое», «как работает», определения."},
    3: {"emoji": "🎯", "name": "Long-tail", "description": "Длинные (3+ слов) специфические запросы с низкой частотностью и высокой конверсией."},
    4: {"emoji": "🔍", "name": "SEO-основные", "description": "Базовые высокочастотные запросы, идущие в title/H1/H2."},
    5: {"emoji": "🧠", "name": "LSI / семантические", "description": "Расширение семантического контекста темы, ожидаемое поисковиками и AI."},
    6: {"emoji": "🔬", "name": "Верхнего уровня", "description": "Абстрактные темы и концепты верхнего уровня, формулируемые LLM."},
}


# ---------------------------------------------------------------- utils

def extract_lr_from_brief(brief_path: Path, default: int = 213) -> int:
    text = brief_path.read_text(encoding="utf-8")
    m = re.search(r"[Кк]од\s*lr[^\d]*(\d+)", text) or re.search(r"\blr\s*[=:]\s*(\d+)", text)
    return int(m.group(1)) if m else default


def normalize(phrase: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", phrase.lower())).strip()


def existing_keys_set(keys_data: dict) -> list[str]:
    out: list[str] = []
    for cat in keys_data.values():
        if not isinstance(cat, dict):
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            if q:
                out.append(q)
    return out


def is_duplicate(phrase: str, existing_normalized: list[str]) -> bool:
    norm = normalize(phrase)
    if not norm:
        return True
    for e in existing_normalized:
        if fuzz.ratio(norm, e) >= FUZZY_THRESHOLD:
            return True
    return False


def pick_seeds(keys_data: dict, max_seeds: int, min_seed_freq: int) -> list[str]:
    """Выбор seeds для расширения.

    Приоритет 1: живые ключи (wordstat.overall ≥ min_seed_freq) из SEO-основных
      и коммерческих, отсортированные по частотности убыванию.
    Приоритет 2 (fallback, если enrichment ещё не прогонялся — поля wordstat нет):
      ключи с relevance ≥ 0.9 из тех же категорий.

    ВНИМАНИЕ: если в ядре после enrichment «живых» ключей нет, функция вернёт пустой
    список — это означает, что seed нужно передать через --seed вручную.
    """
    live_candidates: list[tuple[int, str]] = []
    fallback_candidates: list[tuple[float, str]] = []
    any_enriched = False

    for cat_id in ("4", "1"):
        cat = keys_data.get(cat_id)
        if not isinstance(cat, dict):
            continue
        for k in cat.get("keys", []):
            q = k.get("query", "").strip()
            if not q:
                continue
            ws = k.get("wordstat")
            if isinstance(ws, dict):
                any_enriched = True
                overall = int(ws.get("overall", 0) or 0)
                if overall >= min_seed_freq:
                    live_candidates.append((overall, q))
            rel = float(k.get("relevance", 0))
            if rel >= 0.9:
                fallback_candidates.append((rel, q))

    if live_candidates:
        live_candidates.sort(key=lambda x: -x[0])
        source = live_candidates
    elif not any_enriched:
        fallback_candidates.sort(key=lambda x: -x[0])
        source = [(int(r * 1000), q) for r, q in fallback_candidates]
        print("⚠️  Ядро не прогонялось через wordstat_enrichment — использую fallback по relevance", file=sys.stderr)
    else:
        return []

    seen: set[str] = set()
    picked: list[str] = []
    for _, q in source:
        norm = normalize(q)
        if norm in seen:
            continue
        seen.add(norm)
        picked.append(q)
        if len(picked) >= max_seeds:
            break
    return picked


# ---------------------------------------------------------------- Pixel Tools API

async def submit_expansion(
    client: httpx.AsyncClient, seed: str, lr: int, count_pages: int, min_overall: int
) -> tuple[str, str]:
    """Отправляет seed в wordstatapikeywords, возвращает (seed, report_id)."""
    body_pairs = [
        ("lr", str(lr)),
        ("overall", "1"),
        ("exact", "1"),
        ("quoted", "1"),
        ("count_pages", str(count_pages)),
        ("delete_zero_keywords", "1"),
        ("delete_special_characters", "1"),
        ("min_overall_frequency", str(min_overall)),
        ("requests[]", seed),
    ]
    body = urlencode(body_pairs)
    r = await client.post(
        f"{PIXEL_API_BASE}/wordstatapikeywords?key={PIXEL_KEY}",
        content=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()
    resp = r.json()
    if isinstance(resp, dict) and "report_id" in resp:
        return seed, str(resp["report_id"])
    if isinstance(resp, list) and resp and "report_id" in resp[0]:
        return seed, str(resp[0]["report_id"])
    raise RuntimeError(f"Неожиданный ответ при создании задачи для «{seed}»: {resp}")


async def poll_expansion(client: httpx.AsyncClient, seed: str, report_id: str) -> dict:
    waited = 0
    while waited < MAX_WAIT_SEC:
        r = await client.get(
            f"{PIXEL_API_BASE}/wordstatapikeywords?key={PIXEL_KEY}&report_id={report_id}",
            timeout=60,
        )
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
            print(f"  [{seed[:40]}] в процессе: {progress}% (прошло {waited}с)", file=sys.stderr)
            await asyncio.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            continue

        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return data

    raise TimeoutError(f"Seed «{seed}»: не ответил за {MAX_WAIT_SEC}с (report_id={report_id})")


def parse_expansion(data: dict, lr: int) -> list[dict]:
    """Вернуть список {query, overall, exact, quoted} из ответа wordstatapikeywords."""
    results: list[dict] = []
    if not isinstance(data, dict):
        return results
    for phrase, regions in data.items():
        if phrase == "periods":
            continue
        if not isinstance(regions, dict):
            continue
        lr_data = regions.get(str(lr)) or regions.get(lr)
        if not isinstance(lr_data, dict):
            continue
        results.append({
            "query": phrase.strip(),
            "overall": int(lr_data.get("overall", 0) or 0),
            "exact": int(lr_data.get("exact", 0) or 0),
            "quoted": int(lr_data.get("quoted", 0) or 0),
        })
    return results


async def run_expansion_for_seed(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    seed: str,
    lr: int,
    count_pages: int,
    min_overall: int,
) -> list[dict]:
    async with sem:
        try:
            _, report_id = await submit_expansion(client, seed, lr, count_pages, min_overall)
            print(f"  [{seed[:40]}] report_id={report_id}", file=sys.stderr)
            data = await poll_expansion(client, seed, report_id)
            parsed = parse_expansion(data, lr)
            print(f"  [{seed[:40]}] → {len(parsed)} фраз", file=sys.stderr)
            return [{**row, "source_seed": seed} for row in parsed]
        except Exception as e:
            print(f"  [{seed[:40]}] ОШИБКА: {e}", file=sys.stderr)
            return []


# ---------------------------------------------------------------- main

async def run(args: argparse.Namespace) -> int:
    keys_path = Path(args.keys_path)
    brief_path = Path(args.brief_path)
    output_path = Path(args.output_path)

    if not PIXEL_KEY:
        print("ОШИБКА: PIXELTOOLS_API_KEY не задан в .env", file=sys.stderr)
        return 1

    keys_data = json.loads(keys_path.read_text(encoding="utf-8"))
    lr = args.lr or extract_lr_from_brief(brief_path)

    auto_seeds = pick_seeds(keys_data, args.max_seeds, args.min_seed_freq)
    manual_seeds = [s.strip() for s in (args.seed or []) if s.strip()]

    seeds_seen: set[str] = set()
    seeds: list[str] = []
    for s in manual_seeds + auto_seeds:
        n = normalize(s)
        if n and n not in seeds_seen:
            seeds_seen.add(n)
            seeds.append(s)
        if len(seeds) >= args.max_seeds:
            break

    if not seeds:
        print(
            "ОШИБКА: ни одного seed. В ядре нет ключей с wordstat.overall ≥ "
            f"{args.min_seed_freq}. Передай seeds вручную через --seed \"...\" (можно несколько раз).",
            file=sys.stderr,
        )
        return 1

    print(f"Seeds ({len(seeds)}):", file=sys.stderr)
    for s in seeds:
        print(f"  • {s}", file=sys.stderr)
    print(f"Регион lr={lr}, count_pages={args.count_pages}, min_overall={args.min_overall}", file=sys.stderr)

    existing_raw = existing_keys_set(keys_data)
    existing_normalized = [normalize(q) for q in existing_raw]

    # 1. Параллельный сбор расширений
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [
            run_expansion_for_seed(sem, client, s, lr, args.count_pages, args.min_overall)
            for s in seeds
        ]
        all_results = await asyncio.gather(*tasks)

        # 2. Склейка и дедуп по normalized query (внутри расширений)
        seen_norm: set[str] = set()
        merged: list[dict] = []
        for rows in all_results:
            for row in rows:
                n = normalize(row["query"])
                if not n or n in seen_norm:
                    continue
                seen_norm.add(n)
                merged.append(row)

        print(f"\nВсего уникальных фраз от Wordstat: {len(merged)}", file=sys.stderr)

        # 3. Дедуп относительно исходного ядра
        fresh = [row for row in merged if not is_duplicate(row["query"], existing_normalized)]
        print(f"После дедупа с исходным ядром: {len(fresh)} новых", file=sys.stderr)

        # 4. Кап по max-new-keys (сортировка по overall desc)
        fresh.sort(key=lambda r: -r["overall"])
        if len(fresh) > args.max_new_keys:
            fresh = fresh[: args.max_new_keys]
            print(f"Обрезано до top-{args.max_new_keys} по частотности", file=sys.stderr)

        if not fresh:
            print("Ничего нового не добавлено. Сохраняю исходный keys.json без изменений.", file=sys.stderr)
            output_path.write_text(json.dumps(keys_data, ensure_ascii=False, indent=2), encoding="utf-8")
            return 0

    # 5. Сохраняем fresh-ключи как плоский pending-список.
    #    Claude в сессии прочитает _pending_classification и классифицирует.
    pending = []
    for row in fresh:
        pending.append({
            "query": row["query"],
            "wordstat": {
                "overall": row.get("overall", 0),
                "exact": row.get("exact", 0),
                "quoted": row.get("quoted", 0)
            },
            "low_freq": row.get("overall", 0) < 10,
            "source": "wordstat_expansion"
        })

    keys_data.setdefault("_pending_classification", []).extend(pending)
    keys_data["_expansion_meta"] = {
        "total_added_pending": len(pending),
        "needs_classification": True,
        "note": "Список новых ключей — в _pending_classification. Claude должен их классифицировать в 6 категорий с релевантностью 0-1 и переложить в keys_data[<cat_id>]['keys']."
    }
    output_path.write_text(json.dumps(keys_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nСохранено: {output_path}", file=sys.stderr)
    print(f"   Добавлено в _pending_classification: {len(pending)} ключей", file=sys.stderr)
    print(f"   Топ-5 по частотности:", file=sys.stderr)
    for row in pending[:5]:
        print(f"     • '{row['query']}' — {row['wordstat']['overall']} показов/мес", file=sys.stderr)
    print(f"\nДальше: Claude в сессии классифицирует _pending_classification в 6 категорий.", file=sys.stderr)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys_path")
    parser.add_argument("brief_path")
    parser.add_argument("output_path")
    parser.add_argument("--lr", type=int, help="Yandex region (default: из brief)")
    parser.add_argument("--seed", action="append", help="Seed-запрос вручную (можно повторять). Идут первыми, дополняются авто-seeds.")
    parser.add_argument("--max-seeds", type=int, default=15, help="Максимум seeds суммарно (manual + auto, default: 15)")
    parser.add_argument("--min-seed-freq", type=int, default=50, help="Минимальная overall-частотность для авто-выбора seed (default: 50)")
    parser.add_argument("--count-pages", type=int, default=10, help="Страниц Wordstat на seed, 1-41 (default: 10)")
    parser.add_argument("--min-overall", type=int, default=10, help="API-фильтр по общей частоте (default: 10)")
    parser.add_argument("--max-new-keys", type=int, default=200, help="Капа на суммарное число новых ключей (default: 200)")
    args = parser.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
