#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов RAG-системы салона красоты.
Поддерживает различные режимы тестирования и генерацию отчетов.
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, description=""):
    """Выполняет команду и возвращает результат."""
    print(f"\n{'='*60}")
    if description:
        print(f"🔍 {description}")
    print(f"Команда: {' '.join(command)}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"⏱️  Время выполнения: {end_time - start_time:.2f} сек")
    
    if result.returncode == 0:
        print("✅ Успешно")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ Ошибка")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)
    
    return result


def check_dependencies():
    """Проверяет наличие необходимых зависимостей."""
    print("🔍 Проверка зависимостей...")
    
    required_packages = ['pytest', 'pytest-cov', 'pytest-mock']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Все зависимости установлены")
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Запускает модульные тесты."""
    command = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        command.append("-v")
    
    if coverage:
        command.extend([
            "--cov=beauty_salon_rag",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Исключаем интеграционные тесты для модульного тестирования
    command.extend([
        "--ignore=tests/test_integration.py",
        "-x"  # Остановка на первой ошибке
    ])
    
    return run_command(command, "Запуск модульных тестов")


def run_integration_tests(verbose=False):
    """Запускает интеграционные тесты."""
    command = ["python", "-m", "pytest", "tests/test_integration.py"]
    
    if verbose:
        command.append("-v")
    
    command.append("-x")  # Остановка на первой ошибке
    
    return run_command(command, "Запуск интеграционных тестов")


def run_specific_test_file(test_file, verbose=False):
    """Запускает тесты из конкретного файла."""
    command = ["python", "-m", "pytest", f"tests/{test_file}"]
    
    if verbose:
        command.append("-v")
    
    return run_command(command, f"Запуск тестов из {test_file}")


def run_performance_tests(verbose=False):
    """Запускает тесты производительности."""
    command = ["python", "-m", "pytest", "tests/test_integration.py::TestPerformanceIntegration"]
    
    if verbose:
        command.append("-v")
    
    return run_command(command, "Запуск тестов производительности")


def run_linting():
    """Запускает проверку кода линтерами."""
    print("\n🔍 Проверка качества кода...")
    
    # Проверяем наличие flake8
    try:
        import flake8
        command = ["python", "-m", "flake8", "beauty_salon_rag/", "tests/", "--max-line-length=100"]
        result = run_command(command, "Проверка стиля кода (flake8)")
        if result.returncode != 0:
            return False
    except ImportError:
        print("⚠️  flake8 не установлен, пропускаем проверку стиля")
    
    return True


def generate_test_report():
    """Генерирует отчет о тестировании."""
    print("\n📊 Генерация отчета о тестировании...")
    
    # Запускаем все тесты с покрытием
    command = [
        "python", "-m", "pytest", "tests/",
        "--cov=beauty_salon_rag",
        "--cov-report=html:htmlcov",
        "--cov-report=term",
        "--cov-report=xml",
        "--junit-xml=test-results.xml"
    ]
    
    result = run_command(command, "Генерация полного отчета")
    
    if result.returncode == 0:
        print("\n📈 Отчеты созданы:")
        print("  - HTML отчет: htmlcov/index.html")
        print("  - XML отчет: coverage.xml")
        print("  - JUnit XML: test-results.xml")
    
    return result


def run_smoke_tests():
    """Запускает быстрые smoke-тесты."""
    print("\n🚀 Запуск smoke-тестов...")
    
    # Тестируем только основные функции
    smoke_tests = [
        "tests/test_config.py::TestConfig::test_init_default_config",
        "tests/test_data_loader.py::TestDataLoader::test_load_services_json_success",
        "tests/test_gpt_client.py::TestGPTClient::test_init_success",
        "tests/test_main.py::TestBeautySalonRAG::test_init_success"
    ]
    
    command = ["python", "-m", "pytest"] + smoke_tests + ["-v"]
    
    return run_command(command, "Smoke-тесты ос��овных компонентов")


def main():
    """Главная функция скрипта."""
    parser = argparse.ArgumentParser(description="Запуск тестов RAG-системы салона красоты")
    
    parser.add_argument("--unit", action="store_true", help="Запустить только модульные тесты")
    parser.add_argument("--integration", action="store_true", help="Запустить только интеграционные тесты")
    parser.add_argument("--performance", action="store_true", help="Запустить тесты производительности")
    parser.add_argument("--smoke", action="store_true", help="Запустить smoke-тесты")
    parser.add_argument("--file", type=str, help="Запустить тесты из конкретного файла")
    parser.add_argument("--coverage", action="store_true", help="Включить анализ покрытия кода")
    parser.add_argument("--report", action="store_true", help="Сгенерировать полный отчет")
    parser.add_argument("--lint", action="store_true", help="Проверить качество кода")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--all", action="store_true", help="Запустить все тесты и проверки")
    
    args = parser.parse_args()
    
    print("🧪 Система тестирования RAG-системы салона красоты")
    print("=" * 60)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    success = True
    
    try:
        if args.smoke:
            result = run_smoke_tests()
            success = success and (result.returncode == 0)
        
        elif args.unit:
            result = run_unit_tests(args.verbose, args.coverage)
            success = success and (result.returncode == 0)
        
        elif args.integration:
            result = run_integration_tests(args.verbose)
            success = success and (result.returncode == 0)
        
        elif args.performance:
            result = run_performance_tests(args.verbose)
            success = success and (result.returncode == 0)
        
        elif args.file:
            result = run_specific_test_file(args.file, args.verbose)
            success = success and (result.returncode == 0)
        
        elif args.report:
            result = generate_test_report()
            success = success and (result.returncode == 0)
        
        elif args.lint:
            success = success and run_linting()
        
        elif args.all:
            # Запускаем все проверки
            print("\n🎯 Запуск полного набора тестов и проверок...")
            
            # 1. Smoke-тесты
            result = run_smoke_tests()
            success = success and (result.returncode == 0)
            
            # 2. Линтинг
            if success:
                success = success and run_linting()
            
            # 3. Модульные тесты
            if success:
                result = run_unit_tests(args.verbose, True)
                success = success and (result.returncode == 0)
            
            # 4. Интеграционные тесты
            if success:
                result = run_integration_tests(args.verbose)
                success = success and (result.returncode == 0)
            
            # 5. Тесты производительности
            if success:
                result = run_performance_tests(args.verbose)
                success = success and (result.returncode == 0)
        
        else:
            # По умолчанию запускаем модульные тесты
            result = run_unit_tests(args.verbose, args.coverage)
            success = success and (result.returncode == 0)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        sys.exit(1)
    
    # Итоговый результат
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("💥 Обнаружены ошибки в тестах")
        sys.exit(1)


if __name__ == "__main__":
    main()