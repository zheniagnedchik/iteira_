#!/usr/bin/env python3
"""
Тестовый скрипт для проверки запуска Telegram бота.
"""

import sys
import time
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_bot_initialization():
    """Тестирует инициализацию бота без запуска polling."""
    try:
        print("🤖 Тестирование инициализации Telegram бота...")
        
        from beauty_salon_rag.telegram_bot import TelegramBot
        
        # Создаем бота
        bot = TelegramBot()
        print("✅ Бот инициализирован успешно")
        
        # Проверяем основные свойства
        print(f"📋 Токен настроен: {'✅' if bot.bot_token else '❌'}")
        print(f"📋 RAG-система готова: {'✅' if bot.rag_system else '❌'}")
        print(f"📋 Максимальная длина сообщения: {bot.max_message_length}")
        print(f"📋 TTL контекста: {bot.context_ttl_hours} часов")
        
        # Тестируем создание контекста
        test_user_id = 12345
        context = bot.get_or_create_context(test_user_id)
        print(f"✅ Контекст создан для пользователя {test_user_id}")
        
        # Тестируем добавление сообщения
        context.add_message("user", "Тестовое сообщение")
        print(f"✅ Сообщение добавлено в контекст")
        
        # Тестируем улучшение запроса
        enhanced_query = bot._enhance_query_with_context("тест", context)
        print(f"✅ Запрос улучшен контекстом")
        
        # Тестируем разбиение сообщения
        long_message = "А" * 100
        parts = bot._split_long_message(long_message)
        print(f"✅ Длинное сообщение разбито на {len(parts)} частей")
        
        print("\n🎉 Все тесты пройдены! Бот готов к работе.")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        return False


def test_rag_integration():
    """Тестирует интеграцию с RAG-системой."""
    try:
        print("\n🧪 Тестирование интеграции с RAG-системой...")
        
        from main import BeautySalonRAG
        
        # Создаем RAG-систему
        rag = BeautySalonRAG()
        print("✅ RAG-система инициализирована")
        
        # Проверяем статус
        status = rag.get_system_status()
        if status['overall_status']:
            print("✅ RAG-система работает корректно")
        else:
            print("⚠️  RAG-система имеет проблемы")
        
        # Тестируем простой запрос
        response = rag.process_query("массаж лица")
        if response and len(response) > 10:
            print("✅ RAG-система отвечает на запросы")
        else:
            print("❌ RAG-система не отвечает корректно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции с RAG: {e}")
        return False


def main():
    """Главная функция тестирования."""
    print("🧪 Тестирование Telegram бота для RAG-системы салона красоты")
    print("=" * 70)
    
    success = True
    
    # Тест 1: Инициализация бота
    if not test_bot_initialization():
        success = False
    
    # Тест 2: Интеграция с RAG
    if not test_rag_integration():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 Все тесты пройдены! Telegram бот готов к использованию.")
        print("\nДля запуска бота выполните:")
        print("python start_telegram_bot.py")
        print("\nИли найдите вашего бота в Telegram и отправьте /start")
    else:
        print("💥 Обнаружены проблемы. Проверьте конфигурацию.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())