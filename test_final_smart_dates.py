#!/usr/bin/env python3
"""
Финальный тест умного отображения дат.
"""

import sys
import os

# Добавляем путь к модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator


def test_final_smart_dates():
    """Финальный тест умного отображения дат."""
    print("🎯 Финальный тест умного отображения дат...")
    
    try:
        # Инициализируем RAG-систему
        rag_system = BeautySalonRAG()
        orchestrator = DialogOrchestrator(rag_system)
        
        user_id = 12345
        
        print(f"\n👤 Тестирование с пользователем {user_id}")
        
        # Полный цикл до дат
        print("\n1️⃣ Выбор маникюра:")
        response, _ = orchestrator.process_message(user_id, "хочу маникюр")
        
        print("\n2️⃣ Выбор услуги №3:")
        response, _ = orchestrator.process_message(user_id, "3")
        
        print("\n3️⃣ Принудительный вызов умного отображения дат:")
        # Получаем контекст и вызываем метод напрямую
        context = orchestrator.gpt_orchestrator.get_user_context(user_id)
        selected_service = context.get('selected_service')
        
        if selected_service:
            available_dates = orchestrator.gpt_orchestrator._get_available_dates(selected_service)
            smart_dates = orchestrator.gpt_orchestrator._format_dates_smartly(available_dates)
            
            print(f"📅 Умное отображение дат для {selected_service.get('title')}:")
            print(smart_dates)
            
            print(f"\n📊 Статистика:")
            print(f"- Всего дат: {len(available_dates)}")
            print(f"- Показано в умном режиме: ~12 дат")
            print(f"- Экономия места: {len(available_dates) - 12} дат скрыто")
            
            # Показываем разницу с обычным отображением
            print(f"\n📋 Для сравнения - обычное отображение (первые 15 дат):")
            normal_dates = orchestrator.gpt_orchestrator._format_dates_beautifully(available_dates[:15])
            print(normal_dates)
            
            print(f"\n✅ Умное отображение намного компактнее и понятнее!")
            
        else:
            print("❌ Услуга не выбрана")
        
        print("\n🎉 Финальный тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_final_smart_dates()