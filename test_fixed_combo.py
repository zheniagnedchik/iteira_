#!/usr/bin/env python3
"""
Тест исправленной комбо-записи с полными данными о мастерах
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def test_fixed_combo():
    """Тест исправленной комбо-записи"""
    
    print("🎯 ТЕСТ ИСПРАВЛЕННОЙ КОМБО-ЗАПИСИ")
    print("=" * 60)
    print("🔧 Исправление: combo_service2 теперь получается через search_with_details")
    print("=" * 60)
    
    # Инициализация
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    user_id = 12345
    user_name = "Евгений"
    
    print(f"✅ Система: {orchestrator.system_type}")
    print()
    
    # Быстро проходим диалог
    print("📱 Быстрое прохождение до критического момента:")
    print("-" * 50)
    
    # Шаги 1-6
    orchestrator.process_message(user_id, "/start", user_name)
    orchestrator.process_message(user_id, "Евгений", user_name)  
    orchestrator.process_message(user_id, "хочу записаться на маникюр и окрашивание", user_name)
    orchestrator.process_message(user_id, "Маникюр классический", user_name)
    orchestrator.process_message(user_id, "Окрашивание", user_name)
    orchestrator.process_message(user_id, "в один", user_name)
    print("1-6. Диалог до выбора даты ✓")
    
    print()
    print("🎯 КРИТИЧЕСКИЙ ТЕСТ - запрос слотов на 25 августа:")
    print("=" * 60)
    
    # Критический момент - запрос слотов
    response = orchestrator.process_message(user_id, "25 августа", user_name)
    
    # Извлекаем текст
    response_text = response[0] if isinstance(response, tuple) else response
    
    print(f"📝 Ответ системы:")
    print(response_text)
    print()
    
    # Анализ результата
    print("🔍 АНАЛИЗ РЕЗУЛЬТАТА:")
    print("-" * 40)
    
    if "К сожалению" in response_text and "нет свободных слотов" in response_text:
        print("❌ ПРОБЛЕМА НЕ РЕШЕНА")
        print("📝 Система всё ещё не может найти комбо-слоты")
        print("🔍 Проверяем логи для дополнительной диагностики...")
    elif "уточню возможные варианты" in response_text or "Один момент" in response_text:
        print("⏳ ЗАГЛУШКА")
        print("📝 Система показывает заглушку вместо реальных слотов")
        print("🔍 Возможно процесс ещё не завершён")
    elif ":" in response_text and ("утром" in response_text.lower() or "вечером" in response_text.lower() or "время" in response_text.lower()):
        print("✅ ПРОБЛЕМА РЕШЕНА!")
        print("📝 Система показывает реальные слоты времени!")
        print("🎉 Комбо-запись работает корректно!")
    else:
        print("❓ НЕОПРЕДЕЛЁННЫЙ РЕЗУЛЬТАТ")
        print("📝 Получен неожиданный тип ответа")
    
    print("=" * 60)

if __name__ == "__main__":
    test_fixed_combo()
