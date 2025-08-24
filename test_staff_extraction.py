#!/usr/bin/env python3
"""
Тест извлечения мастеров методом _get_all_staff_for_service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.search_module import SearchModule
from beauty_salon_rag.dialog_assistant import DialogAssistant

def test_staff_extraction():
    """Тест извлечения мастеров DialogAssistant"""
    
    print("🔍 ТЕСТ ИЗВЛЕЧЕНИЯ МАСТЕРОВ")
    print("=" * 60)
    
    # Инициализация
    gpt_client = GPTClient()
    search_module = SearchModule()
    assistant = DialogAssistant(gpt_client, search_module)
    
    # Получаем данные услуги
    print("1️⃣ Получение данных услуги:")
    print("-" * 40)
    manicure_results = search_module.search_with_details("Маникюр классический")
    
    if not manicure_results:
        print("❌ Услуга не найдена!")
        return
        
    service_data = manicure_results[0]
    print(f"Услуга: {service_data.get('title')}")
    print(f"ID: {service_data.get('id')}")
    
    # Проверяем структуру companies
    print(f"\n2️⃣ Структура companies:")
    print("-" * 40)
    companies = service_data.get('companies', [])
    print(f"Количество компаний: {len(companies)}")
    
    if companies:
        company = companies[0]
        staff_in_company = company.get('staff', [])
        print(f"Мастеров в первой компании: {len(staff_in_company)}")
        
        if staff_in_company:
            first_master = staff_in_company[0]
            print(f"Первый мастер: {first_master.get('name')} (ID: {first_master.get('id')})")
    
    # Тестируем метод _get_all_staff_for_service
    print(f"\n3️⃣ Тест метода _get_all_staff_for_service:")
    print("-" * 40)
    extracted_staff = assistant._get_all_staff_for_service(service_data)
    print(f"Метод вернул: {len(extracted_staff)} мастеров")
    
    if extracted_staff:
        print("Извлеченные мастера:")
        for i, staff in enumerate(extracted_staff[:3]):  # Показываем первых 3
            print(f"  {i+1}. {staff.get('name')} (ID: {staff.get('id')})")
            if i == 2 and len(extracted_staff) > 3:
                print(f"     ... и ещё {len(extracted_staff) - 3} мастеров")
    else:
        print("❌ Метод не извлёк ни одного мастера!")
        
        # Проверяем отладочную информацию
        print("\n🔍 Отладка:")
        print(f"   - Есть корневое поле 'staff': {'staff' in service_data}")
        if 'staff' in service_data:
            print(f"   - Содержимое корневого 'staff': {service_data['staff']}")
        
        print(f"   - Есть поле 'companies': {'companies' in service_data}")
        if 'companies' in service_data:
            companies = service_data['companies']
            print(f"   - Тип 'companies': {type(companies)}")
            print(f"   - Длина 'companies': {len(companies) if isinstance(companies, list) else 'не список'}")
            
            if isinstance(companies, list) and companies:
                company = companies[0]
                print(f"   - Тип первой компании: {type(company)}")
                print(f"   - Поля первой компании: {list(company.keys()) if isinstance(company, dict) else 'не словарь'}")
                
                if isinstance(company, dict):
                    company_staff = company.get('staff', 'НЕТ ПОЛЯ')
                    print(f"   - Поле 'staff' в компании: {type(company_staff) if company_staff != 'НЕТ ПОЛЯ' else 'отсутствует'}")
                    if isinstance(company_staff, list):
                        print(f"   - Длина staff в компании: {len(company_staff)}")

if __name__ == "__main__":
    test_staff_extraction()
