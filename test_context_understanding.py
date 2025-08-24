#!/usr/bin/env python3
"""
Тест контекстного понимания диалога
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_context_understanding():
    """Тестирует контекстное понимание как в примере Евгения."""
    print("🧠 Тест контекстного понимания диалога\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        user_id = 789
        
        # Сценарий как у Евгения
        dialog_flow = [
            ("мне нужно что бы мне выровняли ногти и покрыли гель лаком", "Должен предложить маникюр"),
            ("а если я хочу еще окрашивание?", "Должен понять, что имеется в виду окрашивание ВОЛОС"),
            ("осветление", "Должен понять, что это осветление ВОЛОС, а не пилинг лица")
        ]
        
        for i, (message, expected) in enumerate(dialog_flow, 1):
            print(f"💬 Сообщение {i}: '{message}'")
            print(f"   Ожидание: {expected}")
            
            response, metadata = orchestrator.process_message(user_id, message, "Евгений")
            
            print(f"   🤖 Действие: {metadata.get('type')}")
            print(f"   📝 Ответ: {response[:100]}...")
            
            # Анализируем ключевые слова в ответе
            response_lower = response.lower()
            
            if i == 1:  # Первое сообщение про ногти
                if any(word in response_lower for word in ['маникюр', 'ногти', 'гель']):
                    print("   ✅ Правильно понял запрос про ногти")
                else:
                    print("   ❌ Не понял запрос про ногти")
            
            elif i == 2:  # Второе сообщение про окрашивание
                if any(word in response_lower for word in ['волос', 'окраш', 'цвет']):
                    print("   ✅ Правильно понял, что окрашивание = волосы")
                elif any(word in response_lower for word in ['кож', 'лицо', 'пилинг']):
                    print("   ❌ Неправильно связал окрашивание с процедурами для лица")
                else:
                    print("   ⚠️  Неясно, правильно ли понял контекст")
            
            elif i == 3:  # Третье сообщение про осветление
                if any(word in response_lower for word in ['волос', 'осветл', 'блонд']):
                    print("   ✅ Правильно понял, что осветление = волосы")
                elif any(word in response_lower for word in ['пилинг', 'кож', 'лицо']):
                    print("   ❌ Неправильно предложил пилинг вместо осветления волос")
                else:
                    print("   ⚠️  Неясно, правильно ли понял контекст")
            
            print()
        
        print("="*60)
        
        # Проверяем итоговый контекст
        context = orchestrator.get_user_context(user_id)
        history = context.get('dialog_history', [])
        
        print(f"📊 Итоговая статистика:")
        print(f"   Сообщений в истории: {len(history)}")
        print(f"   Текущее состояние: {context.get('current_state')}")
        
        # Анализируем, насколько хорошо система поняла контекст
        all_responses = " ".join([msg.get('message', '') for msg in history if msg.get('role') == 'assistant'])
        
        context_keywords = {
            'ногти': ['маникюр', 'ногти', 'гель'],
            'волосы': ['волос', 'окраш', 'осветл', 'цвет'],
            'лицо': ['пилинг', 'кож', 'лицо']
        }
        
        print(f"\n🔍 Анализ понимания контекста:")
        for category, keywords in context_keywords.items():
            found = any(keyword in all_responses.lower() for keyword in keywords)
            print(f"   {category}: {'✅' if found else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Тестирование контекстного понимания\n")
    
    success = test_context_understanding()
    
    if success:
        print("\n🎉 Тест завершен!")
        print("💡 Проверьте, правильно ли система понимает контекст диалога")
    else:
        print("\n❌ Тест не прошел. Требуется доработка контекстного понимания.")

