#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления GPT промпта.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_gpt_prompt_fix():
    """Тестирует исправление GPT промпта для правильных контактов."""
    
    print("🧪 Тестирование исправления GPT промпта")
    print("=" * 50)
    
    try:
        from main import BeautySalonRAG
        
        # Создаем RAG-систему
        rag_system = BeautySalonRAG()
        
        print("✅ RAG-система инициализирована")
        
        # Тестовые запросы
        test_cases = [
            {
                "query": "newesthair мезотерапия волос",
                "expected_contact": "Клиника: +375296080912",
                "description": "Клиническая процедура (мезотерапия)"
            },
            {
                "query": "массаж лица классический", 
                "expected_contact": "Салон: +375445903030",
                "description": "Салонная процедура (массаж)"
            },
            {
                "query": "ботокс инъекции морщины",
                "expected_contact": "Клиника: +375296080912", 
                "description": "Клиническая процедура (инъекции)"
            },
            {
                "query": "чистка лица ультразвуковая",
                "expected_contact": "Салон: +375445903030",
                "description": "Салонная процедура (чистка)"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n{i}. Тестирование: {test_case['description']}")
            print(f"   Запрос: '{test_case['query']}'")
            
            # Обрабатываем запрос через RAG-систему
            response = rag_system.process_query(test_case['query'])
            
            print(f"   Ответ: {response[:100]}...")
            
            # Проверяем наличие правильного контакта
            if test_case['expected_contact'] in response:
                print(f"   ✅ Правильный контакт: {test_case['expected_contact']}")
            else:
                print(f"   ❌ Неправильный контакт. Ожидался: {test_case['expected_contact']}")
                print(f"   Полный ответ: {response}")
            
            # Проверяем отсутствие старых фраз
            old_phrases = [
                "К сожалению, на данный момент нет доступных мастеров",
                "рекомендую проконсультироваться с администратором"
            ]
            
            has_old_phrases = any(phrase in response for phrase in old_phrases)
            if has_old_phrases:
                print(f"   ⚠️  Найдены старые фразы в ответе")
            else:
                print(f"   ✅ Старые фразы отсутствуют")
        
        print("\\n" + "=" * 50)
        print("🎉 Тестирование GPT промпта завершено!")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_gpt_client():
    """Тестирует GPT клиент напрямую."""
    
    print("\\n🔧 Тестирование GPT клиента напрямую")
    print("-" * 40)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        # Создаем GPT клиент
        gpt_client = GPTClient()
        
        print("✅ GPT клиент инициализирован")
        
        # Тестовые данные услуг (без мастеров)
        test_services = [
            {
                "id": "newesthair_test",
                "title": "Newesthair - мезотерапия кожи головы",
                "category": "Мезотерапия",
                "price": 720,
                "duration": 3600,
                "csv_fields": {
                    "Терапевтическая цель": "Биоревитализация кожи головы",
                    "Показания (типичные проблемы)": "сухость, перхоть, возрастное выпадение волос",
                    "Противопоказания (стандартные + уточнения)": "опухоли в области инъекций",
                    "Описание технологии": "гиалуроновая кислота и факторы роста",
                    "Место оказания услуг": "Клиника"
                },
                "staff_info": {
                    "available_masters": [],
                    "total_staff_count": 0
                }
            },
            {
                "id": "massage_test", 
                "title": "Классический массаж лица",
                "category": "Массаж",
                "price": 2500,
                "duration": 3600,
                "csv_fields": {
                    "Терапевтическая цель": "Расслабление и улучшение кровообращения",
                    "Показания (типичные проблемы)": "усталость кожи, снижение тонуса",
                    "Противопоказания (стандартные + уточнения)": "воспаления на коже",
                    "Описание технологии": "ручной массаж лица",
                    "Место оказания услуг": "Салон"
                },
                "staff_info": {
                    "available_masters": [],
                    "total_staff_count": 0
                }
            }
        ]
        
        test_queries = [
            ("newesthair мезотерапия", "Клиника: +375296080912"),
            ("массаж лица", "Салон: +375445903030")
        ]
        
        for query, expected_contact in test_queries:
            print(f"\\n   Запрос: '{query}'")
            
            # Генерируем ответ через GPT
            response = gpt_client.generate_response(query, test_services)
            
            print(f"   Ответ: {response[:100]}...")
            
            if expected_contact in response:
                print(f"   ✅ Правильный контакт: {expected_contact}")
            else:
                print(f"   ❌ Неправильный контакт")
                print(f"   Полный ответ: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании GPT клиента: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция тестирования."""
    success = True
    
    if not test_gpt_prompt_fix():
        success = False
    
    if not test_direct_gpt_client():
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())