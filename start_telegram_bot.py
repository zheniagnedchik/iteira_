#!/usr/bin/env python3
"""
Скрипт запуска Telegram бота для RAG-системы салона красоты.
"""

import sys
import os
import argparse
from pathlib import Path

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.config import config
from beauty_salon_rag.logger import setup_logging, get_logger
from beauty_salon_rag.telegram_bot import TelegramBot


def check_telegram_dependencies() -> bool:
    """Проверяет наличие зависимостей для Telegram бота."""
    print("🔍 Проверка зависимостей Telegram бота...")
    
    required_packages = ['telegram']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой:")
        print(f"pip install python-telegram-bot")
        return False
    
    print("✅ Все зависимости для Telegram бота установлены")
    return True


def check_telegram_config() -> bool:
    """Проверяет конфигурацию Telegram бота."""
    print("🔑 Проверка конфигурации Telegram бота...")
    
    try:
        token = config.get_telegram_token()
        if token and len(token) > 10:  # Минимальная проверка длины
            print("✅ Токен Telegram бота настроен")
            return True
        else:
            print("❌ Токен Telegram бота не настроен или некорректен")
            return False
    except Exception:
        print("❌ Токен Telegram бота не найден")
        print("Создайте бота через @BotFather и добавьте токен в .env:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return False


def check_rag_system() -> bool:
    """Проверяет готовность RAG-системы."""
    print("🧪 Проверка RAG-системы...")
    
    try:
        from main import BeautySalonRAG
        
        # Проверяем инициализацию системы
        rag_system = BeautySalonRAG()
        status = rag_system.get_system_status()
        
        if status['overall_status']:
            print("✅ RAG-система готова к работе")
            return True
        else:
            print("❌ RAG-система имеет проблемы:")
            if not status['search_module']:
                print("   - Поисковый модуль недоступен")
            if not status['consultation_module']:
                print("   - Консультационный модуль недоступен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки RAG-системы: {e}")
        return False


def run_system_check() -> bool:
    """Выполняет полную проверку системы для Telegram бота."""
    print("🤖 Проверка готовности Telegram бота...")
    print("=" * 50)
    
    checks = [
        ("Зависимости Telegram", check_telegram_dependencies),
        ("Конфигурация Telegram", check_telegram_config),
        ("RAG-система", check_rag_system)
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
        print("🎉 Все проверки пройдены! Telegram бот готов к запуску.")
    else:
        print("💥 Обнаружены проблемы. Исправьте их перед запуском бота.")
    
    return all_passed


def start_bot():
    """Запускает Telegram бота."""
    print("🚀 Запуск Telegram бота...")
    print("=" * 50)
    
    try:
        bot = TelegramBot()
        print("✅ Бот инициализирован успешно")
        print("🔄 Бот запущен и ожидает сообщения...")
        print("Нажмите Ctrl+C для остановки")
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка при запуске бота: {e}")
        sys.exit(1)


def show_bot_info():
    """Показывает информацию о боте."""
    print("🤖 Информация о Telegram боте")
    print("=" * 50)
    
    try:
        telegram_config = config.get_telegram_config()
        
        print("📋 Настройки бота:")
        print(f"   Максимальная длина сообщения: {telegram_config.get('max_message_length', 4096)}")
        print(f"   TTL контекста (часы): {telegram_config.get('context_ttl_hours', 24)}")
        print(f"   Максимум сообщений в контексте: {telegram_config.get('max_context_messages', 20)}")
        print(f"   Кнопки быстрых действий: {'✅' if telegram_config.get('enable_buttons', True) else '❌'}")
        
        print("\n🎯 Возможности бота:")
        print("   • Поиск процедур салона красоты")
        print("   • Консультации по услугам")
        print("   • Информация о мастерах и записи")
        print("   • Запоминание контекста диалога")
        print("   • Кнопки быстрых действий")
        print("   • Команды управления (/help, /status, /clear)")
        
        print("\n📱 Команды бота:")
        print("   /start - начать диалог")
        print("   /help - справка по использованию")
        print("   /status - статус системы")
        print("   /clear - очистить историю диалога")
        
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")


def main():
    """Главная функция скрипта."""
    parser = argparse.ArgumentParser(
        description="Скрипт запуска Telegram бота для RAG-системы салона красоты",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python start_telegram_bot.py                # Запуск бота
  python start_telegram_bot.py --check        # Проверка готовности
  python start_telegram_bot.py --info         # Информация о боте
  python start_telegram_bot.py --mode development  # Режим разработки
        """
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Выполнить проверку готовности без запуска бота"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Показать информацию о боте"
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
    
    args = parser.parse_args()
    
    print("🤖 Telegram бот для RAG-системы салона красоты")
    print("=" * 50)
    
    # Настройка окружения
    os.environ['APP_MODE'] = args.mode
    os.environ['PERFORMANCE_MODE'] = args.performance
    
    if args.mode == "development":
        os.environ['DEBUG'] = 'True'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Настройка логирования
    setup_logging()
    
    try:
        if args.info:
            # Показать информацию о боте
            show_bot_info()
            
        elif args.check:
            # Только проверка готовности
            success = run_system_check()
            sys.exit(0 if success else 1)
            
        else:
            # Запуск бота
            if run_system_check():
                start_bot()
            else:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 Работа прервана пользователем")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()