"""
Тесты для централизованной системы логирования.
"""

import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from beauty_salon_rag.logger import (
    LoggerManager, OperationLogger, ColoredFormatter, StructuredFormatter,
    get_logger, get_operation_logger, get_error_logger, get_performance_logger,
    log_operation, setup_logging, shutdown_logging
)


class TestColoredFormatter:
    """Тесты для цветного форматтера."""
    
    def test_colored_formatter_adds_colors(self):
        """Тест добавления цветов к уровням логирования."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        # Создаем тестовую запись
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Проверяем, что цветовые коды добавлены
        assert '\033[32m' in formatted  # Green for INFO
        assert '\033[0m' in formatted   # Reset
        assert 'Test message' in formatted
    
    def test_colored_formatter_different_levels(self):
        """Тест цветов для разных уровней логирования."""
        formatter = ColoredFormatter('%(levelname)s')
        
        levels_and_colors = [
            (logging.DEBUG, '\033[36m'),    # Cyan
            (logging.INFO, '\033[32m'),     # Green
            (logging.WARNING, '\033[33m'),  # Yellow
            (logging.ERROR, '\033[31m'),    # Red
            (logging.CRITICAL, '\033[35m'), # Magenta
        ]
        
        for level, expected_color in levels_and_colors:
            record = logging.LogRecord(
                name="test", level=level, pathname="", lineno=0,
                msg="Test", args=(), exc_info=None
            )
            formatted = formatter.format(record)
            assert expected_color in formatted


class TestStructuredFormatter:
    """Тесты для структурированного форматтера."""
    
    def test_structured_formatter_basic(self):
        """Тест базового структурированного форматирования."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test.module", level=logging.INFO, pathname="/path/test.py",
            lineno=42, msg="Test message", args=(), exc_info=None
        )
        record.module = "test"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        
        # Проверяем, что это валидный Python dict string
        log_dict = eval(formatted)
        
        assert log_dict['level'] == 'INFO'
        assert log_dict['logger'] == 'test.module'
        assert log_dict['message'] == 'Test message'
        assert log_dict['module'] == 'test'
        assert log_dict['function'] == 'test_function'
        assert log_dict['line'] == 42
        assert 'timestamp' in log_dict
    
    def test_structured_formatter_with_extra_fields(self):
        """Тест структурированного форматирования с дополнительными полями."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Error occurred", args=(), exc_info=None
        )
        record.module = "test"
        record.funcName = "test_func"
        record.error_details = {"error_type": "TestError"}
        record.user_id = "user123"
        record.query = "test query"
        record.execution_time = 1.5
        
        formatted = formatter.format(record)
        log_dict = eval(formatted)
        
        assert log_dict['error_details'] == {"error_type": "TestError"}
        assert log_dict['user_id'] == "user123"
        assert log_dict['query'] == "test query"
        assert log_dict['execution_time'] == 1.5


class TestLoggerManager:
    """Тесты для менеджера логгеров."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        # Используем временную директорию для логов
        self.temp_dir = tempfile.mkdtemp()
        self.logger_manager = LoggerManager()
        self.logger_manager.log_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.logger_manager.shutdown()
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_logger_basic(self):
        """Тест получения базового логгера."""
        logger = self.logger_manager.get_logger("test.logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.logger"
        assert len(logger.handlers) > 0
    
    def test_get_logger_console_only(self):
        """Тест логгера только с консольным выводом."""
        logger = self.logger_manager.get_logger(
            "test.console", 
            log_to_file=False, 
            log_to_console=True
        )
        
        # Должен быть только консольный обработчик
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        
        assert len(console_handlers) >= 1
        assert len(file_handlers) == 0
    
    def test_get_logger_file_only(self):
        """Тест логгера только с файловым выводом."""
        logger = self.logger_manager.get_logger(
            "test.file", 
            log_to_file=True, 
            log_to_console=False
        )
        
        # Должен быть только файловый обработчик
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)]
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        
        assert len(console_handlers) == 0
        assert len(file_handlers) >= 1
    
    def test_get_logger_structured(self):
        """Тест логгера со структурированным форматированием."""
        logger = self.logger_manager.get_logger(
            "test.structured", 
            structured_logging=True
        )
        
        # Проверяем, что используется структурированный форматтер
        for handler in logger.handlers:
            assert isinstance(handler.formatter, StructuredFormatter)
    
    def test_logger_caching(self):
        """Тест кэширования логгеров."""
        logger1 = self.logger_manager.get_logger("test.cache")
        logger2 = self.logger_manager.get_logger("test.cache")
        
        # Должен вернуться тот же объект
        assert logger1 is logger2
    
    def test_create_specialized_loggers(self):
        """Тест создания специализированных логгеров."""
        operation_logger = self.logger_manager.create_operation_logger("test_op")
        error_logger = self.logger_manager.create_error_logger()
        performance_logger = self.logger_manager.create_performance_logger()
        
        assert "operations.test_op" in operation_logger.name
        assert "errors" in error_logger.name
        assert "performance" in performance_logger.name
    
    def test_shutdown(self):
        """Тест корректного завершения работы."""
        logger = self.logger_manager.get_logger("test.shutdown")
        
        # Проверяем, что логгер создан
        assert "test.shutdown" in self.logger_manager.loggers
        
        self.logger_manager.shutdown()
        
        # После shutdown логгеры должны быть очищены
        assert len(self.logger_manager.loggers) == 0


class TestOperationLogger:
    """Тесты для логгера операций."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.operation_logger = OperationLogger(
            self.mock_logger, 
            "test_operation"
        )
    
    def test_operation_logger_success(self):
        """Тест успешного выполнения операции."""
        with self.operation_logger:
            pass  # Успешное выполнение
        
        # Проверяем, что логирование началось и завершилось
        assert self.mock_logger.info.call_count == 2
        
        # Первый вызов - начало операции
        start_call = self.mock_logger.info.call_args_list[0]
        assert "Starting operation: test_operation" in start_call[0][0]
        
        # Второй вызов - завершение операции
        end_call = self.mock_logger.info.call_args_list[1]
        assert "Operation completed: test_operation" in end_call[0][0]
        assert end_call[1]['extra']['status'] == 'success'
    
    def test_operation_logger_with_exception(self):
        """Тест операции с исключением."""
        with pytest.raises(ValueError):
            with self.operation_logger:
                raise ValueError("Test error")
        
        # Проверяем логирование ошибки
        assert self.mock_logger.info.call_count == 1  # Только начало
        assert self.mock_logger.error.call_count == 1  # Ошибка
        
        error_call = self.mock_logger.error.call_args_list[0]
        assert "Operation failed: test_operation" in error_call[0][0]
        assert error_call[1]['extra']['status'] == 'error'
        assert error_call[1]['extra']['error_type'] == 'ValueError'
    
    def test_operation_logger_with_context(self):
        """Тест операции с контекстом."""
        with self.operation_logger as op_logger:
            op_logger.add_context(user_id="123", query="test")
            op_logger.log_step("validation", field="input")
        
        # Проверяем, что контекст добавлен
        end_call = self.mock_logger.info.call_args_list[1]
        extra = end_call[1]['extra']
        assert extra['user_id'] == "123"
        assert extra['query'] == "test"
        
        # Проверяем логирование шага
        assert self.mock_logger.debug.call_count == 1
        step_call = self.mock_logger.debug.call_args_list[0]
        assert "test_operation -> validation" in step_call[0][0]


class TestLogOperationDecorator:
    """Тесты для декоратора логирования операций."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.mock_logger = Mock(spec=logging.Logger)
    
    def test_log_operation_decorator_success(self):
        """Тест успешного выполнения функции с декоратором."""
        @log_operation("test_function", logger=self.mock_logger)
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        
        assert result == 5
        assert self.mock_logger.info.call_count == 2  # Начало и конец
    
    def test_log_operation_decorator_with_exception(self):
        """Тест функции с исключением и декоратором."""
        @log_operation("test_function", logger=self.mock_logger)
        def test_func():
            raise RuntimeError("Test error")
        
        with pytest.raises(RuntimeError):
            test_func()
        
        assert self.mock_logger.info.call_count == 1   # Только начало
        assert self.mock_logger.error.call_count == 1  # Ошибка
    
    def test_log_operation_decorator_with_args_logging(self):
        """Тест декоратора с логированием аргументов."""
        @log_operation("test_function", logger=self.mock_logger, log_args=True)
        def test_func(x, y=None):
            return x
        
        test_func(1, y=2)
        
        # Проверяем, что информация об аргументах логируется
        end_call = self.mock_logger.info.call_args_list[1]
        extra = end_call[1]['extra']
        assert extra['args_count'] == 1
        assert 'y' in extra['kwargs_keys']


class TestGlobalFunctions:
    """Тесты для глобальных функций логирования."""
    
    def test_get_logger_function(self):
        """Тест глобальной функции get_logger."""
        logger = get_logger("test.global")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.global"
    
    def test_specialized_logger_functions(self):
        """Тест функций для получения специализированных логгеров."""
        op_logger = get_operation_logger("test_operation")
        error_logger = get_error_logger()
        perf_logger = get_performance_logger()
        
        assert isinstance(op_logger, logging.Logger)
        assert isinstance(error_logger, logging.Logger)
        assert isinstance(perf_logger, logging.Logger)
        
        assert "operations" in op_logger.name
        assert "errors" in error_logger.name
        assert "performance" in perf_logger.name
    
    @patch('beauty_salon_rag.logger.logger_manager')
    def test_setup_and_shutdown_logging(self, mock_manager):
        """Тест функций setup и shutdown."""
        setup_logging()
        shutdown_logging()
        
        # Проверяем, что методы менеджера были вызваны
        mock_manager.shutdown.assert_called_once()


class TestLoggingIntegration:
    """Интеграционные тесты системы логирования."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_logging_creates_files(self):
        """Тест создания файлов логов."""
        manager = LoggerManager()
        manager.log_dir = Path(self.temp_dir)
        
        logger = manager.get_logger("test.file.creation", log_to_file=True)
        logger.info("Test message")
        
        # Проверяем, что файл создан
        log_files = list(Path(self.temp_dir).glob("*.log"))
        assert len(log_files) > 0
        
        # Проверяем содержимое файла
        log_file = log_files[0]
        content = log_file.read_text(encoding='utf-8')
        assert "Test message" in content
        
        manager.shutdown()
    
    def test_log_rotation(self):
        """Тест ротации логов."""
        manager = LoggerManager()
        manager.log_dir = Path(self.temp_dir)
        
        logger = manager.get_logger("test.rotation", log_to_file=True)
        
        # Записываем много данных для проверки ротации
        large_message = "x" * 1000
        for i in range(100):
            logger.info(f"Message {i}: {large_message}")
        
        # Проверяем, что файлы созданы
        log_files = list(Path(self.temp_dir).glob("*.log*"))
        assert len(log_files) > 0
        
        manager.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])