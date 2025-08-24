#!/usr/bin/env python3
"""
Тест исправления проблемы с потерей last_time_slots для комбо
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_assistant import DialogAssistant
from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule

def test_combo_slot_preservation():
    """Тестируем сохранение last_time_slots для select_time_combo"""
    
    print("🧪 ТЕСТ: Сохранение last_time_slots для комбо")
    print("=" * 60)
    
    # Инициализация компонентов
    gpt_client = GPTClient()
    search_module = SearchModule()
    dialog_assistant = DialogAssistant(gpt_client, search_module)
    
    # Симулируем полный flow комбо-записи
    user_id = "test_user"
    
    print("🎬 Симулируем полный диалог:")
    print()
    
    # 1. Начальный контекст
    initial_context = {
        'user_name': 'Евгений',
        'dialog_stage': 'start',
        'conversation_history': []
    }
    
    # 2. Первое сообщение - комбо запрос
    print("👤 Пользователь: хочу записаться на маникюр и окрашивание")
    result1 = dialog_assistant.process_message(user_id, "хочу записаться на маникюр и окрашивание", initial_context)
    print(f"🤖 Бот: {result1['response'][:100]}...")
    print(f"📊 Контекст: is_combo={result1['context'].get('is_combo')}")
    print()
    
    # 3. Выбор первой услуги
    print("👤 Пользователь: Маникюр классический")
    result2 = dialog_assistant.process_message(user_id, "Маникюр классический", result1['context'])
    print(f"🤖 Бот: {result2['response'][:100]}...")
    print(f"📊 Контекст: combo_service1={result2['context'].get('combo_service1', {}).get('title', 'НЕТ')}")
    print()
    
    # 4. Выбор второй услуги
    print("👤 Пользователь: Окрашивание")
    result3 = dialog_assistant.process_message(user_id, "Окрашивание", result2['context'])
    print(f"🤖 Бот: {result3['response'][:100]}...")
    print(f"📊 Контекст: combo_service2={result3['context'].get('combo_service2', {}).get('title', 'НЕТ')}")
    print()
    
    # 5. Выбор "в один день"
    print("👤 Пользователь: один")
    result4 = dialog_assistant.process_message(user_id, "один", result3['context'])
    print(f"🤖 Бот: {result4['response'][:150]}...")
    print(f"📊 Действие: {result4.get('action')}")
    print()
    
    # 6. Выбор даты
    print("👤 Пользователь: 1 сентября")
    result5 = dialog_assistant.process_message(user_id, "1 сентября", result4['context'])
    print(f"🤖 Бот: {result5['response'][:150]}...")
    print(f"📊 last_time_slots: {len(result5['context'].get('last_time_slots', []))} слотов")
    print()
    
    # 7. КРИТИЧЕСКИЙ МОМЕНТ: Выбор времени
    print("👤 Пользователь: 12:30")
    print("🔍 ПРОВЕРЯЕМ: сохраняются ли last_time_slots для select_time_combo")
    result6 = dialog_assistant.process_message(user_id, "12:30", result5['context'])
    
    print(f"🤖 Бот: {result6['response']}")
    print()
    print("🔍 ДИАГНОСТИКА:")
    print(f"   📊 Действие: {result6.get('action')}")
    print(f"   📊 last_time_slots в финальном контексте: {len(result6['context'].get('last_time_slots', []))} слотов")
    
    if result6['context'].get('last_time_slots'):
        print("   ✅ last_time_slots СОХРАНЕНЫ!")
        slot_data = result6['context']['last_time_slots'][0]
        if isinstance(slot_data, dict):
            print(f"   📋 Структура слота: {list(slot_data.keys())}")
            if 'sequential_groups' in slot_data:
                groups = slot_data['sequential_groups']
                print(f"   🎯 sequential_groups: {len(groups)} групп")
                if groups:
                    first_service = groups[0].get('first_service', {})
                    second_service = groups[0].get('second_service', {})
                    print(f"   👤 Мастер 1: {first_service.get('master_name', 'НЕТ')}")
                    print(f"   👤 Мастер 2: {second_service.get('master_name', 'НЕТ')}")
    else:
        print("   ❌ last_time_slots ПОТЕРЯНЫ!")
    
    # Проверяем результат подтверждения
    if "Детальное расписание" in result6['response']:
        print("\n✅ УСПЕХ: Детальное расписание отображается!")
    elif "уточняются администратором" in result6['response']:
        print("\n❌ ПРОБЛЕМА: Всё ещё показываются заглушки")
    else:
        print(f"\n🔍 НЕОПРЕДЕЛЁННО: {result6['response']}")
    
    print()
    print("=" * 60)
    print("🎯 ИТОГ ТЕСТА")
    
    has_slots = bool(result6['context'].get('last_time_slots'))
    has_details = "Детальное расписание" in result6['response']
    
    if has_slots and has_details:
        print("✅ ТЕСТ ПРОЙДЕН: Слоты сохраняются и отображаются детали!")
    elif has_slots and not has_details:
        print("⚠️  ЧАСТИЧНО: Слоты сохраняются, но детали не отображаются")
    elif not has_slots:
        print("❌ ТЕСТ ПРОВАЛЕН: Слоты не сохраняются")
    
    print()

if __name__ == "__main__":
    test_combo_slot_preservation()
