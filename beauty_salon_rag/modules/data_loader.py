"""
Модуль для загрузки и работы с данными JSON файлов.
Обеспечивает загрузку services.json и services_no_staff.json с обработкой ошибок.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..logger import get_logger, log_operation
from ..error_handler import DataLoadError, ValidationError, handle_error

# Получаем логгер для модуля
logger = get_logger(__name__)


class DataLoader:
    """Класс для загрузки и работы с JSON файлами данных."""
    
    def __init__(self, base_path: str = "."):
        """
        Инициализация загрузчика данных.
        
        Args:
            base_path: Базовый путь к файлам данных
        """
        self.base_path = Path(base_path)
        self._services_cache: Optional[Dict[str, Any]] = None
        self._services_no_staff_cache: Optional[Dict[str, Any]] = None
    
    @log_operation("load_services_json")
    def load_services_json(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Загружает данные из services.json с полной информацией об услугах.
        
        Args:
            force_reload: Принудительная перезагрузка данных
            
        Returns:
            Словарь с данными услуг
            
        Raises:
            DataLoadError: При ошибке загрузки файла
        """
        if self._services_cache is not None and not force_reload:
            logger.debug("Используется кэшированная версия services.json")
            return self._services_cache
            
        file_path = self.base_path / "services.json"
        
        try:
            if not file_path.exists():
                raise DataLoadError(
                    f"Файл {file_path} не найден",
                    file_path=str(file_path)
                )
                
            logger.debug(f"Загрузка данных из {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # Валидация структуры данных
            self._validate_services_structure(data, str(file_path))
                
            self._services_cache = data
            items_count = len(data['data']['items'])
            logger.info(f"Успешно загружено {items_count} услуг из services.json")
            return data
            
        except json.JSONDecodeError as e:
            raise DataLoadError(
                f"Ошибка парсинга JSON в файле {file_path}: {e}",
                file_path=str(file_path),
                details={"json_error": str(e)}
            )
        except IOError as e:
            raise DataLoadError(
                f"Ошибка чтения файла {file_path}: {e}",
                file_path=str(file_path),
                details={"io_error": str(e)}
            )
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(
                f"Неожиданная ошибка при загрузке {file_path}: {e}",
                file_path=str(file_path),
                details={"unexpected_error": str(e)}
            )
    
    @log_operation("load_services_no_staff_json")
    def load_services_no_staff_json(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Загружает данные из services_no_staff.json с облегченной информацией об услугах.
        
        Args:
            force_reload: Принудительная перезагрузка данных
            
        Returns:
            Словарь с данными услуг без информации о персонале
            
        Raises:
            DataLoadError: При ошибке загрузки файла
        """
        if self._services_no_staff_cache is not None and not force_reload:
            logger.debug("Используется кэшированная версия services_no_staff.json")
            return self._services_no_staff_cache
            
        file_path = self.base_path / "services_no_staff.json"
        
        try:
            if not file_path.exists():
                raise DataLoadError(
                    f"Файл {file_path} не найден",
                    file_path=str(file_path)
                )
                
            logger.debug(f"Загрузка данных из {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # Валидация структуры данных
            self._validate_services_structure(data, str(file_path))
                
            self._services_no_staff_cache = data
            items_count = len(data['data']['items'])
            logger.info(f"Успешно загружено {items_count} услуг из services_no_staff.json")
            return data
            
        except json.JSONDecodeError as e:
            raise DataLoadError(
                f"Ошибка парсинга JSON в файле {file_path}: {e}",
                file_path=str(file_path),
                details={"json_error": str(e)}
            )
        except IOError as e:
            raise DataLoadError(
                f"Ошибка чтения файла {file_path}: {e}",
                file_path=str(file_path),
                details={"io_error": str(e)}
            )
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(
                f"Неожиданная ошибка при загрузке {file_path}: {e}",
                file_path=str(file_path),
                details={"unexpected_error": str(e)}
            )
    
    def _validate_services_structure(self, data: Any, file_path: str):
        """
        Валидирует структуру данных услуг.
        
        Args:
            data: Данные для валидации
            file_path: Путь к файлу для контекста ошибки
            
        Raises:
            DataLoadError: При некорректной структуре данных
        """
        if not isinstance(data, dict):
            raise DataLoadError(
                "Некорректный формат данных: ожидается объект JSON",
                file_path=file_path,
                details={"actual_type": type(data).__name__}
            )
            
        if 'data' not in data:
            raise DataLoadError(
                "Некорректная структура данных: отсутствует поле 'data'",
                file_path=file_path,
                details={"available_keys": list(data.keys())}
            )
            
        if 'items' not in data['data']:
            raise DataLoadError(
                "Некорректная структура данных: отсутствует поле 'data.items'",
                file_path=file_path,
                details={"available_keys": list(data['data'].keys())}
            )
            
        if not isinstance(data['data']['items'], list):
            raise DataLoadError(
                "Некорректная структура данных: 'items' должен быть массивом",
                file_path=file_path,
                details={"actual_type": type(data['data']['items']).__name__}
            )

    @log_operation("get_services_by_ids")
    def get_services_by_ids(self, service_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получает услуги по массиву ID из полного файла services.json.
        
        Args:
            service_ids: Список ID услуг для поиска
            
        Returns:
            Список найденных услуг
            
        Raises:
            DataLoadError: При ошибке загрузки данных
            ValidationError: При некорректных входных параметрах
        """
        if not isinstance(service_ids, list):
            raise ValidationError(
                "service_ids должен быть списком",
                field="service_ids",
                value=type(service_ids).__name__
            )
            
        if not service_ids:
            logger.warning("Передан пустой список ID услуг")
            return []
        
        logger.debug(f"Поиск услуг по {len(service_ids)} ID")
            
        # Загружаем полные данные услуг
        services_data = self.load_services_json()
        items = services_data['data']['items']
        
        # Создаем индекс для быстрого поиска по ID
        services_index = {item.get('id'): item for item in items if 'id' in item}
        
        found_services = []
        missing_ids = []
        invalid_ids = []
        
        for service_id in service_ids:
            if not isinstance(service_id, str):
                invalid_ids.append(service_id)
                logger.warning(f"Некорректный ID услуги: {service_id} (ожидается строка)")
                continue
                
            if service_id in services_index:
                found_services.append(services_index[service_id])
            else:
                missing_ids.append(service_id)
        
        if missing_ids:
            logger.warning(f"Не найдены услуги с ID: {missing_ids}")
        
        if invalid_ids:
            logger.warning(f"Некорректные ID услуг: {invalid_ids}")
            
        logger.info(f"Найдено {len(found_services)} услуг из {len(service_ids)} запрошенных")
        return found_services
    
    @log_operation("validate_service_exists")
    def validate_service_exists(self, service_id: str) -> bool:
        """
        Проверяет существование услуги по ID.
        
        Args:
            service_id: ID услуги для проверки
            
        Returns:
            True если услуга существует, False иначе
        """
        if not isinstance(service_id, str):
            logger.warning(f"Некорректный тип ID услуги: {type(service_id).__name__}")
            return False
            
        try:
            services_data = self.load_services_json()
            items = services_data['data']['items']
            
            for item in items:
                if item.get('id') == service_id:
                    logger.debug(f"Услуга с ID {service_id} найдена")
                    return True
            
            logger.debug(f"Услуга с ID {service_id} не найдена")
            return False
            
        except DataLoadError as e:
            logger.error(f"Ошибка при проверке существования услуги {service_id}: {e}")
            return False
    
    @log_operation("get_all_service_ids")
    def get_all_service_ids(self) -> List[str]:
        """
        Получает список всех ID услуг.
        
        Returns:
            Список всех ID услуг
        """
        try:
            services_data = self.load_services_json()
            items = services_data['data']['items']
            
            service_ids = [item.get('id') for item in items if 'id' in item]
            valid_ids = [sid for sid in service_ids if sid is not None]
            
            logger.info(f"Получено {len(valid_ids)} ID услуг")
            return valid_ids
            
        except DataLoadError as e:
            logger.error(f"Ошибка при получении списка ID услуг: {e}")
            return []
    
    def clear_cache(self):
        """Очищает кэш загруженных данных."""
        self._services_cache = None
        self._services_no_staff_cache = None
        logger.info("Кэш данных очищен")


# Удобные функции для быстрого доступа
def load_services() -> Dict[str, Any]:
    """
    Быстрая загрузка services.json.
    
    Returns:
        Данные услуг
    """
    loader = DataLoader()
    return loader.load_services_json()


def load_services_no_staff() -> Dict[str, Any]:
    """
    Быстрая загрузка services_no_staff.json.
    
    Returns:
        Данные услуг без персонала
    """
    loader = DataLoader()
    return loader.load_services_no_staff_json()


def find_services_by_ids(service_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Быстрый поиск услуг по ID.
    
    Args:
        service_ids: Список ID услуг
        
    Returns:
        Список найденных услуг
    """
    loader = DataLoader()
    return loader.get_services_by_ids(service_ids)