"""
Консультационный модуль для RAG-системы салона красоты.
Обеспечивает консультирование клиентов на основе полных данных об услугах.
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


class ConsultationModuleError(BeautySalonError):
    """Исключение для ошибок консультационного модуля."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            user_message="Произошла ошибка при формировании ответа. Попробуйте позже.",
            **kwargs
        )


class ConsultationModule:
    """Класс для консультирования клиентов на основе полных данных об услугах."""
    
    def __init__(self, base_path: str = "."):
        """
        Инициализация консультационного модуля.
        
        Args:
            base_path: Базовый путь к файлам данных
        """
        self.base_path = Path(base_path)
        self.data_loader = DataLoader(base_path)
        
        try:
            self.gpt_client = GPTClient()
            logger.info("Консультационный модуль инициализирован успешно")
        except GPTClientError as e:
            logger.error(f"Ошибка инициализации GPT клиента: {e}")
            raise ConsultationModuleError(
                f"Ошибка инициализации GPT клиента: {e}",
                details={"base_path": str(base_path), "gpt_error": str(e)}
            )
    
    def load_full_services(self) -> Dict[str, Any]:
        """
        Загружает полные данные услуг из services.json.
        
        Returns:
            Словарь с полными данными услуг включая информацию о мастерах
            
        Raises:
            ConsultationModuleError: При ошибке загрузки данных
        """
        try:
            return self.data_loader.load_services_json()
        except DataLoadError as e:
            logger.error(f"Ошибка загрузки полных данных: {e}")
            raise ConsultationModuleError(f"Ошибка загрузки полных данных: {e}")
    
    def get_services_by_ids(self, service_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получает полную информацию об услугах по их ID из services.json.
        
        Args:
            service_ids: Список ID услуг
            
        Returns:
            Список словарей с полной информацией об услугах
            
        Raises:
            ConsultationModuleError: При ошибке получения данных
            ValueError: При некорректных входных параметрах
        """
        if not isinstance(service_ids, list):
            raise ValueError("service_ids должен быть списком")
        
        if not service_ids:
            logger.info("Получен пустой список ID услуг")
            return []
        
        try:
            found_services = self.data_loader.get_services_by_ids(service_ids)
            logger.info(f"Получена полная информация для {len(found_services)} услуг")
            return found_services
            
        except DataLoadError as e:
            logger.error(f"Ошибка получения услуг по ID: {e}")
            raise ConsultationModuleError(f"Ошибка получения услуг по ID: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении услуг: {e}")
            raise ConsultationModuleError(f"Неожиданная ошибка при получении услуг: {e}")
    
    def format_staff_info(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует информацию о мастерах и датах записи для услуги.
        
        Args:
            service: Словарь с данными услуги
            
        Returns:
            Словарь с отформатированной информацией о мастерах
        """
        staff_info = {
            "available_masters": [],
            "total_staff_count": 0,
            "companies": []
        }
        
        companies = service.get('companies', [])
        if not companies:
            logger.warning(f"Нет информации о компаниях для услуги {service.get('id', 'unknown')}")
            return staff_info
        
        for company in companies:
            if isinstance(company, dict):
                company_info = {
                    "company_id": company.get('company_id'),
                    "service_id": company.get('service_id'),
                    "staff_count": company.get('staff_count', 0),
                    "staff": []
                }
                
                staff = company.get('staff', [])
                for staff_member in staff:
                    if isinstance(staff_member, dict):
                        master_info = {
                            "id": staff_member.get('id'),
                            "name": staff_member.get('name'),
                            "booking_dates": staff_member.get('booking_dates', [])
                        }
                        company_info["staff"].append(master_info)
                        staff_info["available_masters"].append(master_info)
                
                staff_info["companies"].append(company_info)
                staff_info["total_staff_count"] += company_info["staff_count"]
        
        return staff_info
    
    def format_service_details(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматирует детальную информацию об услуге для консультации.
        
        Args:
            service: Словарь с данными услуги
            
        Returns:
            Словарь с отформатированной информацией об услуге
        """
        # Базовая информация об услуге
        formatted_service = {
            "id": service.get('id'),
            "title": service.get('title'),
            "category": service.get('category'),
            "price": service.get('price'),
            "duration": service.get('duration'),
            "duration_formatted": self._format_duration(service.get('duration')),
            "staff_info": self.format_staff_info(service)
        }
        
        # CSV поля с дополнительной информацией
        csv_fields = service.get('csv_fields', {})
        formatted_service.update({
            "therapeutic_goal": csv_fields.get('Терапевтическая цель', ''),
            "indications": csv_fields.get('Показания (типичные проблемы)', ''),
            "contraindications": csv_fields.get('Противопоказания (стандартные + уточнения)', ''),
            "technology_description": csv_fields.get('Описание технологии', ''),
            "details": csv_fields.get('Детали', ''),
            "service_location": csv_fields.get('Место оказания услуг', '')
        })
        
        return formatted_service
    
    def _format_duration(self, duration: Optional[int]) -> str:
        """
        Форматирует длительность процедуры в читаемый вид.
        
        Args:
            duration: Длительность в секундах
            
        Returns:
            Отформатированная строка с длительностью
        """
        if not duration or not isinstance(duration, (int, float)):
            return "Не указано"
        
        duration = int(duration)
        
        if duration < 60:
            return f"{duration} сек"
        elif duration < 3600:
            minutes = duration // 60
            return f"{minutes} мин"
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            if minutes > 0:
                return f"{hours} ч {minutes} мин"
            else:
                return f"{hours} ч"
    
    @log_operation("generate_consultation_response")
    def generate_consultation_response(self, query: str, service_ids: List[str]) -> str:
        """
        Генерирует консультационный ответ на основе найденных услуг.
        
        Args:
            query: Запрос клиента
            service_ids: Список ID найденных услуг
            
        Returns:
            Сгенерированный ответ консультанта
            
        Raises:
            ConsultationModuleError: При ошибке генерации ответа
            ValidationError: При некорректных входных параметрах
        """
        if not isinstance(query, str) or not query.strip():
            raise ValidationError(
                "Запрос должен быть непустой строкой",
                field="query",
                value=query
            )
        
        if not isinstance(service_ids, list):
            raise ValidationError(
                "service_ids должен быть списком",
                field="service_ids",
                value=type(service_ids).__name__
            )
        
        query = query.strip()
        logger.debug(f"Генерация консультационного ответа для запроса: '{query}' с {len(service_ids)} услугами")
        
        try:
            # Получаем полную информацию об услугах
            services = self.get_services_by_ids(service_ids)
            
            if not services:
                logger.info("Услуги не найдены для консультации")
                return self._generate_no_services_response(query)
            
            # Форматируем данные для GPT
            formatted_services = [self.format_service_details(service) for service in services]
            
            # Генерируем ответ через GPT
            response = self.gpt_client.generate_response(query, formatted_services)
            
            logger.info(f"Сгенерирован консультационный ответ для запроса: '{query}'")
            return response
            
        except (GPTClientError, ValidationError) as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            raise ConsultationModuleError(
                f"Ошибка при генерации ответа: {e}",
                details={
                    "query": query,
                    "service_ids": service_ids,
                    "error_type": type(e).__name__
                }
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации ответа: {e}")
            raise ConsultationModuleError(
                f"Неожиданная ошибка при генерации ответа: {e}",
                details={
                    "query": query,
                    "service_ids": service_ids,
                    "unexpected_error": str(e)
                }
            )
    
    def _generate_no_services_response(self, query: str) -> str:
        """
        Генерирует ответ когда услуги не найдены.
        
        Args:
            query: Запрос клиента
            
        Returns:
            Стандартный ответ об отсутствии услуг
        """
        return (
            f"К сожалению, по вашему запросу '{query}' не найдено подходящих услуг. "
            "Возможно, стоит уточнить запрос или обратиться к нашему администратору "
            "для получения более подробной консультации о доступных процедурах."
        )
    
    def get_booking_info(self, service_ids: List[str]) -> Dict[str, Any]:
        """
        Получает информацию о записи для указанных услуг.
        
        Args:
            service_ids: Список ID услуг
            
        Returns:
            Словарь с информацией о доступных мастерах и датах
            
        Raises:
            ConsultationModuleError: При ошибке получения данных
        """
        try:
            services = self.get_services_by_ids(service_ids)
            
            booking_info = {
                "services": [],
                "all_masters": [],
                "total_services": len(services)
            }
            
            for service in services:
                service_booking = {
                    "service_id": service.get('id'),
                    "service_title": service.get('title'),
                    "price": service.get('price'),
                    "duration": service.get('duration'),
                    "duration_formatted": self._format_duration(service.get('duration')),
                    "staff_info": self.format_staff_info(service)
                }
                
                booking_info["services"].append(service_booking)
                
                # Собираем всех мастеров
                staff_info = service_booking["staff_info"]
                for master in staff_info["available_masters"]:
                    if master not in booking_info["all_masters"]:
                        booking_info["all_masters"].append(master)
            
            logger.info(f"Получена информация о записи для {len(services)} услуг")
            return booking_info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о записи: {e}")
            raise ConsultationModuleError(f"Ошибка получения информации о записи: {e}")
    
    def health_check(self) -> bool:
        """
        Проверяет работоспособность консультационного модуля.
        
        Returns:
            True если модуль работает корректно, False иначе
        """
        try:
            # Проверяем загрузку данных
            services_data = self.load_full_services()
            if not services_data or 'data' not in services_data:
                return False
            
            # Проверяем GPT клиент
            if not self.gpt_client.health_check():
                return False
            
            logger.info("Проверка работоспособности консультационного модуля прошла успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки работоспособности: {e}")
            return False


# Удобные функции для быстрого доступа
def get_consultation_response(query: str, service_ids: List[str], base_path: str = ".") -> str:
    """
    Быстрое получение консультационного ответа.
    
    Args:
        query: Запрос клиента
        service_ids: Список ID услуг
        base_path: Путь к файлам данных
        
    Returns:
        Консультационный ответ
    """
    consultation_module = ConsultationModule(base_path)
    return consultation_module.generate_consultation_response(query, service_ids)


def get_services_with_staff_info(service_ids: List[str], base_path: str = ".") -> List[Dict[str, Any]]:
    """
    Быстрое получение услуг с информацией о мастерах.
    
    Args:
        service_ids: Список ID услуг
        base_path: Путь к файлам данных
        
    Returns:
        Список услуг с отформатированной информацией о мастерах
    """
    consultation_module = ConsultationModule(base_path)
    services = consultation_module.get_services_by_ids(service_ids)
    return [consultation_module.format_service_details(service) for service in services]