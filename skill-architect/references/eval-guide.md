# Тестирование и оптимизация скиллов

## 1. Тест-кейсы

Создай 3–5 реалистичных промптов. Сохрани в `evals/evals.json`:

```json
{
  "skill_name": "skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "Конкретный запрос со всеми деталями",
      "expected_output": "Описание ожидаемого результата"
    }
  ]
}
```

Правила: конкретные, разный уровень формальности, edge cases. Assertions — после первого запуска.

## 2. Запуск

Для каждого тест-кейса — два сабагента параллельно:
- **С скиллом** → `workspace/iteration-1/eval-<ID>/with_skill/`
- **Без скилла** → `workspace/iteration-1/eval-<ID>/without_skill/`

## 3. Итерации

1. Покажи результаты пользователю (eval-viewer)
2. Прочитай фидбэк (пустой = ок)
3. Улучши скилл
4. Перезапусти → повтори

### Философия улучшений

- **Генерализируй** — не overfitь
- **Lean prompt** — убирай непродуктивные инструкции
- **Explain why** — reasoning вместо правил
- **Бандли повторяющееся** — одинаковый helper в каждом запуске → scripts/

## 4. Оптимизация description

20 запросов: 10 should-trigger + 10 should-NOT-trigger.

**Should-trigger:** разные формулировки, casual/formal, implicit.
**Should-NOT-trigger:** near-misses, genuinely tricky. Не очевидно нерелевантные.

```bash
python -m scripts.run_loop \
  --eval-set evals/trigger_eval.json \
  --skill-path <skill-dir> \
  --max-iterations 5
```

Train/test split 60/40. Лучший description по test score.

## 5. Слепое A/B сравнение

Для серьёзных изменений:
1. Запусти обе версии на одних тестах
2. Отдай грейдеру без указания версий
3. Грейдер оценивает content + structure (1–5) и выбирает победителя
4. Проанализируй *почему* победитель победил
