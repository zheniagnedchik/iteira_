#!/usr/bin/env python3
"""
Модуль для пошагового подтверждения записи и сбора персональных данных.
Персональные данные НЕ попадают в GPT - обрабатываются локально.
"""

import re
import uuid
from typing import Dict, Any, Optional, Tuple
import logging


class BookingConfirmation:
    """Класс для управления процессом подтверждения записи"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Этапы подтверждения записи
        self.STAGES = {
            'confirm_booking': 'Подтверждение записи (да/нет)',
            'collect_first_name': 'Сбор имени',
            'collect_last_name': 'Сбор фамилии', 
            'collect_phone': 'Сбор телефона',
            'final_confirmation': 'Финальное подтверждение',
            'completed': 'Запись создана'
        }
    
    def start_booking_confirmation(self, booking_details: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Начинает процесс подтверждения записи
        
        Args:
            booking_details: Детали записи (услуга, мастер, дата, время, стоимость)
            
        Returns:
            Tuple[str, Dict]: (сообщение, обновленный контекст)
        """
        try:
            # Формируем сообщение для подтверждения в стиле салона
            service_name = booking_details.get('service_name', 'Услуга')
            master_name = booking_details.get('master_name', 'Мастер')
            date_time = booking_details.get('date_time', 'Дата и время')
            location = booking_details.get('location', 'Салон красоты Итейра')
            address = booking_details.get('address', 'ул. Немига, 5')
            price = booking_details.get('price', 0)
            
            # Извлекаем имя из контекста, если оно есть (предполагаем, что оно передается)
            client_name = booking_details.get('client_name', 'Клиент')
            
            message = f"""{client_name}, прекрасно! Записываю вас на {service_name} {date_time}.

📍 Локация: {location}, {address}
💰 Стоимость: {price} руб.
👤 Мастер: {master_name}

Подтверждаете запись?

Напишите 'ДА' - если хотите записаться
Напишите 'НЕТ' - если передумали"""
            
            # Обновляем контекст
            context_update = {
                'booking_stage': 'confirm_booking',
                'booking_details': booking_details,
                'personal_data': {}  # Персональные данные хранятся отдельно
            }
            
            return message, context_update
            
        except Exception as e:
            self.logger.error(f"Ошибка при начале подтверждения записи: {e}")
            return "Произошла ошибка. Попробуйте снова.", {}
    
    def process_booking_step(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Обрабатывает текущий этап подтверждения записи
        
        Args:
            user_message: Сообщение пользователя
            context: Текущий контекст диалога
            
        Returns:
            Tuple[str, Dict]: (ответное сообщение, обновленный контекст)
        """
        try:
            booking_stage = context.get('booking_stage')
            personal_data = context.get('personal_data', {})
            
            if booking_stage == 'confirm_booking':
                return self._handle_initial_confirmation(user_message, context)
            elif booking_stage == 'collect_first_name':
                return self._handle_first_name_collection(user_message, context)
            elif booking_stage == 'collect_last_name':
                return self._handle_last_name_collection(user_message, context)
            elif booking_stage == 'collect_phone':
                return self._handle_phone_collection(user_message, context)
            elif booking_stage == 'final_confirmation':
                return self._handle_final_confirmation(user_message, context)
            else:
                self.logger.warning(f"Неизвестный этап booking_stage: {booking_stage}")
                return "Произошла ошибка в процессе записи.", context
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке этапа записи: {e}")
            return "Произошла ошибка. Попробуйте снова.", context
    
    def _handle_initial_confirmation(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает первичное подтверждение записи"""
        user_input = user_message.strip().lower()
        
        if user_input in ['да', 'yes', 'ок', 'окей', 'согласен', 'подтверждаю']:
            message = "Отлично! Для записи мне нужны ваши данные.\n\nВведите ваше имя:"
            context['booking_stage'] = 'collect_first_name'
            return message, context
            
        elif user_input in ['нет', 'no', 'отмена', 'не хочу', 'передумал']:
            message = "Понятно! Если захотите записаться позже - просто напишите мне ✨"
            # Очищаем данные о записи
            context.pop('booking_stage', None)
            context.pop('booking_details', None)
            context.pop('personal_data', None)
            return message, context
            
        else:
            message = """Пожалуйста, ответьте:
• 'ДА' - если хотите записаться
• 'НЕТ' - если передумали"""
            return message, context
    
    def _handle_first_name_collection(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сбор имени"""
        first_name = user_message.strip()
        
        # Простая валидация имени
        if len(first_name) < 2 or len(first_name) > 50:
            message = "Пожалуйста, введите корректное имя (от 2 до 50 символов):"
            return message, context
        
        # Сохраняем имя (НЕ в GPT!)
        if 'personal_data' not in context:
            context['personal_data'] = {}
        context['personal_data']['first_name'] = first_name
        context['booking_stage'] = 'collect_last_name'
        
        message = "Спасибо! Теперь введите вашу фамилию:"
        return message, context
    
    def _handle_last_name_collection(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сбор фамилии"""
        last_name = user_message.strip()
        
        # Простая валидация фамилии
        if len(last_name) < 2 or len(last_name) > 50:
            message = "Пожалуйста, введите корректную фамилию (от 2 до 50 символов):"
            return message, context
        
        # Сохраняем фамилию (НЕ в GPT!)
        context['personal_data']['last_name'] = last_name
        context['booking_stage'] = 'collect_phone'
        
        message = """Отлично! Пожалуйста, укажите номер телефона в международном формате, начиная с плюса (+) и кода страны. Например: +375291234567, +79161234567, +14155550100"""
        return message, context
    
    def _handle_phone_collection(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сбор телефона"""
        phone = user_message.strip()
        
        # Валидация телефона
        if not self._validate_phone(phone):
            message = """Пожалуйста, введите номер телефона в корректном международном формате.
Примеры: +375291234567, +79161234567, +14155550100"""
            return message, context
        
        # Сохраняем телефон (НЕ в GPT!)
        context['personal_data']['phone'] = phone
        context['booking_stage'] = 'final_confirmation'
        
        # Формируем финальное подтверждение с маскированными данными
        message = self._format_final_confirmation(context)
        return message, context
    
    def _handle_final_confirmation(self, user_message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает финальное подтверждение"""
        user_input = user_message.strip().lower()
        
        if user_input in ['да', 'yes', 'подтверждаю', 'ок', 'окей']:
            # Создаем запись
            booking_id = self._create_booking(context)
            message = self._format_success_message(context, booking_id)
            
            # Очищаем персональные данные из контекста после создания записи
            context['booking_stage'] = 'completed'
            # НЕ удаляем personal_data - они могут понадобиться для логирования
            
            return message, context
            
        elif user_input in ['нет', 'no', 'отмена']:
            message = "Запись отменена. Если захотите записаться позже - просто напишите мне ✨"
            # Очищаем данные о записи
            context.pop('booking_stage', None)
            context.pop('booking_details', None)
            context.pop('personal_data', None)
            return message, context
            
        else:
            message = """Для подтверждения напишите 'ДА' или 'ПОДТВЕРЖДАЮ'
Для отмены напишите 'НЕТ' или 'ОТМЕНА'"""
            return message, context
    
    def _validate_phone(self, phone: str) -> bool:
        """Валидирует номер телефона"""
        # Простая регулярка для международного формата
        pattern = r'^\+\d{10,15}$'
        return bool(re.match(pattern, phone))
    
    def _format_final_confirmation(self, context: Dict[str, Any]) -> str:
        """Форматирует сообщение финального подтверждения с маскированными данными"""
        try:
            personal_data = context.get('personal_data', {})
            booking_details = context.get('booking_details', {})
            
            # Маскируем персональные данные
            first_name = personal_data.get('first_name', '')
            last_name = personal_data.get('last_name', '')
            phone = personal_data.get('phone', '')
            
            masked_first_name = first_name[0] + '*' * (len(first_name) - 1) if first_name else ''
            masked_last_name = last_name[0] + '*' * (len(last_name) - 1) if last_name else ''
            masked_phone = phone[:4] + '*' * (len(phone) - 6) + phone[-2:] if len(phone) > 6 else phone
            
            service_name = booking_details.get('service_name', 'Услуга')
            master_name = booking_details.get('master_name', 'Мастер')
            date_time = booking_details.get('date_time', 'Дата и время')
            location = booking_details.get('location', 'Салон красоты Итейра')
            address = booking_details.get('address', 'Минск, ул. Немига, 5 (2 этаж)')
            
            message = f"""ПОДТВЕРЖДЕНИЕ ЗАПИСИ:

Клиент: {masked_first_name} {masked_last_name}
Телефон: {masked_phone}
Услуга: {service_name}
Мастер: {master_name}
Дата и время: {date_time}
Место: {location}
Адрес: {address}

Для подтверждения напишите 'ДА' или 'ПОДТВЕРЖДАЮ'
Для отмены напишите 'НЕТ' или 'ОТМЕНА'"""
            
            return message
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании финального подтверждения: {e}")
            return "Ошибка при формировании подтверждения."
    
    def _create_booking(self, context: Dict[str, Any]) -> str:
        """Создает запись и возвращает ID"""
        try:
            # Генерируем уникальный ID записи
            booking_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"
            
            # Здесь должна быть интеграция с реальной системой записи
            # Пока возвращаем тестовый ID
            
            personal_data = context.get('personal_data', {})
            booking_details = context.get('booking_details', {})
            
            # Логируем создание записи (без вывода персональных данных в обычные логи)
            self.logger.info(f"Создана запись {booking_id} для услуги {booking_details.get('service_name')}")
            
            return booking_id
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании записи: {e}")
            return f"ERROR-{uuid.uuid4().hex[:6].upper()}"
    
    def _format_success_message(self, context: Dict[str, Any], booking_id: str) -> str:
        """Форматирует сообщение об успешном создании записи"""
        try:
            personal_data = context.get('personal_data', {})
            booking_details = context.get('booking_details', {})
            
            first_name = personal_data.get('first_name', '')
            last_name = personal_data.get('last_name', '')
            phone = personal_data.get('phone', '')
            
            service_name = booking_details.get('service_name', 'Услуга')
            master_name = booking_details.get('master_name', 'Мастер')
            date_time = booking_details.get('date_time', 'Дата и время')
            location = booking_details.get('location', 'Салон красоты Итейра')
            address = booking_details.get('address', 'Минск, ул. Немига, 5 (2 этаж)')
            salon_phone = booking_details.get('salon_phone', '+375445903030')
            
            message = f"""ЗАПИСЬ УСПЕШНО СОЗДАНА! (ТЕСТОВЫЙ РЕЖИМ)

Номер записи: {booking_id}
Клиент: {first_name} {last_name}
Телефон: {phone}
Услуга: {service_name}
Мастер: {master_name}
Дата и время: {date_time}
Место: {location}
Адрес: {address}
Телефон: {salon_phone}

Благодарим за доверие и выбор салонов премиум-класса Итейра.
Желаем Вам отличного настроения и красоты в каждом дне! 🌷"""
            
            return message
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании сообщения об успехе: {e}")
            return f"Запись создана! Номер: {booking_id}"
    
    def is_in_booking_process(self, context: Dict[str, Any]) -> bool:
        """Проверяет, находится ли пользователь в процессе подтверждения записи"""
        booking_stage = context.get('booking_stage')
        return booking_stage in self.STAGES and booking_stage != 'completed'
    
    def get_current_stage(self, context: Dict[str, Any]) -> Optional[str]:
        """Возвращает текущий этап процесса записи"""
        return context.get('booking_stage')
