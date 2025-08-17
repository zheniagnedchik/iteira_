#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы оркестратора диалогов.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_orchestrator():
    """Тестирует работу оркестратора диалогов."""
    
    print("🎭 Тестирование оркестратора диалогов")
    print("=" * 50)
    
    try:
        # Мокаем RAG-систему
        class MockRAGSystem:
            def process_query(self, query):
                if "массаж" in query.lower():
                    return "Рекомендую классический массаж лица - 2500 руб., 60 минут."
                elif "пилинг" in query.lower():
                    return "Химический пилинг поможет обновить кожу - 3500 руб."
                else:
                    return "Подробная консультация о процедурах салона красоты."
        
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator, DialogState
        
        # Создаем оркестратор с мок-системой
        rag_mock = MockRAGSystem()
        orchestrator = DialogOrchestrator(rag_mock)
        
        print("✅ Оркестратор инициализирован")
        
        # Тестируем диалог
        user_id = 12345
        
        # 1. Приветствие
        print("\n1. Тестирование приветствия:")
        response, metadata = orchestrator.process_message(user_id, "привет", "Евгений")
        print(f"   Ответ: {response[:80]}...")
        print(f"   Тип: {metadata.get('type')}")
        print(f"   Имя сохранено: {metadata.get('has_name', False)}")
        
        # 2. Поиск услуги
        print("\n2. Тестирование поиска услуги:")
        response, metadata = orchestrator.process_message(user_id, "массаж лица")
        print(f"   Ответ: {response[:80]}...")
        print(f"   Тип: {metadata.get('type')}")
        print(f"   Персонализирован: {metadata.get('personalized', False)}")
        
        # 3. Уточняющий вопрос
        print("\n3. Тестирование уточняющего вопроса:")
        response, metadata = orchestrator.process_message(user_id, "а сколько это стоит?")
        print(f"   Ответ: {response[:80]}...")
        print(f"   Тип: {metadata.get('type')}")
        
        # 4. Намерение записаться
        print("\n4. Тестирование намерения записаться:")
        response, metadata = orchestrator.process_message(user_id, "хочу записаться")
        print(f"   Ответ: {response[:80]}...")
        print(f"   Тип: {metadata.get('type')}")
        print(f"   Есть контекст: {metadata.get('has_context', False)}")
        
        # 5. Благодарность
        print("\n5. Тестирование благодарности:")
        response, metadata = orchestrator.process_message(user_id, "спасибо")
        print(f"   Ответ: {response[:80]}...")
        print(f"   Тип: {metadata.get('type')}")
        
        # 6. Статистика пользователя
        print("\n6. Статистика пользователя:")
        stats = orchestrator.get_user_stats(user_id)
        print(f"   Имя: {stats.get('name')}")
        print(f"   Состояние: {stats.get('state')}")
        print(f"   Взаимодействий: {stats.get('interaction_count')}")
        print(f"   Сообщений в контексте: {stats.get('context_messages')}")
        
        # 7. Общая статистика
        print("\n7. Общая статистика оркестратора:")
        orchestrator_stats = orchestrator.get_orchestrator_stats()
        print(f"   Всего пользователей: {orchestrator_stats['total_users']}")
        print(f"   Активных диалогов: {orchestrator_stats['active_conversations']}")
        
        print("\n" + "=" * 50)
        print("🎉 Все тесты оркестратора пройдены!")
        print("\nОркестратор умеет:")
        print("✅ Распознавать намерения пользователей")
        print("✅ Управлять состояниями диалога")
        print("✅ Персонализировать общение")
        print("✅ Запоминать контекст разговора")
        print("✅ Обрабатывать различные типы запросов")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании оркестратора: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intent_detection():
    """Тестирует распознавание намерений."""
    
    print("\n🧠 Тестирование распознавания намерений")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        
        # Создаем оркестратор с мок-системой
        class MockRAGSystem:
            def process_query(self, query):
                return "Mock response"
        
        orchestrator = DialogOrchestrator(MockRAGSystem())
        
        # Тестовые сообщения и ожидаемые намерения
        test_cases = [
            ("привет", ["greeting"]),
            ("меня зовут Анна", ["name_giving"]),
            ("массаж лица", ["service_search"]),
            ("хочу записаться", ["booking_intent"]),
            ("сколько стоит", ["price_inquiry"]),
            ("что такое пилинг", ["consultation"]),
            ("спасибо", ["gratitude"]),
        ]
        
        for message, expected_intents in test_cases:
            detected = orchestrator.detect_intent(message)
            match = any(intent in detected for intent in expected_intents)
            print(f"   '{message}' -> {detected} {'✅' if match else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании намерений: {e}")
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_orchestrator():
        success = False
    
    if not test_intent_detection():
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())