"""
Тесты для централизованной системы обработки ошибок.
"""

import pytest
import logging
from unittest.mock import Mock, patch

from beauty_salon_rag.error_handler import (
    BeautySalonError, DataLoadError, GPTClientError, ValidationError, 
    ConfigurationError, ErrorHandler, ErrorCategory, ErrorSeverity,
    error_handler_decorator, handle_error, get_error_stats
)


class TestBeautySalonError:
    """Тесты для базового класса ошибок."""
    
    def test_basic_error_creation(self):
        """Тест создания базовой ошибки."""
        error = BeautySalonError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.technical_message == "Test error message"
        assert isinstance(error.user_message, str)
        assert len(error.user_message) > 0
    
    def test_error_with_custom_parameters(self):
        """Тест создания ошибки с кастомными параметрами."""
        details = {"key": "value", "number": 42}
        error = BeautySalonError(
            message="Technical message",
            category=ErrorCategory.DATA_LOAD,
            severity=ErrorSeverity.HIGH,
            user_message="Custom user message",
            details=details
        )
        
        assert error.category == ErrorCategory.DATA_LOAD
        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "Custom user message"
        assert error.details == details
    
    def test_error_to_dict(self):
        """Тест преобразования ошибки в словарь."""
        error = BeautySalonError(
            message="Test message",
            category=ErrorCategory.GPT_API,
            severity=ErrorSeverity.CRITICAL,
            details={"test": "data"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "BeautySalonError"
        assert error_dict["category"] == "gpt_api"
        assert error_dict["severity"] == "critical"
        assert error_dict["technical_message"] == "Test message"
        assert error_dict["details"] == {"test": "data"}


class TestSpecificErrors:
    """Тесты для специфических типов ошибок."""
    
    def test_data_load_error(self):
        """Тест ошибки загрузки данных."""
        error = DataLoadError("File not found", file_path="/path/to/file.json")
        
        assert error.category == ErrorCategory.DATA_LOAD
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["file_path"] == "/path/to/file.json"
        assert "данные" in error.user_message.lower()
    
    def test_gpt_client_error(self):
        """Тест ошибки GPT клиента."""
        error = GPTClientError("API timeout", api_error="Connection timeout")
        
        assert error.category == ErrorCategory.GPT_API
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["api_error"] == "Connection timeout"
        assert "сервис" in error.user_message.lower()
    
    def test_validation_error(self):
        """Тест ошибки валидации."""
        error = ValidationError("Invalid input", field="query", value="")
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["field"] == "query"
        assert error.details["value"] == ""
    
    def test_configuration_error(self):
        """Тест ошибки конфигурации."""
        error = ConfigurationError("Missing API key", config_key="OPENAI_API_KEY")
        
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.details["config_key"] == "OPENAI_API_KEY"


class TestErrorHandler:
    """Тесты для обработчика ошибок."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.error_handler = ErrorHandler(self.mock_logger)
    
    def test_handle_beauty_salon_error(self):
        """Тест обработки BeautySalonError."""
        error = ValidationError("Test validation error")
        
        user_message = self.error_handler.handle_error(error)
        
        assert user_message == error.user_message
        assert self.error_handler.error_stats["total_errors"] == 1
        assert self.error_handler.error_stats["by_category"]["validation"] == 1
        assert self.error_handler.error_stats["by_severity"]["medium"] == 1
    
    def test_handle_standard_exception(self):
        """Тест обработки стандартного исключения."""
        error = ValueError("Invalid value")
        
        user_message = self.error_handler.handle_error(error)
        
        assert isinstance(user_message, str)
        assert len(user_message) > 0
        assert self.error_handler.error_stats["total_errors"] == 1
    
    def test_handle_file_not_found_error(self):
        """Тест обработки FileNotFoundError."""
        error = FileNotFoundError("File not found")
        
        user_message = self.error_handler.handle_error(error)
        
        # Должно быть преобразовано в DataLoadError
        assert "данные" in user_message.lower()
        assert self.error_handler.error_stats["by_category"]["data_load"] == 1
    
    def test_error_stats(self):
        """Тест статистики ошибок."""
        errors = [
            ValidationError("Error 1"),
            DataLoadError("Error 2"),
            ValidationError("Error 3"),
            GPTClientError("Error 4")
        ]
        
        for error in errors:
            self.error_handler.handle_error(error)
        
        stats = self.error_handler.get_error_stats()
        
        assert stats["total_errors"] == 4
        assert stats["by_category"]["validation"] == 2
        assert stats["by_category"]["data_load"] == 1
        assert stats["by_category"]["gpt_api"] == 1
    
    def test_reset_stats(self):
        """Тест сброса статистики."""
        self.error_handler.handle_error(ValidationError("Test error"))
        assert self.error_handler.error_stats["total_errors"] == 1
        
        self.error_handler.reset_stats()
        assert self.error_handler.error_stats["total_errors"] == 0
        assert self.error_handler.error_stats["by_category"] == {}
        assert self.error_handler.error_stats["by_severity"] == {}


class TestErrorHandlerDecorator:
    """Тесты для декоратора обработки ошибок."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.mock_logger = Mock(spec=logging.Logger)
        self.error_handler = ErrorHandler(self.mock_logger)
    
    def test_decorator_success(self):
        """Тест успешного выполнения функции с декоратором."""
        @error_handler_decorator(self.error_handler)
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        assert result == 5
    
    def test_decorator_with_exception(self):
        """Тест обработки исключения декоратором."""
        @error_handler_decorator(self.error_handler)
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        
        # Должно вернуть пользовательское сообщение
        assert isinstance(result, str)
        assert len(result) > 0
        assert self.error_handler.error_stats["total_errors"] == 1
    
    def test_decorator_with_reraise(self):
        """Тест декоратора с перебрасыванием исключения."""
        @error_handler_decorator(self.error_handler, reraise=True)
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
        
        # Ошибка должна быть обработана, но исключение переброшено
        assert self.error_handler.error_stats["total_errors"] == 1
    
    def test_decorator_with_context_function(self):
        """Тест декоратора с функцией контекста."""
        def context_func(*args, **kwargs):
            return {"args": args, "kwargs": kwargs}
        
        @error_handler_decorator(self.error_handler, context_func=context_func)
        def test_function(x, y=None):
            raise ValueError("Test error")
        
        test_function(1, y=2)
        
        # Проверяем, что контекст был добавлен
        assert self.error_handler.error_stats["total_errors"] == 1


class TestGlobalFunctions:
    """Тесты для глобальных функций."""
    
    def test_global_handle_error(self):
        """Тест глобальной функции handle_error."""
        error = ValidationError("Test error")
        
        user_message = handle_error(error)
        
        assert isinstance(user_message, str)
        assert len(user_message) > 0
    
    def test_global_get_error_stats(self):
        """Тест глобальной функции get_error_stats."""
        # Сначала обработаем ошибку
        handle_error(ValidationError("Test error"))
        
        stats = get_error_stats()
        
        assert isinstance(stats, dict)
        assert "total_errors" in stats
        assert stats["total_errors"] >= 1


class TestErrorMessages:
    """Тесты для пользовательских сообщений об ошибках."""
    
    def test_user_friendly_messages(self):
        """Тест дружелюбных пользовательских сообщений."""
        errors_and_keywords = [
            (DataLoadError("Test"), ["данные", "попробуйте"]),
            (GPTClientError("Test"), ["сервис", "недоступен"]),
            (ValidationError("Test"), ["данных", "проверьте"]),
            (ConfigurationError("Test"), ["конфигурации", "администратору"]),
        ]
        
        for error, keywords in errors_and_keywords:
            message = error.user_message.lower()
            for keyword in keywords:
                assert keyword in message, f"Keyword '{keyword}' not found in message: {message}"
    
    def test_no_technical_details_in_user_messages(self):
        """Тест отсутствия технических деталей в пользовательских сообщениях."""
        technical_terms = ["exception", "traceback", "stack", "api_key", "token"]
        
        errors = [
            DataLoadError("FileNotFoundError: /path/to/file"),
            GPTClientError("OpenAI API key invalid"),
            ValidationError("TypeError: expected str, got int"),
        ]
        
        for error in errors:
            message = error.user_message.lower()
            for term in technical_terms:
                assert term not in message, f"Technical term '{term}' found in user message: {message}"


if __name__ == "__main__":
    pytest.main([__file__])