#!/usr/bin/env python3
"""
Тест исправления сохранения контекста.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_context_preservation():
    """Тестирует сохранение контекста между вызовами."""
    print("🔄 Тестирование сохранения контекста...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Шаг 1: Выбираем маникюр
        print("\n1️⃣ Выбор маникюра:")
        response, metadata = orchestrator.process_message(user_id, "хочу маникюр")
        print(f"Ответ: {response[:100]}...")
        
        # Шаг 2: Выбираем услугу №3
        print("\n2️⃣ Выбор услуги №3:")
        response, metadata = orchestrator.process_message(user_id, "3")
        print(f"Ответ: {response[:100]}...")
        print(f"Метаданные: {metadata}")
        
        # Проверяем контекст пользователя
        context = orchestrator.gpt_orchestrator.get_user_context(user_id)
        print(f"\n🔍 Контекст пользователя:")
        print(f"- Выбранная услуга: {context.get('selected_service', {}).get('title', 'НЕТ')}")
        print(f"- Доступные услуги: {len(context.get('available_services', []))}")
        print(f"- История диалога: {len(context.get('dialog_history', []))}")
        
        # Шаг 3: Запрашиваем даты
        print("\n3️⃣ Запрос дат:")
        response, metadata = orchestrator.process_message(user_id, "какие даты есть?")
        print(f"Ответ: {response[:200]}...")
        print(f"Метаданные: {metadata}")
        
        # Проверяем, что даты отображаются красиво
        if "📅" in response and "**" in response:
            print("✅ Даты отображаются с красивым форматированием!")
        else:
            print("❌ Даты НЕ отображаются красиво")
        
        print("\n✅ Тестирование контекста завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_context_preservation()