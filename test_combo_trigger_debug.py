#!/usr/bin/env python3
"""
Диагностика проблемы с триггером "один" в комбо-записи
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_assistant import DialogAssistant
from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule

def test_combo_trigger():
    """Тестируем триггер 'один' для комбо-записи"""
    
    print("🔍 ДИАГНОСТИКА: Триггер 'один' в комбо-записи")
    print("=" * 50)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    dialog_assistant = DialogAssistant(gpt_client, search_module)
    
    # Контекст после выбора обеих услуг (как у Евгения)
    context = {
        'user_name': 'Евгений',
        'dialog_stage': 'ask_combo_dates',
        'is_combo': True,
        'combo_service1': {
            'title': 'Окрашивание',
            'price': 325,
            'id': 'service_456',
            'companies': [{
                'staff': [
                    {'id': 201, 'name': 'Калеко Андрей', 'booking_dates': ['2025-09-01']}
                ]
            }]
        },
        'combo_service2': {
            'title': 'Маникюр классический', 
            'price': 60,
            'id': 'service_123',
            'companies': [{
                'staff': [
                    {'id': 101, 'name': 'Сакович Ольга', 'booking_dates': ['2025-09-01']}
                ]
            }]
        }
    }
    
    print("📋 Контекст:")
    print(f"   ✅ is_combo: {context['is_combo']}")
    print(f"   ✅ combo_service1: {context['combo_service1']['title']}")
    print(f"   ✅ combo_service2: {context['combo_service2']['title']}")
    print(f"   🎯 dialog_stage: {context['dialog_stage']}")
    print()
    
    # Тестируем сообщение "один"
    message = "один"
    user_id = "test_user"
    
    print(f"👤 Сообщение: '{message}'")
    print("-" * 30)
    
    try:
        result = dialog_assistant.process_message(
            user_id=user_id,
            message=message,
            context=context
        )
        
        response = result['response']
        updated_context = result['context']
        action = result['action']
        
        print(f"🤖 Ответ: {response[:150]}{'...' if len(response) > 150 else ''}")
        print()
        print(f"🔧 Действие: {action}")
        print(f"📊 Новый этап: {updated_context.get('dialog_stage')}")
        
        # Проверяем, что произошло
        if action == 'show_dates':
            print("✅ УСПЕХ: Распознан триггер для показа дат")
        elif action == 'show_combo_time_slots':
            print("✅ УСПЕХ: Переход к показу комбо-слотов")
        elif "НА ЭТОЙ НЕДЕЛЕ" in response or "НА СЛЕДУЮЩЕЙ НЕДЕЛЕ" in response:
            print("✅ УСПЕХ: Показаны даты для комбо")
        elif "Наши основные направления" in response:
            print("❌ ПРОБЛЕМА: Система вернулась к общему меню!")
            print("   Возможные причины:")
            print("   - Не сработал триггер 'один'")
            print("   - Потерян контекст комбо")
            print("   - GPT неправильно распарсил сообщение")
        else:
            print("⚠️  НЕОПРЕДЕЛЁННО: Неожиданная реакция системы")
            
        # Дополнительные проверки
        if updated_context.get('is_combo'):
            print(f"✅ Комбо-флаг сохранён: {updated_context.get('is_combo')}")
        else:
            print("❌ ПОТЕРЯН комбо-флаг!")
            
        if updated_context.get('combo_service1') and updated_context.get('combo_service2'):
            print("✅ Комбо-услуги сохранены")
        else:
            print("❌ ПОТЕРЯНЫ комбо-услуги!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 50)
    print("🎯 ДИАГНОЗ")
    
    # Проверяем триггеры в коде
    trigger_found = False
    expected_triggers = ["в один день", "одну дату", "вместе", "совместно", "за раз", "сразу обе"]
    
    for trigger in expected_triggers:
        if trigger in message.lower():
            trigger_found = True
            print(f"✅ Найден триггер: '{trigger}'")
            break
    
    if not trigger_found:
        print("❌ ПРОБЛЕМА: 'один' не входит в список триггеров!")
        print("   Текущие триггеры:")
        for trigger in expected_triggers:
            print(f"   - '{trigger}'")
        print()
        print("💡 РЕШЕНИЕ: Добавить 'один' в триггеры show_dates")
    
    print()

if __name__ == "__main__":
    test_combo_trigger()
