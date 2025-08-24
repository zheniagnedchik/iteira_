#!/usr/bin/env python3
"""
Тест слотов на завтра - более стабильные данные
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_tomorrow_slots():
    """Тест слотов на завтра"""
    
    print("🔍 ТЕСТ: Слоты на завтра")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Завтрашняя дата
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    
    print(f"📅 Тестируем дату: {tomorrow_str}")
    print()
    
    # Поиск услуг
    manicure_results = search_module.search_with_details("маникюр классический")
    coloring_results = search_module.search_with_details("окрашивание")
    
    manicure_service = manicure_results[0]
    coloring_service = coloring_results[0]
    
    print(f"✅ Маникюр: {manicure_service.get('title')}")
    print(f"✅ Окрашивание: {coloring_service.get('title')}")
    print()
    
    # Тестируем слоты
    print("🔍 Слоты маникюра на завтра:")
    manicure_slots = assistant._get_time_slots(manicure_service, tomorrow_str)
    print(f"  Найдено: {len(manicure_slots)}")
    if manicure_slots:
        times = [slot.get('time') for slot in manicure_slots[:5]]
        masters = [slot.get('master_name') for slot in manicure_slots[:5]]
        print(f"  Примеры времени: {times}")
        print(f"  Мастера: {masters}")
    print()
    
    print("🔍 Слоты окрашивания на завтра:")
    coloring_slots = assistant._get_time_slots(coloring_service, tomorrow_str)
    print(f"  Найдено: {len(coloring_slots)}")
    if coloring_slots:
        times = [slot.get('time') for slot in coloring_slots[:5]]
        masters = [slot.get('master_name') for slot in coloring_slots[:5]]
        print(f"  Примеры времени: {times}")
        print(f"  Мастера: {masters}")
    print()
    
    # Если есть слоты для обеих услуг - тестируем комбо
    if manicure_slots and coloring_slots:
        print("🎯 Создание комбо-слотов:")
        combo_slots = assistant._get_combo_time_slots(manicure_service, coloring_service, tomorrow_str)
        print(f"  Комбо-слоты: {len(combo_slots) if combo_slots else 0}")
        
        if combo_slots and len(combo_slots) > 0:
            slot_data = combo_slots[0]
            if isinstance(slot_data, dict):
                sequential = slot_data.get('sequential_groups', [])
                separate = slot_data.get('separate_slots', {})
                print(f"  ✅ Последовательных групп: {len(sequential)}")
                print(f"  📋 Отдельных слотов: service1={len(separate.get('service1', []))}, service2={len(separate.get('service2', []))}")
                
                if sequential:
                    print("\n  🎯 Примеры последовательных групп:")
                    for i, group in enumerate(sequential[:3]):  # Показываем первые 3
                        print(f"    Группа {i+1}: {group.get('start_time')} → {group.get('description', 'Нет описания')}")
                        first = group.get('first_service', {})
                        second = group.get('second_service', {})
                        print(f"      1️⃣ {first.get('title', 'N/A')}: {first.get('start', 'N/A')}-{first.get('end', 'N/A')} ({first.get('master_name', 'N/A')})")
                        print(f"      2️⃣ {second.get('title', 'N/A')}: {second.get('start', 'N/A')}-{second.get('end', 'N/A')} ({second.get('master_name', 'N/A')})")
                        print()
                
                print("  ✅ КОМБО-ЗАПИСЬ ВОЗМОЖНА!")
            else:
                print("  ❌ Неожиданный формат комбо-слотов")
        else:
            print("  ❌ Комбо-слоты не созданы")
    else:
        print("❌ КОМБО НЕВОЗМОЖНО - нет слотов для одной или обеих услуг")
        print(f"   Маникюр: {len(manicure_slots)} слотов")
        print(f"   Окрашивание: {len(coloring_slots)} слотов")
    
    print("\n" + "=" * 60)
    print("🏁 ЗАВЕРШЕНИЕ ТЕСТА")

if __name__ == "__main__":
    test_tomorrow_slots()
