#!/usr/bin/env python3
"""
Простой скрипт для быстрого перезапуска бота
"""

import subprocess
import sys
import os

def main():
    """Быстрый перезапуск"""
    print("🔄 Быстрый перезапуск Telegram бота...")
    
    try:
        # Запускаем полный скрипт перезапуска
        result = subprocess.run([sys.executable, "restart_telegram_bot.py"], check=True)
        print("✅ Перезапуск завершен")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка перезапуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
