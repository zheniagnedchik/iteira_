#!/usr/bin/env python3
"""
Проверка статуса Telegram бота
"""

import sys
import os
import time
import subprocess

def check_bot_status():
    """Проверяет, запущен ли Telegram бот"""
    
    print("🔍 ПРОВЕРКА СТАТУСА TELEGRAM БОТА")
    print("=" * 50)
    
    # Проверяем процессы
    try:
        result = subprocess.run(['pgrep', '-f', 'start_telegram_bot'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Бот запущен! PID(s): {', '.join(pids)}")
            return True
        else:
            print("❌ Бот не запущен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def wait_for_bot_startup():
    """Ждет запуска бота и проверяет логи"""
    
    print("\n⏳ Ожидание запуска бота...")
    
    for attempt in range(10):  # Максимум 10 попыток
        time.sleep(2)
        
        if check_bot_status():
            print(f"✅ Бот запустился после {(attempt + 1) * 2} секунд")
            
            # Даем еще немного времени для полной инициализации
            time.sleep(3)
            
            # Проверяем логи на ошибки
            try:
                with open('logs/beauty_salon_rag_telegram_bot.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Берем последние 10 строк
                recent_logs = lines[-10:] if len(lines) > 10 else lines
                
                has_errors = False
                has_success = False
                
                for line in recent_logs:
                    if 'ERROR' in line and 'Conflict' in line:
                        has_errors = True
                    elif 'bot is running' in line.lower():
                        has_success = True
                
                if has_errors:
                    print("⚠️  В логах есть ошибки конфликта")
                    return False
                elif has_success:
                    print("🎉 Бот успешно запущен и работает!")
                    return True
                else:
                    print("🔄 Бот запущен, но статус неясен")
                    return True
                    
            except FileNotFoundError:
                print("⚠️  Лог файл не найден, но процесс запущен")
                return True
            except Exception as e:
                print(f"⚠️  Ошибка чтения логов: {e}")
                return True
        
        print(f"⏳ Попытка {attempt + 1}/10...")
    
    print("❌ Бот не запустился за отведенное время")
    return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ПРОВЕРКИ TELEGRAM БОТА")
    print("=" * 50)
    
    if wait_for_bot_startup():
        print("\n🎊 TELEGRAM БОТ ГОТОВ К ТЕСТИРОВАНИЮ!")
        print("\n📱 ИНСТРУКЦИИ ДЛЯ РЕАЛЬНОГО ТЕСТА:")
        print("1. Откройте Telegram")
        print("2. Найдите вашего бота")
        print("3. Начните с сообщения 'Привет'")
        print("\n🎯 ТЕСТ КОМБО-ЗАПИСИ:")
        print("   → 'Привет'")
        print("   → 'Евгений'") 
        print("   → 'хочу записаться на маникюр и окрашивание'")
        print("   → 'классический'")
        print("   → 'Окрашивание'")
        print("   → 'в один день'")
        print("   → Выберите дату")
        print("   → Выберите время")
        print("   → 'ДА'")
        print("\n🔍 Следите за тем, как система обрабатывает каждый этап!")
        
    else:
        print("\n❌ ПРОБЛЕМЫ С ЗАПУСКОМ БОТА")
        print("🛠️  Попробуйте перезапустить вручную:")
        print("   python start_telegram_bot.py")
