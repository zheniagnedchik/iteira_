@echo off
REM Скрипт запуска RAG-системы салона красоты для Windows

echo 🌸 RAG-система салона красоты 🌸
echo ================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8 или выше.
    pause
    exit /b 1
)

REM Запускаем систему с переданными аргументами
python start.py %*

REM Если запуск без аргументов, ждем нажатия клавиши
if "%1"=="" (
    pause
)