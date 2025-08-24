#!/usr/bin/env python3
"""
Тест полного диалога комбо-записи на основе реального сценария Евгения
"""

import os
import sys
sys.path.append('/Users/yauheni/Desktop/PLUG/iteira')

from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator
from beauty_salon_rag.config import Config

def test_full_combo_dialog():
    """Тестируем полный диалог комбо-записи как в реальном боте"""
    
    print("🎭 ТЕСТ: Полный диалог комбо-записи (реальный сценарий)")
    print("=" * 70)
    
    # Инициализация системы
    config = Config()
    config.USE_NEW_DIALOG_SYSTEM = True  # Убеждаемся что используем новую систему
    orchestrator = DialogOrchestrator(config.to_dict())
    
    user_id = "eugene_test"
    
    # Массив диалога: [пользователь, ожидаемые ключевые слова в ответе]
    dialog_steps = [
        # Шаг 1: Старт
        {
            "user": "/start", 
            "expect": ["Здравствуйте", "Итейра", "Как к Вам обращаться"]
        },
        
        # Шаг 2: Имя (с опечаткой как в реальном диалоге)
        {
            "user": "tdutybq", 
            "expect": ["tdutybq", "приятно", "записаться"]
        },
        
        # Шаг 3: Запрос комбо
        {
            "user": "хочу записаться на маникюр и окрашивание", 
            "expect": ["Маникюр классический", "Экспресс-маникюр", "Японский маникюр", "Окрашивание"]
        },
        
        # Шаг 4: Выбор маникюра
        {
            "user": "Маникюр классический", 
            "expect": ["окрашивание", "Окрашивание —", "Сложное окрашивание", "Мелирование"]
        },
        
        # Шаг 5: Выбор окрашивания
        {
            "user": "Окрашивание", 
            "expect": ["Маникюр классический", "Окрашивание", "один день", "разные дни"]
        },
        
        # Шаг 6: В один день
        {
            "user": "в один", 
            "expect": ["даты доступны", "августа", "сентября"]
        },
        
        # Шаг 7: Выбор даты
        {
            "user": "1 сентября", 
            "expect": ["1 сентября", "Последовательная запись", "Калеко Андрей", "Сакович Ольга"]
        },
        
        # Шаг 8: Выбор времени
        {
            "user": "16:30", 
            "expect": ["16:30", "Детальное расписание", "Калеко Андрей", "Сакович Ольга", "Подтверждаете"]
        },
        
        # Шаг 9: Подтверждение записи
        {
            "user": "да", 
            "expect": ["имя", "данные"]
        },
        
        # Шаг 10: Имя
        {
            "user": "Евгений", 
            "expect": ["фамилию"]
        },
        
        # Шаг 11: Фамилия
        {
            "user": "Гнедчик", 
            "expect": ["телефон", "+375", "международном формате"]
        },
        
        # Шаг 12: Телефон
        {
            "user": "+375257196682", 
            "expect": ["подтверждения", "ДА", "ПОДТВЕРЖДАЮ"]
        },
        
        # Шаг 13: Финальное подтверждение
        {
            "user": "да", 
            "expect": ["ЗАПИСЬ УСПЕШНО СОЗДАНА", "Евгений Гнедчик", "Детальное расписание", "Калеко Андрей", "Сакович Ольга"]
        }
    ]
    
    print("🎬 Начинаем диалог:")
    print()
    
    all_success = True
    context = {}
    
    for step_num, step in enumerate(dialog_steps, 1):
        user_message = step["user"]
        expected_keywords = step["expect"]
        
        print(f"👤 Шаг {step_num}: {user_message}")
        
        try:
            # Обработка сообщения через оркестратор (как в реальном боте)
            if step_num == 1:  # Первое сообщение
                response, context = orchestrator.process_message(user_id, user_message)
            else:
                response, context = orchestrator.process_message(user_id, user_message)
            
            # Извлекаем текст ответа если это tuple
            response_text = response[0] if isinstance(response, tuple) else response
            
            print(f"🤖 Бот: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
            
            # Проверяем ожидаемые ключевые слова
            missing_keywords = []
            for keyword in expected_keywords:
                if keyword.lower() not in response_text.lower():
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                print(f"⚠️  ВНИМАНИЕ: Не найдены ключевые слова: {missing_keywords}")
                # Не считаем это критической ошибкой, но отмечаем
            else:
                print(f"✅ Все ключевые слова найдены")
            
            print()
            
        except Exception as e:
            print(f"❌ ОШИБКА на шаге {step_num}: {e}")
            all_success = False
            import traceback
            traceback.print_exc()
            break
    
    print("=" * 70)
    print("🎯 ИТОГОВАЯ ОЦЕНКА")
    print()
    
    # Проверяем финальный результат
    if "ЗАПИСЬ УСПЕШНО СОЗДАНА" in response_text:
        print("🎉 УСПЕХ: Запись успешно создана!")
        
        # Проверяем детали записи
        checks = [
            ("Имя клиента", "Евгений Гнедчик" in response_text),
            ("Телефон", "+375257196682" in response_text),
            ("Комбо услуга", "Окрашивание + Маникюр классический" in response_text),
            ("Детальное расписание", "Детальное расписание" in response_text),
            ("Мастер окрашивания", "Калеко Андрей" in response_text),
            ("Мастер маникюра", "Сакович Ольга" in response_text),
            ("Время", "16:30" in response_text),
            ("Дата", "01 сентября" in response_text or "1 сентября" in response_text),
            ("Стоимость", "385" in response_text),
            ("Адрес", "ул. Немига, 5" in response_text),
        ]
        
        print("📋 Проверка деталей записи:")
        all_details_ok = True
        for check_name, is_ok in checks:
            status = "✅" if is_ok else "❌"
            print(f"   {status} {check_name}")
            if not is_ok:
                all_details_ok = False
        
        print()
        if all_details_ok:
            print("🏆 ОТЛИЧНО: Все детали записи корректны!")
            print("✨ Комбо-запись работает идеально!")
        else:
            print("⚠️  ЧАСТИЧНО: Запись создана, но некоторые детали неточны")
            
    elif all_success:
        print("⚠️  ЧАСТИЧНО: Диалог прошёл без ошибок, но запись не создана")
    else:
        print("❌ ПРОВАЛ: Произошли ошибки в процессе диалога")
    
    print()
    print("🔍 Финальный контекст:")
    interesting_keys = ['user_name', 'dialog_stage', 'is_combo', 'combo_service1', 'combo_service2', 
                       'selected_date', 'selected_time', 'personal_data', 'booking_details']
    for key in interesting_keys:
        if key in context:
            value = context[key]
            if isinstance(value, dict) and 'title' in value:
                print(f"   {key}: {value['title']}")
            elif isinstance(value, dict):
                print(f"   {key}: {len(value)} полей")
            else:
                print(f"   {key}: {value}")
    
    print()

if __name__ == "__main__":
    test_full_combo_dialog()
