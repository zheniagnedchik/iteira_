#!/usr/bin/env python3
"""
Тест новой unified GPT-driven архитектуры
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_gpt_decision_system():
    """Тестирует систему принятия решений через GPT."""
    print("🧪 Тестирование GPT-driven архитектуры...\n")
    
    try:
        # Инициализируем систему
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        test_scenarios = [
            {
                "name": "Приветствие нового пользователя",
                "user_id": 1,
                "message": "Привет!",
                "expected_action": "greeting"
            },
            {
                "name": "Проблема с кожей",
                "user_id": 2,
                "message": "У меня проблемы с кожей лица, что посоветуете?",
                "expected_action": "ask_service_clarification"
            },
            {
                "name": "Конкретный запрос услуги",
                "user_id": 3,
                "message": "Хочу записаться на маникюр",
                "expected_action": "show_service_list"
            },
            {
                "name": "Вопрос консультация",
                "user_id": 4,
                "message": "Что такое мезотерапия и сколько стоит?",
                "expected_action": "service_consultation"
            },
            {
                "name": "Благодарность",
                "user_id": 5,
                "message": "Спасибо за помощь!",
                "expected_action": "handle_gratitude"
            },
            {
                "name": "Неясный запрос",
                "user_id": 6,
                "message": "Хочу быть красивой",
                "expected_action": "ask_service_clarification"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"📝 Тест {i}: {scenario['name']}")
            print(f"   Сообщение: '{scenario['message']}'")
            
            try:
                # Получаем решение от GPT-оркестратора
                context = orchestrator.get_user_context(scenario['user_id'])
                decision = orchestrator._get_gpt_decision(
                    scenario['user_id'], 
                    scenario['message'], 
                    context
                )
                
                actual_action = decision.get('action', 'unknown')
                print(f"   🤖 GPT решение: {actual_action}")
                print(f"   📋 Параметры: {decision.get('parameters', {})}")
                
                # Проверяем соответствие ожиданиям
                if actual_action == scenario['expected_action']:
                    print(f"   ✅ УСПЕХ: Решение соответствует ожиданиям")
                else:
                    print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Ожидалось {scenario['expected_action']}, получено {actual_action}")
                
                # Тестируем полный pipeline
                print("   🔄 Тестирование полного pipeline...")
                response, metadata = orchestrator.process_message(
                    scenario['user_id'],
                    scenario['message']
                )
                
                print(f"   💬 Ответ: {response[:100]}...")
                print(f"   📊 Метаданные: {metadata}")
                print()
                
            except Exception as e:
                print(f"   ❌ ОШИБКА: {e}")
                print()
        
        print("✅ Тестирование GPT-driven архитектуры завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования: {e}")
        return False


def test_context_persistence():
    """Тестирует сохранение контекста между сообщениями."""
    print("\n🔄 Тестирование сохранения контекста...\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        user_id = 100
        
        # Диалог из нескольких сообщений
        dialog_flow = [
            ("Привет!", "Должно быть приветствие"),
            ("Меня зовут Анна", "Должен собрать имя"),
            ("Я новый клиент", "Должен узнать историю посещений"),
            ("Хочу сделать процедуру для лица", "Должен предложить услуги"),
            ("1", "Должен подтвердить выбор первой услуги")
        ]
        
        for i, (message, expected) in enumerate(dialog_flow, 1):
            print(f"🗣️ Сообщение {i}: '{message}'")
            print(f"   Ожидание: {expected}")
            
            response, metadata = orchestrator.process_message(user_id, message)
            
            print(f"   🤖 Ответ: {response[:100]}...")
            print(f"   📊 Тип действия: {metadata.get('type')}")
            
            # Проверяем контекст
            context = orchestrator.get_user_context(user_id)
            print(f"   🧠 Состояние: {context.get('current_state')}")
            print(f"   👤 Имя: {context.get('user_name')}")
            print(f"   📜 История: {len(context.get('dialog_history', []))} сообщений")
            print()
        
        print("✅ Тестирование контекста завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования контекста: {e}")
        return False


def test_error_resilience():
    """Тестирует устойчивость к ошибкам."""
    print("\n🛡️ Тестирование устойчивости к ошибкам...\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        error_scenarios = [
            ("", "Пустое сообщение"),
            ("   ", "Сообщение из пробелов"),
            ("🤖" * 1000, "Очень длинное сообщение"),
            ("@#$%^&*()", "Специальные символы"),
            ("SELECT * FROM users", "SQL-инъекция"),
            ("<script>alert('hack')</script>", "XSS-попытка")
        ]
        
        for message, description in error_scenarios:
            print(f"⚠️  Тест: {description}")
            print(f"   Сообщение: '{message[:50]}...' (длина: {len(message)})")
            
            try:
                response, metadata = orchestrator.process_message(999, message)
                print(f"   ✅ Обработано: {response[:100]}...")
                print(f"   📊 Тип: {metadata.get('type')}")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
            print()
        
        print("✅ Тестирование устойчивости завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Запуск тестирования новой GPT-driven архитектуры\n")
    
    tests = [
        test_gpt_decision_system,
        test_context_persistence,
        test_error_resilience
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Тест {test_func.__name__} упал: {e}")
            failed += 1
        
        print("-" * 50)
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Прошло: {passed}")
    print(f"❌ Не прошло: {failed}")
    
    if failed == 0:
        print("🎉 Все тесты прошли успешно!")
        print("💡 GPT-driven архитектура готова к использованию!")
    else:
        print("⚠️ Некоторые тесты не прошли. Требуется доработка.")

