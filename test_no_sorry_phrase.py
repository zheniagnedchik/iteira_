#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отсутствия фразы "К сожалению".
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_no_sorry_phrase():
    """Тестирует отсутствие фразы 'К сожалению' в ответах."""
    
    print("🚫 Тестирование отсутствия фразы 'К сожалению'")
    print("=" * 50)
    
    try:
        from main import BeautySalonRAG
        
        # Создаем RAG-систему
        rag_system = BeautySalonRAG()
        
        print("✅ RAG-система инициализирована")
        
        # Тестовые запросы, которые могут вызвать сообщение о недоступности
        test_queries = [
            "newesthair мезотерапия волос",
            "массаж лица классический", 
            "ботокс инъекции морщины",
            "чистка лица ультразвуковая",
            "dermaheal процедура",
            "xl hair мезотерапия",
            "пилинг химический"
        ]
        
        forbidden_phrases = [
            "к сожалению",
            "К сожалению", 
            "к сожаленью",
            "К сожаленью"
        ]
        
        positive_phrases = [
            "Благодарю за ожидание",
            "данная услуга доступна для записи только по телефону"
        ]
        
        all_passed = True
        
        for i, query in enumerate(test_queries, 1):
            print(f"\\n{i}. Тестирование запроса: '{query}'")
            
            # Обрабатываем запрос через RAG-систему
            response = rag_system.process_query(query)
            
            # Проверяем отсутствие запрещенных фраз
            has_forbidden = False
            for phrase in forbidden_phrases:
                if phrase in response:
                    print(f"   ❌ Найдена запрещенная фраза: '{phrase}'")
                    has_forbidden = True
                    all_passed = False
            
            if not has_forbidden:
                print(f"   ✅ Запрещенные фразы отсутствуют")
            
            # Проверяем наличие позитивных фраз (если есть контакты)
            if "📞" in response:
                has_positive = any(phrase in response for phrase in positive_phrases)
                if has_positive:
                    print(f"   ✅ Используется позитивная формулировка")
                else:
                    print(f"   ⚠️  Нет позитивной формулировки в сообщении с контактами")
                    all_passed = False
            
            # Показываем часть ответа для проверки
            print(f"   Фрагмент ответа: {response[:100]}...")
        
        print("\\n" + "=" * 50)
        if all_passed:
            print("🎉 Все тесты пройдены! Фраза 'К сожалению' не используется.")
        else:
            print("❌ Некоторые тесты не пройдены. Требуется доработка.")
        
        return all_passed
        
    except Exception as e:
        print(f"\\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_gpt_responses():
    """Тестирует GPT клиент напрямую на отсутствие негативных фраз."""
    
    print("\\n🔧 Тестирование GPT клиента напрямую")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        # Создаем GPT клиент
        gpt_client = GPTClient()
        
        print("✅ GPT клиент инициализирован")
        
        # Тестовые данные услуг без мастеров
        test_services = [
            {
                "id": "test_clinical",
                "title": "Newesthair - мезотерапия кожи головы",
                "category": "Мезотерапия",
                "price": 720,
                "duration": 3600,
                "csv_fields": {
                    "Место оказания услуг": "Клиника"
                },
                "staff_info": {
                    "available_masters": [],
                    "total_staff_count": 0
                }
            },
            {
                "id": "test_salon", 
                "title": "Классический массаж лица",
                "category": "Массаж",
                "price": 2500,
                "duration": 3600,
                "csv_fields": {
                    "Место оказания услуг": "Салон"
                },
                "staff_info": {
                    "available_masters": [],
                    "total_staff_count": 0
                }
            }
        ]
        
        test_queries = [
            "newesthair мезотерапия",
            "массаж лица"
        ]
        
        all_passed = True
        
        for query in test_queries:
            print(f"\\n   Запрос: '{query}'")
            
            # Генерируем ответ через GPT
            response = gpt_client.generate_response(query, test_services)
            
            # Проверяем отсутствие "К сожалению"
            if "к сожалению" in response.lower():
                print(f"   ❌ Найдена фраза 'К сожалению'")
                all_passed = False
            else:
                print(f"   ✅ Фраза 'К сожалению' отсутствует")
            
            # Проверяем наличие позитивной формулировки
            if "Благодарю за ожидание" in response:
                print(f"   ✅ Используется позитивная формулировка")
            else:
                print(f"   ⚠️  Нет позитивной формулировки")
            
            print(f"   Фрагмент: {response[:100]}...")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании GPT клиента: {e}")
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_no_sorry_phrase():
        success = False
    
    if not test_direct_gpt_responses():
        success = False
    
    if success:
        print("\\n🎉 Все проверки пройдены! Система использует только позитивные формулировки.")
    else:
        print("\\n❌ Требуется дополнительная настройка системы.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())