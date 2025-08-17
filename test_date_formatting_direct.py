#!/usr/bin/env python3
"""
Прямой тест форматирования дат.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.gpt_orchestrator import GPTOrchestrator


def test_date_formatting_direct():
    """Тестирует форматирование дат напрямую."""
    print("🔧 Прямой тест форматирования дат...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = GPTOrchestrator(rag_system)
        
        # Создаем тестовые даты
        test_dates = [
            "14.08.2025", "15.08.2025", "16.08.2025", "17.08.2025", "18.08.2025",
            "19.08.2025", "20.08.2025", "21.08.2025", "22.08.2025", "23.08.2025",
            "24.08.2025", "25.08.2025", "26.08.2025", "27.08.2025", "28.08.2025"
        ]
        
        print(f"\n📅 Тестируем с {len(test_dates)} датами")
        
        # Тестируем умное форматирование
        print("\n1️⃣ Умное форматирование:")
        smart_result = orchestrator._format_dates_smartly(test_dates)
        print(f"Результат:\n{smart_result}")
        
        # Проверяем результат
        if "🔥 Ближайшие варианты:" in smart_result:
            print("✅ Умное группирование работает!")
        else:
            print("❌ Умное группирование НЕ работает")
        
        if "📅 Дополнительные варианты:" in smart_result:
            print("✅ Дополнительные варианты показываются!")
        else:
            print("❌ Дополнительные варианты НЕ показываются")
        
        # Тестируем обычное форматирование
        print("\n2️⃣ Обычное форматирование:")
        normal_result = orchestrator._format_dates_beautifully(test_dates[:10])
        print(f"Результат:\n{normal_result}")
        
        print("\n✅ Прямой тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_date_formatting_direct()