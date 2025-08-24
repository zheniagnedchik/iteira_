#!/usr/bin/env python3
"""
Тест эффективных вопросов - минимум вопросов, максимум пользы
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.unified_gpt_orchestrator import UnifiedGPTOrchestrator
from main import BeautySalonRAG


def test_efficient_filtering():
    """Тестирует эффективную фильтрацию с минимумом вопросов."""
    print("⚡ Тест эффективной фильтрации услуг\n")
    
    try:
        rag_system = BeautySalonRAG()
        orchestrator = UnifiedGPTOrchestrator(rag_system)
        
        # Сценарий как у Евгения с лазерной эпиляцией
        user_id = 54321
        
        print("🎯 Сценарий: Лазерная эпиляция ног")
        print("="*50)
        
        # Первое сообщение
        response1, metadata1 = orchestrator.process_message(user_id, "хочу лазерную эпиляцию", "Евгений")
        print(f"💬 Запрос: 'хочу лазерную эпиляцию'")
        print(f"🎯 Действие: {metadata1.get('type')}")
        print(f"📝 Ответ: {response1[:150]}...")
        print()
        
        # Второе сообщение - уточнение "ноги"
        response2, metadata2 = orchestrator.process_message(user_id, "ноги", "Евгений")
        print(f"💬 Уточнение: 'ноги'")
        print(f"🎯 Действие: {metadata2.get('type')}")
        print(f"📝 Ответ: {response2}")
        print()
        
        # Анализируем эффективность
        print("📊 АНАЛИЗ ЭФФЕКТИВНОСТИ:")
        print("="*50)
        
        # Считаем количество вопросов во втором ответе
        question_indicators = ['?', '🔹', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        question_count = sum(response2.count(indicator) for indicator in question_indicators)
        
        print(f"❓ Количество вопросов/пунктов: {question_count}")
        
        # Проверяем, упоминаются ли зоны ног
        leg_keywords = ['голень', 'бедр', 'нога', 'зон']
        mentioned_zones = [keyword for keyword in leg_keywords if keyword.lower() in response2.lower()]
        
        print(f"🦵 Упомянуты зоны ног: {mentioned_zones}")
        
        # Проверяем, упоминаются ли цены
        price_mentioned = any(price in response2 for price in ['50', '70', '120', '155'])
        print(f"💰 Упомянуты цены: {'✅' if price_mentioned else '❌'}")
        
        # Проверяем на лишние вопросы
        unnecessary_keywords = ['тип кожи', 'противопоказан', 'курс процедур', 'бюджет', 'беременность']
        unnecessary_found = [keyword for keyword in unnecessary_keywords if keyword.lower() in response2.lower()]
        
        print(f"⚠️  Лишние вопросы: {unnecessary_found if unnecessary_found else 'Нет ✅'}")
        
        # Оценка эффективности
        efficiency_score = 0
        if question_count <= 3:
            efficiency_score += 30
        if mentioned_zones:
            efficiency_score += 30
        if price_mentioned:
            efficiency_score += 20
        if not unnecessary_found:
            efficiency_score += 20
        
        print(f"\n🎯 ОЦЕНКА ЭФФЕКТИВНОСТИ: {efficiency_score}/100")
        
        if efficiency_score >= 80:
            print("✅ ОТЛИЧНО - Эффективная фильтрация!")
        elif efficiency_score >= 60:
            print("🟡 ХОРОШО - Можно улучшить")
        else:
            print("❌ ПЛОХО - Требуется оптимизация")
        
        print("\n💡 Идеальный вопрос для 'ноги' должен быть:")
        print("'Какую зону ног: только голени (120₽) или бёдра+голени (155₽)?'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("⚡ Тестирование эффективности вопросов\n")
    
    success = test_efficient_filtering()
    
    if success:
        print("\n🎉 Тест завершен!")
        print("💡 Цель: один точный вопрос лучше четырёх общих")
    else:
        print("\n❌ Тест не прошел. Требуется оптимизация.")

