#!/usr/bin/env python3
"""
Тест конкретно на 1 сентября 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_september_1st():
    """Детальная проверка 1 сентября 2025"""
    
    print("🔍 ТЕСТ: 1 сентября 2025")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Целевая дата
    target_date = "2025-09-01"
    print(f"📅 Проверяем дату: {target_date} (1 сентября)")
    print()
    
    # Поиск услуг
    print("🔍 Поиск услуг...")
    manicure_results = search_module.search_with_details("маникюр классический")
    coloring_results = search_module.search_with_details("окрашивание")
    
    if not manicure_results or not coloring_results:
        print("❌ Услуги не найдены")
        return
    
    manicure_service = manicure_results[0]
    coloring_service = coloring_results[0]
    
    print(f"✅ Найден маникюр: {manicure_service.get('title')}")
    print(f"✅ Найдено окрашивание: {coloring_service.get('title')}")
    print()
    
    # Проверяем доступные даты для каждой услуги
    print("📅 Проверка доступных дат...")
    manicure_dates = assistant._get_available_dates_for_service(manicure_service)
    coloring_dates = assistant._get_available_dates_for_service(coloring_service)
    
    print(f"Всего дат маникюра: {len(manicure_dates)}")
    print(f"Всего дат окрашивания: {len(coloring_dates)}")
    
    # Проверяем наличие 1 сентября
    print(f"\n🔍 Проверка наличия {target_date}:")
    manicure_has_date = target_date in manicure_dates
    coloring_has_date = target_date in coloring_dates
    
    print(f"  📋 В маникюре: {'✅ ЕСТЬ' if manicure_has_date else '❌ НЕТ'}")
    print(f"  📋 В окрашивании: {'✅ ЕСТЬ' if coloring_has_date else '❌ НЕТ'}")
    
    if not manicure_has_date:
        print(f"\n📅 Ближайшие даты маникюра к 1 сентября:")
        september_dates = [d for d in manicure_dates if d.startswith('2025-09')]
        if september_dates:
            print(f"  Сентябрь 2025: {september_dates[:10]}")
        else:
            print("  ❌ В сентябре 2025 нет дат")
            # Показываем последние доступные даты
            print(f"  Последние доступные: {sorted(manicure_dates)[-10:]}")
    
    if not coloring_has_date:
        print(f"\n📅 Ближайшие даты окрашивания к 1 сентября:")
        september_dates = [d for d in coloring_dates if d.startswith('2025-09')]
        if september_dates:
            print(f"  Сентябрь 2025: {september_dates[:10]}")
        else:
            print("  ❌ В сентябре 2025 нет дат")
            # Показываем последние доступные даты
            print(f"  Последние доступные: {sorted(coloring_dates)[-10:]}")
    
    # Проверяем пересечение дат
    combo_dates = assistant._get_combo_available_dates(manicure_service, coloring_service)
    combo_has_date = target_date in combo_dates
    
    print(f"\n📋 Пересечение дат:")
    print(f"  Всего общих дат: {len(combo_dates)}")
    print(f"  1 сентября в пересечении: {'✅ ЕСТЬ' if combo_has_date else '❌ НЕТ'}")
    
    if not combo_has_date:
        september_combo = [d for d in combo_dates if d.startswith('2025-09')]
        if september_combo:
            print(f"  Сентябрь 2025 в пересечении: {september_combo[:10]}")
        else:
            print("  ❌ В сентябре 2025 нет общих дат")
            print(f"  Последние общие даты: {sorted(combo_dates)[-10:]}")
    
    # Если дата есть в пересечении - проверяем слоты
    if combo_has_date:
        print(f"\n🎯 Проверка слотов на {target_date}:")
        
        # Слоты маникюра
        print("  Получение слотов маникюра...")
        manicure_slots = assistant._get_time_slots(manicure_service, target_date)
        print(f"  ✅ Слоты маникюра: {len(manicure_slots)}")
        
        # Слоты окрашивания
        print("  Получение слотов окрашивания...")
        coloring_slots = assistant._get_time_slots(coloring_service, target_date)
        print(f"  ✅ Слоты окрашивания: {len(coloring_slots)}")
        
        if manicure_slots and coloring_slots:
            print("  🎯 Создание комбо-слотов...")
            combo_slots = assistant._get_combo_time_slots(manicure_service, coloring_service, target_date)
            print(f"  ✅ Комбо-слоты: {len(combo_slots) if combo_slots else 0}")
            
            if combo_slots and len(combo_slots) > 0:
                slot_data = combo_slots[0]
                if isinstance(slot_data, dict):
                    sequential = slot_data.get('sequential_groups', [])
                    print(f"    📋 Последовательных групп: {len(sequential)}")
                    
                    if sequential:
                        print("    🎯 Первые 3 группы:")
                        for i, group in enumerate(sequential[:3]):
                            print(f"      Группа {i+1}: {group.get('start_time')} → {group.get('description', 'N/A')}")
            
            print("  ✅ 1 СЕНТЯБРЯ - КОМБО ВОЗМОЖНО!")
        else:
            print(f"  ❌ Нет слотов: маникюр={len(manicure_slots)}, окрашивание={len(coloring_slots)}")
    else:
        print(f"\n❌ 1 СЕНТЯБРЯ НЕ ДОСТУПЕН ДЛЯ КОМБО")
        print("   Причина: дата отсутствует в данных мастеров")
    
    print("\n" + "=" * 60)
    print("🏁 РЕЗУЛЬТАТ ПРОВЕРКИ")

if __name__ == "__main__":
    test_september_1st()
