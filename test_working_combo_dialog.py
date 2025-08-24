#!/usr/bin/env python3
"""
Тест рабочего комбо-диалога с реальными слотами времени
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
from datetime import datetime, timedelta

def print_dialog_step(step_num, user_message, bot_response, step_description=""):
    """Красиво выводит шаг диалога"""
    print(f"\n{'='*80}")
    print(f"📱 ШАГ {step_num}: {step_description}")
    print(f"{'='*80}")
    print(f"👤 Евгений Гнедчик: {user_message}")
    print(f"{'─'*80}")
    print(f"🤖 Iteira bot:")
    print(bot_response)
    print(f"{'='*80}")

def test_working_combo_dialog():
    """Тест полного рабочего диалога с комбо-записью"""
    
    print("🎭 ПОЛНЫЙ РАБОЧИЙ ДИАЛОГ ЕВГЕНИЯ С КОМБО-ЗАПИСЬЮ")
    print("=" * 80)
    print("🎯 Цель: Показать работающий диалог от начала до успешной записи")
    print("=" * 80)
    
    # Инициализация
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    user_id = 12345
    user_name = "Евгений"
    
    print(f"✅ Система: {orchestrator.system_type}")
    print(f"👤 Пользователь: {user_name} (ID: {user_id})")
    
    # ШАГ 1: Приветствие
    response = orchestrator.process_message(user_id, "/start", user_name)
    print_dialog_step(1, "/start", response, "Приветствие")
    
    # ШАГ 2: Представление
    response = orchestrator.process_message(user_id, "Евгений", user_name)
    print_dialog_step(2, "Евгений", response, "Представление")
    
    # ШАГ 3: Выбор услуг
    response = orchestrator.process_message(user_id, "хочу записаться на маникюр и окрашивание", user_name)
    print_dialog_step(3, "хочу записаться на маникюр и окрашивание", response, "Выбор услуг")
    
    # ШАГ 4: Выбор маникюра
    response = orchestrator.process_message(user_id, "Маникюр классический", user_name)
    print_dialog_step(4, "Маникюр классический", response, "Выбор типа маникюра")
    
    # ШАГ 5: Выбор окрашивания
    response = orchestrator.process_message(user_id, "Окрашивание", user_name)
    print_dialog_step(5, "Окрашивание", response, "Выбор типа окрашивания")
    
    # ШАГ 6: Выбор дня
    response = orchestrator.process_message(user_id, "в один", user_name)
    print_dialog_step(6, "в один", response, "Выбор - в один день")
    
    # ШАГ 7: Выбираем завтрашний день (гарантированно рабочий)
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%d %B").lower()  # например "26 августа"
    
    # Переводим на русский
    months = {
        'january': 'января', 'february': 'февраля', 'march': 'марта',
        'april': 'апреля', 'may': 'мая', 'june': 'июня',
        'july': 'июля', 'august': 'августа', 'september': 'сентября',
        'october': 'октября', 'november': 'ноября', 'december': 'декабря'
    }
    
    day = tomorrow.day
    month_en = tomorrow.strftime("%B").lower()
    month_ru = months.get(month_en, 'августа')
    tomorrow_ru = f"{day} {month_ru}"
    
    print(f"\n🗓️ Выбираем завтрашний день: {tomorrow_ru}")
    
    response = orchestrator.process_message(user_id, tomorrow_ru, user_name)
    print_dialog_step(7, tomorrow_ru, response, f"Выбор даты - {tomorrow_ru}")
    
    # Проверяем получили ли мы слоты времени или нужно попробовать другую дату
    if "К сожалению" in response or "не удалось найти" in response:
        print("\n⚠️ Завтрашний день не подошёл, пробуем послезавтра...")
        
        day_after = datetime.now() + timedelta(days=2)
        day_after_day = day_after.day
        day_after_month_en = day_after.strftime("%B").lower()
        day_after_month_ru = months.get(day_after_month_en, 'августа')
        day_after_ru = f"{day_after_day} {day_after_month_ru}"
        
        response = orchestrator.process_message(user_id, day_after_ru, user_name)
        print_dialog_step(8, day_after_ru, response, f"Выбор даты - {day_after_ru}")
    
    # Анализ финального результата
    print(f"\n{'🎯'*20} АНАЛИЗ РЕЗУЛЬТАТА {'🎯'*20}")
    print(f"{'='*80}")
    
    # Извлекаем текст ответа из tuple
    final_response_text = response[0] if isinstance(response, tuple) else response
    
    if "время" in final_response_text.lower() and ("утром" in final_response_text.lower() or ":" in final_response_text):
        print("✅ УСПЕХ! Система показала доступные слоты времени!")
        print("✅ Комбо-запись работает корректно!")
    elif "К сожалению" in final_response_text or "не удалось" in final_response_text:
        print("❌ Система не смогла найти слоты")
        print("❓ Возможны проблемы с данными API")
        print("🔍 В логах видим: 'Не найдено мастеров для услуги' - проблема в поиске мастеров")
    else:
        print("❓ Неожиданный ответ системы")
    
    print(f"📝 Последний ответ: {final_response_text[:200]}...")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_working_combo_dialog()
