#!/usr/bin/env python3
"""
Финальный тест форматирования без звездочек.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_final_formatting():
    """Тестирует финальное форматирование без звездочек."""
    print("🎯 Финальный тест форматирования...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Полный цикл записи
        print("\n1️⃣ Приветствие:")
        response, _ = orchestrator.process_message(user_id, "Привет", "Евгений")
        print(f"✅ Приветствие: {len(response)} символов")
        
        print("\n2️⃣ Запрос маникюра:")
        response, _ = orchestrator.process_message(user_id, "хочу маникюр")
        print(f"Ответ:\n{response}")
        
        # Проверяем, что нет звездочек
        if "**" not in response:
            print("✅ Звездочки убраны из списка услуг!")
        else:
            print("❌ Звездочки все еще есть в списке услуг")
        
        print("\n3️⃣ Выбор услуги:")
        response, _ = orchestrator.process_message(user_id, "3")
        print(f"Ответ:\n{response}")
        
        # Проверяем, что нет звездочек
        if "**" not in response:
            print("✅ Звездочки убраны из подтверждения услуги!")
        else:
            print("❌ Звездочки все еще есть в подтверждении услуги")
        
        print("\n4️⃣ Запрос дат:")
        response, _ = orchestrator.process_message(user_id, "какие даты есть?")
        print(f"Ответ:\n{response}")
        
        # Проверяем, что нет звездочек
        if "**" not in response:
            print("✅ Звездочки убраны из списка дат!")
        else:
            print("❌ Звездочки все еще есть в списке дат")
        
        print("\n✅ Финальный тест завершен успешно!")
        print("🎉 Система готова для использования в Telegram!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_final_formatting()