#!/usr/bin/env python3
"""
Тест умных вопросов - GPT сам решает, какие вопросы задавать
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_smart_questions():
    """Тестирует, что GPT задает релевантные вопросы для разных типов услуг."""
    print("🧠 Тест умных вопросов GPT\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        # Тестовые сценарии
        scenarios = [
            {
                'message': 'я хочу лазерную эпиляцию',
                'expected_keywords': ['зон', 'област', 'тип кожи', 'опыт', 'противопоказан'],
                'unexpected_keywords': ['бюджет', 'как давно', 'проблема беспокоит']
            },
            {
                'message': 'хочу покрасить волосы',
                'expected_keywords': ['цвет', 'оттенок', 'окрашивали', 'текущий'],
                'unexpected_keywords': ['зон', 'тип кожи', 'как давно беспокоит']
            },
            {
                'message': 'у меня акне',
                'expected_keywords': ['давно', 'беспокоит', 'лечени', 'пробовали'],
                'unexpected_keywords': ['зон эпиляции', 'цвет волос', 'оттенок']
            },
            {
                'message': 'нужен массаж',
                'expected_keywords': ['тип массаж', 'зон', 'расслабля', 'лечебн'],
                'unexpected_keywords': ['цвет волос', 'эпиляция', 'как давно беспокоит']
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            user_id = 1000 + i
            message = scenario['message']
            expected = scenario['expected_keywords']
            unexpected = scenario['unexpected_keywords']
            
            print(f"🧪 Тест {i}: '{message}'")
            
            response, metadata = orchestrator.process_message(user_id, message, f"Тестер{i}")
            
            action = metadata.get('type')
            print(f"   🎯 Действие: {action}")
            
            if action == 'ask_service_clarification':
                response_lower = response.lower()
                
                # Проверяем ожидаемые ключевые слова
                found_expected = sum(1 for keyword in expected if keyword.lower() in response_lower)
                found_unexpected = sum(1 for keyword in unexpected if keyword.lower() in response_lower)
                
                print(f"   ✅ Релевантных вопросов: {found_expected}/{len(expected)}")
                print(f"   ❌ Нерелевантных вопросов: {found_unexpected}")
                
                # Показываем что найдено
                found_keywords = [keyword for keyword in expected if keyword.lower() in response_lower]
                unwanted_keywords = [keyword for keyword in unexpected if keyword.lower() in response_lower]
                
                if found_keywords:
                    print(f"   🎯 Найдено: {', '.join(found_keywords)}")
                if unwanted_keywords:
                    print(f"   ⚠️  Нежелательно: {', '.join(unwanted_keywords)}")
                
                # Оценка качества
                relevance_score = found_expected / len(expected) * 100
                irrelevance_penalty = found_unexpected * 10
                
                final_score = max(0, relevance_score - irrelevance_penalty)
                print(f"   📊 Оценка релевантности: {final_score:.1f}%")
                
                if final_score >= 50:
                    print(f"   ✅ ХОРОШО")
                else:
                    print(f"   ❌ ТРЕБУЕТ УЛУЧШЕНИЯ")
                    
            else:
                print(f"   ⚠️  Ожидалось ask_service_clarification, получено {action}")
            
            print(f"   💬 Ответ: {response[:80]}...")
            print()
        
        print("="*60)
        print("🎉 Тест завершен!")
        print("💡 Проверьте, задает ли GPT релевантные вопросы для каждого типа услуг")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Тестирование умных вопросов\n")
    
    success = test_smart_questions()
    
    if success:
        print("\n🎯 Анализируйте результаты:")
        print("• GPT должен задавать разные вопросы для разных услуг")
        print("• Вопросы должны быть релевантными конкретной услуге")
        print("• Не должно быть шаблонных вопросов для всех услуг")
    else:
        print("\n❌ Тест не прошел. Требуется доработка логики умных вопросов.")

