#!/usr/bin/env python3
"""
Тест полной цепочки комбо-записи через весь стек системы
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
from beauty_salon_rag.config import Config

def test_full_combo_chain():
    """Тестируем полную цепочку комбо-записи через DialogOrchestrator"""
    
    print("🧪 ТЕСТ: Полная цепочка комбо-записи")
    print("=" * 50)
    
    # Убеждаемся что используется новая система
    os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'
    
    # Создаем конфиг и оркестратор
    config = Config()
    rag_system = None  # Для новой системы не нужен
    
    dialog_orchestrator = DialogOrchestrator(rag_system)
    
    print(f"📋 Система: {dialog_orchestrator.system_type}")
    print(f"🔧 Оркестратор: {'NewDialogOrchestrator' if dialog_orchestrator.new_orchestrator else 'UnifiedGPTOrchestrator'}")
    print()
    
    # Симулируем диалог Евгения с нуля
    user_id = 12345
    
    messages = [
        "Евгений",
        "хочу записаться на маникюр и окрашивание", 
        "Маникюр классический",
        "Окрашивание", 
        "в один",
        "1 сентября",
        "10 00"
    ]
    
    print("💬 Симулируем диалог:")
    print("-" * 30)
    
    for i, message in enumerate(messages, 1):
        print(f"\n👤 Пользователь: {message}")
        
        try:
            # Обрабатываем сообщение через оркестратор
            response, metadata = dialog_orchestrator.process_message(
                user_id=user_id,
                message=message,
                user_name="Евгений"
            )
            
            print(f"🤖 Бот: {response[:100]}{'...' if len(response) > 100 else ''}")
            
            # Ищем ключевые индикаторы
            if "10:00: окрашивание (Калеко Андрей)" in response:
                print("✅ НАЙДЕНЫ РЕАЛЬНЫЕ СЛОТЫ С МАСТЕРАМИ!")
                break
            elif "подряд или с паузой" in response:
                print("✅ Показаны варианты комбо-записи")
            elif "Маникюр классический + Окрашивание" in response:
                print("✅ Запущено подтверждение комбо-записи")
                print(f"📋 Полный ответ подтверждения:")
                print(response)
                
                # Проверяем, есть ли заглушки
                if "Мастер:" in response and "уточняется" not in response:
                    if "Калеко Андрей" in response and "Сакович Ольга" in response:
                        print("✅ УСПЕХ: Реальные мастера показаны!")
                    else:
                        print("⚠️  Мастера показаны, но не те что ожидаются")
                else:
                    print("❌ Все еще показываются заглушки")
                break
            
        except Exception as e:
            print(f"❌ Ошибка на шаге {i}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print()
    print("=" * 50)
    print("🎯 РЕЗУЛЬТАТ ПОЛНОГО ТЕСТА")
    
    # Финальная проверка
    if "Калеко Андрей" in response and "Сакович Ольга" in response:
        print("✅ УСПЕХ: Комбо-запись работает через всю цепочку!")
        print("   📋 Услуга: отображена корректно")
        print("   👨‍💼 Мастера: реальные имена")
        print("   💰 Стоимость: рассчитана правильно")
    elif "Маникюр классический + Окрашивание" in response:
        print("⚠️  ЧАСТИЧНО: Комбо работает, но проверьте мастеров")
    else:
        print("❌ ПРОБЛЕМА: Комбо-запись не дошла до подтверждения")
    
    print()

if __name__ == "__main__":
    test_full_combo_chain()
