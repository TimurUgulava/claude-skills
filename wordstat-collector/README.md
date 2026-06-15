# wordstat-collector

Скилл для сбора семантического ядра — списка поисковых запросов с реальной частотностью Яндекс Wordstat — через Pixel Tools API.

На вход: фраза-маркер + регион. На выходе: `keys.xlsx` с классифицированными запросами и числом показов в месяц.

## Установка

```bash
pip install httpx python-dotenv rapidfuzz openpyxl
cp .env.example .env
# впиши PIXELTOOLS_API_KEY в .env
python scripts/smoke_test.py
```

Ключ Pixel Tools: https://tools.pixelplus.ru/ → ЛК → API.

## Как работает

1. **Маркер + регион** → стартовые seed-запросы.
2. **`wordstat_enrichment.py`** — частотность seed'ов (`wordstatapi`), мёртвые отсеиваются.
3. **`wordstat_expansion.py`** — расширение через `wordstatapikeywords` (связанные запросы с частотностью).
4. **Классификация** в 6 категорий + релевантность (выполняет Claude в сессии).
5. **`clustering.py`** (опционально) — кластеризация по подобию топа Яндекса (`gruppirovka`).
6. **`export_xlsx.py`** → `keys.xlsx`.

Подробности — в `SKILL.md` и `references/`.

## Состав

```
wordstat-collector/
├── SKILL.md                       # описание скилла и workflow
├── README.md
├── .env.example                   # шаблон ключа
├── .gitignore
├── references/
│   ├── 01-discovery.md            # маркер + регион (lr-коды)
│   ├── 02-keyword-research.md     # логика сбора и кластеризации
│   └── 03-api-setup.md            # Pixel Tools setup, лимиты
└── scripts/
    ├── smoke_test.py              # проверка ключа и зависимостей
    ├── wordstat_enrichment.py     # частотность через wordstatapi
    ├── wordstat_expansion.py      # расширение через wordstatapikeywords
    ├── clustering.py              # кластеризация через gruppirovka
    └── export_xlsx.py             # выгрузка в keys.xlsx
```

Источник данных — только Pixel Tools. Сторонние LLM-сервисы не используются.
