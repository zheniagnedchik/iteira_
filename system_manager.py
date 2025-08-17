#!/usr/bin/env python3
"""
System Manager для RAG-системы салона красоты
Проверяет состояние системы и Telegram бота, перезапускает при необходимости
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from beauty_salon_rag.config import config
from beauty_salon_rag.logger import setup_logging, get_logger


class SystemManager:
    """Менеджер системы для мониторинга и управления RAG-системой и Telegram ботом."""
    
    def __init__(self):
        """Инициализация менеджера системы."""
        setup_logging()
        self.logger = get_logger(__name__)
        
        # Файлы для хранения PID процессов
        self.pid_dir = Path("pids")
        self.pid_dir.mkdir(exist_ok=True)
        
        self.telegram_pid_file = self.pid_dir / "telegram_bot.pid"
        self.system_pid_file = self.pid_dir / "rag_system.pid"
        
        # Лог файлы
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.system_log = self.log_dir / "system_manager.log"
        self.telegram_log = self.log_dir / "telegram_bot_output.log"
        self.rag_log = self.log_dir / "rag_system_output.log"
        
        self.logger.info("System Manager initialized")
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """Проверяет зависимости системы."""
        self.logger.info("Checking system dependencies...")
        
        errors = []
        
        # Проверка Python пакетов
        required_packages = [
            ('openai', 'openai'),
            ('python-dotenv', 'dotenv'),
            ('python-telegram-bot', 'telegram'),
            ('psutil', 'psutil')
        ]
        
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                errors.append(f"Missing package: {package_name}")
        
        # Проверка файлов данных
        services_file = Path(config.get('data.services_file', 'services.json'))
        services_no_staff_file = Path(config.get('data.services_no_staff_file', 'services_no_staff.json'))
        
        if not services_file.exists():
            errors.append(f"Missing data file: {services_file}")
        
        if not services_no_staff_file.exists():
            errors.append(f"Missing data file: {services_no_staff_file}")
        
        # Проверка конфигурации
        try:
            config.get_openai_key()
        except Exception as e:
            errors.append(f"OpenAI API key issue: {e}")
        
        try:
            config.get_telegram_token()
        except Exception as e:
            errors.append(f"Telegram bot token issue: {e}")
        
        success = len(errors) == 0
        if success:
            self.logger.info("All dependencies check passed")
        else:
            self.logger.error(f"Dependencies check failed: {errors}")
        
        return success, errors
    
    def check_rag_system(self) -> Tuple[bool, str]:
        """Проверяет работоспособность RAG-системы."""
        self.logger.info("Checking RAG system health...")
        
        try:
            from main import BeautySalonRAG
            
            # Создаем экземпляр системы
            rag_system = BeautySalonRAG()
            
            # Проверяем статус
            status = rag_system.get_system_status()
            
            if status['overall_status']:
                # Тестируем простой запрос
                response = rag_system.process_query("массаж лица")
                
                if response and len(response) > 10:
                    self.logger.info("RAG system health check passed")
                    return True, "RAG system is healthy"
                else:
                    error_msg = "RAG system returns empty responses"
                    self.logger.error(error_msg)
                    return False, error_msg
            else:
                error_msg = f"RAG system status check failed: {status}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"RAG system health check failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def check_telegram_bot(self) -> Tuple[bool, str]:
        """Проверяет готовность Telegram бота."""
        self.logger.info("Checking Telegram bot readiness...")
        
        try:
            from beauty_salon_rag.telegram_bot import TelegramBot
            
            # Создаем экземпляр бота (без запуска polling)
            bot = TelegramBot()
            
            # Проверяем основные компоненты
            if not bot.bot_token:
                return False, "Bot token not configured"
            
            if not bot.rag_system:
                return False, "RAG system not initialized in bot"
            
            if not bot.orchestrator:
                return False, "Dialog orchestrator not initialized"
            
            # Тестируем оркестратор
            response, metadata = bot.orchestrator.process_message(
                user_id=999999,  # Тестовый ID
                message="привет",
                user_name="Тест"
            )
            
            if response and "Итейра" in response:
                self.logger.info("Telegram bot health check passed")
                return True, "Telegram bot is ready"
            else:
                return False, "Bot orchestrator not working properly"
                
        except Exception as e:
            error_msg = f"Telegram bot check failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def is_process_running(self, pid_file: Path) -> Tuple[bool, Optional[int]]:
        """Проверяет, запущен ли процесс по PID файлу."""
        if not pid_file.exists():
            return False, None
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Проверяем, существует ли процесс
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if process.is_running():
                    return True, pid
            
            # Если процесс не запущен, удаляем PID файл
            pid_file.unlink()
            return False, None
            
        except (ValueError, psutil.NoSuchProcess, FileNotFoundError):
            # Удаляем некорректный PID файл
            if pid_file.exists():
                pid_file.unlink()
            return False, None
    
    def stop_process(self, pid_file: Path, process_name: str) -> bool:
        """Останавливает процесс по PID файлу."""
        is_running, pid = self.is_process_running(pid_file)
        
        if not is_running:
            self.logger.info(f"{process_name} is not running")
            return True
        
        try:
            self.logger.info(f"Stopping {process_name} (PID: {pid})...")
            
            process = psutil.Process(pid)
            
            # Сначала пробуем мягкое завершение
            process.terminate()
            
            # Ждем до 10 секунд
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Если не завершился, принудительно убиваем
                self.logger.warning(f"Force killing {process_name} (PID: {pid})")
                process.kill()
                process.wait(timeout=5)
            
            # Удаляем PID файл
            if pid_file.exists():
                pid_file.unlink()
            
            self.logger.info(f"{process_name} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop {process_name}: {e}")
            return False
    
    def start_telegram_bot(self) -> Tuple[bool, Optional[int]]:
        """Запускает Telegram бота в фоновом режиме."""
        self.logger.info("Starting Telegram bot...")
        
        try:
            # Запускаем бота в фоновом режиме
            process = subprocess.Popen(
                [sys.executable, "start_telegram_bot.py"],
                stdout=open(self.telegram_log, 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid  # Создаем новую группу процессов
            )
            
            # Сохраняем PID
            with open(self.telegram_pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Ждем немного и проверяем, что процесс запустился
            time.sleep(3)
            
            if process.poll() is None:  # Процесс еще запущен
                self.logger.info(f"Telegram bot started successfully (PID: {process.pid})")
                return True, process.pid
            else:
                self.logger.error("Telegram bot failed to start")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot: {e}")
            return False, None
    
    def start_rag_system(self) -> Tuple[bool, Optional[int]]:
        """Запускает RAG-систему в интерактивном режиме (если нужно)."""
        # В данном случае RAG-система работает внутри Telegram бота
        # Но можно добавить отдельный веб-интерфейс или API
        self.logger.info("RAG system runs within Telegram bot")
        return True, None
    
    def perform_full_check(self) -> Dict[str, any]:
        """Выполняет полную проверку системы."""
        self.logger.info("Starting full system check...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'dependencies': {'status': False, 'errors': []},
            'rag_system': {'status': False, 'message': ''},
            'telegram_bot': {'status': False, 'message': ''},
            'processes': {
                'telegram_running': False,
                'telegram_pid': None
            },
            'overall_status': False
        }
        
        # 1. Проверка зависимостей
        deps_ok, deps_errors = self.check_dependencies()
        results['dependencies']['status'] = deps_ok
        results['dependencies']['errors'] = deps_errors
        
        if not deps_ok:
            self.logger.error("Dependencies check failed, stopping full check")
            return results
        
        # 2. Проверка RAG-системы
        rag_ok, rag_msg = self.check_rag_system()
        results['rag_system']['status'] = rag_ok
        results['rag_system']['message'] = rag_msg
        
        # 3. Проверка Telegram бота
        bot_ok, bot_msg = self.check_telegram_bot()
        results['telegram_bot']['status'] = bot_ok
        results['telegram_bot']['message'] = bot_msg
        
        # 4. Проверка запущенных процессов
        tg_running, tg_pid = self.is_process_running(self.telegram_pid_file)
        results['processes']['telegram_running'] = tg_running
        results['processes']['telegram_pid'] = tg_pid
        
        # 5. Общий статус
        results['overall_status'] = deps_ok and rag_ok and bot_ok
        
        self.logger.info(f"Full system check completed. Overall status: {results['overall_status']}")
        return results
    
    def restart_system(self) -> bool:
        """Перезапускает всю систему."""
        self.logger.info("Restarting entire system...")
        
        success = True
        
        # 1. Останавливаем все процессы
        if not self.stop_process(self.telegram_pid_file, "Telegram bot"):
            success = False
        
        # Небольшая пауза между остановкой и запуском
        time.sleep(2)
        
        # 2. Запускаем Telegram бота
        bot_started, bot_pid = self.start_telegram_bot()
        if not bot_started:
            success = False
        
        if success:
            self.logger.info("System restart completed successfully")
        else:
            self.logger.error("System restart completed with errors")
        
        return success
    
    def generate_status_report(self, results: Dict) -> str:
        """Генерирует отчет о состоянии системы."""
        report = []
        report.append("=" * 60)
        report.append("🔧 ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ")
        report.append("=" * 60)
        report.append(f"Время проверки: {results['timestamp']}")
        report.append("")
        
        # Зависимости
        deps_status = "✅ OK" if results['dependencies']['status'] else "❌ FAIL"
        report.append(f"📦 Зависимости: {deps_status}")
        if results['dependencies']['errors']:
            for error in results['dependencies']['errors']:
                report.append(f"   - {error}")
        report.append("")
        
        # RAG система
        rag_status = "✅ OK" if results['rag_system']['status'] else "❌ FAIL"
        report.append(f"🧠 RAG-система: {rag_status}")
        report.append(f"   {results['rag_system']['message']}")
        report.append("")
        
        # Telegram бот
        bot_status = "✅ OK" if results['telegram_bot']['status'] else "❌ FAIL"
        report.append(f"🤖 Telegram бот: {bot_status}")
        report.append(f"   {results['telegram_bot']['message']}")
        report.append("")
        
        # Процессы
        report.append("🔄 Запущенные процессы:")
        tg_status = "✅ Запущен" if results['processes']['telegram_running'] else "❌ Остановлен"
        tg_pid = f" (PID: {results['processes']['telegram_pid']})" if results['processes']['telegram_pid'] else ""
        report.append(f"   Telegram бот: {tg_status}{tg_pid}")
        report.append("")
        
        # Общий статус
        overall_status = "✅ СИСТЕМА РАБОТАЕТ" if results['overall_status'] else "❌ ЕСТЬ ПРОБЛЕМЫ"
        report.append(f"🎯 Общий статус: {overall_status}")
        report.append("")
        
        # Рекомендации
        if not results['overall_status']:
            report.append("💡 Рекомендации:")
            if not results['dependencies']['status']:
                report.append("   - Установите недостающие зависимости")
            if not results['rag_system']['status']:
                report.append("   - Проверьте конфигурацию RAG-системы")
            if not results['telegram_bot']['status']:
                report.append("   - Проверьте настройки Telegram бота")
            if not results['processes']['telegram_running']:
                report.append("   - Запустите Telegram бота")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_status_report(self, report: str):
        """Сохраняет отчет в файл."""
        report_file = self.log_dir / f"system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"Status report saved to {report_file}")


def main():
    """Главная функция менеджера системы."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="System Manager для RAG-системы салона красоты",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python system_manager.py --check                    # Проверить систему
  python system_manager.py --restart                  # Перезапустить систему
  python system_manager.py --check-and-restart        # Проверить и перезапустить при проблемах
  python system_manager.py --stop                     # Остановить все процессы
  python system_manager.py --start                    # Запустить систему
  python system_manager.py --status                   # Показать статус процессов
        """
    )
    
    parser.add_argument("--check", action="store_true", help="Проверить состояние системы")
    parser.add_argument("--restart", action="store_true", help="Перезапустить систему")
    parser.add_argument("--check-and-restart", action="store_true", help="Проверить и перезапустить при проблемах")
    parser.add_argument("--stop", action="store_true", help="Остановить все процессы")
    parser.add_argument("--start", action="store_true", help="Запустить систему")
    parser.add_argument("--status", action="store_true", help="Показать статус процессов")
    parser.add_argument("--save-report", action="store_true", help="Сохранить отчет в файл")
    
    args = parser.parse_args()
    
    print("🔧 System Manager для RAG-системы салона красоты")
    print("=" * 60)
    
    try:
        manager = SystemManager()
        
        if args.status:
            # Показать статус процессов
            print("📊 Статус процессов:")
            
            tg_running, tg_pid = manager.is_process_running(manager.telegram_pid_file)
            tg_status = f"✅ Запущен (PID: {tg_pid})" if tg_running else "❌ Остановлен"
            print(f"   Telegram бот: {tg_status}")
            
        elif args.stop:
            # Остановить все процессы
            print("🛑 Остановка всех процессов...")
            manager.stop_process(manager.telegram_pid_file, "Telegram bot")
            print("✅ Все процессы остановлены")
            
        elif args.start:
            # Запустить систему
            print("🚀 Запуск системы...")
            
            # Проверяем готовность
            results = manager.perform_full_check()
            
            if not results['overall_status']:
                print("❌ Система не готова к запуску:")
                report = manager.generate_status_report(results)
                print(report)
                sys.exit(1)
            
            # Запускаем
            success = manager.restart_system()
            
            if success:
                print("✅ Система запущена успешно")
            else:
                print("❌ Ошибки при запуске системы")
                sys.exit(1)
                
        elif args.restart:
            # Перезапустить систему
            print("🔄 Перезапуск системы...")
            success = manager.restart_system()
            
            if success:
                print("✅ Система перезапущена успешно")
            else:
                print("❌ Ошибки при перезапуске системы")
                sys.exit(1)
                
        elif args.check_and_restart:
            # Проверить и перезапустить при проблемах
            print("🔍 Проверка системы...")
            
            results = manager.perform_full_check()
            report = manager.generate_status_report(results)
            print(report)
            
            if args.save_report:
                manager.save_status_report(report)
            
            if results['overall_status']:
                # Проверяем, запущены ли процессы
                if not results['processes']['telegram_running']:
                    print("\n🚀 Система готова, но процессы не запущены. Запускаем...")
                    success = manager.restart_system()
                    
                    if success:
                        print("✅ Система запущена успешно")
                    else:
                        print("❌ Ошибки при запуске")
                        sys.exit(1)
                else:
                    print("\n✅ Система работает нормально, перезапуск не требуется")
            else:
                print("\n⚠️  Обнаружены проблемы. Попытка перезапуска...")
                success = manager.restart_system()
                
                if success:
                    print("✅ Система перезапущена")
                    
                    # Повторная проверка
                    print("\n🔍 Повторная проверка...")
                    time.sleep(5)  # Даем время на запуск
                    
                    new_results = manager.perform_full_check()
                    if new_results['overall_status']:
                        print("✅ Система работает после перезапуска")
                    else:
                        print("❌ Проблемы остались после перезапуска")
                        sys.exit(1)
                else:
                    print("❌ Не удалось перезапустить систему")
                    sys.exit(1)
                    
        else:
            # По умолчанию - проверка
            print("🔍 Проверка состояния системы...")
            
            results = manager.perform_full_check()
            report = manager.generate_status_report(results)
            print(report)
            
            if args.save_report:
                manager.save_status_report(report)
            
            if not results['overall_status']:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Операция прервана пользователем")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()