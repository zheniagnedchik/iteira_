#!/usr/bin/env python3
"""
Тест полного диалога комбо-записи - чистый вид без технических деталей
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def test_clean_combo_dialog():
    """Показываем чистый диалог комбо-записи как в реальном боте"""
    
    print("💬 ДИАЛОГ КОМБО-ЗАПИСИ")
    print("=" * 50)
    print()
    
    # Инициализация системы (без вывода)
    config = {
        'USE_NEW_DIALOG_SYSTEM': True,
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'YCLIENTS_LOGIN': os.getenv('YCLIENTS_LOGIN'),
        'YCLIENTS_PASSWORD': os.getenv('YCLIENTS_PASSWORD')
    }
    orchestrator = DialogOrchestrator(config)
    
    user_id = "eugene_test"
    
    # Диалог-сценарий
    dialog_steps = [
        "/start",
        "tdutybq", 
        "хочу записаться на маникюр и окрашивание",
        "Маникюр классический",
        "Окрашивание",
        "в один",
        "1 сентября",
        "16:30",
        "да",
        "Евгений",
        "Гнедчик", 
        "+375257196682",
        "да"
    ]
    
    context = {}
    
    for step_num, user_message in enumerate(dialog_steps, 1):
        
        print(f"👤 Пользователь: {user_message}")
        
        try:
            # Обработка сообщения
            response, context = orchestrator.process_message(user_id, user_message)
            
            # Извлекаем текст ответа
            response_text = response[0] if isinstance(response, tuple) else response
            
            print(f"🤖 Бот: {response_text}")
            print()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break
    
    print("=" * 50)
    print("✅ Диалог завершён")

if __name__ == "__main__":
    test_clean_combo_dialog()
