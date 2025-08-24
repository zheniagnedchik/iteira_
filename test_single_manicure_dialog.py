#!/usr/bin/env python3
"""
Тест диалога обычной записи на маникюр (не комбо) в формате вопрос-ответ
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

# Отключаем все логи
import logging
logging.disable(logging.CRITICAL)

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def main():
    print("ДИАЛОГ ЗАПИСИ НА МАНИКЮР")
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
        "да"  # финальное подтверждение
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
