#!/usr/bin/env python3
"""
Тест исправленной комбо-записи - проверяем правильное подтверждение с реальными данными
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_assistant import DialogAssistant
from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule

def test_fixed_combo_booking():
    """Тестируем полный диалог комбо-записи с правильным подтверждением"""
    
    print("🧪 ТЕСТ: Исправленная комбо-запись")
    print("=" * 50)
    
    # Инициализация компонентов
    gpt_client = GPTClient()
    search_module = SearchModule()
    dialog_assistant = DialogAssistant(gpt_client, search_module)
    
    # Контекст с уже подготовленной комбо-записью (как после select_time_combo)
    context = {
        'user_name': 'Евгений',
        'dialog_stage': 'booking_confirmation',
        'is_combo': True,
        'combo_service1': {
            'title': 'Маникюр классический',
            'price': 60,
            'id': 'service_123',
            'companies': [{
                'staff': [
                    {'id': 101, 'name': 'Сакович Ольга', 'booking_dates': ['2025-09-01']}
                ]
            }]
        },
        'combo_service2': {
            'title': 'Окрашивание',
            'price': 325,
            'id': 'service_456',
            'companies': [{
                'staff': [
                    {'id': 201, 'name': 'Калеко Андрей', 'booking_dates': ['2025-09-01']}
                ]
            }]
        },
        'selected_date': '2025-09-01',
        'selected_time': '10:00',
        'last_time_slots': [{
            'sequential_groups': [{
                'type': 'sequential',
                'start_time': '10:00',
                'first_service': {
                    'title': 'Окрашивание',
                    'start': '10:00',
                    'end': '11:00',
                    'master_name': 'Калеко Андрей',
                    'master_id': 201
                },
                'second_service': {
                    'title': 'Маникюр классический',
                    'start': '11:00',
                    'end': '12:00',
                    'master_name': 'Сакович Ольга',
                    'master_id': 101
                }
            }]
        }]
    }
    
    print("📋 Контекст подготовлен:")
    print(f"   👤 Клиент: {context['user_name']}")
    print(f"   🔗 Комбо: {context['combo_service1']['title']} + {context['combo_service2']['title']}")
    print(f"   📅 Дата: {context['selected_date']}")
    print(f"   ⏰ Время: {context['selected_time']}")
    print()
    
    # Имитируем выбор времени для комбо (это должно запустить подтверждение)
    print("1️⃣ Тестируем действие select_time_combo")
    print("-" * 30)
    
    try:
        # Создаем решение для select_time_combo
        decision = {
            'action': 'select_time_combo',
            'stage': 'booking_confirmation',
            'extracted_info': {'time': '10:00'}
        }
        
        response = {
            'text': 'Начинаем подтверждение...',
            'action': 'select_time_combo'
        }
        
        # Эмулируем логику из process_message
        updated_context = context.copy()
        
        # Проверяем срабатывание логики select_time_combo
        if decision.get('action') == 'select_time_combo':
            print("✅ Распознано действие select_time_combo")
            
            # Подготавливаем детали комбо-записи
            booking_details = dialog_assistant._prepare_combo_booking_details(updated_context, decision)
            print("✅ Подготовлены детали комбо-записи:")
            print(f"   📋 Услуга: {booking_details['service_name']}")
            print(f"   👨‍💼 Мастера: {booking_details['master_name']}")
            print(f"   📅 Дата/время: {booking_details['date_time']}")
            print(f"   💰 Стоимость: {booking_details['price']} руб.")
            print()
            
            # Запускаем подтверждение записи
            confirmation_response, confirmation_context = dialog_assistant.booking_confirmation.start_booking_confirmation(booking_details)
            
            print("✅ Запущен процесс подтверждения записи:")
            print(f"📝 Ответ бота:")
            print(confirmation_response)
            print()
            print(f"🔧 Обновленный контекст:")
            print(f"   📍 booking_stage: {confirmation_context.get('booking_stage')}")
            print(f"   📋 booking_details: {len(confirmation_context.get('booking_details', {}))} полей")
            
        else:
            print("❌ Действие select_time_combo НЕ обработано!")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("2️⃣ Проверка исправления заглушек")
    print("-" * 30)
    
    # Проверяем, что заглушки заменены реальными данными
    if 'booking_details' in confirmation_context:
        details = confirmation_context['booking_details']
        
        issues = []
        if details.get('service_name') in ['Услуга', 'Комбо-услуга']:
            issues.append("service_name содержит заглушку")
        if details.get('master_name') == 'Мастер':
            issues.append("master_name содержит заглушку")
        if details.get('date_time') == 'Дата и время':
            issues.append("date_time содержит заглушку")
            
        if issues:
            print("❌ Найдены заглушки:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Все заглушки заменены реальными данными!")
            print(f"   📋 Услуга: {details.get('service_name')}")
            print(f"   👨‍💼 Мастер: {details.get('master_name')}")
            print(f"   📅 Дата/время: {details.get('date_time')}")
    
    print()
    print("=" * 50)
    print("🎯 РЕЗУЛЬТАТ ТЕСТА")
    
    if 'Калеко Андрей' in confirmation_response and 'Сакович Ольга' in confirmation_response:
        print("✅ УСПЕХ: Комбо-запись работает с реальными мастерами!")
    elif 'Мастер' in confirmation_response:
        print("❌ ПРОБЛЕМА: Все еще показывается заглушка 'Мастер'")
    else:
        print("⚠️  ЧАСТИЧНО: Комбо-запись работает, но нужна проверка")
    
    print()

if __name__ == "__main__":
    test_fixed_combo_booking()
