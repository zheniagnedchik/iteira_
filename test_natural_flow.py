#!/usr/bin/env python3
"""
Тест естественного потока диалога с новой логикой
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from beauty_salon_rag.new_dialog_orchestrator import NewDialogOrchestrator


def test_natural_flow():
    """Тестирует новый естественный поток диалога"""
    print("🌟 ТЕСТ ЕСТЕСТВЕННОГО ПОТОКА ДИАЛОГА")
    print("=" * 50)
    
    try:
        config = {}
        orchestrator = NewDialogOrchestrator(config)
        
        user_id = "test_natural"
        
        print("1️⃣ Проходим до выбора услуги...")
        orchestrator.process_message(user_id, "Привет")
        orchestrator.process_message(user_id, "Евгений")
        orchestrator.process_message(user_id, "хочу записаться на маникюр")
        response1 = orchestrator.process_message(user_id, "Маникюр классический")
        
        print(f"\n📝 ПОСЛЕ ВЫБОРА УСЛУГИ:")
        print("=" * 40)
        print(response1)
        print("=" * 40)
        
        if "На какую дату хотели бы записаться?" in response1:
            print("✅ Спрашивает дату вместо показа всех дат")
        else:
            print("❌ Не спрашивает дату")
        
        print(f"\n2️⃣ Называем конкретную дату...")
        response2 = orchestrator.process_message(user_id, "22 августа")
        
        print(f"\n📝 ПОСЛЕ ВЫБОРА ДАТЫ:")
        print("=" * 40)
        print(response2)
        print("=" * 40)
        
        if "🌅 **Утро" in response2 and "☀️ **День" in response2 and "🌙 **Вечер" in response2:
            print("✅ Показывает периоды времени вместо всех слотов")
        else:
            print("❌ Не показывает периоды времени")
        
        print(f"\n3️⃣ Выбираем период...")
        response3 = orchestrator.process_message(user_id, "утро")
        
        print(f"\n📝 ПОСЛЕ ВЫБОРА ПЕРИОДА:")
        print("=" * 40)
        print(response3)
        print("=" * 40)
        
        if "🔹" in response3 and "Свободные слоты" in response3:
            print("✅ Показывает конкретные слоты в выбранном периоде")
        else:
            print("❌ Не показывает конкретные слоты")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_natural_flow()

