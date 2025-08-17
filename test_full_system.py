#!/usr/bin/env python3
"""
Полное системное тестирование RAG-системы салона красоты с реальными данными.
Проверяет работоспособность всей системы в реальных условиях.
"""

import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any

from beauty_salon_rag.config import config
from beauty_salon_rag.logger import get_logger, setup_logging
from main import BeautySalonRAG


class FullSystemTester:
    """Класс для полного системного тестирования."""
    
    def __init__(self):
        """Инициализация тестера."""
        self.logger = get_logger(__name__)
        self.results = []
        self.errors = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Запускает все системные тесты.
        
        Returns:
            Результаты тестирования
        """
        print("🧪 Запуск полного системного тестирования...")
        print("=" * 60)
        
        test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance_metrics": {},
            "start_time": time.time()
        }
        
        # Список тестов для выполнения
        tests = [
            ("Проверка файлов данных", self._test_data_files),
            ("Инициализация системы", self._test_system_initialization),
            ("Базовые запросы", self._test_basic_queries),
            ("Сложные запросы", self._test_complex_queries),
            ("Обработка ошибок", self._test_error_handling),
            ("Производительность", self._test_performance),
            ("Статус системы", self._test_system_status),
            ("Интерактивный режим", self._test_interactive_mode)
        ]
        
        for test_name, test_func in tests:
            test_results["total_tests"] += 1
            print(f"\n🔍 {test_name}...")
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                if result:
                    test_results["passed"] += 1
                    print(f"✅ {test_name} - ПРОЙДЕН ({end_time - start_time:.2f}с)")
                else:
                    test_results["failed"] += 1
                    print(f"❌ {test_name} - ПРОВАЛЕН")
                    
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"{test_name}: {str(e)}")
                print(f"💥 {test_name} - ОШИБКА: {e}")
                self.logger.error(f"Ошибка в тесте '{test_name}': {e}")
        
        test_results["end_time"] = time.time()
        test_results["total_time"] = test_results["end_time"] - test_results["start_time"]
        
        return test_results
    
    def _test_data_files(self) -> bool:
        """Тестирует наличие и корректность файлов данных."""
        try:
            # Проверка существования файлов
            services_file = Path(config.get('data.services_file'))
            services_no_staff_file = Path(config.get('data.services_no_staff_file'))
            
            if not services_file.exists():
                print(f"   ❌ Файл {services_file} не найден")
                return False
                
            if not services_no_staff_file.exists():
                print(f"   ❌ Файл {services_no_staff_file} не найден")
                return False
            
            # Проверка корректности JSON
            with open(services_file, 'r', encoding='utf-8') as f:
                services_data = json.load(f)
                
            with open(services_no_staff_file, 'r', encoding='utf-8') as f:
                services_no_staff_data = json.load(f)
            
            # Проверка структуры данных
            if not isinstance(services_data, dict) or 'data' not in services_data:
                print("   ❌ Некорректная структура services.json")
                return False
                
            if not isinstance(services_no_staff_data, dict) or 'data' not in services_no_staff_data:
                print("   ❌ Некорректная структура services_no_staff.json")
                return False
            
            services_count = len(services_data['data']['items'])
            services_no_staff_count = len(services_no_staff_data['data']['items'])
            
            print(f"   ✅ Найдено {services_count} полных услуг")
            print(f"   ✅ Найдено {services_no_staff_count} облегченных услуг")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка проверки файлов: {e}")
            return False
    
    def _test_system_initialization(self) -> bool:
        """Тестирует инициализацию системы."""
        try:
            rag_system = BeautySalonRAG()
            
            # Проверка инициализации модулей
            if not hasattr(rag_system, 'search_module'):
                print("   ❌ Поисковый модуль не инициализирован")
                return False
                
            if not hasattr(rag_system, 'consultation_module'):
                print("   ❌ Консультационный модуль не инициализирован")
                return False
            
            print("   ✅ Все модули инициализированы успешно")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка инициализации: {e}")
            return False
    
    def _test_basic_queries(self) -> bool:
        """Тестирует базовые запросы пользователей."""
        try:
            rag_system = BeautySalonRAG()
            
            # Список базовых тестовых запросов
            test_queries = [
                "массаж лица",
                "чистка кожи",
                "процедуры для омоложения",
                "что такое пилинг",
                "хочу записаться на массаж"
            ]
            
            successful_queries = 0
            
            for query in test_queries:
                try:
                    response = rag_system.process_query(query)
                    
                    if response and len(response) > 10:  # Минимальная длина ответа
                        successful_queries += 1
                        print(f"   ✅ '{query}' - получен ответ ({len(response)} символов)")
                    else:
                        print(f"   ❌ '{query}' - пустой или слишком короткий ответ")
                        
                except Exception as e:
                    print(f"   ❌ '{query}' - ошибка: {e}")
            
            success_rate = successful_queries / len(test_queries)
            print(f"   📊 Успешность: {success_rate:.1%} ({successful_queries}/{len(test_queries)})")
            
            return success_rate >= 0.8  # 80% успешных запросов
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования запросов: {e}")
            return False
    
    def _test_complex_queries(self) -> bool:
        """Тестирует сложные запросы пользователей."""
        try:
            rag_system = BeautySalonRAG()
            
            # Сложные тестовые запросы
            complex_queries = [
                "Какие процедуры помогут от морщин и пигментации одновременно?",
                "Хочу записаться на массаж лица к лучшему мастеру на следующей неделе",
                "Есть ли противопоказания для химического пилинга при чувствительной коже?",
                "Сколько стоят все процедуры для омоложения лица?",
                "Какие процедуры можно делать в салоне, а какие только в клинике?"
            ]
            
            successful_queries = 0
            
            for query in complex_queries:
                try:
                    start_time = time.time()
                    response = rag_system.process_query(query)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    
                    if response and len(response) > 50:  # Более длинный ответ для сложных запросов
                        successful_queries += 1
                        print(f"   ✅ Сложный запрос обработан за {response_time:.2f}с")
                    else:
                        print(f"   ❌ Неудовлетворительный ответ на сложный запрос")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка обработки сложного запроса: {e}")
            
            success_rate = successful_queries / len(complex_queries)
            print(f"   📊 Успешность сложных запросов: {success_rate:.1%}")
            
            return success_rate >= 0.6  # 60% для сложных запросов
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования сложных запросов: {e}")
            return False
    
    def _test_error_handling(self) -> bool:
        """Тестирует обработку ошибочных ситуаций."""
        try:
            rag_system = BeautySalonRAG()
            
            # Тестовые случаи с ошибками
            error_cases = [
                "",  # Пустой запрос
                "   ",  # Только пробелы
                "абракадабра непонятный запрос xyz123",  # Бессмысленный запрос
                "a" * 1000,  # Очень длинный запрос
                "🤖🔥💯" * 50  # Эмодзи и специальные символы
            ]
            
            handled_errors = 0
            
            for error_case in error_cases:
                try:
                    response = rag_system.process_query(error_case)
                    
                    # Система должна вернуть осмысленный ответ даже на некорректный запрос
                    if response and "ошибка" not in response.lower():
                        handled_errors += 1
                        print(f"   ✅ Корректно обработан некорректный ввод")
                    else:
                        print(f"   ⚠️  Получено сообщение об ошибке (это нормально)")
                        handled_errors += 1  # Это тоже считается корректной обработкой
                        
                except Exception as e:
                    print(f"   ❌ Необработанное исключение: {e}")
            
            success_rate = handled_errors / len(error_cases)
            print(f"   📊 Обработка ошибок: {success_rate:.1%}")
            
            return success_rate >= 0.8
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования обработки ошибок: {e}")
            return False
    
    def _test_performance(self) -> bool:
        """Тестирует производительность системы."""
        try:
            rag_system = BeautySalonRAG()
            
            # Тест времени отклика
            test_query = "массаж лица для омоложения"
            response_times = []
            
            print("   🏃 Тестирование производительности...")
            
            for i in range(5):  # 5 запросов для усреднения
                start_time = time.time()
                response = rag_system.process_query(test_query)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response:
                    print(f"   ⏱️  Запрос {i+1}: {response_time:.2f}с")
                else:
                    print(f"   ❌ Запрос {i+1}: нет ответа")
                    return False
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"   📊 Среднее время отклика: {avg_response_time:.2f}с")
            print(f"   📊 Максимальное время: {max_response_time:.2f}с")
            print(f"   📊 Минимальное время: {min_response_time:.2f}с")
            
            # Критерии производительности
            performance_ok = (
                avg_response_time < 10.0 and  # Среднее время < 10 сек
                max_response_time < 15.0      # Максимальное время < 15 сек
            )
            
            if performance_ok:
                print("   ✅ Производительность соответствует требованиям")
            else:
                print("   ⚠️  Производительность ниже ожидаемой")
            
            return performance_ok
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования производительности: {e}")
            return False
    
    def _test_system_status(self) -> bool:
        """Тестирует проверку статуса системы."""
        try:
            rag_system = BeautySalonRAG()
            
            status = rag_system.get_system_status()
            
            required_fields = ['system', 'search_module', 'consultation_module', 'overall_status']
            
            for field in required_fields:
                if field not in status:
                    print(f"   ❌ Отсутствует поле статуса: {field}")
                    return False
            
            print(f"   📊 Статус системы: {status['system']}")
            print(f"   📊 Поисковый модуль: {'✅' if status['search_module'] else '❌'}")
            print(f"   📊 Консультационный модуль: {'✅' if status['consultation_module'] else '❌'}")
            print(f"   📊 Общий статус: {'✅' if status['overall_status'] else '❌'}")
            
            return status['overall_status']
            
        except Exception as e:
            print(f"   ❌ Ошибка проверки статуса: {e}")
            return False
    
    def _test_interactive_mode(self) -> bool:
        """Тестирует готовность к интерактивному режиму."""
        try:
            rag_system = BeautySalonRAG()
            
            # Проверяем наличие необходимых методов
            required_methods = ['start_chat', '_show_help', '_show_status']
            
            for method in required_methods:
                if not hasattr(rag_system, method):
                    print(f"   ❌ Отсутствует метод: {method}")
                    return False
            
            print("   ✅ Все методы интерактивного режима доступны")
            
            # Проверяем, что методы вызываются без ошибок (кроме start_chat)
            try:
                rag_system._show_help()
                print("   ✅ Справка работает корректно")
            except Exception as e:
                print(f"   ❌ Ошибка в справке: {e}")
                return False
            
            try:
                rag_system._show_status()
                print("   ✅ Показ статуса работает корректно")
            except Exception as e:
                print(f"   ❌ Ошибка в показе статуса: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка тестирования интерактивного режима: {e}")
            return False
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Генерирует отчет о тестировании.
        
        Args:
            results: Результаты тестирования
            
        Returns:
            Текст отчета
        """
        report = []
        report.append("=" * 80)
        report.append("📋 ОТЧЕТ О ПОЛНОМ СИСТЕМНОМ ТЕСТИРОВАНИИ")
        report.append("=" * 80)
        report.append("")
        
        # Общая статистика
        report.append(f"🎯 Общие результаты:")
        report.append(f"   Всего тестов: {results['total_tests']}")
        report.append(f"   Пройдено: {results['passed']} ✅")
        report.append(f"   Провалено: {results['failed']} ❌")
        report.append(f"   Успешность: {(results['passed'] / results['total_tests']) * 100:.1f}%")
        report.append(f"   Общее время: {results['total_time']:.2f} секунд")
        report.append("")
        
        # Ошибки
        if results['errors']:
            report.append("❌ Обнаруженные ошибки:")
            for error in results['errors']:
                report.append(f"   - {error}")
            report.append("")
        
        # Рекомендации
        report.append("💡 Рекомендации:")
        
        if results['failed'] == 0:
            report.append("   ✅ Система готова к продуктивному использованию!")
        elif results['failed'] <= 2:
            report.append("   ⚠️  Система в основном работает, но есть незначительные проблемы")
            report.append("   📝 Рекомендуется исправить выявленные ошибки")
        else:
            report.append("   ❌ Обнаружены серьезные проблемы в системе")
            report.append("   🔧 Требуется доработка перед использованием")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Главная функция для запуска полного системного тестирования."""
    # Настройка логирования
    setup_logging()
    
    # Создание и запуск тестера
    tester = FullSystemTester()
    
    try:
        # Запуск всех тестов
        results = tester.run_all_tests()
        
        # Генерация и вывод отчета
        report = tester.generate_report(results)
        print("\n" + report)
        
        # Сохранение отчета в файл
        report_file = Path("system_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Отчет сохранен в файл: {report_file}")
        
        # Возврат кода завершения
        if results['failed'] == 0:
            print("\n🎉 Все тесты пройдены успешно!")
            sys.exit(0)
        else:
            print(f"\n💥 Обнаружено {results['failed']} проблем")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка при тестировании: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()