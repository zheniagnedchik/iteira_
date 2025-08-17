#!/usr/bin/env python3
"""
Скрипт для очистки кэша GPT клиента.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def clear_gpt_cache():
    """Очищает кэш GPT клиента."""
    
    print("🧹 Очистка кэша GPT клиента")
    print("=" * 30)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        # Создаем GPT клиент
        gpt_client = GPTClient()
        
        # Очищаем кэш
        gpt_client.clear_cache()
        
        print("✅ Кэш GPT клиента очищен")
        
        # Показываем статистику
        stats = gpt_client.get_cache_stats()
        print(f"📊 Статистика кэша:")
        print(f"   Всего записей: {stats['total_entries']}")
        print(f"   Валидных записей: {stats['valid_entries']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при очистке кэша: {e}")
        return False


if __name__ == "__main__":
    success = clear_gpt_cache()
    sys.exit(0 if success else 1)