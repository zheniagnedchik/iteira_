#!/usr/bin/env python3
"""
Диагностика проблемы поиска мастеров для комбо-услуг
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.modules.search_module import SearchModule

def test_master_search_issue():
    """Тест поиска мастеров для услуг"""
    
    print("🔍 ДИАГНОСТИКА ПОИСКА МАСТЕРОВ")
    print("=" * 60)
    
    search_module = SearchModule()
    
    print("1️⃣ Тест поиска маникюра:")
    print("-" * 40)
    manicure_results = search_module.search_with_details("маникюр классический")
    print(f"Найдено: {len(manicure_results)} результатов")
    
    if manicure_results:
        first_manicure = manicure_results[0]
        print(f"Первый результат: {first_manicure.get('title', 'Нет названия')}")
        print(f"Мастера: {len(first_manicure.get('staff', []))} человек")
        
        staff_list = first_manicure.get('staff', [])
        for i, staff in enumerate(staff_list[:3]):  # Показываем первых 3
            print(f"  - {staff.get('name', 'Без имени')} (ID: {staff.get('id', 'Нет ID')})")
            if i == 2 and len(staff_list) > 3:
                print(f"  ... и ещё {len(staff_list) - 3} мастеров")
    
    print("\n2️⃣ Тест поиска окрашивания:")
    print("-" * 40)
    coloring_results = search_module.search_with_details("окрашивание")
    print(f"Найдено: {len(coloring_results)} результатов")
    
    if coloring_results:
        first_coloring = coloring_results[0]
        print(f"Первый результат: {first_coloring.get('title', 'Нет названия')}")
        print(f"Мастера: {len(first_coloring.get('staff', []))} человек")
        
        staff_list = first_coloring.get('staff', [])
        for i, staff in enumerate(staff_list[:3]):  # Показываем первых 3
            print(f"  - {staff.get('name', 'Без имени')} (ID: {staff.get('id', 'Нет ID')})")
            if i == 2 and len(staff_list) > 3:
                print(f"  ... и ещё {len(staff_list) - 3} мастеров")
    
    print(f"\n{'🔍'*20} ДЕТАЛЬНЫЙ АНАЛИЗ {'🔍'*20}")
    print("-" * 80)
    
    # Проверяем конкретные названия услуг
    print("3️⃣ Поиск точных названий:")
    print("-" * 40)
    
    exact_searches = [
        "Маникюр классический",
        "маникюр классический", 
        "Окрашивание",
        "окрашивание"
    ]
    
    for search_term in exact_searches:
        results = search_module.search_with_details(search_term)
        print(f"'{search_term}' → {len(results)} результатов")
        if results:
            first_result = results[0]
            print(f"  Название: {first_result.get('title', 'Нет названия')}")
            print(f"  Мастера: {len(first_result.get('staff', []))}")
        print()

if __name__ == "__main__":
    test_master_search_issue()
