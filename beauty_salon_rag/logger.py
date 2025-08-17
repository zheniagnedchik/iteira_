"""
Централизованная система логирования для RAG-системы салона красоты.
Обеспечивает единообразное логирование операций и ошибок.
"""

import logging
import logging.handlers
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .config import config


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом для консоли."""
    
    # Цветовые коды ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированного логирования в JSON."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'query'):
            log_entry['query'] = record.query
        
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        
        return str(log_entry)


class LoggerManager:
    """Менеджер для управления логгерами системы."""
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_dir = Path("logs")
        self._setup_log_directory()
    
    def _setup_log_directory(self):
        """Создает директорию для логов если она не существует."""
        try:
            self.log_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directory: {e}")
            self.log_dir = Path(".")
    
    def get_logger(self, name: str, 
                   log_to_file: bool = True,
                   log_to_console: bool = True,
                   structured_logging: bool = False) -> logging.Logger:
        """
        Получает или создает логгер с заданными параметрами.
        
        Args:
            name: Имя логгера
            log_to_file: Логировать в файл
            log_to_console: Логировать в консоль
            structured_logging: Использовать структурированное логирование
            
        Returns:
            Настроенный логгер
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self._get_log_level())
        
        # Очищаем существующие обработчики
        logger.handlers.clear()
        
        # Добавляем обработчик для консоли
        if log_to_console:
            console_handler = self._create_console_handler(structured_logging)
            logger.addHandler(console_handler)
        
        # Добавляем обработчик для файла
        if log_to_file:
            file_handler = self._create_file_handler(name, structured_logging)
            if file_handler:
                logger.addHandler(file_handler)
        
        # Предотвращаем дублирование логов
        logger.propagate = False
        
        self.loggers[name] = logger
        return logger
    
    def _get_log_level(self) -> int:
        """Получает уровень логирования из конфигурации."""
        level_str = config.get('logging.level', 'INFO').upper()
        return getattr(logging, level_str, logging.INFO)
    
    def _create_console_handler(self, structured: bool = False) -> logging.StreamHandler:
        """Создает обработчик для вывода в консоль."""
        handler = logging.StreamHandler(sys.stdout)
        
        if structured:
            formatter = StructuredFormatter()
        else:
            # Используем цветной форматтер для консоли
            format_str = config.get('logging.format', 
                                  '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            formatter = ColoredFormatter(format_str)
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self, logger_name: str, structured: bool = False) -> Optional[logging.Handler]:
        """Создает обработчик для записи в файл."""
        try:
            # Создаем имя файла на основе имени логгера
            safe_name = logger_name.replace('.', '_').replace('/', '_')
            log_file = self.log_dir / f"{safe_name}.log"
            
            # Используем RotatingFileHandler для ротации логов
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            
            if structured:
                formatter = StructuredFormatter()
            else:
                format_str = config.get('logging.format',
                                      '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                formatter = logging.Formatter(format_str)
            
            handler.setFormatter(formatter)
            return handler
            
        except Exception as e:
            print(f"Warning: Could not create file handler for {logger_name}: {e}")
            return None
    
    def create_operation_logger(self, operation_name: str) -> logging.Logger:
        """
        Создает специализированный логгер для операций.
        
        Args:
            operation_name: Название операции
            
        Returns:
            Логгер для операции
        """
        logger_name = f"beauty_salon_rag.operations.{operation_name}"
        return self.get_logger(logger_name, structured_logging=True)
    
    def create_error_logger(self) -> logging.Logger:
        """Создает специализированный логгер для ошибок."""
        return self.get_logger("beauty_salon_rag.errors", structured_logging=True)
    
    def create_performance_logger(self) -> logging.Logger:
        """Создает специализированный логгер для метрик производительности."""
        return self.get_logger("beauty_salon_rag.performance", structured_logging=True)
    
    def shutdown(self):
        """Корректно закрывает все логгеры."""
        for logger in self.loggers.values():
            for handler in logger.handlers:
                handler.close()
        self.loggers.clear()


class OperationLogger:
    """Контекстный менеджер для логирования операций."""
    
    def __init__(self, logger: logging.Logger, operation_name: str, 
                 log_args: bool = False, log_result: bool = False):
        """
        Инициализация логгера операций.
        
        Args:
            logger: Логгер для записи
            operation_name: Название операции
            log_args: Логировать аргументы
            log_result: Логировать результат
        """
        self.logger = logger
        self.operation_name = operation_name
        self.log_args = log_args
        self.log_result = log_result
        self.start_time = None
        self.context = {}
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra={
                    'execution_time': duration,
                    'operation': self.operation_name,
                    'status': 'success',
                    **self.context
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name} - {exc_val}",
                extra={
                    'execution_time': duration,
                    'operation': self.operation_name,
                    'status': 'error',
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val),
                    **self.context
                }
            )
    
    def add_context(self, **kwargs):
        """Добавляет контекст к логированию операции."""
        self.context.update(kwargs)
    
    def log_step(self, step_name: str, **kwargs):
        """Логирует шаг внутри операции."""
        self.logger.debug(
            f"Operation step: {self.operation_name} -> {step_name}",
            extra={
                'operation': self.operation_name,
                'step': step_name,
                **kwargs
            }
        )


# Глобальный менеджер логгеров
logger_manager = LoggerManager()


def get_logger(name: str, **kwargs) -> logging.Logger:
    """
    Получает логгер с заданным именем.
    
    Args:
        name: Имя логгера
        **kwargs: Дополнительные параметры для настройки
        
    Returns:
        Настроенный логгер
    """
    return logger_manager.get_logger(name, **kwargs)


def get_operation_logger(operation_name: str) -> logging.Logger:
    """Получает логгер для операций."""
    return logger_manager.create_operation_logger(operation_name)


def get_error_logger() -> logging.Logger:
    """Получает логгер для ошибок."""
    return logger_manager.create_error_logger()


def get_performance_logger() -> logging.Logger:
    """Получает логгер для метрик производительности."""
    return logger_manager.create_performance_logger()


def log_operation(operation_name: str, logger: Optional[logging.Logger] = None,
                 log_args: bool = False, log_result: bool = False):
    """
    Декоратор для автоматического логирования операций.
    
    Args:
        operation_name: Название операции
        logger: Логгер (если не указан, создается автоматически)
        log_args: Логировать аргументы функции
        log_result: Логировать результат функции
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_operation_logger(operation_name)
        
        def wrapper(*args, **kwargs):
            with OperationLogger(logger, operation_name, log_args, log_result) as op_logger:
                if log_args:
                    op_logger.add_context(
                        args_count=len(args),
                        kwargs_keys=list(kwargs.keys())
                    )
                
                result = func(*args, **kwargs)
                
                if log_result and result is not None:
                    op_logger.add_context(
                        result_type=type(result).__name__,
                        result_size=len(result) if hasattr(result, '__len__') else None
                    )
                
                return result
        
        return wrapper
    return decorator


def setup_logging():
    """Инициализирует систему логирования."""
    # Настраиваем базовое логирование
    logging.basicConfig(
        level=logger_manager._get_log_level(),
        format=config.get('logging.format', 
                         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[]
    )
    
    # Создаем основные логгеры
    main_logger = get_logger("beauty_salon_rag")
    main_logger.info("Logging system initialized")


def shutdown_logging():
    """Корректно завершает работу системы логирования."""
    logger_manager.shutdown()