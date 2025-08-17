"""
Централизованная система обработки ошибок для RAG-системы салона красоты.
Обеспечивает единообразную обработку ошибок и информативные сообщения для пользователей.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type
from functools import wraps
from enum import Enum


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Категории ошибок."""
    DATA_LOAD = "data_load"
    GPT_API = "gpt_api"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class BeautySalonError(Exception):
    """Базовый класс для всех ошибок системы салона красоты."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 user_message: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Инициализация ошибки.
        
        Args:
            message: Техническое сообщение об ошибке
            category: Категория ошибки
            severity: Уровень серьезности
            user_message: Сообщение для пользователя
            details: Дополнительные детали ошибки
        """
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.details = details or {}
        self.technical_message = message
    
    def _generate_user_message(self) -> str:
        """Генерирует пользовательское сообщение на основе категории ошибки."""
        user_messages = {
            ErrorCategory.DATA_LOAD: "Произошла ошибка при загрузке данных. Попробуйте позже.",
            ErrorCategory.GPT_API: "Сервис временно недоступен. Попробуйте позже.",
            ErrorCategory.VALIDATION: "Проверьте правильность введенных данных.",
            ErrorCategory.CONFIGURATION: "Ошибка конфигурации системы. Обратитесь к администратору.",
            ErrorCategory.SYSTEM: "Произошла системная ошибка. Обратитесь к администратору.",
            ErrorCategory.USER_INPUT: "Некорректный запрос. Попробуйте переформулировать."
        }
        return user_messages.get(self.category, "Произошла неожиданная ошибка.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует ошибку в словарь для логирования."""
        return {
            "error_type": self.__class__.__name__,
            "category": self.category.value,
            "severity": self.severity.value,
            "technical_message": self.technical_message,
            "user_message": self.user_message,
            "details": self.details
        }


class DataLoadError(BeautySalonError):
    """Ошибка загрузки данных."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(
            message=message,
            category=ErrorCategory.DATA_LOAD,
            severity=ErrorSeverity.HIGH,
            user_message="Не удалось загрузить данные услуг. Попробуйте позже или обратитесь к администратору.",
            details=details,
            **kwargs
        )


class GPTClientError(BeautySalonError):
    """Ошибка GPT клиента."""
    
    def __init__(self, message: str, api_error: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if api_error:
            details['api_error'] = api_error
        
        super().__init__(
            message=message,
            category=ErrorCategory.GPT_API,
            severity=ErrorSeverity.HIGH,
            user_message="Сервис ИИ временно недоступен. Попробуйте позже.",
            details=details,
            **kwargs
        )


class ValidationError(BeautySalonError):
    """Ошибка валидации данных."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        details = kwargs.pop('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Проверьте правильность введенных данных и попробуйте снова.",
            details=details,
            **kwargs
        )


class ConfigurationError(BeautySalonError):
    """Ошибка конфигурации."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            user_message="Ошибка конфигурации системы. Обратитесь к администратору.",
            details=details,
            **kwargs
        )


class ErrorHandler:
    """Централизованный обработчик ошибок."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Инициализация обработчика ошибок.
        
        Args:
            logger: Логгер для записи ошибок
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {}
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Обрабатывает ошибку и возвращает сообщение для пользователя.
        
        Args:
            error: Исключение для обработки
            context: Дополнительный контекст ошибки
            
        Returns:
            Сообщение для пользователя
        """
        context = context or {}
        
        # Преобразуем в BeautySalonError если нужно
        if not isinstance(error, BeautySalonError):
            error = self._convert_to_beauty_salon_error(error)
        
        # Обновляем статистику
        self._update_error_stats(error)
        
        # Логируем ошибку
        self._log_error(error, context)
        
        return error.user_message
    
    def _convert_to_beauty_salon_error(self, error: Exception) -> BeautySalonError:
        """Преобразует стандартное исключение в BeautySalonError."""
        error_type = type(error).__name__
        message = str(error)
        
        # Определяем категорию и серьезность на основе типа ошибки
        if isinstance(error, (FileNotFoundError, IOError)):
            return DataLoadError(f"{error_type}: {message}")
        elif isinstance(error, (ValueError, TypeError)):
            return ValidationError(f"{error_type}: {message}")
        elif "openai" in message.lower() or "api" in message.lower():
            return GPTClientError(f"{error_type}: {message}")
        else:
            return BeautySalonError(
                message=f"{error_type}: {message}",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM
            )
    
    def _update_error_stats(self, error: BeautySalonError):
        """Обновляет статистику ошибок."""
        self.error_stats["total_errors"] += 1
        
        category = error.category.value
        self.error_stats["by_category"][category] = self.error_stats["by_category"].get(category, 0) + 1
        
        severity = error.severity.value
        self.error_stats["by_severity"][severity] = self.error_stats["by_severity"].get(severity, 0) + 1
    
    def _log_error(self, error: BeautySalonError, context: Dict[str, Any]):
        """Логирует ошибку с соответствующим уровнем."""
        error_dict = error.to_dict()
        error_dict.update(context)
        
        # Определяем уровень логирования
        log_level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        
        log_level = log_level_map.get(error.severity, logging.ERROR)
        
        # Формируем сообщение для лога
        log_message = f"[{error.category.value.upper()}] {error.technical_message}"
        
        # Добавляем трассировку для критических ошибок
        if error.severity == ErrorSeverity.CRITICAL:
            log_message += f"\nTraceback: {traceback.format_exc()}"
        
        self.logger.log(log_level, log_message, extra={"error_details": error_dict})
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Возвращает статистику ошибок."""
        return self.error_stats.copy()
    
    def reset_stats(self):
        """Сбрасывает статистику ошибок."""
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {}
        }


def error_handler_decorator(error_handler: ErrorHandler, 
                          context_func: Optional[Callable] = None,
                          reraise: bool = False):
    """
    Декоратор для автоматической обработки ошибок в методах.
    
    Args:
        error_handler: Экземпляр ErrorHandler
        context_func: Функция для получения контекста (принимает args, kwargs)
        reraise: Перебрасывать ли ошибку после обработки
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {}
                if context_func:
                    try:
                        context = context_func(*args, **kwargs)
                    except Exception:
                        pass
                
                context.update({
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })
                
                user_message = error_handler.handle_error(e, context)
                
                if reraise:
                    raise
                
                return user_message
        
        return wrapper
    return decorator


# Глобальный экземпляр обработчика ошибок
global_error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Глобальная функция для обработки ошибок.
    
    Args:
        error: Исключение для обработки
        context: Дополнительный контекст
        
    Returns:
        Сообщение для пользователя
    """
    return global_error_handler.handle_error(error, context)


def get_error_stats() -> Dict[str, Any]:
    """Возвращает глобальную статистику ошибок."""
    return global_error_handler.get_error_stats()