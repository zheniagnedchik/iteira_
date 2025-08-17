#!/bin/bash
# Скрипт запуска RAG-системы салона красоты для Unix/Linux/macOS

echo "🌸 RAG-система салона красоты 🌸"
echo "================================"

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

# Проверяем версию Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ Требуется Python 3.8 или выше. Найдена версия: $PYTHON_VERSION"
    exit 1
fi

# Запускаем систему с переданными аргументами
$PYTHON_CMD start.py "$@"