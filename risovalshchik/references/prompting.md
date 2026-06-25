# Промптинг: Nano Banana Pro / 2 vs GPT Image 2

Шпаргалка по формулированию промптов. Обе модели хорошо понимают русский, но **промт всегда пишем на английском** — качество заметно выше. Исключение — текст, который должен появиться на самой картинке: он идёт в кавычках с явным указанием языка (см. ниже).

## Движки и их возможности

| Параметр | Nano Banana Pro / 2 | GPT Image 2 |
|---|---|---|
| Engine ID | `gemini-3-pro-image-preview` | `gpt-image-2` |
| Архитектура | Multimodal reasoning core с внутренним Thinking — модель рассуждает перед генерацией, разруливает логику, физику и spatial-конфликты | Native reasoning, text-first понимание |
| Фотореализм | Очень сильно | Очень сильно |
| Текст на картинке (мультиязычный, русский) | **Сильно** (предложения, параграфы, логотипы) | **Сильно** (чуть точнее на длинных текстах и мелком кегле) |
| Инфографика, диаграммы, мокапы | Очень сильно (Thinking помогает со spatial-layout) | Сильно |
| Длинные сложные промты | Сильно | Сильно |
| Прозрачный фон | Через промт | Нативно (`--transparent`) |
| Разрешение | до 4K | до 2K (`2048×2048`, `1536×2048`, `2048×1536` после верификации) |
| Reference images | До **14 штук** в одном запросе | До 16 в edits endpoint |
| Скорость | Медленнее (Thinking overhead), но выше точность | 5–30 сек |
| Стоимость | Дешевле | Дороже (high 1024×1024 ~$0.21) |

**Правило выбора:**
- Текст на картинке, инфографика, мокапы, сложные сцены с физикой → **обе модели сильны**; Nano Banana Pro быстрее и дешевле, GPT Image 2 чуть точнее на длинных/мелких надписях.
- Нужен прозрачный фон нативно → **GPT Image 2** (`--transparent`).
- Много итераций с одним и тем же объектом по референсу → **Nano Banana** (conversation в MCP держит контекст).
- Итерации через повторную подачу предыдущего результата на вход → **GPT Image 2** с `--reference`.

## Ключевые правила промптинга (работают для обеих моделей)

### 1. Промт — на английском, текст на картинке — с явным языком

Сам промт пишем по-английски. Если на картинке нужна русская надпись — **указываем язык и кавычим буквально**, иначе модель нарисует латиницу даже при русском запросе.

```
The chalkboard reads "МАСТЕРСКАЯ" in Russian Cyrillic letters,
bold condensed sans-serif, white chalk on black background, centered.
```

Маркеры:
- `in Russian Cyrillic letters`
- `Cyrillic script`
- Текст буквально в двойных кавычках → команда «срисуй эти символы как есть, не переводи»

Без этого: «the sign says ПРИВЕТ» → модель напишет `HELLO` или `NEYROMASTERSKAYA`.

### 2. Структура сильного промта

```
[Субъект + детальные прилагательные] doing [действие] in [локация/контекст].
[Композиция и ракурс]. [Свет и атмосфера]. [Стиль/медиум].
[Текст с точной формулировкой, шрифтом и позицией]. [Ограничения].
```

**Слабо:** `a man with laptop`

**Сильно:** `A man in his 40s wearing a grey sweater, sitting at a wooden desk with an open laptop. Out-of-focus bookshelf in the background. Soft window light from the left, warm tones, rule-of-thirds composition. Shot on 50mm lens, shallow depth of field.`

### 3. Без keyword-спама

`8k, masterpiece, trending on artstation, best quality` ничего не добавляют — это артефакт старых Stable-Diffusion эпох. Описывай словами.

### 4. Камера — только для фотореализма

Lens, aperture, depth of field, film grain — **только для photoreal**. Для иллюстраций, инфографики, диаграмм, векторной графики упоминания камеры зашумляют и портят результат.

### 5. Текст в изображении — формат

Всегда указывай: **точный текст в кавычках → шрифт → размер/вес → цвет → позиция**.

```
The sign reads "OPEN 24/7" in bold red sans-serif capitals,
large size, centered on the storefront window.
```

Для русского добавляй `in Russian Cyrillic letters` сразу после кавычек (см. правило 1).

### 6. Spatial logic — explicit

Для сложных сцен описывай пространственные отношения буквально:

```
The cat sits TO THE LEFT of the vase. The book is BEHIND both,
leaning against the wall. The lamp hangs FROM ABOVE, slightly to the right.
```

Модели сильно лучше разруливают сцену с явными «left/right/behind/above», чем с перечислением объектов.

### 7. Physics reasoning

Nano Banana Pro умеет рассуждать о физике — подскажи ей:

```
The glass refracts the light behind it, creating soft caustics on the table.
The shadow falls to the right, consistent with the light source on the upper left.
```

### 8. Негативы — естественным языком

Не Stable-Diffusion-синтаксис, а обычные фразы:

```
No text except the title. No extra fingers. Avoid clutter.
The background should be clean, without people.
```

### 9. Разрешение — явно

Когда нужно hi-res: `4K resolution`, `high detail`. Для GPT Image 2 дополнительно выбирай `--size 2048x2048` (после верификации).

### 10. Self-contained

Промт — один самостоятельный текст. Не разбивай на части, не ссылайся на «предыдущую картинку» текстом — для итераций используй reference-картинку.

## Сценарные шаблоны

### Product mockup

```
A premium cosmetics bottle with the label reading "AURORA" in elegant gold
serif text, placed on a marble surface with soft studio lighting from the
upper left. Shallow depth of field, 85mm lens, luxury editorial photography
style. 4K resolution.
```

### Infographic / диаграмма

```
A clean infographic explaining [topic]. Top-to-bottom layout with four labeled
stages: [Stage 1], [Stage 2], [Stage 3], [Stage 4]. Each stage has a flat vector
icon and a one-sentence description underneath. Sky blue and white palette,
single orange accent (#F78F0D). Clean sans-serif font, flat design with subtle
gradients. No photographic elements.
```

### Style transfer

```
Transform this into a 1970s Japanese woodblock print style with limited color
palette (indigo, rust, cream), strong outlines, and textured washi paper grain.
Preserve the original subject composition.
```

### Multi-reference (brand/character consistency)

```
Using Reference Image 1 for the character's face, and Reference Image 2 for
the background, generate a cinematic portrait. Maintain exact facial features
from Ref 1. Match the lighting and color palette of Ref 2.
```

## Готовые стилевые пресеты

Используй как постфикс к основному описанию:

- **Меловой blackboard** — `chalk drawing on black chalkboard, white chalk strokes, single orange accent (#F78F0D), hand-drawn, loose imperfect lines, slightly smudged texture`
- **Paper sketchnote** — `hand-drawn sketchnote on cream paper, felt-tip marker, warm minimalism, black + orange + grey palette, casual lettering`
- **Corporate clean** — `clean flat vector illustration, corporate style, muted palette with single orange accent, subtle gradient, no photographic elements`
- **Photoreal portrait** — `editorial portrait, natural window light, 85mm lens, shallow depth of field, subtle film grain`

Если в пресете нужна русская надпись — добавляй `with "<русский текст>" in Russian Cyrillic letters` отдельной строкой.

## Типичные ошибки

- **Забыл указать `Russian Cyrillic letters`** → на картинке английская или транслит-версия текста.
- **Keyword spam вместо описания** → модель игнорирует, результат серый.
- **Камера в промте для инфографики** → диаграмма становится «полу-фото», артефакты.
- **Перечислил объекты без spatial-связей** → композиция случайная, объекты налезают друг на друга.
- **Мелкий текст на Nano Banana (до Pro)** — читается плохо. Nano Banana **Pro / 2** (`gemini-3-pro-image-preview`) уже справляется, но для очень длинных текстов лучше GPT Image 2.
- **Множественные объекты одной категории** — обе модели теряют счёт. Пиши «three cats: one black, one white, one orange», не «several cats».
- **Руки и пальцы** — явно указывай позу или прячь: `hands in pockets`, `holding a cup`.

## Aspect ratios

| Назначение | Aspect | GPT Image 2 size | Nano Banana |
|---|---|---|---|
| ТГ-обложка поста | 1:1 | `1024x1024` или `2048x2048` | `1:1` |
| ТГ-сторис, Reels, вертикальный баннер | 9:16 → 2:3 | `1024x1536` или `1536x2048` | `9:16` |
| YouTube preview, ландшафтный баннер | 16:9 → 3:2 | `1536x1024` или `2048x1536` | `16:9` |
| Слайды презентации | 16:9 | `1536x1024` | `16:9` |

Nano Banana принимает `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`.

GPT Image 2 — три 1024-размера, три 2K-размера (после верификации) + `auto`.

## Итеративная работа

- **Nano Banana** через MCP ведёт conversation — повторные команды уточняют ту же картинку («сделай фон темнее», «убери очки»). Сбросить — `mcp__nanobanana__clear_conversation`.
- **GPT Image 2** — каждая генерация независимая. Для итераций передавай предыдущий результат через `--reference <path>` (до 16 референсов в одном запросе).
