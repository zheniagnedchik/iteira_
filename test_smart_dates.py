#!/usr/bin/env python3
"""
Тест умного отображения дат.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_smart_dates():
    """Тестирует умное отображение дат."""
    print("🧠 Тестирование умного отображения дат...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Полный цикл до дат
        print("\n1️⃣ Выбор маникюра:")
        response, _ = orchestrator.process_message(user_id, "хочу маникюр")
        print(f"✅ Услуги показаны")
        
        print("\n2️⃣ Выбор услуги №3:")
        response, _ = orchestrator.process_message(user_id, "3")
        print(f"✅ Услуга выбрана")
        
        print("\n3️⃣ Запрос дат (умное отображение):")
        response, metadata = orchestrator.process_message(user_id, "какие даты есть?")
        print(f"Ответ:\n{response}")
        print(f"Метаданные: {metadata}")
        
        # Проверяем умное форматирование
        if "🔥 Ближайшие дни:" in response:
            print("✅ Умное группирование дат работает!")
        else:
            print("❌ Умное группирование дат НЕ работает")
        
        if "И еще" in response:
            print("✅ Показывается количество оставшихся дат!")
        else:
            print("❌ Количество оставшихся дат НЕ показывается")
        
        print("\n4️⃣ Тест запроса всех дат:")
        response, metadata = orchestrator.process_message(user_id, "все даты")
        print(f"Ответ (первые 200 символов): {response[:200]}...")
        print(f"Метаданные: {metadata}")
        
        print("\n✅ Тестирование умных дат завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_smart_dates()