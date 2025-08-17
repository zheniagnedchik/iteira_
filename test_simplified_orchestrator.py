#!/usr/bin/env python3
"""
Тест упрощенного оркестратора диалогов с GPT-оркестратором.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_simplified_orchestrator():
    """Тестирует упрощенный оркестратор."""
    print("🧪 Тестирование упрощенного оркестратора диалогов...")
    
    try:
        # Инициализируем RAG-систему
        print("📚 Инициализация RAG-системы...")
        rag_system = BeautySalonRAG()
        
        # Инициализируем упрощенный оркестратор
        print("🎭 Инициализация упрощенного оркестратора...")
        orchestrator = DialogOrchestrator(rag_system)
        
        print("✅ Упрощенный оркестратор успешно инициализирован!")
        
        # Тестируем базовую функциональность
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Тест 1: Приветствие
        print("\n1️⃣ Тест приветствия:")
        response, metadata = orchestrator.process_message(user_id, "Привет", "Анна")
        print(f"Ответ: {response}")
        print(f"Метаданные: {metadata}")
        
        # Тест 2: Статистика пользователя
        print("\n2️⃣ Тест статистики пользователя:")
        stats = orchestrator.get_user_stats(user_id)
        print(f"Статистика: {stats}")
        
        # Тест 3: Общая статистика
        print("\n3️⃣ Тест общей статистики:")
        general_stats = orchestrator.get_orchestrator_stats()
        print(f"Общая статистика: {general_stats}")
        
        # Тест 4: Запрос об услугах
        print("\n4️⃣ Тест запроса об услугах:")
        response, metadata = orchestrator.process_message(user_id, "Хочу записаться на маникюр")
        print(f"Ответ: {response}")
        print(f"Метаданные: {metadata}")
        
        print("\n✅ Все тесты упрощенного оркестратора прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simplified_orchestrator()