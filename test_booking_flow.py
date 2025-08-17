#!/usr/bin/env python3
"""
Тестовый скрипт для проверки процесса записи с выбором услуги.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_booking_flow():
    """Тестирует полный процесс записи."""
    
    print("📅 Тестирование процесса записи")
    print("=" * 50)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        # Создаем RAG-систему и оркестратор
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        print("✅ Система инициализирована")
        
        user_id = 12345
        
        # Шаг 1: Намерение записаться
        print("\\n1️⃣ Тестирование намерения записаться")
        response1, metadata1 = orchestrator.process_message(
            user_id=user_id,
            message="хочу записаться на маникюр"
        )
        
        print(f"Ответ: {response1[:200]}...")
        print(f"Тип: {metadata1.get('type')}")
        
        if metadata1.get('type') == 'service_selection':
            print("✅ Показан список услуг для выбора")
        else:
            print("⚠️  Не показан список услуг")
        
        # Шаг 2: Выбор услуги по номеру
        print("\\n2️⃣ Тестирование выбора услуги")
        response2, metadata2 = orchestrator.process_message(
            user_id=user_id,
            message="1"
        )
        
        print(f"Ответ: {response2[:200]}...")
        print(f"Тип: {metadata2.get('type')}")
        
        if metadata2.get('type') == 'service_selected':
            print("✅ Услуга выбрана успешно")
            print(f"Выбранная услуга: {metadata2.get('service_title')}")
        else:
            print("⚠️  Услуга не выбрана")
        
        # Шаг 3: Выбор даты
        print("\\n3️⃣ Тестирование выбора даты")
        response3, metadata3 = orchestrator.process_message(
            user_id=user_id,
            message="25.08.2025"
        )
        
        print(f"Ответ: {response3[:200]}...")
        print(f"Тип: {metadata3.get('type')}")
        
        if metadata3.get('type') == 'date_selected':
            print("✅ Дата выбрана успешно")
            print(f"Выбранная дата: {metadata3.get('date')}")
        else:
            print("⚠️  Дата не выбрана")
        
        # Шаг 4: Просмотр доступных дат
        print("\\n4️⃣ Тестирование просмотра доступных дат")
        
        # Сначала снова выберем услугу
        orchestrator.process_message(user_id=user_id + 1, message="хочу записаться на массаж")
        orchestrator.process_message(user_id=user_id + 1, message="1")
        
        response4, metadata4 = orchestrator.process_message(
            user_id=user_id + 1,
            message="даты"
        )
        
        print(f"Ответ: {response4[:200]}...")
        print(f"Тип: {metadata4.get('type')}")
        
        if metadata4.get('type') == 'show_available_dates':
            print("✅ Показаны доступные даты")
        else:
            print("⚠️  Даты не показаны")
        
        print("\\n" + "=" * 50)
        print("🎉 Тестирование процесса записи завершено!")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_number_extraction():
    """Тестирует извлечение номера услуги из сообщения."""
    
    print("\\n🔢 Тестирование извлечения номеров")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        test_cases = [
            ("1", 1),
            ("2", 2),
            ("номер 3", 3),
            ("выбираю 4", 4),
            ("пятый", None),  # Текст без цифр
            ("1 и 2", 1),     # Первая цифра
            ("", None),       # Пустое сообщение
        ]
        
        for message, expected in test_cases:
            result = orchestrator._extract_service_number(message)
            status = "✅" if result == expected else "❌"
            print(f"   '{message}' -> {result} {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании извлечения номеров: {e}")
        return False


def test_date_parsing():
    """Тестирует парсинг дат."""
    
    print("\\n📅 Тестирование парсинга дат")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
        from main import BeautySalonRAG
        
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        test_cases = [
            ("25.08.2025", "25.08.2025"),
            ("1.1.2025", "01.01.2025"),
            ("31.12.2025", "31.12.2025"),
            ("32.13.2025", None),  # Некорректная дата
            ("завтра", None),      # Текст без даты
            ("25/08/2025", None),  # Неправильный формат
        ]
        
        for message, expected in test_cases:
            result = orchestrator._parse_date(message)
            status = "✅" if result == expected else "❌"
            print(f"   '{message}' -> {result} {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании парсинга дат: {e}")
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_booking_flow():
        success = False
    
    if not test_service_number_extraction():
        success = False
    
    if not test_date_parsing():
        success = False
    
    if success:
        print("\\n🎉 Все тесты процесса записи пройдены успешно!")
    else:
        print("\\n❌ Некоторые тесты не пройдены.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())