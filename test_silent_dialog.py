#!/usr/bin/env python3
"""
Абсолютно тихий тест диалога
"""

import os
import sys
import logging
from io import StringIO

sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

# Полностью отключаем логи
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in logging.Logger.manager.loggerDict:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Перенаправляем stderr
old_stderr = sys.stderr
sys.stderr = StringIO()

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def test_silent_dialog():
    """Тихий диалог"""
    
    print("💬 ДИАЛОГ")
    print()
    
    # Инициализация
    config = {
        'USE_NEW_DIALOG_SYSTEM': True,
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'YCLIENTS_LOGIN': os.getenv('YCLIENTS_LOGIN'),
        'YCLIENTS_PASSWORD': os.getenv('YCLIENTS_PASSWORD')
    }
    orchestrator = DialogOrchestrator(config)
    
    user_id = "test"
    
    steps = [
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
    
    for user_message in steps:
        print(f"👤 {user_message}")
        
        try:
            response, context = orchestrator.process_message(user_id, user_message)
            response_text = response[0] if isinstance(response, tuple) else response
            print(f"🤖 {response_text}")
            print()
            
        except Exception as e:
            print(f"❌ {e}")
            break

if __name__ == "__main__":
    try:
        test_silent_dialog()
    finally:
        # Восстанавливаем stderr
        sys.stderr = old_stderr
