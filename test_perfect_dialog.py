#!/usr/bin/env python3
"""
Идеальный чистый диалог - финальная версия
"""

import os
import sys
import subprocess

def run_perfect_dialog():
    script_content = '''
import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

config = {
    'USE_NEW_DIALOG_SYSTEM': True,
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'YCLIENTS_LOGIN': os.getenv('YCLIENTS_LOGIN'),
    'YCLIENTS_PASSWORD': os.getenv('YCLIENTS_PASSWORD')
}
orchestrator = DialogOrchestrator(config)

user_id = "test"
steps = ["/start", "tdutybq", "хочу записаться на маникюр и окрашивание", "Маникюр классический", "Окрашивание", "в один", "1 сентября", "16:30", "да", "Евгений", "Гнедчик", "+375257196682", "да"]

context = {}
for user_message in steps:
    print(f"USER_MSG:{user_message}")
    try:
        response, context = orchestrator.process_message(user_id, user_message)
        response_text = response[0] if isinstance(response, tuple) else response
        print(f"BOT_MSG:{response_text}")
    except Exception as e:
        print(f"ERROR_MSG:{e}")
        break
'''
    
    print("💬 ДИАЛОГ КОМБО-ЗАПИСИ")
    print("=" * 50)
    print()
    
    # Запускаем в отдельном процессе
    process = subprocess.Popen(
        [sys.executable, '-c', script_content],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # Убираем stderr полностью
        text=True,
        env=os.environ.copy()
    )
    
    # Читаем построчно и показываем только диалог
    for line in process.stdout:
        line = line.strip()
        if line.startswith('USER_MSG:'):
            user_text = line[9:]  # Убираем префикс USER_MSG:
            print(f"👤 {user_text}")
        elif line.startswith('BOT_MSG:'):
            bot_text = line[8:]   # Убираем префикс BOT_MSG:
            print(f"🤖 {bot_text}")
            print()
        elif line.startswith('ERROR_MSG:'):
            error_text = line[10:] # Убираем префикс ERROR_MSG:
            print(f"❌ {error_text}")
            break
    
    process.wait()
    print("=" * 50)
    print("✅ Диалог завершён успешно!")

if __name__ == "__main__":
    run_perfect_dialog()
