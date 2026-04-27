# MAX Incident Bot

Бот для отправки сообщений из Directus в групповой чат MAX.

## Описание

Бот мониторит коллекцию `asudd_incidents` в Directus и при создании новой заявки отправляет сообщение с полной информацией в групповой чат MAX.

## Как это работает

1. Бот опрашивает Directus API каждые N секунд (настраивается)
2. Получает список заявок из коллекции `asudd_incidents`
3. Проверяет, была ли заявка уже обработана
4. Если заявка новая — форматирует сообщение и отправляет в групповой чат MAX
5. Сохраняет ID обработанных заявок в памяти (чтобы не дублировать уведомления)

## Требования

- Python 3.8+
- Токен бота MAX (получить на https://business.max.ru/self в разделе Чат-боты → Интеграция)
- URL и токен доступа к Directus
- ID группового чата MAX

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

### Переменные окружения

| Переменная | Описание |
|------------|----------|
| `MAX_ACCESS_TOKEN` | Токен бота MAX из личного кабинета |
| `DIRECTUS_URL` | URL вашего экземпляра Directus |
| `DIRECTUS_TOKEN` | Токен доступа к Directus API |
| `MAX_CHAT_ID` | ID группового чата для отправки уведомлений |
| `POLLING_INTERVAL` | Интервал опроса Directus в секундах (по умолчанию 10) |

## Запуск

```bash
python bot.py
```

## Структура проекта

- `bot.py` - Основной файл бота с логикой работы
- `config.py` - Конфигурация и переменные окружения
- `directus_client.py` - Клиент для работы с Directus API
- `max_client.py` - Клиент для работы с MAX API
- `requirements.txt` - Зависимости Python

## Формат сообщения

Бот отправляет сообщения в формате Markdown со следующей структурой:

```
🚨 Новая заявка #{ID}

Заголовок: {title}

Описание:
{description}

Статус: {status}
Приоритет: {priority}
Дата создания: {created_at}

---
Заявка создана в Directus
```

## Настройка под вашу коллекцию

Если поля в вашей коллекции `asudd_incidents` отличаются от стандартных, отредактируйте метод `format_incident_message()` в файле `bot.py`:

```python
def format_incident_message(self, incident: Dict[str, Any]) -> str:
    incident_id = incident.get('id', 'Не указан')
    title = incident.get('title', incident.get('name', 'Без названия'))
    description = incident.get('description', incident.get('text', 'Нет описания'))
    # ... адаптируйте под ваши поля
```

## API MAX

Бот использует следующие методы MAX API:

- `POST /messages` — отправка сообщения в чат

Документация: https://dev.max.ru/docs-api
