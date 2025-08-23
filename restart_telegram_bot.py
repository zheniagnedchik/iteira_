#!/usr/bin/env python3
"""
Скрипт для перезапуска Telegram бота
Останавливает текущий процесс и запускает новый
"""

import os
import sys
import subprocess
import time
import signal

def find_bot_processes():
    """Находит все процессы бота"""
    try:
        # Ищем процессы с telegram в названии
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        current_pid = os.getpid()  # Получаем PID текущего процесса
        bot_pids = []
        
        for line in result.stdout.split('\n'):
            if 'python' in line and 'start_telegram_bot.py' in line:
                # Извлекаем PID (второй столбец)
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        # Исключаем собственный процесс
                        if pid != current_pid:
                            bot_pids.append(pid)
                    except ValueError:
                        continue
        
        return bot_pids
    except subprocess.CalledProcessError:
        return []

def stop_bot_processes():
    """Останавливает все процессы бота"""
    pids = find_bot_processes()
    
    if not pids:
        print("✅ Процессы бота не найдены")
        return True
    
    print(f"🔍 Найдено процессов бота: {len(pids)}")
    
    for pid in pids:
        try:
            print(f"🛑 Останавливаю процесс {pid}...")
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            
            # Проверяем, что процесс завершился
            try:
                os.kill(pid, 0)  # Проверяем существование процесса
                print(f"⚠️  Процесс {pid} не завершился, принудительно убиваю...")
                os.kill(pid, signal.SIGKILL)
            except OSError:
                print(f"✅ Процесс {pid} успешно завершен")
                
        except OSError as e:
            print(f"⚠️  Ошибка при завершении процесса {pid}: {e}")
    
    # Ждем немного для полного завершения
    time.sleep(2)
    
    # Проверяем, что все процессы завершены
    remaining_pids = find_bot_processes()
    if remaining_pids:
        print(f"⚠️  Остались активные процессы: {remaining_pids}")
        return False
    else:
        print("✅ Все процессы бота успешно остановлены")
        return True

def start_bot():
    """Запускает бота"""
    print("🚀 Запускаю Telegram бота...")
    
    try:
        # Запускаем бота в фоне
        process = subprocess.Popen(
            [sys.executable, "start_telegram_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Ждем немного, чтобы убедиться, что процесс запустился
        time.sleep(3)
        
        # Проверяем статус процесса
        if process.poll() is None:
            print(f"✅ Бот успешно запущен (PID: {process.pid})")
            print("🔄 Бот работает в фоновом режиме")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Ошибка запуска бота:")
            if stderr:
                print(f"STDERR: {stderr.decode()}")
            if stdout:
                print(f"STDOUT: {stdout.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        return False

def check_bot_status():
    """Проверяет статус бота"""
    pids = find_bot_processes()
    if pids:
        print(f"✅ Бот работает (PID: {pids})")
        return True
    else:
        print("❌ Бот не запущен")
        return False

def main():
    """Основная функция перезапуска"""
    print("🔄 Перезапуск Telegram бота")
    print("=" * 40)
    
    # Проверяем текущий статус
    print("\n1️⃣ Проверка текущего статуса...")
    check_bot_status()
    
    # Останавливаем текущие процессы
    print("\n2️⃣ Остановка текущих процессов...")
    if not stop_bot_processes():
        print("❌ Не удалось полностью остановить все процессы")
        return False
    
    # Запускаем бота
    print("\n3️⃣ Запуск нового процесса...")
    if not start_bot():
        print("❌ Не удалось запустить бота")
        return False
    
    # Финальная проверка
    print("\n4️⃣ Финальная проверка...")
    time.sleep(2)
    if check_bot_status():
        print("\n🎉 Перезапуск успешно завершен!")
        print("💡 Для просмотра логов используйте: tail -f logs/beauty_salon_rag.log")
        return True
    else:
        print("\n❌ Перезапуск не удался")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
