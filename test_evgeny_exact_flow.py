#!/usr/bin/env python3
"""
Точное воспроизведение диалога Евгения для поиска проблемы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_evgeny_exact_flow():
    """Точно воспроизводим поток Евгения"""
    
    print("🔍 ТОЧНОЕ ВОСПРОИЗВЕДЕНИЕ ДИАЛОГА ЕВГЕНИЯ")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Контекст как в реальном диалоге после выбора услуг
    context = {
        'user_name': 'Евгений',
        'dialog_stage': 'booking_or_alternatives',
        'is_combo': True,
        'combo_service1': {
            'title': 'Маникюр классический',
            'price': 60,
            'id': '4d558984-0461-4c42-9052-afc4571e82d2'
        },
        'combo_service2': {
            'title': 'Окрашивание',
            'price': 325,
            'id': 'bd2d7b3c-99ce-4417-968b-319ee7495855'
        }
    }
    
    print("📋 Исходный контекст:")
    print(f"  Пользователь: {context['user_name']}")
    print(f"  Стадия: {context['dialog_stage']}")
    print(f"  Комбо: {context['is_combo']}")
    print(f"  Услуга 1: {context['combo_service1']['title']}")
    print(f"  Услуга 2: {context['combo_service2']['title']}")
    print()
    
    # Проверяем, что у нас есть реальные данные для этих услуг
    print("🔍 Проверка реальных данных услуг...")
    
    # Ищем услуги через поисковик (как в реальном диалоге)
    manicure_search = search_module.search_with_details("маникюр классический")
    coloring_search = search_module.search_with_details("окрашивание")
    
    if manicure_search:
        real_manicure = manicure_search[0]
        print(f"✅ Найден маникюр: {real_manicure.get('title')} (ID: {real_manicure.get('id')})")
        
        # Обновляем контекст реальными данными
        context['combo_service1'] = real_manicure
    else:
        print("❌ Маникюр не найден через поиск!")
    
    if coloring_search:
        real_coloring = coloring_search[0]
        print(f"✅ Найдено окрашивание: {real_coloring.get('title')} (ID: {real_coloring.get('id')})")
        
        # Обновляем контекст реальными данными
        context['combo_service2'] = real_coloring
    else:
        print("❌ Окрашивание не найдено через поиск!")
    
    print()
    
    # ШАГ 1: Сообщение "1 сентября" (точно как у Евгения)
    print("🔄 ШАГ 1: Сообщение '1 сентября'")
    print("-" * 40)
    
    message1 = "1 сентября"
    print(f"Отправляем: '{message1}'")
    
    result1 = assistant.process_message("evgeny_test", message1, context.copy())
    
    print(f"Действие: {result1['action']}")
    print(f"Ответ: {result1['response'][:300]}...")
    
    # Проверяем, что сохранилось в контексте
    context1 = result1['context']
    print(f"\nКонтекст после шага 1:")
    print(f"  selected_date: {context1.get('selected_date')}")
    print(f"  is_combo: {context1.get('is_combo')}")
    print(f"  combo_service1: {context1.get('combo_service1', {}).get('title', 'НЕТ')}")
    print(f"  combo_service2: {context1.get('combo_service2', {}).get('title', 'НЕТ')}")
    
    print()
    
    # ШАГ 2: Если первый шаг неудачен, попробуем "6 сентября"
    if result1['action'] == 'no_combo_slots_available':
        print("🔄 ШАГ 2: Сообщение '6 сентября' (как у Евгения)")
        print("-" * 40)
        
        message2 = "6 сентября"
        print(f"Отправляем: '{message2}'")
        
        result2 = assistant.process_message("evgeny_test", message2, context1.copy())
        
        print(f"Действие: {result2['action']}")
        print(f"Ответ: {result2['response'][:300]}...")
        
        context2 = result2['context']
        print(f"\nКонтекст после шага 2:")
        print(f"  selected_date: {context2.get('selected_date')}")
        print()
    
    # ШАГ 3: Проверим manually что происходит с _get_combo_time_slots
    print("🔍 РУЧНАЯ ПРОВЕРКА КОМБО-СЛОТОВ")
    print("-" * 40)
    
    service1 = context.get('combo_service1')
    service2 = context.get('combo_service2')
    test_date = "2025-09-01"
    
    print(f"Проверяем комбо-слоты для {test_date}...")
    print(f"Услуга 1: {service1.get('title') if service1 else 'НЕТ'}")
    print(f"Услуга 2: {service2.get('title') if service2 else 'НЕТ'}")
    
    if service1 and service2:
        combo_slots = assistant._get_combo_time_slots(service1, service2, test_date)
        print(f"Результат: {len(combo_slots) if combo_slots else 0} комбо-слотов")
        
        if combo_slots and len(combo_slots) > 0:
            slot_data = combo_slots[0]
            if isinstance(slot_data, dict):
                sequential = slot_data.get('sequential_groups', [])
                print(f"Последовательных групп: {len(sequential)}")
                
                # Проверяем логику в DialogAssistant
                has_slots = bool(slot_data.get('sequential_groups') or slot_data.get('separate_slots'))
                print(f"has_slots в логике DialogAssistant: {has_slots}")
                
                if not has_slots:
                    print("❌ DialogAssistant считает что нет слотов!")
                else:
                    print("✅ DialogAssistant видит слоты")
            else:
                print(f"❌ Неожиданный тип: {type(slot_data)}")
        else:
            print("❌ Нет комбо-слотов")
    else:
        print("❌ Нет данных об услугах")
    
    print("\n" + "=" * 60)
    print("🏁 ЗАВЕРШЕНИЕ АНАЛИЗА")

if __name__ == "__main__":
    test_evgeny_exact_flow()
