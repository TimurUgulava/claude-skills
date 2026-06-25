# Окружение и доступ telegram-скилла

Скилл работает через библиотеку **Telethon** поверх уже пройденной авторизации аккаунта пользователя. Сам по себе ничего не настраивает — пользуется уже настроенной авторизацией.

## Что где лежит

| Что | Где | Примечание |
|-----|-----|-----------|
| Файл сессии | `~/.tg/tg_session.session` | **Главный секрет** — пройденная авторизация. Не копировать, не пересылать. |
| `api_id` / `api_hash` | macOS Keychain: services `tg-api-id` / `tg-api-hash`, account `$USER` | Скрипты достают сами через `security`. |
| Зависимость | `telethon` (установлен) | `pip3 install telethon`, если пропал. |

Сессия намеренно одна на аккаунт: дублировать авторизацию = плодить секрет. Минус — нельзя гонять две сессии одновременно (SQLite-файл сессии блокируется); если другой Telegram-клиент в этот момент читает каналы, подожди.

## Переопределение через окружение (опционально)

Скрипты читают, если заданы:
- `TG_API_ID`, `TG_API_HASH` — ключи (иначе берутся из Keychain);
- `TG_SESSION` — путь к файлу сессии без `.session` (иначе дефолт выше).

## Проверка доступа

```bash
python3 ~/.claude/skills/telegram/scripts/tg_resolve.py "тест"
```
Если печатает JSON (пусть и пустой `[]`) и в stderr «совпадений: N» — доступ жив.

## Если доступ отвалился

- **«Нет ключей API»** → проверь Keychain:
  ```bash
  security find-generic-password -s 'tg-api-id'   -a "$USER" -w
  security find-generic-password -s 'tg-api-hash' -a "$USER" -w
  ```
  Пусто → записать заново (взять на my.telegram.org → API development tools):
  ```bash
  security add-generic-password -U -s 'tg-api-id'   -a "$USER" -w 'ЧИСЛО'
  security add-generic-password -U -s 'tg-api-hash' -a "$USER" -w 'СТРОКА'
  ```
- **Сессия слетела (просит код/телефон)** → разовая интерактивная авторизация в терминале:
  ```bash
  cd "~/.tg"
  set -a; source secrets.env; set +a
  python3 tg_auth.py     # введёшь телефон, код из Telegram, 2FA-пароль
  ```
  Это пересоздаст файл сессии. Скилл снова заработает.
- **`database is locked`** → одновременно работает другая Telethon-сессия. Подожди и повтори.
