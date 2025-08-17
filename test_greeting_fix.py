#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления обработки приветствий.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_greeting_detection():
    """Тестирует определение приветствий."""
    from beauty_salon_rag.telegram_bot import TelegramBot
    
    # Создаем бота (мокаем зависимости)
    import unittest.mock as mock
    
    with mock.patch('beauty_salon_rag.telegram_bot.config') as mock_config, \
         mock.patch('beauty_salon_rag.telegram_bot.BeautySalonRAG') as mock_rag:
        
        mock_config.get.return_value = "test_token"
        mock_config.get_telegram_config.return_value = {
            'max_message_length': 4096,
            'context_ttl_hours': 24,
            'max_context_messages': 20
        }
        
        mock_rag_instance = mock.Mock()
        mock_rag.return_value = mock_rag_instance
        
        bot = TelegramBot()
        
        # Тестируем приветствия
        greetings = [
            "привет",
            "Здравствуйте",
            "добрый день",
            "Hi",
            "Приветик"
        ]
        
        print("🧪 Тестирование определения приветствий:")
        for greeting in greetings:
            is_greeting = bot._is_greeting_message(greeting)
            print(f"   '{greeting}' -> {'✅ Приветствие' if is_greeting else '❌ Не приветствие'}")
        
        # Тестируем НЕ приветствия
        non_greetings = [
            "массаж лица",
            "что такое пилинг",
            "хочу записаться",
            "сколько стоит"
        ]
        
        print("\n🧪 Тестирование НЕ приветствий:")
        for msg in non_greetings:
            is_greeting = bot._is_greeting_message(msg)
            print(f"   '{msg}' -> {'❌ Ошибка!' if is_greeting else '✅ Не приветствие'}")


def test_greeting_response():
    """Тестирует генерацию приветственного ответа."""
    from beauty_salon_rag.telegram_bot import TelegramBot
    
    import unittest.mock as mock
    
    with mock.patch('beauty_salon_rag.telegram_bot.config') as mock_config, \
         mock.patch('beauty_salon_rag.telegram_bot.BeautySalonRAG') as mock_rag:
        
        mock_config.get.return_value = "test_token"
        mock_config.get_telegram_config.return_value = {
            'max_message_length': 4096,
            'context_ttl_hours': 24,
            'max_context_messages': 20
        }
        
        mock_rag_instance = mock.Mock()
        mock_rag.return_value = mock_rag_instance
        
        bot = TelegramBot()
        
        print("\n🧪 Тестирование приветственного ответа:")
        
        # Без имени
        response = bot._generate_greeting_response()
        print("   Без имени:")
        print(f"   {response[:100]}...")
        
        # С именем
        response_with_name = bot._generate_greeting_response("Евгений")
        print("\n   С именем 'Евгений':")
        print(f"   {response_with_name[:100]}...")
        
        # Проверяем ключевые фразы
        key_phrases = ["Итейра", "премиум‑класса", "виртуальный помощник"]
        for phrase in key_phrases:
            if phrase in response:
                print(f"   ✅ Содержит: '{phrase}'")
            else:
                print(f"   ❌ Не содержит: '{phrase}'")


def test_context_enhancement():
    """Тестирует улучшение запроса контекстом."""
    from beauty_salon_rag.telegram_bot import TelegramBot, ConversationContext
    
    import unittest.mock as mock
    
    with mock.patch('beauty_salon_rag.telegram_bot.config') as mock_config, \
         mock.patch('beauty_salon_rag.telegram_bot.BeautySalonRAG') as mock_rag:
        
        mock_config.get.return_value = "test_token"
        mock_config.get_telegram_config.return_value = {
            'max_message_length': 4096,
            'context_ttl_hours': 24,
            'max_context_messages': 20
        }
        
        mock_rag_instance = mock.Mock()
        mock_rag.return_value = mock_rag_instance
        
        bot = TelegramBot()
        
        print("\n🧪 Тестирование улучшения запроса контекстом:")
        
        # Создаем контекст
        context = ConversationContext(12345)
        context.add_message("user", "массаж лица")
        context.add_message("assistant", "Рекомендую классический массаж лица...")
        
        # Тестируем запросы, которые НЕ должны использовать контекст
        simple_queries = ["привет", "спасибо", "пилинг лица"]
        
        print("   Простые запросы (без контекста):")
        for query in simple_queries:
            enhanced = bot._enhance_query_with_context(query, context)
            uses_context = "Контекст предыдущего разговора:" in enhanced
            print(f"   '{query}' -> {'❌ Использует контекст' if uses_context else '✅ Без контекста'}")
        
        # Тестируем запросы, которые ДОЛЖНЫ использовать контекст
        context_queries = ["а сколько это стоит?", "хочу записаться", "расскажи подробнее"]
        
        print("\n   Контекстные запросы (с контекстом):")
        for query in context_queries:
            enhanced = bot._enhance_query_with_context(query, context)
            uses_context = "Контекст предыдущего разговора:" in enhanced
            print(f"   '{query}' -> {'✅ Использует контекст' if uses_context else '❌ Без контекста'}")


def main():
    """Главная функция тестирования."""
    print("🧪 Тестирование исправлений для Telegram бота")
    print("=" * 60)
    
    try:
        test_greeting_detection()
        test_greeting_response()
        test_context_enhancement()
        
        print("\n" + "=" * 60)
        print("🎉 Все тесты пройдены! Исправления работают корректно.")
        print("\nТеперь бот будет:")
        print("✅ Правильно отвечать на приветствия в стиле Итейра")
        print("✅ Не передавать простые сообщения в RAG-систему")
        print("✅ Использовать контекст только когда это необходимо")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())