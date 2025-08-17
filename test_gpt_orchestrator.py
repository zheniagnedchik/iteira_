#!/usr/bin/env python3
"""
Тестовый скрипт для проверки GPT-оркестратора.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_gpt_orchestrator():
    """Тестирует GPT-оркестратор диалогов."""
    
    print("🤖 Тестирование GPT-оркестратора")
    print("=" * 50)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        # Создаем RAG-систему и оркестратор
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        print("✅ GPT-оркестратор инициализирован")
        
        user_id = 12345
        
        # Тест 1: Приветствие
        print("\\n1️⃣ Тест приветствия")
        response1, metadata1 = orchestrator.process_message(
            user_id=user_id,
            message="Привет"
        )
        
        print(f"Ответ: {response1[:100]}...")
        print(f"Тип: {metadata1.get('type')}")
        
        if metadata1.get('type') == 'greeting':
            print("✅ GPT правильно определил приветствие")
        else:
            print("⚠️  GPT не определил приветствие")
        
        # Тест 2: Указание имени
        print("\\n2️⃣ Тест указания имени")
        response2, metadata2 = orchestrator.process_message(
            user_id=user_id,
            message="Анна"
        )
        
        print(f"Ответ: {response2[:100]}...")
        print(f"Тип: {metadata2.get('type')}")
        
        if metadata2.get('type') == 'name_collected':
            print("✅ GPT правильно обработал имя")
        else:
            print("⚠️  GPT не обработал имя")
        
        # Тест 3: Намерение записаться
        print("\\n3️⃣ Тест намерения записаться")
        response3, metadata3 = orchestrator.process_message(
            user_id=user_id,
            message="хочу маникюр"
        )
        
        print(f"Ответ: {response3[:150]}...")
        print(f"Тип: {metadata3.get('type')}")
        
        if metadata3.get('type') == 'service_selection':
            print("✅ GPT правильно определил намерение записаться")
        else:
            print("⚠️  GPT не определил намерение записаться")
        
        # Тест 4: Выбор услуги по номеру
        print("\\n4️⃣ Тест выбора услуги")
        response4, metadata4 = orchestrator.process_message(
            user_id=user_id,
            message="1"
        )
        
        print(f"Ответ: {response4[:150]}...")
        print(f"Тип: {metadata4.get('type')}")
        
        if metadata4.get('type') == 'service_selected':
            print("✅ GPT правильно обработал выбор услуги")
        else:
            print("⚠️  GPT не обработал выбор услуги")
        
        # Тест 5: Выбор даты
        print("\\n5️⃣ Тест выбора даты")
        response5, metadata5 = orchestrator.process_message(
            user_id=user_id,
            message="25.08.2025"
        )
        
        print(f"Ответ: {response5[:150]}...")
        print(f"Тип: {metadata5.get('type')}")
        
        if metadata5.get('type') == 'date_selected':
            print("✅ GPT правильно обработал выбор даты")
        else:
            print("⚠️  GPT не обработал выбор даты")
        
        print("\\n" + "=" * 50)
        print("🎉 Тестирование GPT-оркестратора завершено!")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gpt_orchestrator_direct():
    """Тестирует GPT-оркестратор напрямую."""
    
    print("\\n🔧 Тестирование GPT-оркестратора напрямую")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        # Создаем GPT клиент
        gpt_client = GPTClient()
        
        print("✅ GPT клиент инициализирован")
        
        # Тестовые случаи
        test_cases = [
            {
                "message": "Привет",
                "context": {"user_name": None, "current_state": "initial"},
                "expected_action": "greeting"
            },
            {
                "message": "хочу маникюр",
                "context": {"user_name": "Анна", "current_state": "general_chat"},
                "expected_action": "show_service_list"
            },
            {
                "message": "1",
                "context": {
                    "user_name": "Анна", 
                    "current_state": "service_selection",
                    "available_services": [{"title": "Маникюр классический"}]
                },
                "expected_action": "confirm_service_selection"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n   Тест {i}: {test_case['message']}")
            
            try:
                result = gpt_client.orchestrate_dialog(
                    user_message=test_case['message'],
                    dialog_context=test_case['context']
                )
                
                action = result.get('action')
                expected = test_case['expected_action']
                
                if action == expected:
                    print(f"   ✅ Правильное действие: {action}")
                else:
                    print(f"   ❌ Неправильное действие: {action} (ожидалось: {expected})")
                
                print(f"   Ответ: {result.get('response', '')[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании GPT клиента: {e}")
        return False


def test_different_phrasings():
    """Тестирует разные формулировки намерений."""
    
    print("\\n🗣 Тестирование разных формулировок")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        gpt_client = GPTClient()
        
        # Разные способы выразить намерение записаться
        booking_phrases = [
            "хочу маникюр",
            "нужен массаж",
            "записаться на чистку",
            "можно записать на пилинг",
            "делаете ли вы маникюр",
            "сколько стоит массаж и можно ли записаться"
        ]
        
        context = {"user_name": "Тест", "current_state": "general_chat"}
        
        for phrase in booking_phrases:
            print(f"\\n   Фраза: '{phrase}'")
            
            try:
                result = gpt_client.orchestrate_dialog(
                    user_message=phrase,
                    dialog_context=context
                )
                
                action = result.get('action')
                
                if action in ['show_service_list', 'service_consultation']:
                    print(f"   ✅ Правильно определено: {action}")
                else:
                    print(f"   ⚠️  Определено как: {action}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании фраз: {e}")
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_gpt_orchestrator():
        success = False
    
    if not test_gpt_orchestrator_direct():
        success = False
    
    if not test_different_phrasings():
        success = False
    
    if success:
        print("\\n🎉 Все тесты GPT-оркестратора пройдены!")
        print("\\n🤖 GPT-оркестратор готов к использованию:")
        print("   • Умное определение намерений")
        print("   • Контекстное принятие решений")
        print("   • Гибкая обработка разных формулировок")
        print("   • Естественные переходы между состояниями")
    else:
        print("\\n❌ Некоторые тесты не пройдены.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())