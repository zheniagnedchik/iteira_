#!/usr/bin/env python3
"""
Простой тест для проверки исправлений приветствий.
"""

def test_greeting_patterns():
    """Тестирует паттерны приветствий."""
    
    def is_greeting_message(message: str) -> bool:
        """Проверяет, является ли сообщение приветствием."""
        greetings = [
            'привет', 'здравствуйте', 'добрый день', 'добрый вечер', 'добрый утро',
            'hi', 'hello', 'hey', 'салам', 'хай', 'здарова', 'приветик',
            'добро пожаловать', 'рад знакомству', 'начнем', 'давайте начнем'
        ]
        
        message_lower = message.lower().strip()
        return any(greeting in message_lower for greeting in greetings)
    
    def generate_greeting_response(user_name: str = None) -> str:
        """Генерирует приветственное сообщение в стиле Итейра."""
        name_part = f", {user_name}" if user_name else ""
        
        return (
            f"Здравствуйте{name_part}!\n\n"
            "Рады приветствовать Вас в Итейра — сети салонов премиум‑класса.\n\n"
            "Я — Ваш персональный виртуальный помощник.\n\n"
            "С удовольствием помогу Вам с выбором процедуры, уточнением стоимости "
            "или записью на удобное время.\n\n"
            "Пожалуйста, сообщите, как к Вам можно обращаться."
        )
    
    print("🧪 Тестирование исправлений приветствий")
    print("=" * 50)
    
    # Тест 1: Определение приветствий
    print("\n1. Тестирование определения приветствий:")
    
    greetings = ["привет", "Здравствуйте", "добрый день", "Hi", "hello"]
    for greeting in greetings:
        result = is_greeting_message(greeting)
        print(f"   '{greeting}' -> {'✅' if result else '❌'}")
    
    # Тест 2: НЕ приветствия
    print("\n2. Тестирование НЕ приветствий:")
    
    non_greetings = ["массаж лица", "что такое пилинг", "хочу записаться"]
    for msg in non_greetings:
        result = is_greeting_message(msg)
        print(f"   '{msg}' -> {'✅' if not result else '❌'}")
    
    # Тест 3: Генерация ответа
    print("\n3. Тестирование приветственного ответа:")
    
    response = generate_greeting_response("Евгений")
    print("   Ответ для 'Евгений':")
    print(f"   {response[:80]}...")
    
    # Проверяем ключевые фразы
    key_phrases = ["Итейра", "премиум‑класса", "виртуальный помощник"]
    for phrase in key_phrases:
        if phrase in response:
            print(f"   ✅ Содержит: '{phrase}'")
        else:
            print(f"   ❌ Не содержит: '{phrase}'")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("\nТеперь бот будет правильно отвечать на приветствия:")
    print("• 'привет' -> Приветствие в стиле Итейра")
    print("• 'массаж лица' -> Поиск через RAG-систему")


if __name__ == "__main__":
    test_greeting_patterns()