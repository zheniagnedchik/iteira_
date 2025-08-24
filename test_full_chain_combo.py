#!/usr/bin/env python3
"""
Тест полной цепочки как в Telegram боте: DialogOrchestrator -> NewDialogOrchestrator -> DialogAssistant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def test_full_chain_combo():
    """Тест полной цепочки Евгения через DialogOrchestrator"""
    
    print("🔍 ТЕСТ ПОЛНОЙ ЦЕПОЧКИ (как в Telegram)")
    print("=" * 60)
    
    # Инициализация как в TelegramBot
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    print(f"✅ Используется система: {orchestrator.system_type}")
    print()
    
    # Пользователь Евгений
    user_id = 12345
    user_name = "Евгений"
    
    # Симулируем диалог Евгения
    messages = [
        "хочу записаться на маникюр и окрашивание",
        "Маникюр классический", 
        "Окрашивание",
        "в один",
        "1 сентября"
    ]
    
    print("🔄 СИМУЛЯЦИЯ ДИАЛОГА ЕВГЕНИЯ:")
    print("-" * 40)
    
    for i, message in enumerate(messages, 1):
        print(f"\n📝 ШАГ {i}: '{message}'")
        print("-" * 30)
        
        try:
            response, metadata = orchestrator.process_message(
                user_id=user_id,
                message=message,
                user_name=user_name
            )
            
            print(f"Ответ: {response[:200]}...")
            print(f"Система: {metadata.get('system', 'неизвестно')}")
            print(f"Тип: {metadata.get('type', 'неизвестно')}")
            
            # Проверяем специально для шага 5 (1 сентября)
            if i == 5 and "нет свободных слотов" in response:
                print("❌ ПРОБЛЕМА: Показывается сообщение об отсутствии слотов!")
                print("Но мы знаем что на 1 сентября есть 43 комбо-группы...")
                break
            elif i == 5 and ("варианты" in response.lower() or "группа" in response.lower()):
                print("✅ УСПЕХ: Показываются варианты комбо-записи!")
                break
                
        except Exception as e:
            print(f"❌ ОШИБКА на шаге {i}: {e}")
            break
    
    print("\n" + "=" * 60)
    print("🏁 РЕЗУЛЬТАТ ТЕСТА")

if __name__ == "__main__":
    test_full_chain_combo()
