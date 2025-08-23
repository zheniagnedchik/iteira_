#!/usr/bin/env python3
"""
Быстрый тест логики перехода от уточнения к показу услуг
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_clarification_to_services():
    """Тестирует переход от уточнения к показу услуг."""
    print("🔄 Тест перехода: уточнение → показ услуг\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        user_id = 456
        
        # Шаг 1: Проблема с волосами
        print("1️⃣ Пользователь: 'выпадают волосы'")
        response1, metadata1 = orchestrator.process_message(user_id, "выпадают волосы")
        print(f"   Действие: {metadata1.get('type')}")
        print(f"   Ответ: {response1[:50]}...")
        
        # Проверяем состояние
        context = orchestrator.get_user_context(user_id)
        print(f"   Состояние: {context.get('current_state')}\n")
        
        # Шаг 2: Ответ на уточняющие вопросы
        print("2️⃣ Пользователь: 'Проблема полгода, готов к курсу'")
        response2, metadata2 = orchestrator.process_message(user_id, "Проблема полгода, готов к курсу")
        print(f"   Действие: {metadata2.get('type')}")
        print(f"   Услуг найдено: {metadata2.get('services_count', 0)}")
        print(f"   Ответ: {response2[:100]}...")
        
        # Проверяем результат
        if metadata2.get('type') == 'show_service_list':
            print("\n✅ УСПЕХ: Система корректно перешла к показу услуг!")
        else:
            print(f"\n❌ ОШИБКА: Ожидался show_service_list, получен {metadata2.get('type')}")
        
        return metadata2.get('type') == 'show_service_list'
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    success = test_clarification_to_services()
    if success:
        print("\n🎉 Логика работает правильно!")
    else:
        print("\n⚠️ Требуется доработка логики.")
