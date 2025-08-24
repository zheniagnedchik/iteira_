#!/usr/bin/env python3
"""
Тест последовательных записей: сначала маникюр, потом окрашивание
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

# Отключаем все логи
import logging
logging.disable(logging.CRITICAL)

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
from beauty_salon_rag.gpt_client import GPTClient
from beauty_salon_rag.modules.data_loader import DataLoader

def clear_all_caches_and_context():
    """Полностью очищает весь кеш и контекст системы"""
    try:
        # Очищаем кеш GPT клиента
        gpt_client = GPTClient()
        gpt_client.clear_cache()
        print("✅ Кеш GPT клиента очищен")
        
        # Очищаем кеш данных
        data_loader = DataLoader()
        data_loader.clear_cache()
        print("✅ Кеш данных очищен")
        
    except Exception as e:
        print(f"⚠️ Ошибка при очистке кеша: {e}")

def clear_user_context(orchestrator, user_id):
    """Очищает контекст пользователя"""
    try:
        orchestrator.clear_user_context(user_id)
        print(f"✅ Контекст пользователя {user_id} очищен")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке контекста: {e}")

def main():
    print("ДИАЛОГ ПОСЛЕДОВАТЕЛЬНЫХ ЗАПИСЕЙ")
    print("=" * 60)
    print()
    
    # Полная очистка кеша и контекста перед стартом
    print("🧹 Очистка системы перед стартом:")
    clear_all_caches_and_context()
    print()
    
    config = {
        'USE_NEW_DIALOG_SYSTEM': True,
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'YCLIENTS_LOGIN': os.getenv('YCLIENTS_LOGIN'),
        'YCLIENTS_PASSWORD': os.getenv('YCLIENTS_PASSWORD')
    }
    orchestrator = DialogOrchestrator(config)
    
    user_id = "test"
    context = {}
    
    # Дополнительно очищаем контекст пользователя
    clear_user_context(orchestrator, user_id)
    
    steps = [
        # Первая запись - маникюр (полный цикл)
        "/start",
        "Евгений",
        "Хочу записаться на маникюр",
        "Маникюр классический", 
        "26 августа",
        "10:00",
        "Сакович Ольга",  # выбор мастера
        "да",  # подтверждение записи
        "Евгений",  # имя
        "Гнедчик",  # фамилия
        "+375257196682",  # телефон
        "да",  # финальное подтверждение первой записи
        
        # Вторая запись - окрашивание
        "а теперь запиши еще на окрашивание",
        "Окрашивание",
        "какие есть даты?",
        "27 августа", 
        "19:00",
        "Калеко Андрей",  # выбор мастера
        "да",  # подтверждение записи
        "да"   # финальное подтверждение второй записи (данные уже есть)
    ]
    
    for i, user_message in enumerate(steps, 1):
        print(f"ВОПРОС {i}: {user_message}")
        print()
        
        try:
            response, context = orchestrator.process_message(user_id, user_message)
            response_text = response[0] if isinstance(response, tuple) else response
            
            print(f"ОТВЕТ {i}:")
            print(response_text)
            print()
            print("-" * 60)
            print()
            
        except Exception as e:
            print(f"ОШИБКА: {e}")
            break

if __name__ == "__main__":
    main()
