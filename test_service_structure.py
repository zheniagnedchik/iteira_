#!/usr/bin/env python3
"""
Тест структуры данных услуг для понимания проблемы с мастерами
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.modules.search_module import SearchModule

def test_service_structure():
    """Анализ структуры данных услуг"""
    
    print("🔍 АНАЛИЗ СТРУКТУРЫ ДАННЫХ УСЛУГ")
    print("=" * 80)
    
    search_module = SearchModule()
    
    # Ищем маникюр
    print("1️⃣ Поиск маникюра:")
    print("-" * 40)
    manicure_results = search_module.search_with_details("Маникюр классический")
    
    if manicure_results:
        service = manicure_results[0]
        print(f"Название: {service.get('title', 'Нет названия')}")
        print(f"ID: {service.get('id', 'Нет ID')}")
        print(f"Структура полей: {list(service.keys())}")
        print()
        
        # Анализируем companies
        companies = service.get('companies', [])
        print(f"Компаний: {len(companies)}")
        
        if companies:
            company = companies[0]
            print(f"Первая компания: {json.dumps(company, indent=2, ensure_ascii=False)}")
            
            staff = company.get('staff', [])
            print(f"\nМастера в первой компании: {len(staff)}")
            
            if staff:
                print("Первый мастер:")
                master = staff[0]
                print(f"  - ID: {master.get('id')}")
                print(f"  - Имя: {master.get('name')}")
                print(f"  - Даты: {master.get('booking_dates', [])[:3]}...")
        
        print(f"\n{'='*60}")
        
        # Проверяем есть ли прямое поле staff
        direct_staff = service.get('staff', 'НЕТ ПОЛЯ')
        print(f"Прямое поле 'staff': {direct_staff}")
        
        # Считаем общее количество мастеров
        total_masters = 0
        for company in companies:
            total_masters += len(company.get('staff', []))
        
        print(f"Общее количество мастеров: {total_masters}")
    else:
        print("❌ Маникюр не найден!")

if __name__ == "__main__":
    test_service_structure()
