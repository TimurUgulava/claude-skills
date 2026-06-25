#!/usr/bin/env python3
"""Генерация изображений через OpenAI Image API (GPT Image).

Usage:
  python generate_gpt_image.py --prompt "..." [--size 1024x1024] [--n 1]
                               [--quality high] [--output-dir ~/Downloads/images]
                               [--model gpt-image-1] [--reference path/to/img.png]

Поддерживает:
  - text-to-image (generations endpoint)
  - image editing с референсами (edits endpoint) — если передан --reference
  - прозрачный фон (--transparent)

Читает OPENAI_API_KEY из .env в корне скилла либо из окружения.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_ROOT / ".env"


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip())


def api_request(
    url: str,
    api_key: str,
    payload: dict,
    files: list[tuple[str, str]] | None = None,
    allow_fallback: bool = True,
) -> dict:
    """Отправляет multipart (для edits) или JSON (для generations).

    files — список кортежей (field_name, filepath). Один ключ может повторяться
    (для image[] при нескольких референсах — это требование OpenAI API).
    """
    if files:
        boundary = f"----rzvlshk{int(time.time()*1000)}"
        body = bytearray()
        for key, value in payload.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.extend(f"{value}\r\n".encode())
        for key, filepath in files:
            fname = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                content = f.read()
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(
                f'Content-Disposition: form-data; name="{key}"; filename="{fname}"\r\n'.encode()
            )
            body.extend(b"Content-Type: image/png\r\n\r\n")
            body.extend(content)
            body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode())

        req = urllib.request.Request(
            url,
            data=bytes(body),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
    else:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")
        needs_verification = (
            e.code == 403
            and "verified" in err_body.lower()
            and payload.get("model") == "gpt-image-2"
            and allow_fallback
        )
        if needs_verification:
            print(
                "WARN: gpt-image-2 требует верификации организации OpenAI. "
                "Откатываюсь на gpt-image-1. "
                "Верифицируй аккаунт: https://platform.openai.com/settings/organization/general",
                file=sys.stderr,
            )
            payload["model"] = "gpt-image-1"
            return api_request(url, api_key, payload, files, allow_fallback=False)
        print(f"ERROR [{e.code}]: {err_body}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Промпт для генерации")
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=[
            "1024x1024", "1024x1536", "1536x1024",
            "2048x2048", "1536x2048", "2048x1536",
            "auto",
        ],
        help="Размер. 1024-ряд — универсальный, 2048-ряд — только gpt-image-2 (2K).",
    )
    parser.add_argument("--n", type=int, default=1, help="Количество вариантов (1-10)")
    parser.add_argument(
        "--quality",
        default="high",
        choices=["low", "medium", "high", "auto"],
        help="Качество рендера",
    )
    parser.add_argument(
        "--model",
        default="gpt-image-2",
        choices=["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"],
        help="Модель. gpt-image-2 — актуальная (требует Organization Verification). "
             "При 403 verification автоматически откатится на gpt-image-1.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path.home() / "Downloads" / "images"),
        help="Папка для сохранения",
    )
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="Прозрачный фон (требует format=png)",
    )
    parser.add_argument(
        "--reference",
        action="append",
        help="Путь к референс-изображению (можно несколько). Переключает на edits endpoint.",
    )
    parser.add_argument(
        "--output-format",
        default="png",
        choices=["png", "jpeg", "webp"],
    )
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY не найден в .env или окружении", file=sys.stderr)
        sys.exit(2)

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.reference:
        url = "https://api.openai.com/v1/images/edits"
        payload = {
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "n": str(args.n),
            "quality": args.quality,
        }
        if len(args.reference) == 1:
            files = [("image", args.reference[0])]
        else:
            files = [("image[]", path) for path in args.reference]
        result = api_request(url, api_key, payload, files)
    else:
        url = "https://api.openai.com/v1/images/generations"
        payload = {
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "n": args.n,
            "quality": args.quality,
            "output_format": args.output_format,
        }
        if args.transparent:
            payload["background"] = "transparent"
            payload["output_format"] = "png"
        result = api_request(url, api_key, payload)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    saved = []
    for i, item in enumerate(result.get("data", [])):
        b64 = item.get("b64_json")
        if not b64:
            print(f"WARN: item {i} не содержит b64_json", file=sys.stderr)
            continue
        ext = args.output_format if not args.reference else "png"
        out_path = output_dir / f"gpt_{timestamp}_{i+1}.{ext}"
        out_path.write_bytes(base64.b64decode(b64))
        saved.append(str(out_path))

    usage = result.get("usage", {})
    print(json.dumps({"saved": saved, "usage": usage}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
