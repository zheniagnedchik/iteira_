#!/usr/bin/env python3
"""
Тест ожидания реальных слотов времени вместо заглушки
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def wait_for_real_response(orchestrator, user_id, message, user_name, timeout=30):
    """Ждёт реального ответа, а не заглушки"""
    print(f"Отправляем: '{message}'")
    print("Ожидаем реального ответа...")
    
    start_time = time.time()
    response = orchestrator.process_message(user_id, message, user_name)
    end_time = time.time()
    
    # Извлекаем текст из tuple
    response_text = response[0] if isinstance(response, tuple) else response
    
    print(f"⏱️ Время обработки: {end_time - start_time:.2f} секунд")
    print(f"📝 Ответ: {response_text}")
    print()
    
    # Проверяем является ли это заглушкой
    if "уточню возможные варианты" in response_text or "Один момент" in response_text:
        print("❌ Получена заглушка вместо реальных слотов")
        return response, True  # True = заглушка
    elif ":" in response_text and ("утром" in response_text or "вечером" in response_text):
        print("✅ Получены реальные слоты времени!")
        return response, False  # False = реальные слоты
    else:
        print("❓ Неопределённый тип ответа")
        return response, None

def test_wait_for_slots():
    """Тест с ожиданием реальных слотов"""
    
    print("🎯 ТЕСТ ПОЛУЧЕНИЯ РЕАЛЬНЫХ СЛОТОВ")
    print("=" * 60)
    
    # Инициализация
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    user_id = 12345
    user_name = "Евгений"
    
    print(f"✅ Система: {orchestrator.system_type}")
    print()
    
    # Быстро проходим диалог до проблемного места
    print("📱 Быстрое прохождение диалога:")
    print("-" * 40)
    
    orchestrator.process_message(user_id, "/start", user_name)
    print("1. Приветствие ✓")
    
    orchestrator.process_message(user_id, "Евгений", user_name)  
    print("2. Имя ✓")
    
    orchestrator.process_message(user_id, "хочу записаться на маникюр и окрашивание", user_name)
    print("3. Выбор услуг ✓")
    
    orchestrator.process_message(user_id, "Маникюр классический", user_name)
    print("4. Выбор маникюра ✓")
    
    orchestrator.process_message(user_id, "Окрашивание", user_name)
    print("5. Выбор окрашивания ✓")
    
    orchestrator.process_message(user_id, "в один", user_name)
    print("6. В один день ✓")
    
    print()
    print("🎯 КРИТИЧЕСКИЙ МОМЕНТ - запрос слотов:")
    print("=" * 60)
    
    # Теперь тестируем проблемный запрос
    response, is_placeholder = wait_for_real_response(
        orchestrator, user_id, "25 августа", user_name
    )
    
    if is_placeholder:
        print("🔍 ДИАГНОСТИКА ЗАГЛУШКИ:")
        print("-" * 40)
        print("Возможные причины:")
        print("1. Система ещё обрабатывает запрос в фоне")
        print("2. Ошибка в получении слотов от API")  
        print("3. Проблема с данными о мастерах")
        print("4. Неполная реализация show_combo_time_slots")
        
        print("\n🔍 Проверка логов ошибок...")
        # Можно добавить проверку логов здесь
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_wait_for_slots()
