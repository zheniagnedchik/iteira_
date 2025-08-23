#!/bin/bash

# Скрипт для быстрого перезапуска Telegram бота

echo "🔄 Перезапуск Telegram бота..."

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Останавливаем существующие процессы
echo "🛑 Останавливаем существующие процессы..."
pkill -f "python.*telegram" 2>/dev/null || true
pkill -f "start_telegram_bot.py" 2>/dev/null || true

# Ждем завершения процессов
sleep 2

# Запускаем бота
echo "🚀 Запускаем бота..."
python restart_telegram_bot.py

echo "✅ Готово!"
