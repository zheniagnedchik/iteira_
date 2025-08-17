#!/usr/bin/env python3
"""
Тест красивого форматирования сообщений.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_beautiful_formatting():
    """Тестирует красивое форматирование сообщений."""
    print("🎨 Тестирование красивого форматирования...")
    
    try:
        # Инициализируем RAG-систему
        print("📚 Инициализация RAG-системы...")
        rag_system = BeautySalonRAG()
        
        # Инициализируем оркестратор
        print("🎭 Инициализация оркестратора...")
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Тест 1: Приветствие
        print("\n1️⃣ Приветствие:")
        response, metadata = orchestrator.process_message(user_id, "Привет", "Евгений")
        print(f"Ответ: {response[:100]}...")
        
        # Тест 2: Выбор маникюра
        print("\n2️⃣ Выбор маникюра:")
        response, metadata = orchestrator.process_message(user_id, "хочу маникюр")
        print(f"Ответ:\n{response}")
        
        # Тест 3: Выбор услуги
        print("\n3️⃣ Выбор услуги №3:")
        response, metadata = orchestrator.process_message(user_id, "3")
        print(f"Ответ:\n{response}")
        
        # Тест 4: Запрос дат
        print("\n4️⃣ Запрос дат:")
        response, metadata = orchestrator.process_message(user_id, "какие даты есть?")
        print(f"Ответ:\n{response}")
        
        # Тест 5: Запрос о мастерах
        print("\n5️⃣ Запрос о мастерах:")
        response, metadata = orchestrator.process_message(user_id, "кто его делает?")
        print(f"Ответ:\n{response}")
        
        print("\n✅ Тестирование форматирования завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_beautiful_formatting()