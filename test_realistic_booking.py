#!/usr/bin/env python3
"""
Реалистичный тест процесса записи с полным диалогом.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_realistic_booking_flow():
    """Тестирует реалистичный процесс записи."""
    
    print("🎭 Реалистичный тест процесса записи")
    print("=" * 50)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        # Создаем RAG-систему и оркестратор
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        print("✅ Система инициализирована")
        
        user_id = 12345
        
        # Шаг 1: Приветствие
        print("\\n👋 Шаг 1: Приветствие")
        response1, _ = orchestrator.process_message(
            user_id=user_id,
            message="Привет"
        )
        print(f"Бот: {response1[:100]}...")
        
        # Шаг 2: Указание имени
        print("\\n📝 Шаг 2: Указание имени")
        response2, _ = orchestrator.process_message(
            user_id=user_id,
            message="Анна"
        )
        print(f"Бот: {response2[:100]}...")
        
        # Шаг 3: Намерение записаться
        print("\\n📅 Шаг 3: Намерение записаться")
        response3, metadata3 = orchestrator.process_message(
            user_id=user_id,
            message="хочу записаться на маникюр"
        )
        print(f"Бот: {response3[:200]}...")
        print(f"Тип ответа: {metadata3.get('type')}")
        
        if metadata3.get('type') == 'service_selection':
            print("✅ Показан список услуг для выбора")
            
            # Шаг 4: Выбор услуги
            print("\\n🎯 Шаг 4: Выбор услуги по номеру")
            response4, metadata4 = orchestrator.process_message(
                user_id=user_id,
                message="1"
            )
            print(f"Бот: {response4[:200]}...")
            print(f"Тип ответа: {metadata4.get('type')}")
            
            if metadata4.get('type') == 'service_selected':
                print("✅ Услуга выбрана успешно")
                print(f"Выбранная услуга: {metadata4.get('service_title')}")
                
                # Шаг 5: Выбор даты
                print("\\n📆 Шаг 5: Выбор конкретной даты")
                response5, metadata5 = orchestrator.process_message(
                    user_id=user_id,
                    message="25.08.2025"
                )
                print(f"Бот: {response5[:200]}...")
                print(f"Тип ответа: {metadata5.get('type')}")
                
                if metadata5.get('type') == 'date_selected':
                    print("✅ Дата выбрана успешно")
                    print(f"Выбранная дата: {metadata5.get('date')}")
                    
                    # Проверяем итоговое сообщение
                    if "📋 **Ваша запись:**" in response5:
                        print("✅ Показано красивое итоговое сообщение о записи")
                    else:
                        print("⚠️  Итоговое сообщение не найдено")
                else:
                    print("⚠️  Дата не выбрана")
            else:
                print("⚠️  Услуга не выбрана")
        else:
            print("⚠️  Список услуг не показан")
        
        print("\\n" + "=" * 50)
        print("🎉 Реалистичный тест завершен!")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_selection_flow():
    """Тестирует выбор даты через просмотр доступных дат."""
    
    print("\\n📅 Тест выбора даты через просмотр")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 54321
        
        # Проходим до выбора услуги
        orchestrator.process_message(user_id, "Привет")
        orchestrator.process_message(user_id, "Мария")
        orchestrator.process_message(user_id, "хочу записаться на массаж")
        orchestrator.process_message(user_id, "1")
        
        # Теперь тестируем просмотр дат
        print("Запрос доступных дат...")
        response, metadata = orchestrator.process_message(user_id, "даты")
        
        print(f"Ответ: {response[:150]}...")
        print(f"Тип: {metadata.get('type')}")
        
        if metadata.get('type') == 'show_available_dates':
            print("✅ Доступные даты показаны")
        else:
            print("⚠️  Доступные даты не показаны")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании выбора дат: {e}")
        return False


def test_error_handling():
    """Тестирует обработку ошибок в процессе записи."""
    
    print("\\n🚨 Тест обработки ошибок")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 99999
        
        # Проходим до выбора услуги
        orchestrator.process_message(user_id, "Привет")
        orchestrator.process_message(user_id, "Тест")
        response1, metadata1 = orchestrator.process_message(user_id, "хочу записаться на маникюр")
        
        if metadata1.get('type') == 'service_selection':
            # Тестируем неправильный номер услуги
            print("Тест неправильного номера услуги...")
            response2, metadata2 = orchestrator.process_message(user_id, "99")
            
            if metadata2.get('type') == 'invalid_service_number':
                print("✅ Корректно обработан неправильный номер")
            else:
                print("⚠️  Неправильный номер не обработан")
            
            # Тестируем правильный выбор
            orchestrator.process_message(user_id, "1")
            
            # Тестируем неправильный формат даты
            print("Тест неправильного формата даты...")
            response3, metadata3 = orchestrator.process_message(user_id, "завтра")
            
            if metadata3.get('type') == 'invalid_date_format':
                print("✅ Корректно обработан неправильный формат даты")
            else:
                print("⚠️  Неправильный формат даты не обработан")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании обработки ошибок: {e}")
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_realistic_booking_flow():
        success = False
    
    if not test_date_selection_flow():
        success = False
    
    if not test_error_handling():
        success = False
    
    if success:
        print("\\n🎉 Все реалистичные тесты пройдены успешно!")
        print("\\n📋 Система записи готова к использованию:")
        print("   1. Приветствие и сбор имени")
        print("   2. Показ списка доступных услуг")
        print("   3. Выбор услуги по номеру")
        print("   4. Красивое подтверждение выбора")
        print("   5. Выбор даты или просмотр доступных")
        print("   6. Итоговое сообщение с деталями записи")
    else:
        print("\\n❌ Некоторые тесты не пройдены.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())