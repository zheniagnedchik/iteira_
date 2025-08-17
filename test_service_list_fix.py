#!/usr/bin/env python3
"""
Тест исправления показа списка услуг.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_service_list():
    """Тестирует показ списка услуг."""
    print("🧪 Тестирование показа списка услуг...")
    
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
        response, metadata = orchestrator.process_message(user_id, "Привет", "Анна")
        print(f"Ответ: {response[:100]}...")
        
        # Тест 2: Запрос маникюра
        print("\n2️⃣ Запрос маникюра:")
        response, metadata = orchestrator.process_message(user_id, "хочу маникюр")
        print(f"Ответ: {response}")
        print(f"Метаданные: {metadata}")
        
        # Проверяем, есть ли в ответе список услуг
        if "1." in response and "💰" in response:
            print("✅ Список услуг отображается корректно!")
        else:
            print("❌ Список услуг НЕ отображается!")
        
        # Тест 3: Еще один запрос
        print("\n3️⃣ Запрос 'покажи':")
        response, metadata = orchestrator.process_message(user_id, "покажи")
        print(f"Ответ: {response}")
        print(f"Метаданные: {metadata}")
        
        # Тест 4: Запрос массажа
        print("\n4️⃣ Запрос массажа:")
        response, metadata = orchestrator.process_message(user_id, "хочу массаж")
        print(f"Ответ: {response}")
        print(f"Метаданные: {metadata}")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_service_list()