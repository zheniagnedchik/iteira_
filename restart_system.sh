#!/bin/bash
# Скрипт для проверки и перезапуска RAG-системы салона красоты

echo "🔧 Проверка и перезапуск RAG-системы салона красоты"
echo "============================================================"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python не найден. Установите Python 3.8 или выше."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Запускаем system manager
$PYTHON_CMD system_manager.py --check-and-restart --save-report

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 Система работает нормально!"
    echo "📱 Telegram бот доступен по токену: 8467103145:AAH0Zmop8-j_TtHdUUQHJzoXaq1IOX6BKTM"
    echo "💬 Отправьте боту /start для начала работы"
else
    echo ""
    echo "💥 Обнаружены проблемы с системой"
    echo "📋 Проверьте логи в директории logs/"
fi

exit $exit_code