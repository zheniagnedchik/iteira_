#!/usr/bin/env python3
"""
Простой скрипт запуска RAG-системы салона красоты.
Обеспечивает удобный запуск системы с различными режимами и опциями.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.config import config
from beauty_salon_rag.logger import setup_logging


def check_dependencies() -> bool:
    """
    Проверяет наличие необходимых зависимостей.
    
    Returns:
        True если все зависимости установлены
    """
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        'openai',
        'dotenv'  # python-dotenv imports as 'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Все зависимости установлены")
    return True


def check_data_files() -> bool:
    """
    Проверяет наличие файлов данных.
    
    Returns:
        True если файлы данных найдены
    """
    print("📁 Проверка файлов данных...")
    
    services_file = Path(config.get('data.services_file', 'services.json'))
    services_no_staff_file = Path(config.get('data.services_no_staff_file', 'services_no_staff.json'))
    
    missing_files = []
    
    if not services_file.exists():
        missing_files.append(str(services_file))
    
    if not services_no_staff_file.exists():
        missing_files.append(str(services_no_staff_file))
    
    if missing_files:
        print(f"❌ Отсутствуют файлы данных: {', '.join(missing_files)}")
        print("Убедитесь, что файлы данных находятся в корневой директории проекта")
        return False
    
    print("✅ Файлы данных найдены")
    return True


def check_api_key() -> bool:
    """
    Проверяет наличие API ключа OpenAI.
    
    Returns:
        True если API ключ настроен
    """
    print("🔑 Проверка API ключа OpenAI...")
    
    try:
        api_key = config.get_openai_key()
        if api_key and len(api_key) > 10:  # Минимальная проверка длины
            print("✅ API ключ OpenAI настроен")
            return True
        else:
            print("❌ API ключ OpenAI не настроен или некорректен")
            return False
    except Exception:
        print("❌ API ключ OpenAI не найден")
        print("Создайте файл .env и добавьте в него:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False


def setup_environment(mode: str = "production", performance: str = "balanced"):
    """
    Настраивает переменные окружения для запуска.
    
    Args:
        mode: Режим работы приложения
        performance: Режим производительности
    """
    print(f"⚙️  Настройка окружения (режим: {mode}, производительность: {performance})...")
    
    # Устанавливаем переменные окружения
    os.environ['APP_MODE'] = mode
    os.environ['PERFORMANCE_MODE'] = performance
    
    # Настройки для разных режимов
    if mode == "development":
        os.environ['DEBUG'] = 'True'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    elif mode == "testing":
        os.environ['DEBUG'] = 'True'
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['INTERACTIVE_MODE'] = 'False'
    else:  # production
        os.environ['DEBUG'] = 'False'
        os.environ['LOG_LEVEL'] = 'INFO'
    
    print("✅ Окружение настроено")


def run_system_check() -> bool:
    """
    Выполняет полную проверку системы.
    
    Returns:
        True если система готова к запуску
    """
    print("🧪 Выполнение проверки системы...")
    print("=" * 50)
    
    checks = [
        ("Зависимости", check_dependencies),
        ("Файлы данных", check_data_files),
        ("API ключ", check_api_key)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ Ошибка при проверке {check_name}: {e}")
            all_passed = False
        print()
    
    print("=" * 50)
    if all_passed:
        print("🎉 Все проверки пройдены! Система готова к запуску.")
    else:
        print("💥 Обнаружены проблемы. Исправьте их перед запуском системы.")
    
    return all_passed


def start_interactive_mode():
    """Запускает интерактивный режим системы."""
    print("🚀 Запуск интерактивного режима...")
    print("=" * 50)
    
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n👋 Работа системы завершена пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка при запуске системы: {e}")
        sys.exit(1)


def run_single_query(query: str):
    """
    Выполняет один запрос без интерактивного режима.
    
    Args:
        query: Запрос пользователя
    """
    print(f"🔍 Обработка запроса: '{query}'")
    print("=" * 50)
    
    try:
        from main import BeautySalonRAG
        
        # Отключаем интерактивный режим
        os.environ['INTERACTIVE_MODE'] = 'False'
        
        rag_system = BeautySalonRAG()
        response = rag_system.process_query(query)
        
        print("\n💬 Ответ системы:")
        print("-" * 30)
        print(response)
        print("-" * 30)
        
    except Exception as e:
        print(f"💥 Ошибка при обработке запроса: {e}")
        sys.exit(1)


def run_tests():
    """Запускает тесты системы."""
    print("🧪 Запуск тестов системы...")
    print("=" * 50)
    
    try:
        # Запускаем скрипт тестирования
        result = subprocess.run([sys.executable, "run_tests.py", "--smoke"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Все тесты пройдены успешно!")
        else:
            print("\n❌ Обнаружены ошибки в тестах")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Файл run_tests.py не найден")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Ошибка при запуске тестов: {e}")
        sys.exit(1)


def run_full_system_test():
    """Запускает полное системное тестирование."""
    print("🔬 Запуск полного системного тестирования...")
    print("=" * 50)
    
    try:
        # Запускаем полное системное тестирование
        result = subprocess.run([sys.executable, "test_full_system.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Полное тестирование завершено успешно!")
        else:
            print("\n❌ Обнаружены проблемы при полном тестировании")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Файл test_full_system.py не найден")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Ошибка при полном тестировании: {e}")
        sys.exit(1)


def main():
    """Главная функция скрипта запуска."""
    parser = argparse.ArgumentParser(
        description="Скрипт запуска RAG-системы салона красоты",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python start.py                          # Интерактивный режим
  python start.py --check                  # Проверка системы
  python start.py --query "массаж лица"    # Одиночный запрос
  python start.py --test                   # Быстрые тесты
  python start.py --full-test              # Полное тестирование
  python start.py --mode development       # Режим разработки
  python start.py --performance speed      # Быстрый режим
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["development", "testing", "production"],
        default="production",
        help="Режим работы приложения"
    )
    
    parser.add_argument(
        "--performance",
        choices=["speed", "quality", "balanced"],
        default="balanced", 
        help="Режим производительности"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Выполнить проверку системы без запуска"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Выполнить одиночный запрос без интерактивного режима"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Запустить быстрые тесты системы"
    )
    
    parser.add_argument(
        "--full-test",
        action="store_true",
        help="Запустить полное системное тестирование"
    )
    
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Пропустить проверку системы при запуске"
    )
    
    args = parser.parse_args()
    
    print("🌸 RAG-система салона красоты 🌸")
    print("=" * 50)
    
    # Настройка окружения
    setup_environment(args.mode, args.performance)
    
    # Настройка логирования
    setup_logging()
    
    try:
        # Выполнение действий в зависимости от аргументов
        if args.check:
            # Только проверка системы
            success = run_system_check()
            sys.exit(0 if success else 1)
            
        elif args.test:
            # Быстрые тесты
            if not args.no_check:
                if not run_system_check():
                    sys.exit(1)
            run_tests()
            
        elif args.full_test:
            # Полное тестирование
            if not args.no_check:
                if not run_system_check():
                    sys.exit(1)
            run_full_system_test()
            
        elif args.query:
            # Одиночный запрос
            if not args.no_check:
                if not run_system_check():
                    sys.exit(1)
            run_single_query(args.query)
            
        else:
            # Интерактивный режим (по умолчанию)
            if not args.no_check:
                if not run_system_check():
                    sys.exit(1)
            start_interactive_mode()
    
    except KeyboardInterrupt:
        print("\n\n👋 Работа прервана пользователем")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()