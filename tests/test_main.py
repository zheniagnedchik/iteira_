"""
Тесты для главного модуля RAG-системы салона красоты.
"""

import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

from main import BeautySalonRAG, main
from beauty_salon_rag.modules.search_module import SearchModuleError
from beauty_salon_rag.modules.consultation_module import ConsultationModuleError
from beauty_salon_rag.error_handler import BeautySalonError


class TestBeautySalonRAG:
    """Тесты для класса BeautySalonRAG."""
    
    @pytest.fixture
    def mock_modules(self):
        """Фикстура с мок-объектами модулей."""
        with patch('main.SearchModule') as mock_search, \
             patch('main.ConsultationModule') as mock_consultation:
            
            mock_search_instance = Mock()
            mock_consultation_instance = Mock()
            
            mock_search.return_value = mock_search_instance
            mock_consultation.return_value = mock_consultation_instance
            
            yield {
                'search_class': mock_search,
                'consultation_class': mock_consultation,
                'search_instance': mock_search_instance,
                'consultation_instance': mock_consultation_instance
            }
    
    def test_init_success(self, mock_modules):
        """Тест успешной инициализации RAG-системы."""
        rag_system = BeautySalonRAG("/test/path")
        
        assert rag_system.base_path == "/test/path"
        assert rag_system.search_module is not None
        assert rag_system.consultation_module is not None
        
        mock_modules['search_class'].assert_called_once_with("/test/path")
        mock_modules['consultation_class'].assert_called_once_with("/test/path")
    
    def test_init_search_module_error(self, mock_modules):
        """Тест ошибки инициализации поискового модуля."""
        mock_modules['search_class'].side_effect = SearchModuleError("Search error")
        
        with pytest.raises(SearchModuleError):
            BeautySalonRAG()
    
    def test_init_consultation_module_error(self, mock_modules):
        """Тест ошибки инициализации консультационного модуля."""
        mock_modules['consultation_class'].side_effect = ConsultationModuleError("Consultation error")
        
        with pytest.raises(ConsultationModuleError):
            BeautySalonRAG()
    
    def test_process_query_success(self, mock_modules):
        """Тест успешной обработки запроса."""
        # Настройка моков
        mock_modules['search_instance'].find_services.return_value = ["service-1", "service-2"]
        mock_modules['consultation_instance'].generate_consultation_response.return_value = "Тестовый ответ"
        
        rag_system = BeautySalonRAG()
        result = rag_system.process_query("массаж лица")
        
        assert result == "Тестовый ответ"
        mock_modules['search_instance'].find_services.assert_called_once_with("массаж лица")
        mock_modules['consultation_instance'].generate_consultation_response.assert_called_once_with(
            "массаж лица", ["service-1", "service-2"]
        )
    
    def test_process_query_empty_string(self, mock_modules):
        """Тест обработки пустого запроса."""
        rag_system = BeautySalonRAG()
        
        result = rag_system.process_query("")
        assert "Пожалуйста, введите корректный запрос" in result
        
        result = rag_system.process_query("   ")
        assert "Пожалуйста, введите корректный запрос" in result
    
    def test_process_query_invalid_type(self, mock_modules):
        """Тест обработки запроса некорректного типа."""
        rag_system = BeautySalonRAG()
        
        result = rag_system.process_query(None)
        assert "Пожалуйста, введите корректный запрос" in result
        
        result = rag_system.process_query(123)
        assert "Пожалуйста, введите корректный запрос" in result
    
    def test_process_query_no_services_found(self, mock_modules):
        """Тест обработки запроса когда услуги не найдены."""
        mock_modules['search_instance'].find_services.return_value = []
        
        rag_system = BeautySalonRAG()
        result = rag_system.process_query("несуществующая услуга")
        
        assert "не найдено подходящих услуг" in result
        assert "несуществующая услуга" in result
        mock_modules['consultation_instance'].generate_consultation_response.assert_not_called()
    
    @patch('main.handle_error')
    def test_process_query_search_error(self, mock_handle_error, mock_modules):
        """Тест обработки ошибки поиска."""
        mock_modules['search_instance'].find_services.side_effect = SearchModuleError("Search failed")
        mock_handle_error.return_value = "Ошибка поиска"
        
        rag_system = BeautySalonRAG()
        result = rag_system.process_query("тест")
        
        assert result == "Ошибка поиска"
        mock_handle_error.assert_called_once()
    
    @patch('main.handle_error')
    def test_process_query_consultation_error(self, mock_handle_error, mock_modules):
        """Тест обработки ошибки консультации."""
        mock_modules['search_instance'].find_services.return_value = ["service-1"]
        mock_modules['consultation_instance'].generate_consultation_response.side_effect = \
            ConsultationModuleError("Consultation failed")
        mock_handle_error.return_value = "Ошибка консультации"
        
        rag_system = BeautySalonRAG()
        result = rag_system.process_query("тест")
        
        assert result == "Ошибка консультации"
        mock_handle_error.assert_called_once()
    
    def test_generate_no_results_response(self, mock_modules):
        """Тест генерации ответа об отсутствии результатов."""
        rag_system = BeautySalonRAG()
        result = rag_system._generate_no_results_response("тестовый запрос")
        
        assert "тестовый запрос" in result
        assert "не найдено подходящих услуг" in result
        assert "уточнить запрос" in result
    
    def test_get_system_status_all_healthy(self, mock_modules):
        """Тест получения статуса системы когда все модули работают."""
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        status = rag_system.get_system_status()
        
        assert status['system'] == "Beauty Salon RAG"
        assert status['search_module'] is True
        assert status['consultation_module'] is True
        assert status['overall_status'] is True
    
    def test_get_system_status_search_unhealthy(self, mock_modules):
        """Тест получения статуса системы когда поисковый модуль не работает."""
        mock_modules['search_instance'].health_check.return_value = False
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        status = rag_system.get_system_status()
        
        assert status['search_module'] is False
        assert status['consultation_module'] is True
        assert status['overall_status'] is False
    
    def test_get_system_status_consultation_unhealthy(self, mock_modules):
        """Тест получения статуса системы когда консультационный модуль не работает."""
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = False
        
        rag_system = BeautySalonRAG()
        status = rag_system.get_system_status()
        
        assert status['search_module'] is True
        assert status['consultation_module'] is False
        assert status['overall_status'] is False
    
    def test_get_system_status_exception(self, mock_modules):
        """Тест получения статуса системы при исключении."""
        mock_modules['search_instance'].health_check.side_effect = Exception("Health check failed")
        
        rag_system = BeautySalonRAG()
        status = rag_system.get_system_status()
        
        assert status['overall_status'] is False
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_exit_command(self, mock_print, mock_input, mock_modules):
        """Тест команды выхода в чат-интерфейсе."""
        mock_input.side_effect = ['выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что было выведено приветствие и прощание
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Добро пожаловать" in call for call in print_calls)
        assert any("До свидания" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_help_command(self, mock_print, mock_input, mock_modules):
        """Тест команды помощи в чат-интерфейсе."""
        mock_input.side_effect = ['помощь', 'выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что была показана справка
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Справка по использованию" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_status_command(self, mock_print, mock_input, mock_modules):
        """Тест команды статуса в чат-интерфейсе."""
        mock_input.side_effect = ['статус', 'выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что был показан статус
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Статус системы" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_query_processing(self, mock_print, mock_input, mock_modules):
        """Тест обработки запроса в чат-интерфейсе."""
        mock_input.side_effect = ['массаж лица', 'выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        mock_modules['search_instance'].find_services.return_value = ["service-1"]
        mock_modules['consultation_instance'].generate_consultation_response.return_value = "Ответ о массаже"
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что запрос был обработан
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Ищу подходящие услуги" in call for call in print_calls)
        assert any("Ответ о массаже" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_empty_input(self, mock_print, mock_input, mock_modules):
        """Тест пустого ввода в чат-интерфейсе."""
        mock_input.side_effect = ['', '   ', 'выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Пустые вводы должны игнорироваться
        mock_modules['search_instance'].find_services.assert_not_called()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_keyboard_interrupt(self, mock_print, mock_input, mock_modules):
        """Тест прерывания чата клавиатурой."""
        mock_input.side_effect = KeyboardInterrupt()
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что было выведено прощание
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("До свидания" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_unhealthy_system(self, mock_print, mock_input, mock_modules):
        """Тест запуска чата с неработающей системой."""
        mock_input.side_effect = ['выход']
        mock_modules['search_instance'].health_check.return_value = False
        mock_modules['consultation_instance'].health_check.return_value = False
        
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверяем, что было показано предупреждение
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Внимание: Обнаружены проблемы" in call for call in print_calls)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_start_chat_exception_handling(self, mock_print, mock_input, mock_modules):
        """Тест обработки исключений в чат-интерфейсе."""
        mock_input.side_effect = ['тест', 'выход']
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = True
        
        # Мокаем process_query чтобы он вызывал исключение
        rag_system = BeautySalonRAG()
        with patch.object(rag_system, 'process_query', side_effect=Exception("Test error")):
            rag_system.start_chat()
        
        # Проверяем, что ошибка была обработана
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("произошла ошибка" in call for call in print_calls)
    
    def test_show_help(self, mock_modules):
        """Тест показа справки."""
        rag_system = BeautySalonRAG()
        
        with patch('builtins.print') as mock_print:
            rag_system._show_help()
            
            # Проверяем, что справка была выведена
            print_calls = []
            for call in mock_print.call_args_list:
                if call[0]:  # Проверяем, что есть позиционные аргументы
                    print_calls.append(str(call[0][0]))
            assert any("Справка по использованию" in call for call in print_calls)
    
    def test_show_status(self, mock_modules):
        """Тест показа статуса."""
        mock_modules['search_instance'].health_check.return_value = True
        mock_modules['consultation_instance'].health_check.return_value = False
        
        rag_system = BeautySalonRAG()
        
        with patch('builtins.print') as mock_print:
            rag_system._show_status()
            
            # Проверяем, что статус был выведен
            print_calls = []
            for call in mock_print.call_args_list:
                if call[0]:  # Проверяем, что есть позиционные аргументы
                    print_calls.append(str(call[0][0]))
            assert any("Статус системы" in call for call in print_calls)
            assert any("Работает" in call for call in print_calls)
            assert any("Недоступен" in call for call in print_calls)


class TestMainFunction:
    """Тесты для главной функции приложения."""
    
    @patch('main.setup_logging')
    @patch('main.BeautySalonRAG')
    def test_main_success(self, mock_rag_class, mock_setup_logging):
        """Тест успешного запуска главной функции."""
        mock_rag_instance = Mock()
        mock_rag_class.return_value = mock_rag_instance
        
        main()
        
        mock_setup_logging.assert_called_once()
        mock_rag_class.assert_called_once()
        mock_rag_instance.start_chat.assert_called_once()
    
    @patch('main.setup_logging')
    @patch('main.BeautySalonRAG')
    @patch('sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_rag_class, mock_setup_logging):
        """Тест прерывания главной функции клавиатурой."""
        mock_rag_class.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_exit.assert_called_once_with(0)
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("прервана пользователем" in call for call in print_calls)
    
    @patch('main.setup_logging')
    @patch('main.BeautySalonRAG')
    @patch('main.handle_error')
    @patch('sys.exit')
    def test_main_exception(self, mock_exit, mock_handle_error, mock_rag_class, mock_setup_logging):
        """Тест обработки исключения в главной функции."""
        mock_rag_class.side_effect = Exception("Critical error")
        mock_handle_error.return_value = "Критическая ошибка"
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_handle_error.assert_called_once()
        mock_exit.assert_called_once_with(1)
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Критическая ошибка" in call for call in print_calls)


class TestMainIntegration:
    """Интеграционные тесты для главного модуля."""
    
    @patch('main.SearchModule')
    @patch('main.ConsultationModule')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_full_workflow_integration(self, mock_print, mock_input, mock_consultation_class, mock_search_class):
        """Интеграционный тест полного рабочего процесса."""
        # Настройка моков
        mock_search_instance = Mock()
        mock_consultation_instance = Mock()
        
        mock_search_class.return_value = mock_search_instance
        mock_consultation_class.return_value = mock_consultation_instance
        
        mock_search_instance.health_check.return_value = True
        mock_consultation_instance.health_check.return_value = True
        mock_search_instance.find_services.return_value = ["service-1", "service-2"]
        mock_consultation_instance.generate_consultation_response.return_value = "Подробный ответ о процедурах"
        
        # Симуляция пользовательского ввода
        mock_input.side_effect = ['массаж лица для омоложения', 'выход']
        
        # Запуск системы
        rag_system = BeautySalonRAG()
        rag_system.start_chat()
        
        # Проверка вызовов
        mock_search_instance.find_services.assert_called_with('массаж лица для омоложения')
        mock_consultation_instance.generate_consultation_response.assert_called_with(
            'массаж лица для омоложения', ["service-1", "service-2"]
        )
        
        # Проверка вывода
        print_calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Проверяем, что есть позиционные аргументы
                print_calls.append(str(call[0][0]))
        assert any("Добро пожаловать" in call for call in print_calls)
        assert any("Подробный ответ о процедурах" in call for call in print_calls)
        assert any("До свидания" in call for call in print_calls)