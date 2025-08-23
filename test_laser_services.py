#!/usr/bin/env python3
"""
Тест для просмотра услуг лазерной эпиляции
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_laser_services():
    """Показывает, какие услуги находятся для лазерной эпиляции."""
    print("🔍 Анализ услуг лазерной эпиляции\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        # Запрос как у Евгения
        user_id = 12345
        message = "хочу лазерную эпиляцию"
        
        print(f"🧪 Запрос: '{message}'\n")
        
        # Получаем список услуг напрямую через поиск
        search_module = rag_system.search_module
        service_ids = search_module.find_services("лазерная эпиляция")
        
        print(f"📊 Найдено услуг: {len(service_ids)}")
        print(f"🔢 ID услуг: {service_ids}\n")
        
        # Получаем полную информацию об услугах
        consultation_module = rag_system.consultation_module
        services = consultation_module.get_services_by_ids(service_ids)
        
        print("📋 Детали найденных услуг:")
        print("="*60)
        
        for i, service in enumerate(services, 1):
            print(f"\n{i}️⃣ {service.get('name', 'Без названия')}")
            print(f"   💰 Цена: {service.get('price', 'Не указана')}")
            print(f"   ⏱️  Время: {service.get('duration', 'Не указано')}")
            print(f"   📝 Описание: {service.get('description', 'Нет описания')[:100]}...")
            
            # Смотрим категорию
            category = service.get('category', 'Не указана')
            print(f"   🏷️  Категория: {category}")
        
        print("\n" + "="*60)
        print("\n🎯 Анализ различий между услугами:")
        
        # Анализируем, чем отличаются услуги
        categories = set()
        prices = []
        durations = []
        
        for service in services:
            if service.get('category'):
                categories.add(service.get('category'))
            if service.get('price'):
                try:
                    price_str = str(service.get('price', '')).replace(' руб.', '').replace(',', '.')
                    price = float(price_str)
                    prices.append(price)
                except:
                    pass
            if service.get('duration'):
                durations.append(service.get('duration'))
        
        print(f"📂 Категории: {list(categories)}")
        if prices:
            print(f"💰 Диапазон цен: {min(prices)} - {max(prices)} руб.")
        if durations:
            print(f"⏱️  Варианты времени: {list(set(durations))}")
        
        print("\n🤔 Вопрос: какие вопросы нужно задать, чтобы выбрать между этими услугами?")
        
        # Ключевые различия
        differences = []
        if len(categories) > 1:
            differences.append("Разные категории услуг")
        if len(set(prices)) > 1:
            differences.append("Разные цены")
        if len(set(durations)) > 1:
            differences.append("Разное время выполнения")
            
        for diff in differences:
            print(f"   ✅ {diff}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("🔬 Анализ услуг лазерной эпиляции\n")
    test_laser_services()
