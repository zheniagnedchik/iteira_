#!/usr/bin/env python3
"""
Тест комбо-записи с актуальными датами
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_current_date_combo():
    """Тест комбо с актуальными датами, чтобы избежать ошибки API"""
    
    print("🔍 ТЕСТ: Комбо с актуальными датами")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Получаем актуальные даты
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    print(f"📅 Сегодня: {today.strftime('%Y-%m-%d')}")
    print(f"📅 Завтра: {tomorrow.strftime('%Y-%m-%d')}")
    print(f"📅 Послезавтра: {day_after.strftime('%Y-%m-%d')}")
    print()
    
    # Поиск услуг
    manicure_results = search_module.search_with_details("маникюр классический")
    coloring_results = search_module.search_with_details("окрашивание")
    
    if not manicure_results or not coloring_results:
        print("❌ Не найдены услуги")
        return
    
    manicure_service = manicure_results[0]
    coloring_service = coloring_results[0]
    
    print(f"✅ Маникюр: {manicure_service.get('title')}")
    print(f"✅ Окрашивание: {coloring_service.get('title')}")
    print()
    
    # Проверим доступные даты для каждой услуги
    manicure_dates = assistant._get_available_dates_for_service(manicure_service)
    coloring_dates = assistant._get_available_dates_for_service(coloring_service)
    
    print(f"📅 Даты маникюра: {len(manicure_dates)}")
    print(f"📅 Даты окрашивания: {len(coloring_dates)}")
    
    # Проверяем актуальные даты
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    day_after_str = day_after.strftime('%Y-%m-%d')
    
    print(f"\n🔍 Проверка наличия актуальных дат:")
    print(f"  Завтра ({tomorrow_str}) в маникюре: {'✅' if tomorrow_str in manicure_dates else '❌'}")
    print(f"  Завтра ({tomorrow_str}) в окрашивании: {'✅' if tomorrow_str in coloring_dates else '❌'}")
    print(f"  Послезавтра ({day_after_str}) в маникюре: {'✅' if day_after_str in manicure_dates else '❌'}")
    print(f"  Послезавтра ({day_after_str}) в окрашивании: {'✅' if day_after_str in coloring_dates else '❌'}")
    
    # Найдем первую общую дату
    combo_dates = assistant._get_combo_available_dates(manicure_service, coloring_service)
    
    # Фильтруем только будущие даты
    future_dates = []
    for date_str in combo_dates:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj.date() >= today.date():
                future_dates.append(date_str)
        except ValueError:
            continue
    
    print(f"\n📅 Общих будущих дат: {len(future_dates)}")
    if future_dates:
        print(f"Первые 5: {future_dates[:5]}")
        
        # Тестируем слоты на первую доступную дату
        test_date = future_dates[0]
        print(f"\n🔍 Тест слотов на {test_date}:")
        
        # Слоты для маникюра
        print("  Получение слотов маникюра...")
        manicure_slots = assistant._get_time_slots(manicure_service, test_date)
        print(f"  ✅ Слоты маникюра: {len(manicure_slots)}")
        
        # Слоты для окрашивания  
        print("  Получение слотов окрашивания...")
        coloring_slots = assistant._get_time_slots(coloring_service, test_date)
        print(f"  ✅ Слоты окрашивания: {len(coloring_slots)}")
        
        if manicure_slots and coloring_slots:
            print(f"  Примеры времени маникюра: {[slot.get('time') for slot in manicure_slots[:3]]}")
            print(f"  Примеры времени окрашивания: {[slot.get('time') for slot in coloring_slots[:3]]}")
            
            # Комбо-слоты
            print("  Создание комбо-слотов...")
            combo_slots = assistant._get_combo_time_slots(manicure_service, coloring_service, test_date)
            print(f"  ✅ Комбо-слоты: {len(combo_slots) if combo_slots else 0}")
            
            if combo_slots and len(combo_slots) > 0:
                slot_data = combo_slots[0]
                if isinstance(slot_data, dict):
                    sequential = slot_data.get('sequential_groups', [])
                    separate = slot_data.get('separate_slots', {})
                    print(f"  📋 Последовательных групп: {len(sequential)}")
                    print(f"  📋 Отдельных слотов: {len(separate.get('service1', []))} + {len(separate.get('service2', []))}")
                    
                    if sequential:
                        print("  🎯 Пример последовательной группы:")
                        group = sequential[0]
                        print(f"    Время начала: {group.get('start_time')}")
                        print(f"    Описание: {group.get('description')}")
                        
                        first_service = group.get('first_service', {})
                        second_service = group.get('second_service', {})
                        print(f"    1️⃣ {first_service.get('title')}: {first_service.get('start')}-{first_service.get('end')} ({first_service.get('master_name')})")
                        print(f"    2️⃣ {second_service.get('title')}: {second_service.get('start')}-{second_service.get('end')} ({second_service.get('master_name')})")
                else:
                    print("  ❌ Неожиданный формат комбо-слотов")
            else:
                print("  ❌ Комбо-слоты не созданы")
        else:
            print("  ❌ Нет слотов для одной или обеих услуг")
    else:
        print("❌ Нет общих будущих дат")
    
    print("\n" + "=" * 60)
    print("🏁 ЗАВЕРШЕНИЕ ТЕСТА")

if __name__ == "__main__":
    test_current_date_combo()
