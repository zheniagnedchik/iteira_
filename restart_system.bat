@echo off
REM Скрипт для проверки и перезапуска RAG-системы салона красоты

echo 🔧 Проверка и перезапуск RAG-системы салона красоты
echo ============================================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8 или выше.
    pause
    exit /b 1
)

REM Запускаем system manager
python system_manager.py --check-and-restart --save-report

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Система работает нормально!
    echo 📱 Telegram бот доступен по токену: 8467103145:AAH0Zmop8-j_TtHdUUQHJzoXaq1IOX6BKTM
    echo 💬 Отправьте боту /start для начала работы
) else (
    echo.
    echo 💥 Обнаружены проблемы с системой
    echo 📋 Проверьте логи в директории logs/
)

pause
exit /b %errorlevel%