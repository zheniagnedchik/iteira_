#!/usr/bin/env python3
"""
Простой скрипт для запуска Telegram бота в фоновом режиме.
"""

import subprocess
import sys
import signal
import time

def signal_handler(sig, frame):
    print('\n👋 Остановка бота...')
    sys.exit(0)

def main():
    print("🤖 Запуск Telegram бота для RAG-системы салона красоты")
    print("=" * 60)
    print("Бот будет работать до нажатия Ctrl+C")
    print("=" * 60)
    
    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Запускаем бота
        process = subprocess.Popen([
            sys.executable, "start_telegram_bot.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        print("✅ Бот запущен! Найдите его в Telegram и отправьте /start")
        print("📱 Токен бота: 8467103145:AAH0Zmop8-j_TtHdUUQHJzoXaq1IOX6BKTM")
        print("💬 Отправьте боту сообщение для тестирования")
        print("\nЛоги бота:")
        print("-" * 40)
        
        # Читаем вывод бота
        for line in process.stdout:
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()