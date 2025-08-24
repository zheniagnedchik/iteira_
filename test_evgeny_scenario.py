#!/usr/bin/env python3
"""
Тест точного сценария Евгения
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_evgeny_scenario():
    """Воспроизводим точный сценарий Евгения."""
    print("👤 Тест сценария Евгения\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        user_id = 12345  # ID Евгения
        
        # Точный сценарий из его сообщений
        messages = [
            "хочу эпиляцию",
            "вся нога что подойдет?",
            "вся ногаэ"  # с опечаткой как у него
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"📱 Сообщение {i}: '{message}'")
            
            response, metadata = orchestrator.process_message(user_id, message, "Евгений")
            
            action = metadata.get('type')
            print(f"   🎯 Действие: {action}")
            print(f"   💬 Ответ: {response}")
            print()
            
            # Проверяем на зацикливание
            if i > 1:
                # Анализируем ответ
                if "подтвердите" in response.lower() and "речь идет" in response.lower():
                    print("   ⚠️  ЗАЦИКЛИВАНИЕ: Система переспрашивает confirmation")
                elif "155" in response or "крупная" in response.lower():
                    print("   ✅ УСПЕХ: Предложил правильную услугу")
                else:
                    print("   ❓ Неясный ответ")
        
        # Итоговый анализ
        context = orchestrator.get_user_context(user_id)
        history = context.get('dialog_history', [])
        
        print("📊 ФИНАЛЬНЫЙ АНАЛИЗ:")
        print(f"   Всего сообщений: {len(history)}")
        print(f"   Состояние: {context.get('current_state')}")
        
        # Проверяем последние ответы системы
        bot_responses = [msg for msg in history if msg.get('role') == 'assistant']
        if len(bot_responses) >= 2:
            last_response = bot_responses[-1]['message']
            prev_response = bot_responses[-2]['message']
            
            # Простая проверка на зацикливание
            if "подтвердите" in last_response and "подтвердите" in prev_response:
                print("   ❌ ЗАЦИКЛИВАНИЕ: Переспрашивает подтверждение")
            else:
                print("   ✅ Нет зацикливания")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Воспроизведение проблемы Евгения\n")
    test_evgeny_scenario()

