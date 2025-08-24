#!/usr/bin/env python3
"""
Детальный анализ структуры услуг лазерной эпиляции
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def analyze_laser_services():
    """Детальный анализ структуры услуг лазерной эпиляции."""
    print("🔬 Детальный анализ услуг лазерной эпиляции\n")
    
    try:
        rag_system = BeautySalonRAG()
        
        # Получаем список услуг напрямую через поиск
        search_module = rag_system.search_module
        service_ids = search_module.find_services("лазерная эпиляция")
        
        # Получаем полную информацию об услугах
        consultation_module = rag_system.consultation_module
        services = consultation_module.get_services_by_ids(service_ids)
        
        print("📋 ПОЛНАЯ структура найденных услуг:")
        print("="*80)
        
        for i, service in enumerate(services, 1):
            print(f"\n🔍 УСЛУГА {i}:")
            print(f"💰 Цена: {service.get('price', 'Не указана')}")
            
            # Выводим ВСЕ поля услуги
            for key, value in service.items():
                if key != 'price':  # price уже показали
                    if isinstance(value, (dict, list)):
                        print(f"   {key}: {json.dumps(value, ensure_ascii=False, indent=4)}")
                    else:
                        print(f"   {key}: {value}")
            print("-" * 60)
        
        print("\n🎯 КЛЮЧЕВЫЕ поля для различения услуг:")
        
        # Анализируем различающиеся поля
        all_keys = set()
        for service in services:
            all_keys.update(service.keys())
        
        different_fields = {}
        for key in all_keys:
            values = []
            for service in services:
                value = service.get(key)
                if value not in values:
                    values.append(value)
            if len(values) > 1:
                different_fields[key] = values
        
        for field, values in different_fields.items():
            print(f"✅ {field}: {len(values)} разных значений")
            for value in values[:3]:  # показываем первые 3
                if len(str(value)) < 100:
                    print(f"   - {value}")
                else:
                    print(f"   - {str(value)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    analyze_laser_services()

