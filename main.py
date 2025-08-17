#!/usr/bin/env python3
"""
Главный модуль RAG-системы для поиска услуг салона красоты.
Координирует работу поискового и консультационного модулей.
"""

import sys
from typing import Optional, Dict, Any

from beauty_salon_rag.modules.search_module import SearchModule, SearchModuleError
from beauty_salon_rag.modules.consultation_module import ConsultationModule, ConsultationModuleError
from beauty_salon_rag.config import config
from beauty_salon_rag.logger import get_logger, log_operation, setup_logging
from beauty_salon_rag.error_handler import handle_error, BeautySalonError, ErrorSeverity


class BeautySalonRAG:
    """Главный класс RAG-системы салона красоты."""
    
    def __init__(self, base_path: str = "."):
        """
        Инициализация RAG-системы.
        
        Args:
            base_path: Базовый путь к файлам данных
        """
        self.base_path = base_path
        self.logger = get_logger(__name__)
        
        # Получение режима работы из конфигурации
        self.app_mode = config.get_app_mode()
        self.performance_mode = config.get_performance_mode()
        
        try:
            # Инициализация модулей
            self.search_module = SearchModule(base_path)
            self.consultation_module = ConsultationModule(base_path)
            
            # Оптимизация производительности в зависимости от режима
            self._optimize_performance()
            
            self.logger.info(f"RAG-система салона красоты инициализирована успешно (режим: {self.app_mode}, производительность: {self.performance_mode})")
            
        except (SearchModuleError, ConsultationModuleError) as e:
            self.logger.error(f"Ошибка инициализации системы: {e}")
            raise
    
    @log_operation("process_query")
    def process_query(self, query: str) -> str:
        """
        Обрабатывает пользовательский запрос через двухэтапную систему.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            Ответ системы
        """
        if not isinstance(query, str) or not query.strip():
            return "Пожалуйста, введите корректный запрос."
        
        query = query.strip()
        self.logger.info(f"Обработка запроса: '{query}'")
        
        try:
            # Этап 1: Поиск релевантных услуг
            self.logger.debug("Этап 1: Поиск релевантных услуг")
            service_ids = self.search_module.find_services(query)
            
            if not service_ids:
                self.logger.info("Релевантные услуги не найдены")
                return self._generate_no_results_response(query)
            
            self.logger.info(f"Найдено {len(service_ids)} релевантных услуг: {service_ids}")
            
            # Этап 2: Генерация консультационного ответа
            self.logger.debug("Этап 2: Генерация консультационного ответа")
            response = self.consultation_module.generate_consultation_response(query, service_ids)
            
            self.logger.info("Запрос обработан успешно")
            return response
            
        except Exception as e:
            # Используем централизованную обработку ошибок
            user_message = handle_error(e, context={"query": query, "operation": "process_query"})
            return user_message
    
    def _generate_no_results_response(self, query: str) -> str:
        """
        Генерирует ответ когда услуги не найдены.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            Ответ об отсутствии результатов
        """
        return (
            f"К сожалению, по вашему запросу '{query}' не найдено подходящих услуг. "
            "Возможно, стоит уточнить запрос или обратиться к нашему администратору "
            "для получения более подробной консультации о доступных процедурах.\n\n"
            "Попробуйте использовать другие ключевые слова или задать более конкретный вопрос."
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Получает статус работоспособности системы.
        
        Returns:
            Словарь со статусом компонентов системы
        """
        status = {
            "system": "Beauty Salon RAG",
            "search_module": False,
            "consultation_module": False,
            "overall_status": False
        }
        
        try:
            # Проверка поискового модуля
            status["search_module"] = self.search_module.health_check()
            
            # Проверка консультационного модуля  
            status["consultation_module"] = self.consultation_module.health_check()
            
            # Общий статус
            status["overall_status"] = status["search_module"] and status["consultation_module"]
            
            self.logger.info(f"Статус системы: {status}")
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки статуса системы: {e}")
        
        return status
    
    def _optimize_performance(self):
        """Оптимизирует производительность системы в зависимости от режима."""
        try:
            # Оптимизация GPT клиентов в модулях
            if hasattr(self.search_module, 'gpt_client'):
                self.search_module.gpt_client.optimize_for_performance(self.performance_mode)
            
            if hasattr(self.consultation_module, 'gpt_client'):
                self.consultation_module.gpt_client.optimize_for_performance(self.performance_mode)
            
            self.logger.info(f"Система оптимизирована для режима: {self.performance_mode}")
            
        except Exception as e:
            self.logger.warning(f"Не удалось оптимизировать производительность: {e}")
    
    def get_performance_info(self) -> Dict[str, Any]:
        """
        Получает информацию о производительности системы.
        
        Returns:
            Информация о производительности
        """
        info = {
            "app_mode": self.app_mode,
            "performance_mode": self.performance_mode,
            "caching_enabled": config.is_caching_enabled(),
            "interactive_mode": config.is_interactive_mode(),
            "debug_mode": config.is_debug_mode()
        }
        
        # Добавляем метрики производительности GPT клиентов
        try:
            if hasattr(self.search_module, 'gpt_client'):
                info["search_gpt_metrics"] = self.search_module.gpt_client.get_performance_metrics()
            
            if hasattr(self.consultation_module, 'gpt_client'):
                info["consultation_gpt_metrics"] = self.consultation_module.gpt_client.get_performance_metrics()
                
        except Exception as e:
            self.logger.warning(f"Не удалось получить метрики производительности: {e}")
        
        return info
    
    def start_chat(self):
        """Запускает интерактивный чат-интерфейс."""
        # Проверяем, включен ли интерактивный режим
        if not config.is_interactive_mode():
            print("❌ Интерактивный режим отключен в конфигурации")
            return
        
        print("🌸 Добро пожаловать в систему поиска услуг салона красоты! 🌸")
        print("Я помогу вам найти подходящие процедуры и записаться к мастеру.")
        print("Введите 'помощь' для получения справки или 'выход' для завершения работы.")
        
        # Показываем информацию о режиме работы
        if config.is_debug_mode():
            print(f"🔧 Режим работы: {self.app_mode} | Производительность: {self.performance_mode}")
        print()
        
        # Проверка статуса системы при запуске
        status = self.get_system_status()
        if not status["overall_status"]:
            print("⚠️  Внимание: Обнаружены проблемы с системой. Некоторые функции могут работать некорректно.")
            if not status["search_module"]:
                print("   - Поисковый модуль недоступен")
            if not status["consultation_module"]:
                print("   - Консультационный модуль недоступен")
            print()
        
        while True:
            try:
                # Получение пользовательского ввода
                user_input = input("Ваш вопрос: ").strip()
                
                if not user_input:
                    continue
                
                # Обработка команд
                if user_input.lower() in ['выход', 'exit', 'quit', 'q']:
                    print("До свидания! Будем рады видеть вас снова! 👋")
                    break
                
                elif user_input.lower() in ['помощь', 'help', 'h']:
                    self._show_help()
                    continue
                
                elif user_input.lower() in ['статус', 'status']:
                    self._show_status()
                    continue
                
                elif user_input.lower() in ['производительность', 'performance', 'perf']:
                    self._show_performance()
                    continue
                
                # Обработка запроса
                print("\n🔍 Ищу подходящие услуги...")
                response = self.process_query(user_input)
                print(f"\n💬 {response}\n")
                print("-" * 80)
                
            except KeyboardInterrupt:
                print("\n\nДо свидания! Будем рады видеть вас снова! 👋")
                break
                
            except Exception as e:
                self.logger.error(f"Ошибка в чат-интерфейсе: {e}")
                print("Извините, произошла ошибка. Попробуйте еще раз.")
    
    def _show_help(self):
        """Показывает справочную информацию."""
        help_text = """
📋 Справка по использованию системы:

🔍 Поиск услуг:
   • Опишите желаемую процедуру: "массаж лица", "чистка кожи"
   • Укажите проблему: "акне", "морщины", "сухость кожи"
   • Спросите о категории: "какие есть процедуры для лица?"

💬 Консультация:
   • Задайте вопрос о процедуре: "что такое RF-лифтинг?"
   • Узнайте о показаниях: "поможет ли пилинг от пигментации?"
   • Спросите о противопоказаниях: "можно ли делать массаж при куперозе?"

📅 Запись к мастеру:
   • "Хочу записаться на массаж лица"
   • "Какие мастера делают чистку?"
   • "Когда можно записаться на процедуру?"

🎯 Команды:
   • 'помощь' или 'help' - показать эту справку
   • 'статус' или 'status' - проверить работу системы
   • 'производительность' или 'performance' - показать метрики производительности
   • 'выход' или 'exit' - завершить работу

💡 Советы:
   • Формулируйте запросы четко и конкретно
   • Используйте ключевые слова, связанные с косметологией
   • Не стесняйтесь задавать уточняющие вопросы
        """
        print(help_text)
    
    def _show_status(self):
        """Показывает статус системы."""
        status = self.get_system_status()
        
        print("\n📊 Статус системы:")
        print(f"   Поисковый модуль: {'✅ Работает' if status['search_module'] else '❌ Недоступен'}")
        print(f"   Консультационный модуль: {'✅ Работает' if status['consultation_module'] else '❌ Недоступен'}")
        print(f"   Общий статус: {'✅ Система работает' if status['overall_status'] else '❌ Есть проблемы'}")
        print()
    
    def _show_performance(self):
        """Показывает информацию о производительности системы."""
        perf_info = self.get_performance_info()
        
        print("\n⚡ Информация о производительности:")
        print(f"   Режим приложения: {perf_info['app_mode']}")
        print(f"   Режим производительности: {perf_info['performance_mode']}")
        print(f"   Кэширование: {'✅ Включено' if perf_info['caching_enabled'] else '❌ Отключено'}")
        print(f"   Интерактивный режим: {'✅ Включен' if perf_info['interactive_mode'] else '❌ Отключен'}")
        print(f"   Режим отладки: {'✅ Включен' if perf_info['debug_mode'] else '❌ Отключен'}")
        
        # Показываем метрики GPT клиентов если доступны
        if 'search_gpt_metrics' in perf_info:
            cache_stats = perf_info['search_gpt_metrics'].get('cache_stats', {})
            print(f"\n📊 Метрики поискового GPT:")
            print(f"   Записей в кэше: {cache_stats.get('valid_entries', 0)}")
            print(f"   Коэффициент попаданий в кэш: {cache_stats.get('cache_hit_rate', 0):.1%}")
        
        if 'consultation_gpt_metrics' in perf_info:
            cache_stats = perf_info['consultation_gpt_metrics'].get('cache_stats', {})
            print(f"\n📊 Метрики консультационного GPT:")
            print(f"   Записей в кэше: {cache_stats.get('valid_entries', 0)}")
            print(f"   Коэффициент попаданий в кэш: {cache_stats.get('cache_hit_rate', 0):.1%}")
        
        print()


def main():
    """Главная функция приложения."""
    try:
        # Инициализация системы логирования
        setup_logging()
        
        # Создание и запуск RAG-системы
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
        sys.exit(0)
        
    except Exception as e:
        # Используем централизованную обработку ошибок
        user_message = handle_error(e, context={"operation": "main_startup"})
        print(f"Критическая ошибка при запуске системы: {user_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()