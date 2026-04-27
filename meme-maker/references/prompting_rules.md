# Правила промптов для мемов

## Общие принципы (Nano Banana 2 через MCP `nanobanana`)

### 1. Промпт всегда на английском

Независимо от языка запроса пользователя. Русский в промпте режет качество обеих моделей.

### 2. Русский текст на картинке — только с явным указанием языка

```
the label reads "Новый ChatGPT" in Russian Cyrillic letters, bold black sans-serif
```

**Без `in Russian Cyrillic letters`** модель нарисует латиницу даже при русском в кавычках. Альтернативные маркеры (можно использовать взаимозаменяемо):
- `in Russian Cyrillic letters`
- `Cyrillic script`
- `written in Russian`

Всегда кавычь текст буквально, в двойных кавычках — это сигнал «срисовать как есть, не переводить».

### 3. Spatial-композиция — буквально

Мемы критически зависят от композиции (где Drake, где пёс, где кнопки). Описывай пространство явными словами:

```
TOP PANEL: ...
MIDDLE PANEL: ...
BOTTOM PANEL: ...

LEFT SIDE: a cat. RIGHT SIDE: a dog. The cat is TO THE LEFT OF the dog.
The label is DIRECTLY BELOW the character, CENTERED.
```

Слабо: `a dog with a mug` — модель сама решит, как это скомпоновать.
Сильно: `a cartoon dog sitting at a small wooden table, holding a coffee mug in his right paw, the mug is HELD UP and VISIBLE, with "{ТЕКСТ НА КРУЖКЕ}" printed on its front side`.

### 4. Структура промпта (для каждого мема)

```
[Описание формата: "classic X meme", "three-panel vertical layout"]
[Описание главного субъекта: кто / что / в какой позе]
[Spatial-композиция: что слева/справа/сверху/снизу]
[Текст на картинке: точные русские строки в кавычках + "in Russian Cyrillic letters, bold sans-serif"]
[Стиль: cartoon / photograph / comic / cinematic]
[Aspect: "Square 1:1 format"]
```

### 5. Без keyword-спама

Не нужны `8k, masterpiece, trending, best quality` — это артефакт старых Stable-Diffusion. Современные модели (и Nano Banana 2, и GPT Image 2) игнорируют этот мусор.

### 6. Камера — только для фотореалистичных мемов

Для DiCaprio Cheers, Distracted Boyfriend (они фотореалистичные) — можно упомянуть `cinematic lighting`, `movie still style`, `realistic street photograph`. Для Spongebob, This is Fine, Galaxy Brain — не упоминай объективы и камеры, там cartoon.

### 7. Каждый мем — в своей conversation_id

`conversation_id: meme-<slug>`. Это изолирует контексты — Drake не залезет в рендер Spongebob.

### 8. Aspect ratio

По умолчанию `1:1` (стандарт ТГ-канала). Для сторис — `9:16`, для широких баннеров — `16:9`. Квадрат — лучший выбор для мемов почти всегда.

---

## Промпт-скелеты по шаблонам

Каждый скелет — рабочий промпт с плейсхолдерами `{ТЕКСТ 1}`, `{ТЕКСТ 2}` и т.д. Подставь русские строки (в кавычках и с пометкой Russian Cyrillic) и передай в `mcp__nanobanana__gemini_generate_image`.

### Drake

```
Three-panel vertical meme in the classic "Drake Hotline Bling" reaction meme template, three equal horizontal panels stacked vertically.

TOP PANEL: a rapper in a white puffer jacket turns away from the camera with a disgusted expression, right hand raised palm-out to block his face — to the right of him, a white label box with bold black Russian Cyrillic sans-serif text: "{ТЕКСТ 1}".

MIDDLE PANEL: same rapper, same disgusted turn-away pose — label box next to him reads in Russian Cyrillic: "{ТЕКСТ 2}".

BOTTOM PANEL: same rapper now smiling happily, pointing approvingly with a finger gun at the label — label box reads "{ТЕКСТ 3}" in bold clean sans-serif, black on white.

Clean white backgrounds, classic meme template layout. Square 1:1 format.
```

Для **2-панельного варианта (Drakeposting)** — убери MIDDLE PANEL.

### Distracted Boyfriend

```
Classic "Distracted Boyfriend" meme photograph style, three people on a city street in daylight.

A young man in a blue shirt walks hand-in-hand with his girlfriend in a white dress — a white label on her chest reads "{ТЕКСТ ДЕВУШКИ}" in clean bold sans-serif letters. He looks {straight ahead at her and smiles / turns his head sharply to look} at two women in bright red dresses walking past on the right — labels on them read in Russian Cyrillic letters, bold white sans-serif with thick black outline: "{ТЕКСТ 1}" and "{ТЕКСТ 2}".

{Inverted loyal-boyfriend version — the boyfriend completely ignores the women in red / Classic version — the boyfriend turns to stare at them}.

Realistic street photograph style. Square 1:1 format.
```

**Инверсия** (парень верен) используется, когда мысль пользователя — про верность выбору. **Классика** (оборачивается) — когда ирония про соблазн новым.

### This is Fine

```
Classic "This is Fine" webcomic meme style, flat cartoon coloring, KC Green webcomic aesthetic.

A cartoon dog wearing a small brown pointed hat sits calmly at a small wooden table, eyes half-closed in serene expression, holding a coffee mug with the word "Claude" printed on it in clean sans-serif letters — the mug is held up and visible to the viewer.

The room around him is engulfed in orange flames — fire everywhere on walls, floor, and ceiling. Burning posters on the walls read in bold black sans-serif: "{ТЕКСТ НА СТЕНЕ 1}", "{ТЕКСТ НА СТЕНЕ 2}", and "{ТЕКСТ НА СТЕНЕ 3}" in Russian Cyrillic letters.

A speech bubble from the dog reads "{ТЕКСТ В ПУЗЫРЕ}" in Russian Cyrillic letters, bold black. Square 1:1 format.
```

### Two Buttons

```
Classic "Two Buttons" / "Daily Struggle" meme template, flat cartoon style, beige background.

A cartoon man in a red t-shirt and blue jeans stands in the center, sweating profusely with big beads of sweat on his forehead, his finger hovering nervously between two big red square buttons mounted on the wall.

LEFT button reads in Russian Cyrillic letters, bold white sans-serif: "{ТЕКСТ КНОПКИ 1}". RIGHT button reads in Russian Cyrillic: "{ТЕКСТ КНОПКИ 2}". He is panicking, cannot decide between them.

Bottom caption strip across the image in bold black Russian Cyrillic sans-serif on white background: "{НИЖНЯЯ ПЛАШКА}".

Square 1:1 format.
```

### Galaxy Brain (Expanding Brain)

```
Four-panel vertical "Galaxy Brain" / "Expanding Brain" meme template on clean white background, four equal horizontal frames stacked vertically.

PANEL 1 (top): an ordinary pink human brain on white background, label to the right in Russian Cyrillic bold black sans-serif: "{СТАДИЯ 1}".

PANEL 2: a glowing brain emitting bright radiant light rays in all directions, label to the right in Russian Cyrillic: "{СТАДИЯ 2}".

PANEL 3: a brain made of cosmic nebula with galaxies, stars, and colorful space clouds visible inside it, label: "{СТАДИЯ 3}".

PANEL 4 (bottom): a divine brain emanating golden light waves filling the universe, surrounded by cosmic halo and energy rings, label in bold clean sans-serif: "{СТАДИЯ 4}".

Classic progressive-enlightenment meme template, four-stage vertical stack. Square 1:1 format.
```

### Spongebob Imagination

```
Classic "Imagination" rainbow meme, cartoon style.

A yellow square cartoon sponge character in brown shorts and white shirt with red tie stands underwater on the sandy sea floor, holding up his yellow hands with a big bright colorful rainbow arching between his palms. Inside the rainbow arc, in huge bold white sans-serif letters with thick black outline: "{ТЕКСТ В РАДУГЕ}".

Bottom caption strip below the character in bold white Russian Cyrillic sans-serif with thick black outline: "{ТЕКСТ СНИЗУ}".

Underwater scene with soft blue water, bubbles, and coral silhouettes in the background. Square 1:1 format.
```

### DiCaprio Cheers (Gatsby)

```
Classic "cheers" meme in 1920s Great Gatsby cinematic style.

A handsome man in a black tuxedo with white shirt and black bow tie raises a crystal coupe champagne glass toward the viewer with a confident smile, making direct eye contact with the camera. He stands in an elegant 1920s ballroom with warm golden lighting.

Behind him, a large TV screen mounted on the wall shows breaking-news headlines in Russian Cyrillic letters on a red banner: top line in bold white sans-serif "{НОВОСТЬ 1}", second line "{НОВОСТЬ 2}". The TV screen is clearly visible and well-framed.

Bottom caption below the image in bold white Russian Cyrillic sans-serif with thick black outline: "{ТЕКСТ СНИЗУ}".

Cinematic warm golden lighting, movie-still aesthetic. Square 1:1 format.
```

### Change My Mind

```
Classic "Change My Mind" meme format.

A bearded man in a black t-shirt sits at a small folding table on a brick plaza, looking directly at the camera with a slight smirk. On the table in front of him stands a large white sign with bold black block letters reading "{ТЕЗИС}" in Russian Cyrillic letters. Below the tezis on the same sign, in smaller letters: "Переубедите меня" in Russian Cyrillic.

Outdoor setting, photograph style. Square 1:1 format.
```

### Bernie Asking for Support

```
Classic "Once Again I Am Asking" Bernie Sanders meme.

An elderly man with white hair, glasses, and a grey winter coat sits in a folding chair outdoors, holding a microphone toward the camera with a tired but determined expression. Behind him — soft blurred parking lot background.

Bottom caption in bold white Russian Cyrillic sans-serif with thick black outline: "{ТЕКСТ ПРОСЬБЫ}".

Photograph style, meme template layout. Square 1:1 format.
```

### American Chopper Argument (5 panels)

```
Five-panel "American Chopper argument" meme template, five equal horizontal frames stacked vertically.

In each panel, two men argue across a factory workshop table: a bald older man in a bandana on the left side, and a younger man with slicked-back hair on the right. They gesture angrily at each other.

PANEL 1: older man yelling, caption in Russian Cyrillic at the bottom of the panel: "{РЕПЛИКА 1}".
PANEL 2: younger man responding, caption: "{РЕПЛИКА 2}".
PANEL 3: older man escalating, caption: "{РЕПЛИКА 3}".
PANEL 4: younger man final blow, caption: "{РЕПЛИКА 4}".
PANEL 5: older man resigned, caption: "{РЕПЛИКА 5}".

Industrial workshop background, reality-TV photograph style. Square 1:1 format.
```

### Woman Yelling at Cat

```
Classic "Woman Yelling at Cat" meme, split-panel composition.

LEFT PANEL: a blonde woman with red manicure shouts and points her finger sharply, angry facial expression, photograph style.

RIGHT PANEL: a white cat sits at a dinner table with a plate of vegetables in front of him, looking confused and slightly annoyed, photograph style.

Top caption over the woman in Russian Cyrillic, bold white sans-serif with black outline: "{РЕПЛИКА ЖЕНЩИНЫ}".
Top caption over the cat in Russian Cyrillic: "{РЕПЛИКА КОТА}".

Square 1:1 format.
```

### Is This a Pigeon?

```
Classic "Is This a Pigeon?" anime meme screenshot.

A young man in a grey-green military cadet uniform stands in a sunny green meadow, pointing at a large orange butterfly flying near him. Anime art style, soft pastel colors.

Label on the man in Russian Cyrillic, bold white sans-serif with black outline: "{КТО ОШИБАЕТСЯ}".
Label on the butterfly in Russian Cyrillic: "{ЧТО ЭТО НА САМОМ ДЕЛЕ}".
Bottom caption in Russian Cyrillic: "{ЕГО ВОПРОС}".

Square 1:1 format.
```

### Chad vs Virgin

```
Classic "Virgin vs Chad" comparison meme, two-column layout.

LEFT COLUMN (blue background): a thin, hunched, sad-looking cartoon man labeled in bold white sans-serif at the top: "Virgin {ТИП 1}". Below him, a bulleted list in Russian Cyrillic bold white sans-serif of 3-4 negative traits: "{ЧЕРТА 1}", "{ЧЕРТА 2}", "{ЧЕРТА 3}".

RIGHT COLUMN (red background): a muscular confident cartoon man with strong jaw labeled at the top: "Chad {ТИП 2}". Below him, a bulleted list of 3-4 positive traits in Russian Cyrillic: "{ЧЕРТА 1}", "{ЧЕРТА 2}", "{ЧЕРТА 3}".

Classic MS Paint comic style. Square 1:1 format.
```

### Trade Offer

```
Classic "Trade Offer" meme template, photograph style.

A man in business casual attire holds his hands up in a "let me propose something" gesture, looking straight at the camera. Top caption reads "TRADE OFFER" in bold sans-serif letters.

Below him, two columns side by side on a beige background:
LEFT COLUMN titled "I RECEIVE" with bulleted items in Russian Cyrillic: "{МОЯ СТОРОНА}".
RIGHT COLUMN titled "YOU RECEIVE" with bulleted items in Russian Cyrillic: "{ВАША СТОРОНА}".

Square 1:1 format.
```

### Stonks

```
Classic "Stonks" meme template.

A bald blue humanoid cartoon man in a dark suit stands in front of a large blue chart showing a line {going sharply up / going sharply down}, overlaid with the word {"STONKS" / "NOT STONKS"} in bold yellow sans-serif letters.

Bottom caption in Russian Cyrillic bold white sans-serif with black outline: "{ТЕКСТ КОНТЕКСТА}".

Surreal 3D meme aesthetic. Square 1:1 format.
```

### Ждун

```
Classic "Ждун" Russian meme.

A grey humanoid figure with a sad face, bald head, and a body resembling a seal — sitting with its hands folded in its lap, waiting patiently with a long-suffering expression. Neutral grey background.

Bottom caption in Russian Cyrillic bold black sans-serif on white strip: "{ТЕКСТ ПРО ОЖИДАНИЕ}".

Sculpture photograph style. Square 1:1 format.
```

### Bad Luck Brian / Неудачник

```
Classic "Bad Luck Brian" meme template, school yearbook photograph style.

A portrait of a freckled teenage boy in a red checkered sweater and braces, giving an awkward cheesy smile to the camera, yellow-grey gradient background typical of 2000s school photos.

Top caption in Russian Cyrillic, bold white sans-serif with thick black outline: "{НАСТРОЙКА}".
Bottom caption in Russian Cyrillic, bold white sans-serif with thick black outline: "{ПАНЧ}".

Square 1:1 format.
```

---

## Итерации

**Доработка с сохранением контекста:** тот же `conversation_id`, доработанный промпт → `mcp__nanobanana__gemini_generate_image`. Модель помнит контекст, картинка останется узнаваемой после правок.

**Полная перезагрузка:** `mcp__nanobanana__clear_conversation` с тем же id, потом новый `gemini_generate_image`.

**Точечная правка текста без пересборки:** `mcp__nanobanana__gemini_edit_image` с тем же `conversation_id` и инструкцией вида `keep the exact composition and characters, replace the text "X" with "Y" in Russian Cyrillic letters`.
