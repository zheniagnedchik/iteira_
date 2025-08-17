#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования централизованной обработки ошибок и логирования.
Показывает различные типы ошибок и их обработку.
"""

import sys
import time
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.logger import setup_logging, get_logger, log_operation, OperationLogger
from beauty_salon_rag.error_handler import (
    handle_error, get_error_stats, DataLoadError, GPTClientError, 
    ValidationError, ConfigurationError, BeautySalonError
)


def demonstrate_logging():
    """Демонстрация различных типов логирования."""
    print("=== Демонстрация системы логирования ===\n")
    
    # Получаем различные логгеры
    main_logger = get_logger("demo.main")
    operation_logger = get_logger("demo.operations", structured_logging=True)
    
    # Базовое логирование
    main_logger.info("Запуск демонстрации системы логирования")
    main_logger.debug("Отладочное сообщение (может не отображаться)")
    main_logger.warning("Предупреждение о демонстрации")
    
    # Логирование операции с контекстом
    with OperationLogger(operation_logger, "demo_operation") as op_logger:
        op_logger.add_context(user_id="demo_user", session_id="demo_session")
        op_logger.log_step("initialization", component="demo")
        
        time.sleep(0.1)  # Имитация работы
        
        op_logger.log_step("processing", items_count=5)
        time.sleep(0.1)
        
        op_logger.log_step("completion", status="success")
    
    # Декоратор логирования
    @log_operation("decorated_function")
    def demo_function(x: int, y: int) -> int:
        """Демонстрационная функция с декоратором логирования."""
        time.sleep(0.05)
        return x * y
    
    result = demo_function(3, 4)
    main_logger.info(f"Результат функции: {result}")
    
    print("✅ Демонстрация логирования завершена\n")


def demonstrate_error_handling():
    """Демонстрация обработки различных типов ошибок."""
    print("=== Демонстрация обработки ошибок ===\n")
    
    logger = get_logger("demo.errors")
    
    # Список ошибок для демонстрации
    demo_errors = [
        DataLoadError("Файл services.json не найден", file_path="services.json"),
        GPTClientError("Превышен лимит запросов к API", api_error="Rate limit exceeded"),
        ValidationError("Некорректный формат запроса", field="query", value=""),
        ConfigurationError("Отсутствует API ключ", config_key="OPENAI_API_KEY"),
        ValueError("Стандартная ошибка Python"),
        FileNotFoundError("Файл не найден"),
        ConnectionError("Ошибка соединения")
    ]
    
    print("Обработка различных типов ошибок:\n")
    
    for i, error in enumerate(demo_errors, 1):
        print(f"{i}. {type(error).__name__}: {error}")
        
        # Обрабатываем ошибку
        user_message = handle_error(error, context={
            "demo_step": i,
            "error_type": type(error).__name__
        })
        
        print(f"   👤 Сообщение пользователю: {user_message}")
        print()
    
    # Показываем статистику ошибок
    stats = get_error_stats()
    print("📊 Статистика ошибок:")
    print(f"   Всего ошибок: {stats['total_errors']}")
    print(f"   По категориям: {stats['by_category']}")
    print(f"   По серьезности: {stats['by_severity']}")
    print()


def demonstrate_function_with_errors():
    """Демонстрация функции с различными типами ошибок."""
    print("=== Демонстрация функции с ошибками ===\n")
    
    @log_operation("risky_function")
    def risky_function(operation_type: str):
        """Функция, которая может вызвать различные ошибки."""
        logger = get_logger("demo.risky")
        logger.info(f"Выполнение рискованной операции: {operation_type}")
        
        if operation_type == "data_load":
            raise DataLoadError("Не удалось загрузить данные", file_path="missing_file.json")
        elif operation_type == "gpt_api":
            raise GPTClientError("API недоступен", api_error="Service unavailable")
        elif operation_type == "validation":
            raise ValidationError("Некорректные данные", field="input", value="invalid")
        elif operation_type == "config":
            raise ConfigurationError("Неверная конфигурация", config_key="MISSING_KEY")
        elif operation_type == "system":
            raise RuntimeError("Системная ошибка")
        else:
            return f"Операция '{operation_type}' выполнена успешно"
    
    # Тестируем различные сценарии
    test_cases = [
        "success",
        "data_load", 
        "gpt_api",
        "validation",
        "config",
        "system"
    ]
    
    for case in test_cases:
        print(f"🧪 Тестирование случая: {case}")
        
        try:
            result = risky_function(case)
            print(f"   ✅ Успех: {result}")
        except Exception as e:
            user_message = handle_error(e, context={"test_case": case})
            print(f"   ❌ Ошибка обработана: {user_message}")
        
        print()


def demonstrate_nested_operations():
    """Демонстрация вложенных операций с логированием."""
    print("=== Демонстрация вложенных операций ===\n")
    
    logger = get_logger("demo.nested")
    
    @log_operation("parent_operation")
    def parent_operation():
        """Родительская операция."""
        logger.info("Начало родительской операции")
        
        try:
            child_operation_1()
            child_operation_2()
            child_operation_3()  # Эта операция вызовет ошибку
        except Exception as e:
            logger.error(f"Ошибка в родительской операции: {e}")
            raise
    
    @log_operation("child_operation_1")
    def child_operation_1():
        """Первая дочерняя операция."""
        logger.info("Выполнение дочерней операции 1")
        time.sleep(0.1)
        return "result_1"
    
    @log_operation("child_operation_2") 
    def child_operation_2():
        """Вторая дочерняя операция."""
        logger.info("Выполнение дочерней операции 2")
        time.sleep(0.1)
        return "result_2"
    
    @log_operation("child_operation_3")
    def child_operation_3():
        """Третья дочерняя операция (с ошибкой)."""
        logger.info("Выполнение дочерней операции 3")
        raise ValidationError("Ошибка валидации в дочерней операции", field="data", value="invalid")
    
    try:
        parent_operation()
    except Exception as e:
        user_message = handle_error(e, context={"operation": "nested_demo"})
        print(f"🔄 Обработка ошибки из вложенной операции: {user_message}")
    
    print()


def main():
    """Главная функция демонстрации."""
    print("🚀 Демонстрация централизованной обработки ошибок и логирования")
    print("=" * 70)
    print()
    
    # Инициализируем систему логирования
    setup_logging()
    
    try:
        # Демонстрируем различные аспекты системы
        demonstrate_logging()
        demonstrate_error_handling()
        demonstrate_function_with_errors()
        demonstrate_nested_operations()
        
        # Финальная статистика
        print("=== Финальная статистика ===\n")
        stats = get_error_stats()
        print(f"📈 Всего обработано ошибок: {stats['total_errors']}")
        print(f"📊 Распределение по категориям:")
        for category, count in stats['by_category'].items():
            print(f"   - {category}: {count}")
        print(f"🎯 Распределение по серьезности:")
        for severity, count in stats['by_severity'].items():
            print(f"   - {severity}: {count}")
        
        print("\n✅ Демонстрация завершена успешно!")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка в демонстрации: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())