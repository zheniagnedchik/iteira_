#!/usr/bin/env python3
"""
Простой тест вопрос-ответ для комбо диалога
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

# Отключаем все логи
import logging
logging.disable(logging.CRITICAL)

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def main():
    print("ДИАЛОГ КОМБО-ЗАПИСИ")
    print("=" * 60)
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
