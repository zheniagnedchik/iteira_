#!/usr/bin/env python3
"""
Тест реального поиска комбо-услуг с данными о мастерах
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_real_combo_search():
    """Тест реального поиска маникюра и окрашивания с проверкой данных о мастерах"""
    
    print("🔍 ТЕСТ: Реальный поиск комбо-услуг")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Проверяем поиск маникюра
    print("🔍 ШАГ 1: Поиск маникюра")
    print("-" * 40)
    manicure_results = search_module.search_with_details("маникюр классический")
    print(f"Найдено маникюров: {len(manicure_results)}")
    
    if manicure_results:
        manicure_service = manicure_results[0]
        print(f"Услуга: {manicure_service.get('title', 'Нет названия')}")
        print(f"ID: {manicure_service.get('id', 'Нет ID')}")
        print(f"Цена: {manicure_service.get('price', 'Нет цены')}")
        
        # Проверяем данные о мастерах
        staff_list = assistant._get_all_staff_for_service(manicure_service)
        print(f"Мастеров найдено: {len(staff_list)}")
        
        if staff_list:
            for i, staff in enumerate(staff_list[:3]):  # Первые 3 мастера
                print(f"  Мастер {i+1}: {staff.get('name', 'Без имени')} (ID: {staff.get('id', 'Нет')})")
                booking_dates = staff.get('booking_dates', [])
                print(f"    Доступные даты: {len(booking_dates)} (примеры: {booking_dates[:3]})")
        else:
            print("  ❌ Нет данных о мастерах!")
    else:
        print("❌ Маникюр не найден!")
    
    print()
    
    # Проверяем поиск окрашивания
    print("🔍 ШАГ 2: Поиск окрашивания")
    print("-" * 40)
    coloring_results = search_module.search_with_details("окрашивание")
    print(f"Найдено окрашиваний: {len(coloring_results)}")
    
    if coloring_results:
        coloring_service = coloring_results[0]
        print(f"Услуга: {coloring_service.get('title', 'Нет названия')}")
        print(f"ID: {coloring_service.get('id', 'Нет ID')}")
        print(f"Цена: {coloring_service.get('price', 'Нет цены')}")
        
        # Проверяем данные о мастерах
        staff_list = assistant._get_all_staff_for_service(coloring_service)
        print(f"Мастеров найдено: {len(staff_list)}")
        
        if staff_list:
            for i, staff in enumerate(staff_list[:3]):  # Первые 3 мастера
                print(f"  Мастер {i+1}: {staff.get('name', 'Без имени')} (ID: {staff.get('id', 'Нет')})")
                booking_dates = staff.get('booking_dates', [])
                print(f"    Доступные даты: {len(booking_dates)} (примеры: {booking_dates[:3]})")
        else:
            print("  ❌ Нет данных о мастерах!")
    else:
        print("❌ Окрашивание не найдено!")
    
    print()
    
    # Проверяем комбо с реальными данными
    if manicure_results and coloring_results:
        print("🔍 ШАГ 3: Проверка комбо с реальными данными")
        print("-" * 40)
        
        manicure_service = manicure_results[0]
        coloring_service = coloring_results[0]
        
        # Проверяем пересечение дат
        combo_dates = assistant._get_combo_available_dates(manicure_service, coloring_service)
        print(f"Пересечение дат для комбо: {len(combo_dates)}")
        print(f"Первые 10 дат: {combo_dates[:10]}")
        
        if combo_dates:
            # Проверяем слоты на первую доступную дату
            test_date = combo_dates[0]
            print(f"\n🔍 Слоты на дату {test_date}:")
            
            # Слоты для маникюра
            manicure_slots = assistant._get_time_slots(manicure_service, test_date)
            print(f"Слоты маникюра: {len(manicure_slots)}")
            if manicure_slots:
                print(f"  Примеры времени: {[slot.get('time') for slot in manicure_slots[:5]]}")
            
            # Слоты для окрашивания
            coloring_slots = assistant._get_time_slots(coloring_service, test_date)
            print(f"Слоты окрашивания: {len(coloring_slots)}")
            if coloring_slots:
                print(f"  Примеры времени: {[slot.get('time') for slot in coloring_slots[:5]]}")
            
            # Комбо-слоты
            combo_slots = assistant._get_combo_time_slots(manicure_service, coloring_service, test_date)
            print(f"Комбо-слоты: {len(combo_slots) if combo_slots else 0}")
            
            if combo_slots and len(combo_slots) > 0:
                slot_data = combo_slots[0]
                if isinstance(slot_data, dict):
                    sequential = slot_data.get('sequential_groups', [])
                    print(f"  Последовательных групп: {len(sequential)}")
                    if sequential:
                        print(f"  Пример группы: {sequential[0].get('start_time')} → {sequential[0].get('description', 'Нет описания')}")
        else:
            print("❌ Нет пересечения дат для комбо!")
    
    print("\n" + "=" * 60)
    print("🏁 ЗАВЕРШЕНИЕ ТЕСТА")

if __name__ == "__main__":
    test_real_combo_search()
