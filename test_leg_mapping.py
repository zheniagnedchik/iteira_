#!/usr/bin/env python3
"""
Тест сопоставления "вся нога" с услугой
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_leg_mapping():
    """Тестирует, понимает ли система что 'вся нога' = крупная область."""
    print("🦵 Тест сопоставления 'вся нога'\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        user_id = 99999
        
        # Сценарий как у Евгения
        dialog = [
            ("хочу эпиляцию", "Должен показать варианты зон"),
            ("вся нога", "Должен понять что это крупная область 155₽"),
            ("вся нога", "НЕ ДОЛЖЕН переспрашивать то же самое!")
        ]
        
        for i, (message, expectation) in enumerate(dialog, 1):
            print(f"💬 Сообщение {i}: '{message}'")
            print(f"   Ожидание: {expectation}")
            
            response, metadata = orchestrator.process_message(user_id, message, "Евгений")
            
            action = metadata.get('type')
            print(f"   🎯 Действие: {action}")
            
            # Анализируем ответ
            response_lower = response.lower()
            
            if i == 1:  # Первое сообщение
                if "155" in response or "крупная" in response_lower:
                    print("   ✅ Показал крупную область")
                else:
                    print("   ⚠️  Не показал крупную область")
            
            elif i == 2:  # "вся нога" первый раз
                if "155" in response and ("крупная" in response_lower or "бедра" in response_lower or "голен" in response_lower):
                    print("   ✅ Понял что вся нога = крупная область")
                    # Если понял правильно, можно прервать тест
                    if action == "show_service_list" or action == "confirm_service_selection":
                        print("   🎉 УСПЕХ: Система поняла с первого раза!")
                        break
                else:
                    print("   ❌ НЕ понял что вся нога = крупная область")
            
            elif i == 3:  # "вся нога" второй раз (не должно быть)
                print("   ❌ ЗАЦИКЛИВАНИЕ: Система переспрашивает то же самое!")
            
            print(f"   💬 Ответ: {response[:100]}...")
            print()
        
        # Итоговый анализ
        context = orchestrator.get_user_context(user_id)
        print("📊 ИТОГОВЫЙ АНАЛИЗ:")
        print(f"   Состояние: {context.get('current_state')}")
        print(f"   Сообщений в истории: {len(context.get('dialog_history', []))}")
        
        # Проверяем зацикливание
        history = context.get('dialog_history', [])
        assistant_responses = [msg.get('message', '') for msg in history if msg.get('role') == 'assistant']
        
        if len(assistant_responses) >= 2:
            last_two = assistant_responses[-2:]
            similar_words = 0
            for word in last_two[0].split():
                if word in last_two[1]:
                    similar_words += 1
            
            similarity = similar_words / max(len(last_two[0].split()), 1) * 100
            print(f"   Схожесть последних ответов: {similarity:.1f}%")
            
            if similarity > 50:
                print("   ⚠️  ВОЗМОЖНОЕ ЗАЦИКЛИВАНИЕ!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Тестирование сопоставления услуг\n")
    
    success = test_leg_mapping()
    
    if success:
        print("\n💡 Система должна понимать:")
        print("   'вся нога' = 'крупная область тела' (155₽)")
        print("   'голени' = 'средняя область тела' (120₽)")
        print("   И НЕ переспрашивать одно и то же!")
    else:
        print("\n❌ Тест не прошел.")

