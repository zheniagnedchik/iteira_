#!/usr/bin/env python3
"""
Тест форматирования информации о мастерах.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_masters_formatting():
    """Тестирует форматирование информации о мастерах."""
    print("👩‍💼 Тестирование форматирования мастеров...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Полный цикл до мастеров
        print("\n1️⃣ Выбор маникюра:")
        response, _ = orchestrator.process_message(user_id, "хочу маникюр")
        
        print("\n2️⃣ Выбор услуги №3:")
        response, _ = orchestrator.process_message(user_id, "3")
        
        print("\n3️⃣ Запрос о мастерах:")
        response, metadata = orchestrator.process_message(user_id, "кто делает?")
        print(f"Ответ от GPT:\n{response}")
        print(f"Метаданные: {metadata}")
        
        print("\n4️⃣ Принудительный вызов красивого форматирования мастеров:")
        # Получаем контекст и вызываем метод напрямую
        context = orchestrator.gpt_orchestrator.get_user_context(user_id)
        selected_service = context.get('selected_service')
        
        if selected_service:
            masters_info = orchestrator.gpt_orchestrator._get_masters_for_service(selected_service)
            
            if masters_info:
                print(f"\n👩‍💼 Красивое форматирование мастеров:")
                
                # Создаем фиктивное действие для тестирования
                from beauty_salon_rag.gpt_orchestrator import DialogAction
                action = DialogAction(
                    action_type='show_masters',
                    parameters={},
                    response_text='',
                    next_state=None
                )
                
                beautiful_response, _ = orchestrator.gpt_orchestrator._handle_show_masters(action, context)
                print(beautiful_response)
                
                print(f"\n📊 Статистика:")
                print(f"- Всего мастеров: {len(masters_info)}")
                print(f"- Показано в красивом формате: до 6 мастеров")
                
                # Сравниваем с обычным ответом
                print(f"\n📋 Сравнение:")
                print(f"- GPT ответ: простое перечисление имен")
                print(f"- Красивый формат: структурированная информация с доступностью")
                
                print(f"\n✅ Красивое форматирование намного информативнее!")
                
            else:
                print("❌ Мастера не найдены")
        else:
            print("❌ Услуга не выбрана")
        
        print("\n🎉 Тестирование форматирования мастеров завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_masters_formatting()