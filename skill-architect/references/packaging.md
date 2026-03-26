# Упаковка в .skill и валидация

## Упаковка

После создания всех файлов скилла — упакуй в .skill формат.

### Способ 1: через package_skill.py (предпочтительный)

```bash
CREATOR_DIR=$(find ~/.claude/plugins -path "*/skill-creator/skills/skill-creator" -type d 2>/dev/null | head -1)
cd "$CREATOR_DIR" && python3 -m scripts.package_skill <путь-к-директории-скилла> <путь-для-выходного-файла>
```

### Способ 2: ручная упаковка (fallback)

Если package_skill.py не найден или упал:

```bash
cd <родительская-директория-скилла> && zip -r <skill-name>.skill <skill-name>/ -x "*/__pycache__/*" "*/evals/*" "*/.DS_Store"
```

## После упаковки

Выведи:

> **Скилл собран и упакован.**
>
> ```
> skill-name/
> ├── SKILL.md (X строк)
> ├── references/ (N файлов)
> └── scripts/ (N файлов)
> ```
>
> **Файл:** `<путь>/skill-name.skill`
>
> **Далее:** тестируем или написать User Guide?

---

## Валидационный чек-лист

Проверь перед упаковкой:

```
[ ] SKILL.md существует
[ ] Валидный YAML frontmatter (name + description)
[ ] name: kebab-case, ≤64 символов
[ ] description: ≤1024 символов, без < >
[ ] description: есть "Use when..." и "Do NOT use for..."
[ ] description: НЕ содержит workflow
[ ] SKILL.md ≤ 100 строк (детали в references/)
[ ] References: 1 уровень вложенности
[ ] Нет хардкода путей/токенов
[ ] Нет README.md внутри скилла
[ ] Императивный залог, explain the why
[ ] Минимум 2 примера (в references/ или examples/)
```
