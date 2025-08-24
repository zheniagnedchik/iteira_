#!/usr/bin/env python3
"""
Детальный тест комбо-записи с технической информацией
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для новой системы
os.environ['USE_NEW_DIALOG_SYSTEM'] = 'true'

from main import BeautySalonRAG
from beauty_salon_rag.dialog_orchestrator import DialogOrchestrator

def print_beautiful_separator(title, emoji="🔹"):
    """Красивый разделитель"""
    print(f"\n{emoji * 3} {title} {emoji * 3}")
    print("─" * 80)

def print_dialog_step(step_num, user_input, bot_response, technical_info=None):
    """Красиво выводит диалог с технической информацией"""
    print(f"\n📱 ШАГ {step_num}")
    print("═" * 80)
    print(f"👤 Евгений: \"{user_input}\"")
    print("─" * 80)
    print(f"🤖 Бот: {bot_response[:300]}{'...' if len(bot_response) > 300 else ''}")
    
    if technical_info:
        print("─" * 80)
        print("🔧 Техническая информация:")
        for key, value in technical_info.items():
            print(f"   • {key}: {value}")
    print("═" * 80)

def test_detailed_combo_showcase():
    """Детальная демонстрация комбо-записи"""
    
    print("🎭 ДЕТАЛЬНАЯ ДЕМОНСТРАЦИЯ КОМБО-ЗАПИСИ")
    print("🎯 Тестируем сценарий Евгения с техническими деталями")
    print("💻 Система: DialogAssistant (новая)")
    
    # Инициализация
    rag_system = BeautySalonRAG()
    orchestrator = DialogOrchestrator(rag_system)
    
    user_id = 12345
    user_name = "Евгений"
    
    print_beautiful_separator("ИНИЦИАЛИЗАЦИЯ", "🚀")
    print(f"✅ Система инициализирована: {orchestrator.system_type}")
    print(f"✅ Тип системы: {'Новая структурированная' if orchestrator.system_type == 'new' else 'Старая'}")
    
    # Основные шаги диалога
    steps = [
        {
            "input": "хочу записаться на маникюр и окрашивание",
            "description": "Комбо-запрос"
        },
        {
            "input": "Маникюр классический",
            "description": "Выбор первой услуги"
        },
        {
            "input": "Окрашивание",
            "description": "Выбор второй услуги"
        },
        {
            "input": "в один день",
            "description": "Комбо в один день"
        },
        {
            "input": "1 сентября",
            "description": "Конкретная дата"
        }
    ]
    
    context_tracking = []
    
    for i, step in enumerate(steps, 1):
        print_beautiful_separator(f"ШАГ {i}: {step['description']}", "🎯")
        
        try:
            # Обрабатываем сообщение
            response, metadata = orchestrator.process_message(
                user_id=user_id,
                message=step["input"],
                user_name=user_name
            )
            
            # Собираем техническую информацию
            tech_info = {
                "Система": metadata.get('system', 'неизвестно'),
                "Тип ответа": metadata.get('type', 'неизвестно'),
                "Длина ответа": f"{len(response)} символов"
            }
            
            # Анализируем ключевые слова
            keywords_found = []
            if "комбо" in response.lower() or "последовательная" in response.lower():
                keywords_found.append("Комбо-логика")
            if "маникюр" in response.lower():
                keywords_found.append("Маникюр упомянут")
            if "окрашивание" in response.lower():
                keywords_found.append("Окрашивание упомянуто")
            if "1 сентября" in response.lower() or "сентября" in response.lower():
                keywords_found.append("Дата сохранена")
            if "слотов" in response.lower():
                keywords_found.append("Слоты упомянуты")
            if "варианты" in response.lower() or "время" in response.lower():
                keywords_found.append("Показаны варианты")
                
            if keywords_found:
                tech_info["Ключевые слова"] = ", ".join(keywords_found)
            
            # Специальный анализ для последнего шага
            if i == 5:
                if "нет" in response.lower() and "слотов" in response.lower():
                    tech_info["❌ ПРОБЛЕМА"] = "Система говорит что нет слотов"
                elif "последовательная запись" in response.lower():
                    tech_info["✅ УСПЕХ"] = "Показаны комбо-группы"
                elif "варианты" in response.lower():
                    tech_info["✅ ХОРОШО"] = "Показаны варианты"
                else:
                    tech_info["⚠️ ВНИМАНИЕ"] = "Неожиданный ответ"
            
            # Выводим результат шага
            print_dialog_step(i, step["input"], response, tech_info)
            
            # Сохраняем контекст для анализа
            context_tracking.append({
                "step": i,
                "input": step["input"],
                "response_length": len(response),
                "keywords": keywords_found
            })
            
        except Exception as e:
            print(f"❌ ОШИБКА НА ШАГЕ {i}: {str(e)[:100]}...")
            break
    
    # Итоговый анализ
    print_beautiful_separator("ИТОГОВЫЙ АНАЛИЗ", "📊")
    print(f"✅ Обработано шагов: {len(context_tracking)}")
    print(f"✅ Система: {orchestrator.system_type}")
    
    # Анализ по шагам
    for step_data in context_tracking:
        step_num = step_data["step"]
        keywords = step_data["keywords"]
        status = "✅" if keywords else "⚠️"
        print(f"{status} Шаг {step_num}: {', '.join(keywords) if keywords else 'Нет ключевых слов'}")
    
    # Финальный вердикт
    final_step = context_tracking[-1] if context_tracking else None
    if final_step and any("Слоты" in kw or "варианты" in kw for kw in final_step["keywords"]):
        print(f"\n🎉 РЕЗУЛЬТАТ: Комбо-запись РАБОТАЕТ!")
        print(f"💎 Новая система успешно обработала запрос Евгения")
    else:
        print(f"\n⚠️ РЕЗУЛЬТАТ: Требуется доработка")
        print(f"🔧 Система обработала запрос, но результат отличается от ожидаемого")
    
    print_beautiful_separator("КОНЕЦ ДЕМОНСТРАЦИИ", "🏁")

if __name__ == "__main__":
    test_detailed_combo_showcase()
