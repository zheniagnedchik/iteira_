#!/usr/bin/env python3
"""
Тест детального подтверждения комбо-записи с реальными мастерами
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_assistant import DialogAssistant
from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule

def test_detailed_combo_confirmation():
    """Тестируем детальное подтверждение комбо-записи"""
    
    print("🧪 ТЕСТ: Детальное подтверждение комбо-записи")
    print("=" * 60)
    
    # Инициализация компонентов
    gpt_client = GPTClient()
    search_module = SearchModule()
    dialog_assistant = DialogAssistant(gpt_client, search_module)
    
    # Контекст с детальными данными комбо-записи
    context = {
        'user_name': 'Евгений',
        'dialog_stage': 'booking_confirmation',
        'is_combo': True,
        'combo_service1': {
            'title': 'Окрашивание',
            'price': 325,
            'id': 'service_456'
        },
        'combo_service2': {
            'title': 'Маникюр классический',
            'price': 60,
            'id': 'service_123'
        },
        'selected_date': '2025-09-01',
        'selected_time': '13:30',
        'last_time_slots': [{
            'sequential_groups': [{
                'type': 'sequential',
                'start_time': '13:30',
                'first_service': {
                    'title': 'Окрашивание',
                    'start': '13:30',
                    'end': '15:30',
                    'master_name': 'Калеко Андрей',
                    'master_id': 201
                },
                'second_service': {
                    'title': 'Маникюр классический',
                    'start': '15:30',
                    'end': '16:30',
                    'master_name': 'Сакович Ольга',
                    'master_id': 101
                }
            }]
        }]
    }
    
    print("📋 Тестовый контекст:")
    print(f"   👤 Клиент: {context['user_name']}")
    print(f"   🔗 Комбо: {context['combo_service1']['title']} + {context['combo_service2']['title']}")
    print(f"   📅 Дата: {context['selected_date']}")
    print(f"   ⏰ Время: {context['selected_time']}")
    print(f"   📊 Слоты: {len(context['last_time_slots'][0]['sequential_groups'])} групп")
    print()
    
    print("🔧 Тестируем _prepare_combo_booking_details")
    print("-" * 40)
    
    try:
        # Создаём dummy decision
        decision = {
            'action': 'select_time_combo',
            'extracted_info': {'time': '13:30'}
        }
        
        # Вызываем метод подготовки деталей
        booking_details = dialog_assistant._prepare_combo_booking_details(context, decision)
        
        print("✅ Метод выполнен успешно!")
        print()
        print("📋 Результат booking_details:")
        print(f"   📝 service_name: {booking_details['service_name']}")
        print(f"   💰 price: {booking_details['price']} руб.")
        print(f"   📅 date_time: {booking_details['date_time']}")
        print(f"   📍 location: {booking_details['location']}")
        print()
        
        print("👥 Мастера:")
        master_info = booking_details['master_name']
        if "Детальное расписание" in master_info:
            print("✅ УСПЕХ: Детальное расписание создано!")
            print("📄 Содержимое:")
            print(master_info)
        elif "уточняются" in master_info:
            print("⚠️  ПРОБЛЕМА: Мастера всё ещё уточняются")
            print(f"   Данные: {master_info}")
        else:
            print(f"🔍 Формат мастеров: {master_info}")
        
        print()
        print("🔧 Дополнительные поля:")
        print(f"   master1_name: {booking_details.get('master1_name')}")
        print(f"   master2_name: {booking_details.get('master2_name')}")
        print(f"   service1_time: {booking_details.get('service1_time')}")
        print(f"   service2_time: {booking_details.get('service2_time')}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("🎯 ФИНАЛЬНАЯ ОЦЕНКА")
    
    if 'Калеко Андрей' in booking_details.get('master_name', '') and 'Сакович Ольга' in booking_details.get('master_name', ''):
        print("✅ ОТЛИЧНО: Реальные мастера в детальном описании!")
    elif 'уточняются' in booking_details.get('master_name', ''):
        print("❌ ПРОБЛЕМА: Мастера не извлекаются из last_time_slots")
    else:
        print("⚠️  ПРОВЕРЬТЕ: Нестандартный формат мастеров")
    
    print()

if __name__ == "__main__":
    test_detailed_combo_confirmation()
