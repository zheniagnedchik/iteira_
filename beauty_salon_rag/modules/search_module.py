"""
Поисковый модуль для RAG-системы салона красоты.
Обеспечивает поиск релевантных услуг в облегченном файле services_no_staff.json.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..gpt_client import GPTClient, GPTClientError
from .data_loader import DataLoader, DataLoadError
from ..logger import get_logger, log_operation
from ..error_handler import BeautySalonError, ErrorCategory, ErrorSeverity, ValidationError

# Получаем логгер для модуля
logger = get_logger(__name__)


class SearchModuleError(BeautySalonError):
    """Исключение для ошибок поискового модуля."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            user_message="Произошла ошибка при поиске услуг. Попробуйте переформулировать запрос.",
            **kwargs
        )


class SearchModule:
    """Класс для поиска услуг в облегченных данных через GPT."""
    
    def __init__(self, base_path: str = "."):
        """
        Инициализация поискового модуля.
        
        Args:
            base_path: Базовый путь к файлам данных
        """
        self.base_path = Path(base_path)
        self.data_loader = DataLoader(base_path)
        
        try:
            self.gpt_client = GPTClient()
            logger.info("Поисковый модуль инициализирован успешно")
        except GPTClientError as e:
            logger.error(f"Ошибка инициализации GPT клиента: {e}")
            raise SearchModuleError(
                f"Ошибка инициализации GPT клиента: {e}",
                details={"base_path": str(base_path), "gpt_error": str(e)}
            )
    
    @log_operation("load_light_services")
    def load_light_services(self) -> Dict[str, Any]:
        """
        Загружает облегченные данные услуг из services_no_staff.json.
        
        Returns:
            Словарь с данными услуг без информации о персонале
            
        Raises:
            SearchModuleError: При ошибке загрузки данных
        """
        try:
            return self.data_loader.load_services_no_staff_json()
        except DataLoadError as e:
            logger.error(f"Ошибка загрузки облегченных данных: {e}")
            raise SearchModuleError(
                f"Ошибка загрузки облегченных данных: {e}",
                details={"data_load_error": str(e)}
            )
    
    @log_operation("find_services")
    def find_services(self, query: str) -> List[str]:
        """
        Находит релевантные услуги по текстовому запросу через GPT.
        
        Args:
            query: Поисковый запрос пользователя
            
        Returns:
            Список ID найденных услуг
            
        Raises:
            SearchModuleError: При ошибке поиска
            ValidationError: При некорректных входных параметрах
        """
        if not isinstance(query, str):
            raise ValidationError(
                "Запрос должен быть строкой",
                field="query",
                value=type(query).__name__
            )
            
        if not query.strip():
            logger.warning("Получен пустой запрос")
            return []
        
        query = query.strip()
        logger.debug(f"Поиск услуг для запроса: '{query}'")
        
        try:
            # Загружаем облегченные данные
            services_data = self.load_light_services()
            
            # Выполняем поиск через GPT
            service_ids = self.gpt_client.search_services(query, services_data)
            
            # Валидируем результат
            validated_ids = self._validate_service_ids(service_ids, services_data)
            
            logger.info(f"Найдено {len(validated_ids)} услуг для запроса: '{query}'")
            return validated_ids
            
        except (GPTClientError, ValidationError) as e:
            logger.error(f"Ошибка при поиске услуг: {e}")
            raise SearchModuleError(
                f"Ошибка при поиске услуг: {e}",
                details={"query": query, "error_type": type(e).__name__}
            )
        except DataLoadError as e:
            logger.error(f"Ошибка загрузки данных при поиске: {e}")
            raise SearchModuleError(
                f"Ошибка загрузки данных при поиске: {e}",
                details={"query": query, "data_error": str(e)}
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске услуг: {e}")
            raise SearchModuleError(
                f"Неожиданная ошибка при поиске услуг: {e}",
                details={"query": query, "unexpected_error": str(e)}
            )
    
    def _validate_service_ids(self, service_ids: List[str], services_data: Dict[str, Any]) -> List[str]:
        """
        Валидирует и фильтрует ID услуг.
        
        Args:
            service_ids: Список ID услуг от GPT
            services_data: Данные услуг для проверки
            
        Returns:
            Список валидных ID услуг
        """
        if not isinstance(service_ids, list):
            logger.warning("GPT вернул некорректный формат ID услуг")
            return []
        
        # Создаем индекс существующих ID
        existing_ids = set()
        items = services_data.get('data', {}).get('items', [])
        
        for item in items:
            if isinstance(item, dict) and 'id' in item:
                existing_ids.add(item['id'])
        
        # Фильтруем валидные ID
        valid_ids = []
        invalid_ids = []
        
        for service_id in service_ids:
            if not isinstance(service_id, str):
                logger.warning(f"Некорректный тип ID услуги: {type(service_id)}")
                continue
                
            if service_id in existing_ids:
                valid_ids.append(service_id)
            else:
                invalid_ids.append(service_id)
        
        if invalid_ids:
            logger.warning(f"GPT вернул несуществующие ID услуг: {invalid_ids}")
        
        return valid_ids
    
    def get_service_details_by_ids(self, service_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получает детальную информацию об услугах по их ID из облегченного файла.
        
        Args:
            service_ids: Список ID услуг
            
        Returns:
            Список словарей с информацией об услугах
            
        Raises:
            SearchModuleError: При ошибке получения данных
        """
        if not isinstance(service_ids, list):
            raise ValueError("service_ids должен быть списком")
        
        if not service_ids:
            return []
        
        try:
            services_data = self.load_light_services()
            items = services_data.get('data', {}).get('items', [])
            
            # Создаем индекс для быстрого поиска
            services_index = {item.get('id'): item for item in items if 'id' in item}
            
            found_services = []
            for service_id in service_ids:
                if service_id in services_index:
                    found_services.append(services_index[service_id])
            
            logger.info(f"Получена детальная информация для {len(found_services)} услуг")
            return found_services
            
        except Exception as e:
            logger.error(f"Ошибка получения деталей услуг: {e}")
            raise SearchModuleError(f"Ошибка получения деталей услуг: {e}")
    
    def search_with_details(self, query: str) -> List[Dict[str, Any]]:
        """
        Выполняет поиск и возвращает детальную информацию об найденных услугах.
        
        Args:
            query: Поисковый запрос пользователя
            
        Returns:
            Список словарей с детальной информацией об услугах
            
        Raises:
            SearchModuleError: При ошибке поиска или получения данных
        """
        try:
            # Находим ID услуг
            service_ids = self.find_services(query)
            
            if not service_ids:
                logger.info(f"Услуги не найдены для запроса: '{query}'")
                return []
            
            # Получаем детальную информацию
            return self.get_service_details_by_ids(service_ids)
            
        except SearchModuleError:
            raise
        except Exception as e:
            logger.error(f"Ошибка поиска с деталями: {e}")
            raise SearchModuleError(f"Ошибка поиска с деталями: {e}")
    
    def health_check(self) -> bool:
        """
        Проверяет работоспособность поискового модуля.
        
        Returns:
            True если модуль работает корректно, False иначе
        """
        try:
            # Проверяем загрузку данных
            services_data = self.load_light_services()
            if not services_data or 'data' not in services_data:
                return False
            
            # Проверяем GPT клиент
            if not self.gpt_client.health_check():
                return False
            
            logger.info("Проверка работоспособности поискового модуля прошла успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки работоспособности: {e}")
            return False


# Удобные функции для быстрого доступа
def search_services(query: str, base_path: str = ".") -> List[str]:
    """
    Быстрый поиск услуг по запросу.
    
    Args:
        query: Поисковый запрос
        base_path: Путь к файлам данных
        
    Returns:
        Список ID найденных услуг
    """
    search_module = SearchModule(base_path)
    return search_module.find_services(query)


def search_services_with_details(query: str, base_path: str = ".") -> List[Dict[str, Any]]:
    """
    Быстрый поиск услуг с получением детальной информации.
    
    Args:
        query: Поисковый запрос
        base_path: Путь к файлам данных
        
    Returns:
        Список словарей с информацией об услугах
    """
    search_module = SearchModule(base_path)
    return search_module.search_with_details(query)