# Telegram Bot для RAG-системы салона красоты

Telegram бот предоставляет удобный интерфейс для взаимодействия с RAG-системой салона красоты через мессенджер Telegram. Бот поддерживает контекст диалога, запоминает предыдущие сообщения и может отвечать на уточняющие вопросы.

## 🌟 Возможности

- **Контекстные диалоги**: Бот запоминает историю разговора и может отвечать на уточняющие вопросы
- **Поиск процедур**: Поиск услуг салона красоты по описанию или проблеме
- **Консультации**: Подробная информация о процедурах, показаниях и противопоказаниях
- **Информация о мастерах**: Данные о специалистах и возможности записи
- **Быстрые действия**: Кнопки для популярных запросов
- **Команды управления**: Справка, статус системы, очистка истории

## 🚀 Настройка и запуск

### 1. Создание бота в Telegram

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен бота (например: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройка конфигурации

Добавьте токен бота в файл `.env`:

```env
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_MAX_MESSAGE_LENGTH=4096
TELEGRAM_CONTEXT_TTL_HOURS=24
TELEGRAM_MAX_CONTEXT_MESSAGES=20
TELEGRAM_ENABLE_BUTTONS=True
```

### 3. Установка зависимостей

```bash
pip install python-telegram-bot
```

### 4. Запуск бота

```bash
# Проверка готовности
python start_telegram_bot.py --check

# Запуск бота
python start_telegram_bot.py

# Запуск в режиме разработки
python start_telegram_bot.py --mode development
```

## 💬 Использование бота

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать диалог с ботом |
| `/help` | Показать справку по использованию |
| `/status` | Проверить статус RAG-системы |
| `/clear` | Очистить историю диалога |

### Примеры диалогов

#### Поиск процедуры

```
Пользователь: массаж лица
Бот: Рекомендую следующие процедуры для лица:

1. Классический массаж лица - 2500 руб.
   • Длительность: 60 минут
   • Показания: морщины, усталость кожи
   • Мастера: Анна Петрова, Мария Иванова

2. Лимфодренажный массаж - 3000 руб.
   • Длительность: 45 минут
   • Показания: отеки, дряблость кожи
   • Мастер: Елена Сидорова

Пользователь: расскажи подробнее про первый
Бот: Классический массаж лица - это ручная процедура...
```

#### Консультация

```
Пользователь: что такое RF-лифтинг?
Бот: RF-лифтинг (радиочастотный лифтинг) - это аппаратная процедура...

Пользователь: есть ли противопоказания?
Бот: Да, у RF-лифтинга есть противопоказания:
• Беременность и кормление грудью
• Онкологические заболевания
• Металлические импланты в зоне воздействия...
```

#### Запись к мастеру

```
Пользователь: хочу записаться на массаж лица
Бот: Для записи на массаж лица доступны следующие мастера:

1. Анна Петрова
   • Свободные даты: 15 января, 16 января
   • Время: 10:00-18:00

2. Мария Иванова
   • Свободные даты: 17 января, 18 января
   • Время: 12:00-20:00

Для окончательной записи обратитесь к администратору салона.

Пользователь: хочу к Анне на 15 января
Бот: Отлично! Анна Петрова доступна 15 января...
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |
| `TELEGRAM_MAX_MESSAGE_LENGTH` | Максимальная длина сообщения | `4096` |
| `TELEGRAM_CONTEXT_TTL_HOURS` | Время жизни контекста (часы) | `24` |
| `TELEGRAM_MAX_CONTEXT_MESSAGES` | Максимум сообщений в контексте | `20` |
| `TELEGRAM_ENABLE_BUTTONS` | Включить кнопки быстрых действий | `True` |

### Настройки производительности

Бот автоматически использует настройки производительности из основной конфигурации:

```bash
# Быстрый режим (короткие ответы)
python start_telegram_bot.py --performance speed

# Качественный режим (подробные ответы)
python start_telegram_bot.py --performance quality

# Сбалансированный режим
python start_telegram_bot.py --performance balanced
```

## 🧠 Управление контекстом

### Как работает контекст

1. **Создание**: Контекст создается при первом сообщении пользователя
2. **Сохранение**: Все сообщения сохраняются в памяти бота
3. **Передача в RAG**: При каждом запросе последние 5 сообщений передаются в RAG-систему
4. **Очистка**: Контекст автоматически удаляется через 24 часа неактивности
5. **Ограничения**: Максимум 20 сообщений на пользователя

### Структура контекста

```python
{
    "user_id": 12345,
    "messages": [
        {
            "role": "user",
            "content": "Хочу массаж лица",
            "timestamp": "2024-01-15T10:30:00",
            "metadata": {}
        },
        {
            "role": "assistant", 
            "content": "Рекомендую классический массаж...",
            "timestamp": "2024-01-15T10:30:05",
            "metadata": {}
        }
    ],
    "last_services": ["service-1", "service-2"],
    "user_preferences": {},
    "created_at": "2024-01-15T10:30:00",
    "last_activity": "2024-01-15T10:35:00"
}
```

## 🔧 Разработка и отладка

### Режим разработки

```bash
python start_telegram_bot.py --mode development
```

В режиме разработки:
- Включено подробное логирование (DEBUG)
- Показываются дополнительные сообщения об ошибках
- Логируются все операции с контекстом

### Тестирование

```bash
# Запуск тестов бота
python -m pytest tests/test_telegram_bot.py -v

# Тестирование с покрытием
python -m pytest tests/test_telegram_bot.py --cov=beauty_salon_rag.telegram_bot
```

### Логирование

Бот создает подробные логи:

```
logs/
├── beauty_salon_rag_telegram.log      # Основные операции бота
├── beauty_salon_rag_performance.log   # Метрики производительности
└── beauty_salon_rag_errors.log        # Ошибки и исключения
```

### Мониторинг

Для мониторинга работы бота используйте:

```bash
# Просмотр логов в реальном времени
tail -f logs/beauty_salon_rag_telegram.log

# Статистика ошибок
grep "ERROR" logs/beauty_salon_rag_telegram.log | tail -20

# Активные пользователи
grep "Created new context" logs/beauty_salon_rag_telegram.log | wc -l
```

## 🛠️ API для разработчиков

### Основные классы

#### ConversationContext

```python
from beauty_salon_rag.telegram_bot import ConversationContext

# Создание контекста
context = ConversationContext(user_id=12345)

# Добавление сообщения
context.add_message("user", "Привет!", {"source": "telegram"})

# Получение резюме
summary = context.get_context_summary()

# Проверка истечения
is_expired = context.is_expired(ttl_hours=24)
```

#### TelegramBot

```python
from beauty_salon_rag.telegram_bot import TelegramBot

# Создание бота
bot = TelegramBot()

# Получение/создание контекста
context = bot.get_or_create_context(user_id=12345)

# Улучшение запроса контекстом
enhanced_query = bot._enhance_query_with_context("вопрос", context)

# Разбиение длинного сообщения
parts = bot._split_long_message("длинное сообщение...")
```

### Расширение функциональности

#### Добавление новых команд

```python
@log_operation("telegram_custom_command")
async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользовательская команда."""
    await update.message.reply_text("Пользовательский ответ")

# Регистрация команды
application.add_handler(CommandHandler("custom", self.custom_command))
```

#### Добавление кнопок

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = [
    [InlineKeyboardButton("Новая кнопка", callback_data="new_action")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text("Сообщение", reply_markup=reply_markup)
```

## 🚨 Обработка ошибок

### Типы ошибок

1. **Ошибки Telegram API**: Проблемы с отправкой сообщений
2. **Ошибки RAG-системы**: Проблемы с обработкой запросов
3. **Ошибки контекста**: Проблемы с сохранением истории
4. **Ошибки конфигурации**: Неправильные настройки

### Стратегии обработки

- **Graceful degradation**: При ошибках RAG-системы бот продолжает работать
- **Retry logic**: Автоматические повторы для временных ошибок
- **User feedback**: Понятные сообщения об ошибках для пользователей
- **Logging**: Подробное логирование всех ошибок

## 📊 Метрики и аналитика

### Доступные метрики

- Количество активных пользователей
- Среднее количество сообщений на пользователя
- Время отклика на запросы
- Частота использования команд
- Типы запросов пользователей

### Сбор метрик

```python
# Пример сбора метрик
def collect_metrics(self):
    return {
        "active_users": len(self.contexts),
        "total_messages": sum(len(ctx.messages) for ctx in self.contexts.values()),
        "avg_messages_per_user": total_messages / len(self.contexts) if self.contexts else 0
    }
```

## 🔒 Безопасность

### Рекомендации

1. **Токен бота**: Храните токен в переменных окружения, не в коде
2. **Rate limiting**: Ограничивайте количество запросов от одного пользователя
3. **Валидация входных данных**: Проверяйте все пользовательские сообщения
4. **Логирование**: Не логируйте персональные данные пользователей
5. **Контекст**: Регулярно очищайте старые контексты

### Пример защиты от спама

```python
class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests.get(user_id, [])
        
        # Удаляем старые запросы
        user_requests = [req_time for req_time in user_requests 
                        if now - req_time < self.window_seconds]
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        self.requests[user_id] = user_requests
        return True
```

## 🎯 Лучшие практики

### Для пользователей

1. **Четкие запросы**: Формулируйте вопросы конкретно
2. **Контекст**: Используйте уточняющие вопросы в рамках диалога
3. **Команды**: Изучите доступные команды для эффективной работы

### Для разработчиков

1. **Асинхронность**: Используйте async/await для всех операций
2. **Обработка ошибок**: Всегда обрабатывайте исключения
3. **Логирование**: Логируйте важные операции и ошибки
4. **Тестирование**: Покрывайте код тестами
5. **Документация**: Документируйте новые функции

---

**Версия**: 1.0.0  
**Совместимость**: python-telegram-bot >= 20.0  
**Последнее обновление**: Август 2024