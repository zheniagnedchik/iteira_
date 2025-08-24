#!/usr/bin/env python3
"""
Тест для диагностики проблемы с комбо-записью на примере диалога Евгения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_evgeny_combo_scenario():
    """Воспроизводим точный диалог Евгения с детальным логированием"""
    
    print("🔍 ТЕСТ: Воспроизведение проблемы комбо-записи Евгения")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Контекст как у Евгения
    context = {
        'user_name': 'Евгений',
        'dialog_stage': 'booking_or_alternatives',
        'is_combo': True,
        'combo_service1': {
            'title': 'Маникюр классический',
            'price': 60,
            'id': 'manicure_classic',
            'duration': 3600
        },
        'combo_service2': {
            'title': 'Окрашивание',
            'price': 325,
            'id': 'coloring',
            'duration': 7200
        }
    }
    
    print(f"📋 Начальный контекст:")
    print(f"   Пользователь: {context['user_name']}")
    print(f"   Комбо: {context['is_combo']}")
    print(f"   Услуга 1: {context['combo_service1']['title']}")
    print(f"   Услуга 2: {context['combo_service2']['title']}")
    print()
    
    # Шаг 1: Выбор даты "1 сентября"
    print("🔄 ШАГ 1: Выбор даты '1 сентября'")
    print("-" * 40)
    
    message1 = "1 сентября"
    result1 = assistant.process_message("test_user", message1, context.copy())
    
    print(f"Сообщение: '{message1}'")
    print(f"Действие: {result1['action']}")
    print(f"Ответ: {result1['response'][:200]}...")
    print()
    
    # Обновляем контекст
    context.update(result1['context'])
    
    # Проверяем, что сохранилось в контексте
    print("📊 Контекст после выбора даты:")
    print(f"   selected_date: {context.get('selected_date')}")
    print(f"   is_combo: {context.get('is_combo')}")
    print(f"   combo_service1: {context.get('combo_service1', {}).get('title', 'НЕТ')}")
    print(f"   combo_service2: {context.get('combo_service2', {}).get('title', 'НЕТ')}")
    print()
    
    # Шаг 2: Попробуем другую дату "6 сентября"  
    print("🔄 ШАГ 2: Выбор даты '6 сентября'")
    print("-" * 40)
    
    message2 = "6 сентября"
    result2 = assistant.process_message("test_user", message2, context.copy())
    
    print(f"Сообщение: '{message2}'")
    print(f"Действие: {result2['action']}")
    print(f"Ответ: {result2['response'][:200]}...")
    print()
    
    # Детальная диагностика комбо-слотов
    print("🔍 ДИАГНОСТИКА КОМБО-СЛОТОВ")
    print("-" * 40)
    
    # Получаем данные об услугах
    service1_data = context.get('combo_service1')
    service2_data = context.get('combo_service2')
    
    if service1_data and service2_data:
        print(f"Услуга 1: {service1_data.get('title')}")
        print(f"Услуга 2: {service2_data.get('title')}")
        
        # Проверяем доступные даты для каждой услуги
        dates1 = assistant._get_available_dates_for_service(service1_data)
        dates2 = assistant._get_available_dates_for_service(service2_data)
        
        print(f"\nДоступные даты для услуги 1: {len(dates1)}")
        print(f"Первые 5 дат: {dates1[:5]}")
        
        print(f"\nДоступные даты для услуги 2: {len(dates2)}")
        print(f"Первые 5 дат: {dates2[:5]}")
        
        # Проверяем пересечение дат
        combo_dates = assistant._get_combo_available_dates(service1_data, service2_data)
        print(f"\nПересечение дат для комбо: {len(combo_dates)}")
        print(f"Первые 10 дат: {combo_dates[:10]}")
        
        # Проверяем слоты для конкретной даты
        test_date = "2024-09-01"  # 1 сентября 2024
        print(f"\n🔍 Проверка слотов на {test_date}:")
        
        slots1 = assistant._get_time_slots(service1_data, test_date)
        slots2 = assistant._get_time_slots(service2_data, test_date)
        
        print(f"Слоты для услуги 1: {len(slots1)}")
        if slots1:
            print(f"Примеры: {[slot.get('time') for slot in slots1[:3]]}")
        
        print(f"Слоты для услуги 2: {len(slots2)}")
        if slots2:
            print(f"Примеры: {[slot.get('time') for slot in slots2[:3]]}")
        
        # Проверяем комбо-слоты
        combo_slots = assistant._get_combo_time_slots(service1_data, service2_data, test_date)
        print(f"\nКомбо-слоты на {test_date}: {len(combo_slots) if combo_slots else 0}")
        
        if combo_slots and len(combo_slots) > 0:
            slot_data = combo_slots[0]
            if isinstance(slot_data, dict):
                sequential = slot_data.get('sequential_groups', [])
                separate = slot_data.get('separate_slots', {})
                print(f"Последовательных групп: {len(sequential)}")
                print(f"Отдельных слотов: {len(separate.get('service1', []))} + {len(separate.get('service2', []))}")
                
                if sequential:
                    print("Пример последовательной группы:")
                    group = sequential[0]
                    print(f"  Время: {group.get('start_time')}")
                    print(f"  Услуга 1: {group.get('first_service', {}).get('title')} ({group.get('first_service', {}).get('start')}-{group.get('first_service', {}).get('end')})")
                    print(f"  Услуга 2: {group.get('second_service', {}).get('title')} ({group.get('second_service', {}).get('start')}-{group.get('second_service', {}).get('end')})")
    else:
        print("❌ Не найдены данные об услугах в контексте")
    
    print("\n" + "=" * 60)
    print("🏁 ЗАВЕРШЕНИЕ ТЕСТА")

if __name__ == "__main__":
    test_evgeny_combo_scenario()
