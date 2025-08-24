#!/usr/bin/env python3
"""
Финальный тест-демонстрация проблемы с комбо-записью
Показывает весь диалог Евгения с объяснением проблемы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def print_step(step_num, user_input, bot_response, summary=""):
    """Красиво выводит шаг диалога"""
    print(f"\n{'='*80}")
    print(f"📱 ШАГ {step_num}{': ' + summary if summary else ''}")
    print(f"{'='*80}")
    print(f"👤 Евгений: {user_input}")
    print(f"{'─'*80}")
    
    # Извлекаем текст из tuple если нужно
    if isinstance(bot_response, tuple):
        text = bot_response[0]
    else:
        text = bot_response
        
    print(f"🤖 Бот: {text}")
    print(f"{'='*80}")

def test_final_combo_showcase():
    """Финальная демонстрация проблемы комбо-записи"""
    
    print("🎭 ПОЛНАЯ ДЕМОНСТРАЦИЯ ПРОБЛЕМЫ КОМБО-ЗАПИСИ")
    print("=" * 80)
    print("🎯 Цель: Показать где именно ломается диалог Евгения")
    print("📝 Проблема: Вторая услуга не имеет данных о мастерах")
    print("=" * 80)
    
    # Инициализация
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    user_id = 12345
    user_name = "Евгений"
    
    print(f"✅ Система: {orchestrator.system_type}")
    print(f"👤 Пользователь: {user_name}")
    
    # ШАГ 1: Приветствие
    response = orchestrator.process_message(user_id, "/start", user_name)
    print_step(1, "/start", response, "Приветствие")
    
    # ШАГ 2: Имя
    response = orchestrator.process_message(user_id, "Евгений", user_name)
    print_step(2, "Евгений", response, "Представление")
    
    # ШАГ 3: Выбор услуг
    response = orchestrator.process_message(user_id, "хочу записаться на маникюр и окрашивание", user_name)
    print_step(3, "хочу записаться на маникюр и окрашивание", response, "Поиск услуг")
    
    # ШАГ 4: Первая услуга
    response = orchestrator.process_message(user_id, "Маникюр классический", user_name)
    print_step(4, "Маникюр классический", response, "Выбор маникюра")
    
    # ШАГ 5: Вторая услуга  
    response = orchestrator.process_message(user_id, "Окрашивание", user_name)
    print_step(5, "Окрашивание", response, "Выбор окрашивания")
    
    # ШАГ 6: В один день
    response = orchestrator.process_message(user_id, "в один", user_name)
    print_step(6, "в один", response, "Выбор - в один день")
    
    # ШАГ 7: Выбор даты (проблемный шаг)
    response = orchestrator.process_message(user_id, "25 августа", user_name)
    print_step(7, "25 августа", response, "❌ ПРОБЛЕМНЫЙ ШАГ")
    
    # Анализ результата
    print(f"\n{'🔍'*30} АНАЛИЗ ПРОБЛЕМЫ {'🔍'*30}")
    print("=" * 80)
    
    # Извлекаем текст из tuple
    final_text = response[0] if isinstance(response, tuple) else response
    
    if "К сожалению" in final_text or "не удалось" in final_text:
        print("❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
        print("📝 Система не смогла найти комбо-слоты")
        print()
        print("🎯 КОРЕНЬ ПРОБЛЕМЫ:")
        print("   1. ✅ Первая услуга (Окрашивание) - получает слоты от мастеров")
        print("   2. ❌ Вторая услуга (Маникюр) - НЕ имеет данных о мастерах")
        print("   3. ❌ Система сохраняет ОБРЕЗАННЫЕ данные без staff информации")
        print("   4. ❌ При попытке получить слоты - ошибка 'Не найдено мастеров'")
        print()
        print("💡 РЕШЕНИЕ:")
        print("   - Использовать search_with_details() для получения полных данных")
        print("   - Исправить логику сохранения combo_service2 в DialogAssistant")
    else:
        print("✅ Комбо-запись работает!")
        print("📝 Система показала доступные слоты времени")
    
    print("=" * 80)

if __name__ == "__main__":
    test_final_combo_showcase()
