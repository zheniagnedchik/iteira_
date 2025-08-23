"""
Модуль для работы с API Yclients для получения слотов времени
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .logger import get_logger


class YclientsAPI:
    """Класс для работы с API Yclients"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.base_url = "https://api.yclients.com/api/v1"
        self.headers = {
            "Accept": "application/vnd.yclients.v2+json",
            "Content-Type": "application/json",
            "Authorization": "Bearer sshbjsn834r6dr7dsjg8, User 24483c8842760c7f91255260e74eaf42"
        }
        
        # ID компаний
        self.salon_id = 314923  # Салон красоты (ул. Немига, 5)
        self.clinic_id = 330185  # Клиника (ул. Платонова, 1Б)
        
    def get_available_times(self, staff_id: str, date: str, service_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получает доступные слоты времени для мастера на конкретную дату
        
        Args:
            staff_id: ID мастера
            date: Дата в формате YYYY-MM-DD
            service_data: Данные об услуге (для определения локации)
            
        Returns:
            Список доступных слотов времени
        """
        try:
            # Определяем company_id на основе услуги
            company_id = self._get_company_id(service_data)
            
            # Формируем URL для запроса
            url = f"{self.base_url}/book_times/{company_id}/{staff_id}/{date}"
            
            self.logger.info(f"Запрос слотов времени: company_id={company_id}, staff_id={staff_id}, date={date}")
            
            # Выполняем запрос
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                slots = self._parse_time_slots(data)
                self.logger.info(f"Получено {len(slots)} доступных слотов")
                return slots
            else:
                self.logger.error(f"Ошибка API Yclients: {response.status_code} - {response.text}")
                return []
                
        except requests.RequestException as e:
            self.logger.error(f"Ошибка запроса к API Yclients: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при получении слотов: {e}")
            return []
    
    def _get_company_id(self, service_data: Dict[str, Any]) -> int:
        """
        Определяет ID компании на основе данных об услуге
        
        Args:
            service_data: Данные об услуге
            
        Returns:
            ID компании (салон или клиника)
        """
        # Получаем категорию услуги
        category = service_data.get('category', '').lower()
        title = service_data.get('title', '').lower()
        
        # Услуги клиники (инъекции, лазер, anti-age)
        clinic_keywords = ['инъекц', 'лазер', 'anti-age', 'ботул', 'контур', 'плазм', 'мезо']
        
        # Проверяем по ключевым словам
        for keyword in clinic_keywords:
            if keyword in category or keyword in title:
                self.logger.info(f"Услуга '{title}' относится к клинике")
                return self.clinic_id
        
        # По умолчанию - салон красоты
        self.logger.info(f"Услуга '{title}' относится к салону")
        return self.salon_id
    
    def _parse_time_slots(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсит ответ API и извлекает доступные слоты времени
        
        Args:
            api_data: Ответ от API Yclients
            
        Returns:
            Список слотов времени
        """
        slots = []
        
        try:
            # Предполагаемая структура ответа API
            # Нужно будет адаптировать под реальную структуру после тестирования
            if 'data' in api_data:
                time_slots = api_data['data']
                
                for slot in time_slots:
                    # Извлекаем время начала и конца
                    start_time = slot.get('time', '')
                    duration = slot.get('duration', 60)  # По умолчанию 60 минут
                    available = slot.get('available', True)
                    
                    if available and start_time:
                        slots.append({
                            'time': start_time,
                            'duration': duration,
                            'display_time': self._format_time_for_display(start_time),
                            'available': True
                        })
                        
            self.logger.info(f"Обработано {len(slots)} слотов времени")
            return slots
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга слотов времени: {e}")
            return []
    
    def _format_time_for_display(self, time_str: str) -> str:
        """
        Форматирует время для отображения пользователю
        
        Args:
            time_str: Время в формате API
            
        Returns:
            Отформатированное время для пользователя
        """
        try:
            # Предполагаем формат времени HH:MM
            if ':' in time_str:
                return time_str  # Уже в нужном формате
            
            # Если другой формат - адаптируем
            return time_str
            
        except Exception:
            return time_str
    
    def get_staff_id_from_service(self, service_data: Dict[str, Any], staff_name: str = None) -> Optional[str]:
        """
        Извлекает ID мастера из данных услуги
        
        Args:
            service_data: Данные об услуге
            staff_name: Имя конкретного мастера (опционально)
            
        Returns:
            ID мастера или None
        """
        try:
            # Сначала проверяем старый формат (корневое поле staff)
            staff_list = service_data.get('staff', [])
            
            # Если в корне нет данных, ищем в companies
            if not staff_list:
                companies = service_data.get('companies', [])
                if companies:
                    # Определяем нужную компанию
                    company_id = self._get_company_id(service_data)
                    
                    # Ищем компанию с правильным ID
                    for company in companies:
                        if str(company.get('company_id', '')) == str(company_id):
                            staff_list = company.get('staff', [])
                            break
                    
                    # Если не нашли по ID, берем первую компанию
                    if not staff_list and companies:
                        staff_list = companies[0].get('staff', [])
            
            if not staff_list:
                self.logger.warning("В данных услуги нет информации о мастерах")
                return None
            
            # Если указано имя мастера - ищем его
            if staff_name:
                for staff in staff_list:
                    if isinstance(staff, dict) and staff.get('name', '').lower() == staff_name.lower():
                        return str(staff.get('id', ''))
            
            # Если имя не указано - берем первого доступного мастера
            if isinstance(staff_list[0], dict):
                return str(staff_list[0].get('id', ''))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения ID мастера: {e}")
            return None
    
    def format_time_slots_for_user(self, slots: List[Dict[str, Any]]) -> str:
        """
        Форматирует слоты времени для отображения пользователю
        
        Args:
            slots: Список слотов времени
            
        Returns:
            Отформатированная строка с доступным временем
        """
        if not slots:
            return "К сожалению, на выбранную дату нет доступных слотов. Могу предложить другую дату?"
        
        # Группируем время по периодам дня
        morning_slots = []  # 9:00-12:00
        afternoon_slots = []  # 12:00-17:00
        evening_slots = []  # 17:00-21:00
        
        for slot in slots:
            time_str = slot.get('display_time', slot.get('time', ''))
            
            try:
                hour = int(time_str.split(':')[0])
                
                if 9 <= hour < 12:
                    morning_slots.append(time_str)
                elif 12 <= hour < 17:
                    afternoon_slots.append(time_str)
                elif 17 <= hour < 21:
                    evening_slots.append(time_str)
                    
            except (ValueError, IndexError):
                afternoon_slots.append(time_str)  # По умолчанию в день
        
        # Формируем красивый вывод
        result_parts = []
        
        if morning_slots:
            result_parts.append(f"🌅 **Утром:** {', '.join(morning_slots[:4])}")
        
        if afternoon_slots:
            result_parts.append(f"☀️ **Днем:** {', '.join(afternoon_slots[:4])}")
        
        if evening_slots:
            result_parts.append(f"🌙 **Вечером:** {', '.join(evening_slots[:4])}")
        
        if result_parts:
            return "\n".join(result_parts) + "\n\nКакое время вам удобно?"
        else:
            return "Доступные время: " + ", ".join([slot.get('display_time', slot.get('time', '')) for slot in slots[:8]])
