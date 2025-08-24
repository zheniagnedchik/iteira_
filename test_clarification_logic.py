#!/usr/bin/env python3
"""
Тест новой логики уточнения услуг
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_clarification_logic():
    """Тестирует новую логику уточнения вместо показа всех услуг."""
    print("🔍 Тестирование логики уточнения услуг...\n")
    
    try:
        # Инициализируем систему
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        # Сценарий: пользователь сообщает о проблеме выпадения волос
        user_id = 123
        user_name = "Евгений"
        
        print("👤 Пользователь: Евгений")
        print("💬 Сообщение: 'у меня выпадают волосы'\n")
        
        # Обрабатываем сообщение
        response, metadata = orchestrator.process_message(
            user_id=user_id,
            message="у меня выпадают волосы",
            user_name=user_name
        )
        
        print("🤖 Ответ бота:")
        print(response)
        print()
        
        print("📊 Метаданные:")
        print(f"   Тип действия: {metadata.get('type')}")
        print(f"   Параметры: {metadata.get('action_parameters')}")
        print(f"   Количество услуг: {metadata.get('services_count')}")
        print()
        
        # Проверяем контекст
        context = orchestrator.get_user_context(user_id)
        print("🧠 Состояние контекста:")
        print(f"   current_state: {context.get('current_state')}")
        print(f"   clarification_topic: {context.get('clarification_topic')}")
        print(f"   История сообщений: {len(context.get('dialog_history', []))}")
        print()
        
        # Ожидаемое поведение
        expected_action = "ask_service_clarification"
        expected_state = "clarifying_service"
        
        print("✅ Проверка результатов:")
        
        if metadata.get('type') == expected_action:
            print(f"   ✅ Действие корректно: {expected_action}")
        else:
            print(f"   ❌ Неверное действие: ожидалось {expected_action}, получено {metadata.get('type')}")
        
        if context.get('current_state') == expected_state:
            print(f"   ✅ Состояние корректно: {expected_state}")
        else:
            print(f"   ❌ Неверное состояние: ожидалось {expected_state}, получено {context.get('current_state')}")
        
        # Проверяем, что не показаны конкретные услуги в ответе
        service_keywords = ['Newesthair', 'Dermaheal', 'XL HAIR', 'Hair X', 'DR.CYJ']
        shows_services = any(keyword in response for keyword in service_keywords)
        
        if not shows_services:
            print("   ✅ Услуги НЕ показаны сразу (правильно)")
        else:
            print("   ❌ Услуги показаны сразу (неправильно)")
        
        # Проверяем наличие уточняющих вопросов
        clarification_keywords = ['как давно', 'пробовали', 'готовы', 'бюджет', 'расскажите']
        has_clarification = any(keyword.lower() in response.lower() for keyword in clarification_keywords)
        
        if has_clarification:
            print("   ✅ Есть уточняющие вопросы (правильно)")
        else:
            print("   ❌ Нет уточняющих вопросов (неправильно)")
        
        print("\n" + "="*60)
        
        # Тестируем ответ на уточняющие вопросы
        print("\n🔄 Тестирование ответа на уточняющие вопросы...\n")
        
        clarification_response = "Проблема беспокоит уже полгода, ничего не пробовал, готов к курсу процедур"
        print(f"💬 Ответ пользователя: '{clarification_response}'\n")
        
        response2, metadata2 = orchestrator.process_message(
            user_id=user_id,
            message=clarification_response
        )
        
        print("🤖 Ответ бота:")
        print(response2[:200] + "..." if len(response2) > 200 else response2)
        print()
        
        print("📊 Метаданные:")
        print(f"   Тип действия: {metadata2.get('type')}")
        print(f"   Количество услуг: {metadata2.get('services_count')}")
        
        # Теперь должны показаться услуги
        expected_action2 = "show_service_list"
        
        if metadata2.get('type') == expected_action2:
            print(f"   ✅ После уточнения правильное действие: {expected_action2}")
        else:
            print(f"   ❌ После уточнения неверное действие: ожидалось {expected_action2}, получено {metadata2.get('type')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Тест новой логики уточнения услуг\n")
    
    success = test_clarification_logic()
    
    if success:
        print("\n🎉 Тест завершен!")
        print("💡 Теперь система должна правильно задавать уточняющие вопросы")
        print("   вместо показа всех услуг сразу.")
    else:
        print("\n❌ Тест не прошел. Требуется доработка.")

