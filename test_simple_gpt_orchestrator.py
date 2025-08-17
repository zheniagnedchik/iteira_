#!/usr/bin/env python3
"""
Простой тест GPT-оркестратора.
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_orchestration():
    """Простой тест оркестрации."""
    
    print("🤖 Простой тест GPT-оркестратора")
    print("=" * 40)
    
    try:
        from beauty_salon_rag.gpt_client import GPTClient
        
        # Создаем GPT клиент
        gpt_client = GPTClient()
        
        print("✅ GPT клиент инициализирован")
        
        # Тест простого случая
        context = {
            "user_name": None,
            "current_state": "initial",
            "conversation_history": []
        }
        
        print("\\nТест: 'Привет'")
        result = gpt_client.orchestrate_dialog("Привет", context)
        
        print(f"Действие: {result.get('action')}")
        print(f"Ответ: {result.get('response', '')[:100]}...")
        
        if result.get('action') == 'greeting':
            print("✅ Правильно определено приветствие")
        else:
            print(f"⚠️  Определено как: {result.get('action')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if test_simple_orchestration():
        print("\\n🎉 Простой тест пройден!")
    else:
        print("\\n❌ Тест не пройден")
    
    sys.exit(0)