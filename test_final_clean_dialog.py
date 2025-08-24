#!/usr/bin/env python3
"""
Финальный чистый диалог
"""

import os
import sys
import subprocess

# Запускаем тест в отдельном процессе и фильтруем вывод
def run_clean_dialog():
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
    print(f"👤 {user_message}")
    try:
        response, context = orchestrator.process_message(user_id, user_message)
        response_text = response[0] if isinstance(response, tuple) else response
        print(f"🤖 {response_text}")
        print()
    except Exception as e:
        print(f"❌ {e}")
        break
'''
    
    print("💬 ЧИСТЫЙ ДИАЛОГ")
    print()
    
    # Запускаем в отдельном процессе
    process = subprocess.Popen(
        [sys.executable, '-c', script_content],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    # Читаем построчно и фильтруем
    for line in process.stdout:
        line = line.strip()
        # Пропускаем технические логи
        if any(keyword in line for keyword in [
            'INFO', 'WARNING', 'ERROR', 'timestamp', 'level', 'logger', 
            'Starting operation', 'Operation completed', 'module', 'function',
            'execution_time', 'Успешно загружено', 'инициализирован'
        ]):
            continue
        # Показываем только диалог
        if line.startswith('👤') or line.startswith('🤖') or line == '':
            print(line)
    
    process.wait()

if __name__ == "__main__":
    run_clean_dialog()
