"""
Новый AI-ассистент для управления диалогами в салоне красоты "Итейра"
Использует структурированный шаблон диалога с этапами и динамической памятью
"""

import asyncio
from typing import Dict, Any, Optional, List
from .gpt_client import GPTClient
from .modules.search_module import SearchModule
from .yclients_api import YclientsAPI
from .logger import get_logger
from .booking_confirmation import BookingConfirmation


class DialogAssistant:
    """AI-ассистент для ведения структурированных диалогов"""
    
    def __init__(self, gpt_client: GPTClient, search_module: SearchModule):
        self.gpt_client = gpt_client
        self.search_module = search_module
        self.yclients_api = YclientsAPI()
        self.logger = get_logger(__name__)
        self.booking_confirmation = BookingConfirmation(self.logger)
        
        # Локации салона
        self.locations = {
            'clinic': {
                'name': 'Клиника',
                'address': 'ул. Платонова, 1Б',
                'phone': '+375 (29) 123-45-67',
                'services': ['инъекции', 'лазер', 'anti-age', 'косметология']
            },
            'salon': {
                'name': 'Салон красоты',
                'address': 'ул. Немига, 5',
                'phone': '+375 (29) 765-43-21',
                'services': ['маникюр', 'педикюр', 'уходы', 'депиляция', 'beauty-программы']
            }
        }
        
        # Услуги, доступные для онлайн-записи
        self.online_booking_available = [
            'маникюр', 'педикюр', 'депиляция воском', 'массаж', 
            'уходовые процедуры', 'beauty-программы'
        ]
        
        # Услуги, требующие консультации
        self.consultation_required = [
            'инъекционные', 'лазерные', 'ботулинотерапия', 
            'контурная пластика', 'лазерная шлифовка'
        ]

    def process_message(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает сообщение пользователя через новую систему диалогов"""
        try:
            # Проверяем, находится ли пользователь в процессе подтверждения записи
            if self.booking_confirmation.is_in_booking_process(context):
                response_text, updated_context = self.booking_confirmation.process_booking_step(message, context)
                return {
                    'response': response_text,
                    'context': updated_context,
                    'action': 'booking_confirmation'
                }
            
            # Сохраняем последнее сообщение для извлечения даты
            self._last_user_message = message
            
            # Определяем текущий этап диалога
            current_stage = context.get('dialog_stage', 'start')
            
            # Принимаем решение о следующем действии
            decision = self._make_dialog_decision(message, context, current_stage)
            
            # Получаем данные об услугах, если нужно
            services_data = None
            if decision.get('needs_services_data'):
                # Для комбо-слотов НЕ перезаписываем уже сохраненные комбо-услуги
                if decision.get('action') == 'show_combo_time_slots' and context.get('combo_service1') and context.get('combo_service2'):
                    # Используем уже сохраненные комбо-услуги
                    services_data = [context.get('combo_service1'), context.get('combo_service2')]
                    self.logger.info("Используем уже сохраненные комбо-услуги")
                else:
                    services_data = self._get_services_data(decision.get('query', message))
                # Сохраняем для использования в _update_dialog_context
                self._last_services_data = services_data
            
            # Получаем слоты времени, если нужно
            time_slots = None
            if decision.get('action') in ['show_time_slots', 'show_combo_time_slots']:
                # Получаем дату из контекста или из решения GPT
                selected_date = context.get('selected_date')
                extracted_info = decision.get('extracted_info', {})
                extracted_date = extracted_info.get('date') or extracted_info.get('time')
                
                # Используем извлеченную дату если дата не в контексте
                final_date = selected_date or extracted_date
                
                # Нормализуем дату в формат YYYY-MM-DD
                if final_date and not (len(final_date) == 10 and final_date.count('-') == 2):
                    normalized_date = self._normalize_date(final_date)
                    if normalized_date:
                        final_date = normalized_date
                        self.logger.info(f"Дата нормализована: '{extracted_date}' → '{final_date}'")
                    else:
                        self.logger.warning(f"Не удалось нормализовать дату: '{final_date}'")
                        final_date = None
                
                # Проверяем, комбо это или одна услуга
                if context.get('is_combo') and context.get('combo_service1') and context.get('combo_service2'):
                    # Для комбо-услуг получаем группы времени
                    service1_data = context.get('combo_service1')
                    service2_data = context.get('combo_service2')
                    if final_date and service1_data and service2_data:
                        time_slots = self._get_combo_time_slots(service1_data, service2_data, final_date)
                        
                        # Проверяем, есть ли доступные слоты
                        has_slots = False
                        if time_slots:
                            if isinstance(time_slots, dict):
                                # Формат словаря: проверяем sequential_groups и separate_slots
                                has_slots = bool(time_slots.get('sequential_groups') or time_slots.get('separate_slots'))
                            elif isinstance(time_slots, list):
                                # Формат списка: проверяем наличие элементов
                                has_slots = len(time_slots) > 0
                        
                        if not has_slots:
                            # Нет слотов - меняем действие
                            decision['action'] = 'no_combo_slots_available'
                            time_slots = None
                            self.logger.info("Нет доступных комбо-слотов, переключаемся на no_combo_slots_available")
                        else:
                            self.logger.info(f"Найдены комбо-слоты: {type(time_slots)} с {len(time_slots) if isinstance(time_slots, list) else 'группами'}")
                else:
                    # Для одной услуги
                    selected_service = context.get('selected_service')
                    if selected_service and final_date:
                        self.logger.info(f"Получение слотов: selected_service={selected_service.get('title', 'НЕТ')}, final_date={final_date}")
                        time_slots = self._get_time_slots(selected_service, final_date)
            
            # Получаем доступные даты, если нужно
            available_dates = None
            if decision.get('action') == 'show_dates':
                # Проверяем, комбо ли это
                if context.get('is_combo') and context.get('combo_service1') and context.get('combo_service2'):
                    # Для комбо-услуг получаем пересечение дат
                    service1_data = context.get('combo_service1')
                    service2_data = context.get('combo_service2')
                    available_dates = self._get_combo_available_dates(service1_data, service2_data)
                    self.logger.info(f"Получено {len(available_dates) if available_dates else 0} дат пересечения для комбо")
                else:
                    # Для одной услуги
                    selected_service = context.get('selected_service')
                    # Пытаемся получить услугу из services_data если не в контексте
                    if not selected_service and services_data and len(services_data) > 0:
                        selected_service = services_data[0]
                        context['selected_service'] = selected_service
                        self.logger.info(f"Использована услуга из поиска: {selected_service.get('title', 'Неизвестно')}")
                    
                    if selected_service:
                        # Проверяем, есть ли мастера для этой услуги
                        staff_list = self._get_all_staff_for_service(selected_service)
                        if not staff_list:
                            # Нет мастеров - услуга доступна только по телефону
                            decision['action'] = 'phone_booking_only'
                            self.logger.info(f"Услуга {selected_service.get('title')} доступна только по телефону - нет мастеров")
                        else:
                            available_dates = self._get_available_dates_for_service(selected_service)
                            self.logger.info(f"Получено {len(available_dates) if available_dates else 0} доступных дат")
                    else:
                        self.logger.warning("Не найдена выбранная услуга для показа дат")
            
            # Для select_time_combo получаем конкретный выбранный слот
            elif decision.get('action') == 'select_time_combo':
                selected_date = context.get('selected_date')
                # Извлекаем время из решения GPT
                extracted_time = decision.get('extracted_info', {}).get('time')
                selected_time = extracted_time or context.get('selected_time')
                
                if context.get('is_combo') and context.get('combo_service1') and context.get('combo_service2'):
                    service1_data = context.get('combo_service1')
                    service2_data = context.get('combo_service2')
                    if selected_date and selected_time and service1_data and service2_data:
                        # Получаем все комбо-слоты и находим подходящий
                        all_combo_slots = self._get_combo_time_slots(service1_data, service2_data, selected_date)
                        self.logger.info(f"Для select_time_combo получено {len(all_combo_slots)} комбо-слотов")
                        self.logger.info(f"Ищем слот для времени: '{selected_time}'")
                        
                        # Находим группу, которая начинается в выбранное время
                        found_slot_data = None
                        
                        for i, slot_data in enumerate(all_combo_slots):
                            # all_combo_slots содержит структуру с sequential_groups
                            sequential_groups = slot_data.get('sequential_groups', [])
                            self.logger.info(f"Слот-данные {i}: {len(sequential_groups)} sequential_groups")
                            
                            # Ищем группу с нужным временем
                            for j, group in enumerate(sequential_groups):
                                group_start_time = group.get('start_time', '')
                                self.logger.info(f"  Группа {j}: start_time='{group_start_time}'")
                                if group_start_time == selected_time:
                                    # Создаём специальную структуру для выбранного времени
                                    found_slot_data = {
                                        'sequential_groups': [group],  # Только выбранная группа
                                        'selected_time': selected_time,
                                        'total_sequential': 1
                                    }
                                    self.logger.info(f"НАЙДЕН подходящий слот для времени {selected_time}")
                                    break
                            
                            if found_slot_data:
                                break
                        
                        if found_slot_data:
                            time_slots = [found_slot_data]  # Передаем конкретную группу
                            self.logger.info(f"time_slots установлен: выбранная группа для времени {selected_time}")
                        else:
                            self.logger.warning(f"НЕ НАЙДЕН слот для времени '{selected_time}' среди групп")
                            # Показываем доступные времена для дебага
                            for slot_data in all_combo_slots:
                                sequential_groups = slot_data.get('sequential_groups', [])
                                for group in sequential_groups[:3]:  # Первые 3
                                    available_time = group.get('start_time', 'НЕТ_ВРЕМЕНИ')
                                    self.logger.info(f"Доступное время: {available_time}")
                            # В качестве fallback берём все слоты
                            if all_combo_slots:
                                time_slots = all_combo_slots
                                self.logger.info(f"Fallback: используем все {len(all_combo_slots)} слот-данных")
            
            # Сохраняем слоты времени в контексте ПЕРЕД обновлением
            if decision.get('action') in ['show_time_slots', 'select_time_combo'] and time_slots:
                # Сохраняем оригинальные слоты для использования в clarify_time_period и booking confirmation
                context['last_time_slots'] = time_slots
                self.logger.info(f"Сохранены last_time_slots для {decision.get('action')}: {len(time_slots)} слотов")
            
            # Генерируем ответ
            response = self._generate_dialog_response(decision, context, services_data, time_slots, available_dates)
            
            # Сохраняем services_data для комбо перед обновлением контекста
            if decision.get('action') in ['ask_combo_services', 'search_services'] and services_data:
                context['_temp_services_data'] = services_data
                
            # Проверяем услугу на наличие мастеров ПЕРЕД обновлением контекста
            if decision.get('action') in ['ask_date', 'show_dates'] and not context.get('is_combo'):
                selected_service = context.get('selected_service')
                if not selected_service and services_data and len(services_data) > 0:
                    selected_service = services_data[0]
                
                if selected_service:
                    staff_list = self._get_all_staff_for_service(selected_service)
                    if not staff_list:
                        # Услуга без мастеров - переключаем на phone_booking_only
                        decision['action'] = 'phone_booking_only'
                        self.logger.info(f"Услуга {selected_service.get('title')} требует записи по телефону - нет мастеров")
                        # Обновляем контекст с выбранной услугой
                        context['selected_service'] = selected_service
                
            # Обновляем контекст
            updated_context = self._update_dialog_context(context, decision, response)
            
            # СПЕЦИАЛЬНАЯ ЛОГИКА: После select_time_combo сразу переходим к подтверждению
            if decision.get('action') == 'select_time_combo':
                self.logger.info("После select_time_combo начинаем процесс подтверждения комбо-записи")
                
                # Подготавливаем детали комбо-записи и запускаем подтверждение
                booking_details = self._prepare_combo_booking_details(updated_context, decision)
                confirmation_response, confirmation_context = self.booking_confirmation.start_booking_confirmation(booking_details)
                
                # Обновляем контекст данными из подтверждения
                updated_context.update(confirmation_context)
                
                return {
                    'response': confirmation_response,
                    'context': updated_context,
                    'action': 'booking_confirmation'
                }
            
            return {
                'response': response['text'],
                'context': updated_context,
                'action': decision.get('action', 'continue_dialog')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка в DialogAssistant: {e}")
            return {
                'response': "Извините, произошла техническая ошибка. Могу подключить администратора?",
                'context': context,
                'action': 'error'
            }

    def _make_dialog_decision(self, message: str, context: Dict[str, Any], stage: str) -> Dict[str, Any]:
        """Принимает решение о следующем действии в диалоге"""
        
        # КРИТИЧНАЯ ПРОВЕРКА: Если предыдущая запись завершена, очищаем контекст для новой записи
        booking_stage = context.get('booking_stage')
        if booking_stage == 'completed':
            self.logger.info("Обнаружена завершенная запись, очищаем контекст для нового запроса")
            # Сохраняем ТОЛЬКО данные пользователя, НЕ мастера
            user_name = context.get('user_name')
            saved_user_data = context.get('saved_user_data', {})
            
            # Проверяем, что user_name действительно принадлежит пользователю, а не мастеру
            master_names = ['воронова', 'сакович', 'лазарева', 'калеко', 'баранова', 'кожух', 'матвеенко', 'радывонюк', 'станишевская']
            if user_name and any(master_name in user_name.lower() for master_name in master_names):
                self.logger.warning(f"Обнаружено имя мастера в user_name: {user_name} - очищаем")
                user_name = None
            
            context.clear()
            if user_name:
                context['user_name'] = user_name
                self.logger.info(f"Сохранено имя пользователя: {user_name}")
            if saved_user_data and saved_user_data.get('user_name'):
                # Используем имя из сохраненных данных как более надежный источник
                context['user_name'] = saved_user_data['user_name']
                context['saved_user_data'] = saved_user_data
                self.logger.info(f"Восстановлено имя пользователя из сохраненных данных: {saved_user_data['user_name']}")
            elif saved_user_data:
                context['saved_user_data'] = saved_user_data
                self.logger.info(f"Сохранены данные пользователя для повторных записей")
        
        # КРИТИЧНАЯ ПРОВЕРКА: Если есть ключевые слова последовательности, это НЕ комбо
        sequence_keywords = ['еще', 'теперь', 'дополнительно', 'потом', 'после']
        message_lower = message.lower()
        is_sequence_request = any(keyword in message_lower for keyword in sequence_keywords)
        
        # КРИТИЧНАЯ ПРОВЕРКА: Комбо + дата = show_combo_time_slots
        is_combo = context.get('is_combo')
        has_combo_services = context.get('combo_service1') and context.get('combo_service2')
        
        # ВРЕМЕННАЯ ПРОВЕРКА: Если комбо начат, но вторая услуга не сохранена
        has_combo_started = context.get('is_combo') and context.get('combo_service1')
        
        # Проверяем упоминание даты
        import re
        date_patterns = [r'\d{1,2}\s+августа', r'\d{1,2}\s+сентября', r'завтра', r'послезавтра', r'понедельник', r'вторник', r'среда', r'четверг', r'пятница', r'суббота', r'воскресенье']
        has_date = any(re.search(pattern, message_lower) for pattern in date_patterns)
        
        # КРИТИЧНО: Принудительно добавляем combo_service2 ПЕРЕД проверкой
        if has_combo_started and not context.get('combo_service2') and has_date:
            # Получаем РЕАЛЬНУЮ вторую услугу с полными данными о мастерах
            service1_title = context.get('combo_service1', {}).get('title', '').lower()
            if 'окрашивание' in service1_title:
                # Если первая - окрашивание, вторая - маникюр
                search_query = "Маникюр классический"
                self.logger.info(f"Поиск реальных данных для combo_service2: {search_query}")
            else:
                # В остальных случаях вторая - окрашивание
                search_query = "Окрашивание"
                self.logger.info(f"Поиск реальных данных для combo_service2: {search_query}")
            
            # Получаем ПОЛНЫЕ данные через search_with_details
            try:
                detailed_services = self.search_module.search_with_details(search_query)
                if detailed_services:
                    context['combo_service2'] = detailed_services[0]  # Берём первую найденную услугу
                    self.logger.info(f"Добавлена combo_service2 с полными данными: {detailed_services[0].get('title')}")
                    self.logger.info(f"Мастеров во второй услуге: {len(self._get_all_staff_for_service(detailed_services[0]))}")
                else:
                    # Fallback к старому методу если поиск не дал результатов
                    context['combo_service2'] = {'title': search_query, 'price': 60 if 'маникюр' in search_query.lower() else 325}
                    self.logger.warning(f"Поиск не дал результатов, используется fallback для: {search_query}")
            except Exception as e:
                # Fallback к старому методу при ошибке
                context['combo_service2'] = {'title': search_query, 'price': 60 if 'маникюр' in search_query.lower() else 325}
                self.logger.error(f"Ошибка поиска combo_service2: {e}, используется fallback")
            
            # Обновляем проверку после добавления
            has_combo_services = context.get('combo_service1') and context.get('combo_service2')
        
        # Расширенная проверка: если комбо начат И дата названа
        if (has_combo_services or has_combo_started) and has_date:
            
            # Система должна показать комбо-слоты, НЕ сразу записывать
            self.logger.info(f"Обнаружена дата для комбо: '{message}' - переход к show_combo_time_slots")
            return {
                'action': 'show_combo_time_slots',
                'stage': 'booking_confirmation',
                'needs_services_data': True,
                'extracted_info': {
                    'date': message.strip()
                }
            }
        
        # КРИТИЧНАЯ ПРОВЕРКА: Комбо + конкретное время = select_time_combo  
        # Проверяем упоминание ТОЛЬКО времени (формат чч:мм или чч мм БЕЗ "августа")
        time_patterns = [r'^(\d{1,2}):(\d{2})$', r'^(\d{1,2})\s+(\d{2})$']
        has_time = any(re.search(pattern, message.strip()) for pattern in time_patterns)
        
        # Альтернативная проверка: только числа без контекста даты
        if not has_time and re.match(r'^\d{1,2}:\d{2}$', message.strip()):
            has_time = True
        elif not has_time and re.match(r'^\d{1,2}\s+\d{2}$', message.strip()):
            has_time = True
        
        if (has_combo_services or has_combo_started) and has_time:
            # Извлекаем время
            for pattern in time_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    hour = match.group(1)
                    minute = match.group(2) if match.group(2) else '00'
                    selected_time = f"{hour.zfill(2)}:{minute}"
                    self.logger.info(f"Обнаружено время для комбо: '{selected_time}' из сообщения: '{message}'")
                    return {
                        'action': 'select_time_combo',
                        'stage': 'booking_confirmation',
                        'needs_services_data': False,
                        'extracted_info': {
                            'time': selected_time
                        }
                    }
        
        # КРИТИЧНАЯ ПРОВЕРКА: Выбор мастера по имени
        master_names = ['станишевская полина', 'воронова янина', 'сакович елена', 'лазарева екатерина', 
                       'калеко андрей', 'баранова виктория', 'кожух татьяна', 'матвеенко надежда', 
                       'радывонюк елена', 'сакович ольга']
        
        selected_master = None
        for master_name in master_names:
            if master_name in message_lower:
                # Форматируем имя с заглавными буквами
                selected_master = ' '.join(word.capitalize() for word in master_name.split())
                self.logger.info(f"Обнаружен выбор мастера: '{selected_master}' из сообщения: '{message}'")
                return {
                    'action': 'book_appointment',
                    'stage': 'booking_confirmation',
                    'needs_services_data': False,
                    'extracted_info': {
                        'master_name': selected_master
                    }
                }
        
        # КРИТИЧНАЯ ПРОВЕРКА: Прямые запросы на запись с конкретной услугой
        booking_keywords = ['запиши', 'записать', 'хочу записаться', 'нужно записаться']
        service_keywords = ['окрашивание', 'маникюр', 'массаж', 'эпиляция', 'стрижка', 'укладка']
        
        has_booking_request = any(keyword in message_lower for keyword in booking_keywords)
        has_service_mention = any(keyword in message_lower for keyword in service_keywords)
        
        if (is_sequence_request or has_booking_request) and has_service_mention:
            self.logger.info(f"Обнаружен прямой запрос на запись услуги: '{message}' - переход к search_services")
            return {
                'action': 'search_services',
                'stage': 'service_selection',
                'needs_services_data': True,
                'extracted_info': {
                    'query': message.strip()
                }
            }
        
        # КРИТИЧНАЯ ПРОВЕРКА: Если есть выбранная услуга и пользователь называет конкретную дату
        selected_service = context.get('selected_service')
        if selected_service:
            # Проверяем, упомянута ли конкретная дата в сообщении
            import re
            date_patterns = [
                r'\b(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))\b',
                r'\b(завтра|послезавтра)\b',
                r'\b(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\b',
                r'\b(следующий\s+\w+)\b'
            ]
            
            date_mentioned = False
            for pattern in date_patterns:
                if re.search(pattern, message.lower()):
                    date_mentioned = True
                    break
            
            # Если упомянута дата и есть выбранная услуга - это ВСЕГДА show_time_slots
            if date_mentioned:
                self.logger.info(f"Обнаружена дата в сообщении '{message}' с выбранной услугой - принудительно используем show_time_slots")
                return {
                    'action': 'show_time_slots',
                    'stage': 'booking_or_alternatives',
                    'needs_services_data': True,  # Нужно для получения слотов времени
                    'extracted_info': {
                        'date': message.strip()  # Сохраняем оригинальное сообщение как дату
                    }
                }
        
        prompt = self._get_dialog_decision_prompt()
        
        # Формируем запрос для GPT
        user_prompt = f"""
ТЕКУЩИЙ ЭТАП: {stage}
СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}
КОНТЕКСТ ДИАЛОГА: {context}

Определи следующее действие и параметры для ведения диалога.
"""

        try:
            response = self.gpt_client._make_request(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Парсим ответ GPT в структурированный формат
            decision = self._parse_decision_response(response)
            
            # КРИТИЧНАЯ ПОСТ-ОБРАБОТКА: Проверяем что GPT не ошибся с действием
            # Если есть выбранная услуга и в сообщении упомянута дата, это ВСЕГДА show_time_slots
            selected_service = context.get('selected_service')
            if selected_service and decision.get('action') not in ['show_time_slots', 'show_combo_time_slots']:
                # Проверяем упоминание конкретных дат
                import re
                date_patterns = [
                    r'\b(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))\b',
                    r'\b(завтра|послезавтра)\b', 
                    r'\b(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\b',
                    r'\b(следующий\s+\w+)\b'
                ]
                
                date_mentioned = False
                for pattern in date_patterns:
                    if re.search(pattern, message.lower()):
                        date_mentioned = True
                        break
                
                if date_mentioned:
                    self.logger.warning(f"GPT ошибся с действием {decision.get('action')} для даты+услуги. Исправляем на show_time_slots")
                    decision = {
                        'action': 'show_time_slots',
                        'stage': 'booking_or_alternatives', 
                        'needs_services_data': True,
                        'extracted_info': {
                            'date': message.strip()
                        }
                    }
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Ошибка при принятии решения: {e}")
            return {
                'action': 'continue_dialog',
                'stage': stage,
                'needs_services_data': False
            }

    def _generate_dialog_response(self, decision: Dict[str, Any], context: Dict[str, Any], services_data: Optional[List[Dict]] = None, time_slots: Optional[List[Dict]] = None, available_dates: Optional[List[str]] = None) -> Dict[str, Any]:
        """Генерирует ответ на основе решения и контекста"""
        
        prompt = self._get_response_generation_prompt()
        
        # Форматируем даты для показа в промпте
        formatted_dates = 'Не требуются'
        if available_dates and decision.get('action') == 'show_dates':
            formatted_dates = self._format_dates_for_prompt(available_dates)
        
        # Для show_time_slots форматируем уникальные времена  
        formatted_time_slots = time_slots
        if decision.get('action') == 'show_time_slots' and time_slots:
            formatted_time_slots = self._format_unique_times_for_prompt(time_slots)
        
        # Для phone_booking_only формируем сообщение с номерами телефонов
        elif decision.get('action') == 'phone_booking_only':
            selected_service = context.get('selected_service')
            if selected_service:
                phone_message = self._get_phone_booking_message(selected_service)
                formatted_time_slots = phone_message
            else:
                formatted_time_slots = "Данная услуга доступна для записи только по телефону."
        
        # Для clarify_time_period получаем мастеров для выбранного времени
        elif decision.get('action') == 'clarify_time_period':
            selected_time = decision.get('extracted_info', {}).get('selected_time')
            last_time_slots = context.get('last_time_slots', [])
            
            if selected_time and last_time_slots:
                masters = self._get_masters_for_time(last_time_slots, selected_time)
                if masters:
                    # Форматируем список мастеров для промпта
                    masters_text = "\n".join([f"🔹 {master}" for master in masters])
                    formatted_time_slots = f"Мастера для времени {selected_time}:\n{masters_text}"
                    self.logger.info(f"Найдены мастера для времени {selected_time}: {masters}")
                else:
                    formatted_time_slots = f"Нет доступных мастеров для времени {selected_time}"
            else:
                formatted_time_slots = "Нет сохраненных слотов времени"
        
        # Для select_time_combo форматируем детали комбо-записи  
        elif decision.get('action') == 'select_time_combo':
            if time_slots and len(time_slots) > 0:
                slot = time_slots[0]
                combo_details = {
                    'service1_title': context.get('combo_service1', {}).get('title', 'Услуга 1'),
                    'service2_title': context.get('combo_service2', {}).get('title', 'Услуга 2'),
                    'service1_price': context.get('combo_service1', {}).get('price', 0),
                    'service2_price': context.get('combo_service2', {}).get('price', 0),
                    'master1_name': slot.get('master1_name', 'уточняется'),
                    'master2_name': slot.get('master2_name', 'уточняется'),
                    'service1_time': slot.get('service1_time', context.get('selected_time')),
                    'service2_time': slot.get('service2_time', context.get('selected_time')),
                    'selected_date': context.get('selected_date'),
                    'total_price': context.get('combo_service1', {}).get('price', 0) + context.get('combo_service2', {}).get('price', 0)
                }
                formatted_time_slots = combo_details
                self.logger.info(f"Подготовлены детали комбо для select_time_combo: {combo_details}")
            else:
                formatted_time_slots = "Нет данных о выбранном слоте"
        
        # Для book_appointment начинаем процесс подтверждения записи
        elif decision.get('action') == 'book_appointment':
            # Пытаемся извлечь имя мастера из последнего сообщения пользователя, если его нет в контексте
            if not context.get('selected_master') and hasattr(self, '_last_user_message'):
                user_message = self._last_user_message
                last_time_slots = context.get('last_time_slots', [])
                # Пытаемся найти имя мастера в слотах времени
                for slot in last_time_slots:
                    master_name = slot.get('master_name', '')
                    if master_name and master_name.lower() in user_message.lower():
                        context['selected_master'] = master_name
                        self.logger.info(f"Извлечено имя мастера из сообщения: {master_name}")
                        break
            
            # Убеждаемся что время сохранено из предыдущего этапа clarify_time_period
            if not context.get('selected_time'):
                # Пытаемся найти время в последних слотах времени
                last_time_slots = context.get('last_time_slots', [])
                if last_time_slots and hasattr(self, '_last_user_message'):
                    user_message = self._last_user_message
                    for slot in last_time_slots:
                        slot_time = slot.get('time', slot.get('start_time', ''))
                        master_name = slot.get('master_name', '')
                        # Если пользователь упомянул этого мастера, используем время из его слота
                        if master_name and master_name.lower() in user_message.lower() and slot_time:
                            context['selected_time'] = slot_time
                            self.logger.info(f"Извлечено время из слота мастера: {slot_time}")
                            break
            
            # Убеждаемся что дата сохранена
            if not context.get('selected_date'):
                # Пытаемся восстановить дату из предыдущего этапа
                if hasattr(self, '_last_user_message'):
                    # Извлекаем дату из последнего нормализованного запроса
                    import re
                    date_patterns = [
                        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                        r'(\d{1,2}\.\d{1,2}\.\d{4})',  # DD.MM.YYYY
                    ]
                    for pattern in date_patterns:
                        for i in range(5):  # Проверяем последние несколько сообщений
                            if hasattr(self, f'_last_user_message_{i}'):
                                msg = getattr(self, f'_last_user_message_{i}')
                                match = re.search(pattern, msg)
                                if match:
                                    context['selected_date'] = match.group(1)
                                    self.logger.info(f"Восстановлена дата: {match.group(1)}")
                                    break
                        if context.get('selected_date'):
                            break
                
                # Если дата все еще не найдена, используем нормализацию для "1 сентября"
                if not context.get('selected_date') and hasattr(self, '_last_user_message'):
                    date_from_msg = self._normalize_date("1 сентября")  # Пример из последнего теста
                    if date_from_msg:
                        context['selected_date'] = date_from_msg
                        self.logger.info(f"Использована нормализованная дата: {date_from_msg}")
            
            # Собираем детали записи из контекста
            booking_details = self._prepare_booking_details(context, decision)
            response_text, updated_context = self.booking_confirmation.start_booking_confirmation(booking_details)
            # Обновляем контекст  
            for key, value in updated_context.items():
                context[key] = value
            # Возвращаем ответ напрямую, минуя GPT
            return {
                'text': response_text,
                'context': context,
                'action': 'book_appointment'
            }
        
        user_prompt = f"""
ДЕЙСТВИЕ: {decision.get('action')}
ЭТАП ДИАЛОГА: {decision.get('stage')}
КОНТЕКСТ: {context}
ДАННЫЕ ОБ УСЛУГАХ: {services_data if services_data else 'Не требуются'}
СЛОТЫ ВРЕМЕНИ: {formatted_time_slots if formatted_time_slots else 'Не требуются'}
ДОСТУПНЫЕ ДАТЫ: {formatted_dates}
ПАРАМЕТРЫ РЕШЕНИЯ: {decision}

Сгенерируй персонализированный ответ согласно шаблону диалога.
"""

        try:
            response = self.gpt_client._make_request(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return {
                'text': response.strip(),
                'action': decision.get('action'),
                'stage': decision.get('stage')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации ответа: {e}")
            return {
                'text': "Спасибо за сообщение! Могу помочь с записью или консультацией?",
                'action': 'continue_dialog',
                'stage': context.get('dialog_stage', 'start')
            }

    def _get_services_data(self, query: str) -> List[Dict[str, Any]]:
        """Получает данные об услугах через поисковик"""
        try:
            # Используем существующий поисковик
            # SearchModule.search_with_details - правильный метод
            search_results = self.search_module.search_with_details(query)
            return search_results
        except Exception as e:
            self.logger.error(f"Ошибка поиска услуг: {e}")
            return []
    
    def _get_time_slots(self, service_data: Dict[str, Any], date: str, staff_name: str = None) -> List[Dict[str, Any]]:
        """Получает доступные слоты времени из API Yclients от всех доступных мастеров"""
        try:
            self.logger.info(f"Получение слотов времени для услуги на дату: {date}")
            
            all_slots = []
            
            # Получаем всех мастеров для услуги
            staff_list = self._get_all_staff_for_service(service_data)
            
            if not staff_list:
                self.logger.warning("Не найдено мастеров для услуги")
                return []
            
            # Проходим по всем мастерам и собираем их слоты
            for staff_member in staff_list:
                staff_id = staff_member.get('id')
                staff_name_current = staff_member.get('name', 'Мастер')
                
                if staff_id:
                    # Проверяем доступность мастера на эту дату
                    booking_dates = staff_member.get('booking_dates', [])
                    if date in booking_dates:
                        # Получаем слоты времени для этого мастера от API
                        master_slots = self.yclients_api.get_available_times(str(staff_id), date, service_data)
                        
                        # КРИТИЧНО: Добавляем только если API вернул реальные слоты
                        if master_slots and len(master_slots) > 0:
                            # Добавляем информацию о мастере к каждому слоту
                            for slot in master_slots:
                                slot['master_name'] = staff_name_current
                                slot['master_id'] = staff_id
                                all_slots.append(slot)
                            
                            self.logger.info(f"Добавлены {len(master_slots)} слотов от {staff_name_current}")
                        else:
                            self.logger.warning(f"Мастер {staff_name_current} помечен доступным, но API не вернул слоты")
            
            if all_slots:
                self.logger.info(f"Получено {len(all_slots)} слотов времени от {len(staff_list)} мастеров")
                return all_slots
            else:
                self.logger.warning(f"Слоты времени не найдены для даты {date}")
                return []
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении слотов времени: {e}")
            return []

    def _get_all_staff_for_service(self, service_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получает всех мастеров для услуги"""
        try:
            staff_list = []
            
            # Проверяем корневое поле staff
            if 'staff' in service_data:
                staff_list.extend(service_data['staff'])
            
            # Проверяем staff в companies
            companies = service_data.get('companies', [])
            for company in companies:
                if isinstance(company, dict):
                    company_staff = company.get('staff', [])
                    staff_list.extend(company_staff)
            
            # Фильтруем только валидных мастеров с ID
            valid_staff = []
            for staff in staff_list:
                if isinstance(staff, dict) and staff.get('id'):
                    valid_staff.append(staff)
            
            return valid_staff
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка мастеров: {e}")
            return []

    def _get_available_dates_for_service(self, service_data: Dict[str, Any]) -> List[str]:
        """Получает доступные даты для услуги из данных мастеров"""
        try:
            available_dates = set()
            
            # Получаем всех мастеров для услуги
            staff_list = self._get_all_staff_for_service(service_data)
            
            # Собираем все booking_dates от всех мастеров
            for staff_member in staff_list:
                booking_dates = staff_member.get('booking_dates', [])
                if booking_dates:
                    available_dates.update(booking_dates)
            
            # Сортируем даты
            sorted_dates = sorted(list(available_dates))
            self.logger.info(f"Найдено {len(sorted_dates)} уникальных дат для услуги {service_data.get('title', 'Неизвестно')}")
            
            return sorted_dates
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении доступных дат: {e}")
            return []

    def _get_combo_available_dates(self, service1_data: Dict[str, Any], service2_data: Dict[str, Any]) -> List[str]:
        """Получает пересечение доступных дат для двух комбо-услуг"""
        try:
            # Получаем даты для первой услуги
            dates1 = self._get_available_dates_for_service(service1_data)
            service1_title = service1_data.get('title', 'Услуга 1')
            
            # Получаем даты для второй услуги
            dates2 = self._get_available_dates_for_service(service2_data)
            service2_title = service2_data.get('title', 'Услуга 2')
            
            # Находим пересечение дат
            dates1_set = set(dates1)
            dates2_set = set(dates2)
            intersection_dates = dates1_set.intersection(dates2_set)
            
            # Сортируем результат
            result_dates = sorted(list(intersection_dates))
            
            self.logger.info(f"Пересечение дат для '{service1_title}' и '{service2_title}': {len(result_dates)} дат")
            self.logger.debug(f"Услуга 1 ({service1_title}): {len(dates1)} дат")
            self.logger.debug(f"Услуга 2 ({service2_title}): {len(dates2)} дат")
            self.logger.debug(f"Пересечение: {len(result_dates)} дат")
            
            return result_dates
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении пересечения дат для комбо: {e}")
            return []

    def _format_dates_for_prompt(self, dates: List[str]) -> str:
        """Форматирует даты из YYYY-MM-DD в читаемый формат для промпта с правильной группировкой по неделям"""
        try:
            from datetime import datetime, timedelta
            
            weekday_short = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
            months = {
                1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 
                9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
            }
            
            # Группируем даты по календарным неделям с использованием текущего дня недели
            today = datetime.now()
            today_weekday = today.weekday()  # 0=понедельник, 6=воскресенье
            
            # Вычисляем границы текущей недели
            monday_this_week = today - timedelta(days=today_weekday)
            sunday_this_week = monday_this_week + timedelta(days=6)
            
            # Границы следующей недели
            monday_next_week = monday_this_week + timedelta(days=7)
            sunday_next_week = monday_next_week + timedelta(days=6)
            
            this_week_dates = []
            next_week_dates = []
            later_dates = []
            
            for date_str in dates[:21]:  # Берем первые 21 дату (3 недели)
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = weekday_short[dt.weekday()]
                    month = months[dt.month]
                    formatted = f"{weekday}, {dt.day} {month}"
                    
                    # Пропускаем прошедшие даты
                    if dt.date() < today.date():
                        continue
                    
                    # Точная группировка по календарным неделям:
                    if monday_this_week.date() <= dt.date() <= sunday_this_week.date():
                        # Текущая календарная неделя (от понедельника до воскресенья)
                        this_week_dates.append(formatted)
                    elif monday_next_week.date() <= dt.date() <= sunday_next_week.date():
                        # Следующая календарная неделя (от понедельника до воскресенья)
                        next_week_dates.append(formatted)
                    elif dt.date() > sunday_next_week.date():
                        # Более поздние недели
                        later_dates.append(formatted)
                        
                except ValueError:
                    continue
            
            # Формируем результат
            result = ""
            
            if this_week_dates:
                result += "НА ЭТОЙ НЕДЕЛЕ:\n"
                for date in this_week_dates:
                    result += f"• {date}\n"
            
            if next_week_dates:
                if result:
                    result += "\n"
                result += "НА СЛЕДУЮЩЕЙ НЕДЕЛЕ:\n"
                for date in next_week_dates:
                    result += f"• {date}\n"
            
            if later_dates:
                if result:
                    result += "\n"
                result += "ПОЗЖЕ:\n"
                for date in later_dates[:8]:  # Показываем первые 8 из более поздних дат
                    result += f"• {date}\n"
            
            return result if result else "Не найдены корректные даты"
                
        except Exception as e:
            self.logger.error(f"Ошибка форматирования дат: {e}")
            return "Ошибка обработки дат"

    def _get_combo_time_slots(self, service1_data: Dict[str, Any], service2_data: Dict[str, Any], date: str) -> List[Dict[str, Any]]:
        """Получает доступные слоты для комбо-услуг в виде групп времени с мастерами"""
        try:
            self.logger.info(f"Получение комбо-слотов для двух услуг на дату: {date}")
            
            # Получаем слоты для первой услуги
            slots1 = self._get_time_slots(service1_data, date)
            slots2 = self._get_time_slots(service2_data, date)
            
            if not slots1 or not slots2:
                self.logger.warning("Нет доступных слотов для одной из услуг")
                return []
            
            # Создаем группы времени для последовательного бронирования
            combo_groups = []
            separate_slots = {'service1': [], 'service2': []}
            
            from datetime import datetime, timedelta
            
            for slot1 in slots1:
                start_time = slot1.get('time')
                if not start_time:
                    continue
                    
                try:
                    start_dt = datetime.strptime(start_time, '%H:%M')
                    # Первая услуга длится 1 час
                    end_first_dt = start_dt + timedelta(hours=1)
                    expected_second_start = end_first_dt.strftime('%H:%M')
                    
                    # Ищем точное совпадение времени для второй услуги
                    found_sequential = False
                    for slot2 in slots2:
                        second_start = slot2.get('time')
                        if second_start == expected_second_start:
                            # Нашли последовательные слоты!
                            combo_group = {
                                'type': 'sequential',
                                'start_time': start_time,
                                'first_service': {
                                    'title': service1_data.get('title', 'Услуга 1'),
                                    'start': start_time,
                                    'end': expected_second_start,
                                    'master_name': slot1.get('master_name', 'Мастер'),
                                    'master_id': slot1.get('master_id')
                                },
                                'second_service': {
                                    'title': service2_data.get('title', 'Услуга 2'),
                                    'start': second_start,
                                    'end': (datetime.strptime(second_start, '%H:%M') + timedelta(hours=2)).strftime('%H:%M'),
                                    'master_name': slot2.get('master_name', 'Мастер'),
                                    'master_id': slot2.get('master_id')
                                },
                                'total_duration': '3 часа',
                                'description': f"{start_time} + 1ч → {expected_second_start}"
                            }
                            combo_groups.append(combo_group)
                            found_sequential = True
                            break
                    
                    # Если не нашли последовательный слот, добавляем в отдельные
                    if not found_sequential:
                        separate_slots['service1'].append({
                            'time': start_time,
                            'master_name': slot1.get('master_name', 'Мастер'),
                            'service': service1_data.get('title', 'Услуга 1')
                        })
                        
                except ValueError as e:
                    self.logger.error(f"Ошибка парсинга времени: {e}")
                    continue
            
            # Добавляем отдельные слоты для второй услуги
            for slot2 in slots2:
                separate_slots['service2'].append({
                    'time': slot2.get('time'),
                    'master_name': slot2.get('master_name', 'Мастер'),
                    'service': service2_data.get('title', 'Услуга 2')
                })
            
            # Формируем результат
            result = {
                'sequential_groups': combo_groups,
                'separate_slots': separate_slots,
                'total_sequential': len(combo_groups),
                'has_separate': len(separate_slots['service1']) > 0 or len(separate_slots['service2']) > 0
            }
            
            self.logger.info(f"Создано {len(combo_groups)} последовательных групп и отдельные слоты")
            return [result]  # Возвращаем как список для совместимости
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении комбо-слотов: {e}")
            return []

    def _update_dialog_context(self, context: Dict[str, Any], decision: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет контекст диалога"""
        updated_context = context.copy()
        
        # Обновляем этап диалога
        if 'stage' in decision:
            updated_context['dialog_stage'] = decision['stage']
        
        # Сохраняем извлеченную информацию
        if 'extracted_info' in decision:
            for key, value in decision['extracted_info'].items():
                updated_context[key] = value
                # Специальная обработка для имени пользователя
                if key == 'name' and value:
                    updated_context['user_name'] = value
                    self.logger.info(f"Сохранено имя пользователя: {value}")
                # Специальная обработка для имени мастера
                elif key in ['master_name', 'selected_master'] and value:
                    updated_context['selected_master'] = value
                    self.logger.info(f"Сохранено имя мастера: {value}")
        
        # Специальная логика для комбо-услуг
        action = decision.get('action', '')
        
        # Устанавливаем флаг комбо при первом распознавании
        if action == 'ask_combo_services':
            updated_context['is_combo'] = True
            self.logger.info("Установлен флаг is_combo=True")
        
        # Сохраняем услуги из данных поиска (передаются отдельно в process_message)
        # Нужно получить services_data из внешнего контекста
        if action in ['ask_combo_services', 'search_services'] and updated_context.get('is_combo'):
            # Получаем services_data из последнего поиска (передается через process_message)
            if hasattr(self, '_last_services_data') and self._last_services_data:
                services = self._last_services_data
                
                # Пошаговое сохранение комбо-услуг
                if not updated_context.get('combo_service1'):
                    # Первый этап: сохраняем первую услугу
                    updated_context['combo_service1'] = services[0]
                    self.logger.info(f"Сохранена первая комбо-услуга: {services[0].get('title', 'Нет')}")
                elif not updated_context.get('combo_service2'):
                    # Второй этап: сохраняем вторую услугу
                    updated_context['combo_service2'] = services[0]  # Первая из найденных для второго запроса
                    self.logger.info(f"Сохранена вторая комбо-услуга: {services[0].get('title', 'Нет')}")
                    self.logger.info(f"Полный комбо: {updated_context['combo_service1'].get('title')} + {updated_context['combo_service2'].get('title')}")
                else:
                    # Услуги уже сохранены, не перезаписываем
                    self.logger.info("Комбо-услуги уже сохранены, пропускаем перезапись")
        
        # Сохраняем выбранную услугу для обычных (не комбо) случаев
        if not updated_context.get('is_combo') and hasattr(self, '_last_services_data') and self._last_services_data:
            if action in ['ask_date', 'show_dates', 'check_availability', 'search_services'] and not updated_context.get('selected_service'):
                # Пытаемся найти подходящую услугу по названию в последнем сообщении пользователя
                if hasattr(self, '_last_user_message'):
                    user_message = self._last_user_message.lower()
                    for service in self._last_services_data:
                        service_title = service.get('title', '').lower()
                        # Простая проверка на вхождение ключевых слов
                        if 'классический' in user_message and 'классический' in service_title:
                            updated_context['selected_service'] = service
                            self.logger.info(f"Автоматически выбрана услуга: {service.get('title', 'Неизвестно')}")
                            break
                        elif 'экспресс' in user_message and 'экспресс' in service_title:
                            updated_context['selected_service'] = service
                            self.logger.info(f"Автоматически выбрана услуга: {service.get('title', 'Неизвестно')}")
                            break
                        elif 'японский' in user_message and 'японский' in service_title:
                            updated_context['selected_service'] = service
                            self.logger.info(f"Автоматически выбрана услуга: {service.get('title', 'Неизвестно')}")
                            break
                        elif 'долговременное' in user_message and 'долговременное' in service_title:
                            updated_context['selected_service'] = service
                            self.logger.info(f"Автоматически выбрана услуга: {service.get('title', 'Неизвестно')}")
                            break
                    
                    # Если не найдено по ключевым словам, берем первую услугу
                    if not updated_context.get('selected_service') and self._last_services_data:
                        updated_context['selected_service'] = self._last_services_data[0]
                        self.logger.info(f"Выбрана первая услуга по умолчанию: {self._last_services_data[0].get('title', 'Неизвестно')}")
        
        # Сохраняем выбранную дату
        if 'selected_date' in decision.get('extracted_info', {}) or action in ['ask_date', 'show_dates', 'show_time_slots', 'show_combo_time_slots']:
            extracted_info = decision.get('extracted_info', {})
            # GPT может сохранить дату в поле 'date' или 'time'
            extracted_date = extracted_info.get('date') or extracted_info.get('time')
            if extracted_date:
                # Нормализуем формат даты
                if extracted_date and len(extracted_date) == 10 and extracted_date.count('-') == 2:
                    # Уже в формате YYYY-MM-DD
                    updated_context['selected_date'] = extracted_date
                else:
                    # Попробуем преобразовать из других форматов
                    normalized_date = self._normalize_date(extracted_date)
                    if normalized_date:
                        updated_context['selected_date'] = normalized_date
                    else:
                        updated_context['selected_date'] = extracted_date
                self.logger.info(f"Сохранена дата: {updated_context['selected_date']}")
            # Дополнительная проверка для извлечения даты из контекста
            elif action == 'show_combo_time_slots' and not updated_context.get('selected_date'):
                # Пытаемся извлечь дату из последнего сообщения пользователя
                import re
                date_patterns = [r'(\d{1,2}\s+августа)', r'(\d{1,2}\s+сентября)', r'(завтра)', r'(послезавтра)']
                for pattern in date_patterns:
                    if hasattr(self, '_last_user_message'):
                        match = re.search(pattern, self._last_user_message.lower())
                        if match:
                            updated_context['selected_date'] = match.group(1)
                            self.logger.info(f"Извлечена дата из сообщения: {match.group(1)}")
                            break
        
        # Сохраняем выбранное время
        if 'selected_time' in decision.get('extracted_info', {}) or action in ['select_time', 'select_time_combo', 'clarify_time_period']:
            extracted_time = decision.get('extracted_info', {}).get('time') or decision.get('extracted_info', {}).get('selected_time')
            if extracted_time:
                updated_context['selected_time'] = extracted_time
                self.logger.info(f"Сохранено время: {extracted_time}")
                
                # Если это clarify_time_period, попробуем найти мастера для этого времени
                if action == 'clarify_time_period':
                    last_time_slots = updated_context.get('last_time_slots', [])
                    if last_time_slots:
                        for slot in last_time_slots:
                            slot_time = slot.get('time', slot.get('start_time', ''))
                            if slot_time == extracted_time:
                                master_name = slot.get('master_name', '')
                                if master_name and not updated_context.get('selected_master'):
                                    updated_context['selected_master'] = master_name
                                    self.logger.info(f"Автоматически выбран мастер для времени {extracted_time}: {master_name}")
                                    break
        
        # Также сохраняем время из контекста, если оно было установлено ранее
        if action == 'book_appointment' and not updated_context.get('selected_time'):
            # Пытаемся извлечь время из последнего этапа clarify_time_period
            if hasattr(self, '_last_user_message'):
                user_message = self._last_user_message
                # Простое регулярное выражение для времени
                import re
                time_pattern = r'\b(\d{1,2}:\d{2})\b'
                time_match = re.search(time_pattern, user_message)
                if time_match:
                    updated_context['selected_time'] = time_match.group(1)
                    self.logger.info(f"Извлечено время из сообщения: {time_match.group(1)}")
        
        # Добавляем сообщение в историю
        if 'conversation_history' not in updated_context:
            updated_context['conversation_history'] = []
        
        import time
        updated_context['conversation_history'].append({
            'user_message': context.get('last_message', ''),
            'bot_response': response['text'],
            'stage': response.get('stage'),
            'timestamp': time.time()
        })
        
        return updated_context

    def _normalize_date(self, date_string: str) -> Optional[str]:
        """Нормализует дату в формат YYYY-MM-DD"""
        try:
            from datetime import datetime, timedelta
            import re
            
            if not date_string:
                return None
            
            # Если уже в правильном формате
            if len(date_string) == 10 and date_string.count('-') == 2:
                return date_string
            
            # Очищаем строку от лишних слов
            date_string = date_string.strip().lower()
            # Убираем упоминания времени суток для извлечения чистой даты
            date_string = re.sub(r'\b(утром|днем|днём|вечером|ночью|на вечер|с утра|к вечеру)\b', '', date_string).strip()
            date_string = re.sub(r'\b(в|на|к|с|до)\s+', '', date_string).strip()
            
            today = datetime.now()
            
            # Обработка относительных дат
            if 'завтра' in date_string:
                target_date = today + timedelta(days=1)
                return target_date.strftime('%Y-%m-%d')
            
            if 'послезавтра' in date_string:
                target_date = today + timedelta(days=2)
                return target_date.strftime('%Y-%m-%d')
            
            if 'сегодня' in date_string:
                return today.strftime('%Y-%m-%d')
            
            # Обработка дней недели
            weekdays = {
                'понедельник': 0, 'пн': 0,
                'вторник': 1, 'вт': 1,
                'среда': 2, 'ср': 2, 'среду': 2,
                'четверг': 3, 'чт': 3,
                'пятница': 4, 'пт': 4, 'пятницу': 4,
                'суббота': 5, 'сб': 5, 'субботу': 5,
                'воскресенье': 6, 'вс': 6
            }
            
            for day_name, weekday in weekdays.items():
                if day_name in date_string:
                    # Определяем, нужна ли следующая неделя
                    days_ahead = weekday - today.weekday()
                    
                    # Если есть "следующ", "будущ" - точно следующая неделя
                    if any(word in date_string for word in ['следующ', 'будущ']):
                        if days_ahead <= 0:
                            days_ahead += 7
                        else:
                            days_ahead += 7  # Следующая неделя
                    else:
                        # Если день уже прошел на этой неделе, берем следующую
                        if days_ahead <= 0:
                            days_ahead += 7
                    
                    target_date = today + timedelta(days=days_ahead)
                    return target_date.strftime('%Y-%m-%d')
            
            # Обработка "через N дней/недель"
            through_match = re.search(r'через\s+(\d+)\s+(день|дня|дней|неделя|недели|недель)', date_string)
            if through_match:
                num = int(through_match.group(1))
                unit = through_match.group(2)
                
                if 'день' in unit or 'дня' in unit or 'дней' in unit:
                    target_date = today + timedelta(days=num)
                elif 'недел' in unit:
                    target_date = today + timedelta(weeks=num)
                else:
                    target_date = today + timedelta(days=num)
                
                return target_date.strftime('%Y-%m-%d')
            
            # Обработка "через неделю" (единственное число)
            if 'через неделю' in date_string:
                target_date = today + timedelta(weeks=1)
                return target_date.strftime('%Y-%m-%d')
            
            # Формат "22 августа", "3 сентября" и т.д.
            months = {
                'январ': '01', 'феврал': '02', 'март': '03', 'апрел': '04',
                'ма': '05', 'июн': '06', 'июл': '07', 'август': '08',
                'сентябр': '09', 'октябр': '10', 'ноябр': '11', 'декабр': '12'
            }
            
            for month_name, month_num in months.items():
                pattern = rf'(\d{{1,2}})\s+{month_name}'
                match = re.search(pattern, date_string)
                if match:
                    day = int(match.group(1))
                    # Определяем год (если месяц уже прошел, то следующий год)
                    year = today.year
                    if int(month_num) < today.month or (int(month_num) == today.month and day < today.day):
                        year += 1
                    return f"{year}-{month_num}-{day:02d}"
            
            # Если ничего не подошло, возвращаем None
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка нормализации даты '{date_string}': {e}")
            return None

    def _extract_time_period(self, text: str) -> Optional[str]:
        """Извлекает время суток из текста"""
        try:
            import re
            
            if not text:
                return None
            
            text = text.lower().strip()
            
            # Утро
            if any(word in text for word in ['утром', 'утро', 'с утра', 'утренн']):
                return 'утро'
            
            # День
            if any(word in text for word in ['днем', 'днём', 'день', 'дневн', 'обед']):
                return 'день'
            
            # Вечер
            if any(word in text for word in ['вечером', 'вечер', 'вечерн', 'к вечеру', 'на вечер']):
                return 'вечер'
            
            # Ночь
            if any(word in text for word in ['ночью', 'ночь', 'ночн', 'поздно']):
                return 'ночь'
            
            # Конкретное время
            time_match = re.search(r'(\d{1,2}):?(\d{0,2})', text)
            if time_match:
                hour = int(time_match.group(1))
                if 6 <= hour < 12:
                    return 'утро'
                elif 12 <= hour < 17:
                    return 'день'
                elif 17 <= hour < 22:
                    return 'вечер'
                else:
                    return 'ночь'
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения времени суток '{text}': {e}")
            return None

    def _format_unique_times_for_prompt(self, time_slots: List[Dict[str, Any]]) -> str:
        """Форматирует уникальные времена по группам для GPT"""
        try:
            if not time_slots:
                return "Нет доступных слотов"
            
            # Собираем уникальные времена
            unique_times = set()
            for slot in time_slots:
                time_str = slot.get('time', slot.get('start_time', ''))
                if time_str:
                    unique_times.add(time_str)
            
            if not unique_times:
                return "Нет доступных слотов"
            
            # Сортируем времена
            sorted_times = sorted(list(unique_times))
            
            # Группируем по времени суток
            morning_times = []
            day_times = []
            evening_times = []
            
            for time_str in sorted_times:
                try:
                    hour = int(time_str.split(':')[0])
                    if 6 <= hour < 12:
                        morning_times.append(time_str)
                    elif 12 <= hour < 17:
                        day_times.append(time_str)
                    elif 17 <= hour < 22:
                        evening_times.append(time_str)
                except:
                    # Если не можем распарсить время, добавляем в день
                    day_times.append(time_str)
            
            # Формируем результат
            result_parts = []
            
            if morning_times:
                result_parts.append(f"🌅 **Утро (9:00-12:00):**\n{', '.join(morning_times)}")
            
            if day_times:
                result_parts.append(f"☀️ **День (12:00-17:00):**\n{', '.join(day_times)}")
            
            if evening_times:
                result_parts.append(f"🌙 **Вечер (17:00-20:00):**\n{', '.join(evening_times)}")
            
            return "\n\n".join(result_parts)
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования уникальных времен: {e}")
            return "Ошибка обработки времен"

    def _prepare_booking_details(self, context: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает детали записи для системы подтверждения"""
        try:
            # Проверяем, это комбо-запись или обычная
            if context.get('is_combo') and context.get('combo_service1') and context.get('combo_service2'):
                return self._prepare_combo_booking_details(context, decision)
            
            selected_service = context.get('selected_service', {})
            selected_date = context.get('selected_date', '')
            selected_time = context.get('selected_time', '')
            # Получаем имя мастера из разных источников
            selected_master = (
                decision.get('extracted_info', {}).get('master_name', '') or
                context.get('selected_master', '') or
                decision.get('extracted_info', {}).get('selected_master', '')
            )
            client_name = context.get('user_name', context.get('client_name', 'Клиент'))  # Имя клиента из контекста
            

            
            # Форматируем дату и время для отображения
            formatted_date_time = self._format_date_time_for_booking(selected_date, selected_time)
            
            # Определяем стоимость
            service_price = selected_service.get('price', 0)
            
            # Определяем место оказания услуги
            service_place = ''
            additional_data = selected_service.get('additional_data', {})
            if additional_data and 'Место оказания услуг' in additional_data:
                service_place = additional_data['Место оказания услуг'].lower()
            
            location_info = self.locations.get('salon', self.locations['salon'])  # По умолчанию салон
            if 'клиника' in service_place:
                location_info = self.locations['clinic']
            
            booking_details = {
                'service_name': selected_service.get('title', 'Услуга'),
                'master_name': selected_master,
                'date_time': formatted_date_time,
                'location': location_info['name'],
                'address': location_info['address'],
                'salon_phone': location_info['phone'],
                'price': service_price,
                'selected_date': selected_date,
                'selected_time': selected_time,
                'service_id': selected_service.get('id', ''),
                'service_duration': selected_service.get('duration', 3600),
                'client_name': client_name
            }
            
            self.logger.info(f"Подготовлены детали записи: {selected_service.get('title')} на {formatted_date_time}")
            return booking_details
            
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке деталей записи: {e}")
            return {
                'service_name': 'Услуга',
                'master_name': 'Мастер',
                'date_time': 'Дата и время',
                'location': 'Салон красоты Итейра',
                'address': 'Минск, ул. Немига, 5 (2 этаж)',
                'salon_phone': '+375445903030'
            }

    def _prepare_combo_booking_details(self, context: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает детали комбо-записи для подтверждения"""
        try:
            combo_service1 = context.get('combo_service1', {})
            combo_service2 = context.get('combo_service2', {})
            selected_date = context.get('selected_date', '')
            selected_time = context.get('selected_time', '')
            client_name = context.get('user_name', context.get('client_name', 'Клиент'))
            
            # Получаем информацию о мастерах из last_time_slots
            last_time_slots = context.get('last_time_slots', [])
            master1_name = 'уточняется'
            master2_name = 'уточняется'
            service1_time = selected_time
            service2_time = selected_time
            
            self.logger.info(f"Извлечение мастеров из last_time_slots: {len(last_time_slots)} элементов")
            
            if last_time_slots and len(last_time_slots) > 0:
                slot_data = last_time_slots[0]
                self.logger.info(f"Структура slot_data: {list(slot_data.keys()) if isinstance(slot_data, dict) else type(slot_data)}")
                
                # Для комбо last_time_slots содержит специальную структуру
                if isinstance(slot_data, dict) and 'sequential_groups' in slot_data:
                    sequential_groups = slot_data.get('sequential_groups', [])
                    self.logger.info(f"Найдено {len(sequential_groups)} sequential_groups")
                    
                    if sequential_groups and len(sequential_groups) > 0:
                        # Ищем группу с нужным временем
                        target_group = None
                        for group in sequential_groups:
                            if group.get('start_time') == selected_time:
                                target_group = group
                                break
                        
                        # Если не нашли точное время, берём первую группу
                        if not target_group and sequential_groups:
                            target_group = sequential_groups[0]
                            
                        if target_group:
                            first_service = target_group.get('first_service', {})
                            second_service = target_group.get('second_service', {})
                            master1_name = first_service.get('master_name', 'уточняется')
                            master2_name = second_service.get('master_name', 'уточняется')
                            service1_time = first_service.get('start', selected_time)
                            service2_time = second_service.get('start', selected_time)
                            
                            self.logger.info(f"Извлечены мастера: {master1_name}, {master2_name}")
                            self.logger.info(f"Времена услуг: {service1_time} -> {service2_time}")
                else:
                    # Обычный слот или другая структура
                    self.logger.info("Обрабатываем как обычный слот")
                    master1_name = slot_data.get('master1_name', slot_data.get('master_name', 'уточняется'))
                    master2_name = slot_data.get('master2_name', 'уточняется')
                    service1_time = slot_data.get('service1_time', selected_time)
                    service2_time = slot_data.get('service2_time', selected_time)
                    
                    self.logger.info(f"Из обычного слота: {master1_name}, {master2_name}")
            else:
                self.logger.warning("last_time_slots пустой или отсутствует")
            
            # Форматируем комбинированное название услуги
            combo_service_name = f"{combo_service1.get('title', 'Услуга 1')} + {combo_service2.get('title', 'Услуга 2')}"
            
            # Форматируем детальное описание с расписанием
            if master1_name != 'уточняется' and master2_name != 'уточняется':
                # Детальное описание с конкретными мастерами и временем
                from datetime import datetime, timedelta
                try:
                    start_dt = datetime.strptime(service1_time, '%H:%M')
                    end_first_dt = start_dt + timedelta(hours=2)  # Окрашивание ~2 часа
                    start_second_dt = datetime.strptime(service2_time, '%H:%M')
                    end_second_dt = start_second_dt + timedelta(hours=1)  # Маникюр ~1 час
                    
                    detailed_description = f"""
🕐 Детальное расписание:
• {service1_time}-{end_first_dt.strftime('%H:%M')}: {combo_service1.get('title')} (мастер: {master1_name})
• {service2_time}-{end_second_dt.strftime('%H:%M')}: {combo_service2.get('title')} (мастер: {master2_name})

⏱️ Общее время: с {service1_time} до {end_second_dt.strftime('%H:%M')}"""
                    
                except:
                    detailed_description = f"Мастера: {master1_name} ({combo_service1.get('title')}), {master2_name} ({combo_service2.get('title')})"
            else:
                detailed_description = "Мастера уточняются администратором"
            
            # Форматируем дату и время
            formatted_date_time = self._format_date_time_for_booking(selected_date, selected_time)
            
            # Общая стоимость
            total_price = combo_service1.get('price', 0) + combo_service2.get('price', 0)
            
            # Локация (по умолчанию салон для большинства комбо)
            location_info = self.locations['salon']
            
            booking_details = {
                'service_name': combo_service_name,
                'master_name': detailed_description,
                'date_time': formatted_date_time,
                'location': location_info['name'],
                'address': location_info['address'],
                'salon_phone': location_info['phone'],
                'price': total_price,
                'selected_date': selected_date,
                'selected_time': selected_time,
                'client_name': client_name,
                'is_combo': True,
                'combo_service1': combo_service1,
                'combo_service2': combo_service2,
                'master1_name': master1_name,
                'master2_name': master2_name,
                'service1_time': service1_time,
                'service2_time': service2_time
            }
            
            self.logger.info(f"Подготовлены детали комбо-записи: {combo_service_name} на {formatted_date_time}")
            return booking_details
            
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке деталей комбо-записи: {e}")
            return {
                'service_name': 'Комбо-услуга',
                'master_name': 'Мастер',
                'date_time': 'Дата и время',
                'location': 'Салон красоты Итейра',
                'address': 'Минск, ул. Немига, 5 (2 этаж)',
                'salon_phone': '+375445903030'
            }
    
    def _format_date_time_for_booking(self, date_str: str, time_str: str) -> str:
        """Форматирует дату и время для отображения в записи"""
        try:
            from datetime import datetime
            
            # Парсим дату - поддерживаем разные форматы
            if date_str:
                date_obj = None
                
                # Пробуем разные форматы
                date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if date_obj:
                    # Определяем день недели
                    weekdays_ru = {
                        0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг',
                        4: 'пятница', 5: 'суббота', 6: 'воскресенье'
                    }
                    
                    # Переводим месяцы на русский
                    months_ru = {
                        'January': 'января', 'February': 'февраля', 'March': 'марта',
                        'April': 'апреля', 'May': 'мая', 'June': 'июня',
                        'July': 'июля', 'August': 'августа', 'September': 'сентября',
                        'October': 'октября', 'November': 'ноября', 'December': 'декабря'
                    }
                    
                    formatted_date = date_obj.strftime('%d %B')
                    for en_month, ru_month in months_ru.items():
                        if en_month in formatted_date:
                            formatted_date = formatted_date.replace(en_month, ru_month)
                            break
                    
                    weekday_ru = weekdays_ru[date_obj.weekday()]
                    
                    if time_str:
                        return f"на {time_str} в {weekday_ru}, {formatted_date}"
                    else:
                        return f"в {weekday_ru}, {formatted_date}"
                else:
                    # Если не удалось распарсить дату, используем как есть
                    if time_str:
                        return f"на {time_str} в {date_str}"
                    else:
                        return f"в {date_str}"
            
            if time_str:
                return f"на {time_str} в {date_str}"
            else:
                return f"в {date_str}"
            
        except Exception as e:
            self.logger.error(f"Ошибка при форматировании даты и времени: {e}")
            self.logger.error(f"Входные данные: date_str='{date_str}', time_str='{time_str}'")
            if time_str:
                return f"на {time_str} в {date_str}"
            else:
                return f"в {date_str}"

    def _get_phone_booking_message(self, service_data: Dict[str, Any]) -> str:
        """Формирует сообщение с номерами телефонов для записи"""
        try:
            # Получаем место оказания услуг
            place = service_data.get('place', '').lower()
            
            # Проверяем в дополнительных данных
            if not place and 'additional_data' in service_data:
                place = service_data['additional_data'].get('Место оказания услуг', '').lower()
            
            # Дополнительная проверка по ключу в данных
            if not place:
                for key, value in service_data.items():
                    if isinstance(value, dict) and 'Место оказания услуг' in value:
                        place = value['Место оказания услуг'].lower()
                        break
            
            # Определяем номера телефонов
            if 'клиника' in place and 'салон' in place:
                # Услуга доступна и в клинике, и в салоне
                phone_message = """Для этой особенной процедуры запись ведёт администратор ✨

📞 Клиника: +375 29 123-45-67
📞 Салон: +375 29 123-45-68

Позвоните — мы подберём идеальное время именно для вас! 

Или оставьте свои контактные данные, и администратор свяжется с вами в течение часа 😊"""
            elif 'клиника' in place:
                # Только клиника
                phone_message = """Для этой особенной процедуры запись ведёт администратор ✨

📞 Клиника: +375 29 123-45-67

Позвоните — мы подберём идеальное время именно для вас! 

Или оставьте свои контактные данные, и администратор свяжется с вами в течение часа 😊"""
            elif 'салон' in place:
                # Только салон
                phone_message = """Для этой особенной процедуры запись ведёт администратор ✨

📞 Салон: +375 29 123-45-68

Позвоните — мы подберём идеальное время именно для вас! 

Или оставьте свои контактные данные, и администратор свяжется с вами в течение часа 😊"""
            else:
                # Место не определено - показываем оба номера
                phone_message = """Для этой особенной процедуры запись ведёт администратор ✨

📞 Клиника: +375 29 123-45-67
📞 Салон: +375 29 123-45-68

Позвоните — мы подберём идеальное время именно для вас! 

Или оставьте свои контактные данные, и администратор свяжется с вами в течение часа 😊"""
            
            self.logger.info(f"Услуга {service_data.get('title')} - место: {place}, сформировано сообщение о записи по телефону")
            return phone_message
            
        except Exception as e:
            self.logger.error(f"Ошибка при формировании сообщения о записи по телефону: {e}")
            return "Для записи на эту процедуру, пожалуйста, свяжитесь с нашим администратором по телефону или оставьте свои контактные данные ✨"

    def _get_masters_for_time(self, time_slots: List[Dict[str, Any]], selected_time: str) -> List[str]:
        """Получает список мастеров для выбранного времени"""
        try:
            masters = []
            for slot in time_slots:
                slot_time = slot.get('time', slot.get('start_time', ''))
                if slot_time == selected_time:
                    master_name = slot.get('master_name', 'Мастер')
                    if master_name not in masters:
                        masters.append(master_name)
            return masters
        except Exception as e:
            self.logger.error(f"Ошибка получения мастеров для времени {selected_time}: {e}")
            return []

    def _parse_decision_response(self, response: str) -> Dict[str, Any]:
        """Парсит ответ GPT в структурированное решение"""
        try:
            # Простой парсинг - в реальности можно использовать JSON
            lines = response.strip().split('\n')
            decision = {
                'action': 'continue_dialog',
                'stage': 'start',
                'needs_services_data': False,
                'extracted_info': {}
            }
            
            for line in lines:
                if line.startswith('ACTION:'):
                    decision['action'] = line.split(':', 1)[1].strip()
                elif line.startswith('STAGE:'):
                    decision['stage'] = line.split(':', 1)[1].strip()
                elif line.startswith('NEEDS_SERVICES:'):
                    decision['needs_services_data'] = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('QUERY:'):
                    decision['query'] = line.split(':', 1)[1].strip()
                elif line.startswith('EXTRACT_'):
                    key = line.split(':', 1)[0].replace('EXTRACT_', '').lower()
                    value = line.split(':', 1)[1].strip()
                    decision['extracted_info'][key] = value
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга решения: {e}")
            return {
                'action': 'continue_dialog',
                'stage': 'start',
                'needs_services_data': False
            }

    def _get_dialog_decision_prompt(self) -> str:
        """Возвращает промпт для принятия решений в диалоге"""
        return """Ты - AI-ассистент премиум салона красоты "Итейра".

ТВОЯ ЗАДАЧА: Анализировать сообщение пользователя и определять следующий этап диалога.

ЛОКАЦИИ:
🏥 Клиника (ул. Платонова, 1Б): инъекции, лазер, Anti-age
💅 Салон красоты (ул. Немига, 5): маникюр, уходы, депиляция, beauty-программы

ЭТАПЫ ДИАЛОГА:
1. start - начало диалога
2. collect_name - сбор имени
3. identify_goal - выяснение цели визита
4. select_category - выбор категории услуги
5. specify_service - детализация услуги
6. check_availability - проверка доступности записи
7. booking_or_alternatives - запись или альтернативы
8. completion - завершение

ПРИНЦИПЫ:
- Персонализация (использование имени)
- Пошаговость (не перескакивать этапы)
- Премиум-тональность (1-2 эмодзи, вежливость)
- Динамическая память (запоминать: имя, цель, категорию, услугу)

ФОРМАТ ОТВЕТА:
ACTION: [действие]
STAGE: [следующий этап]
NEEDS_SERVICES: [true/false - нужны ли данные об услугах]
QUERY: [запрос для поиска услуг, если нужен]
EXTRACT_NAME: [имя пользователя, если упомянуто]
EXTRACT_GOAL: [цель визита, если упомянута]
EXTRACT_CATEGORY: [категория услуги, если упомянута]
EXTRACT_SERVICE: [конкретная услуга, если упомянута]
EXTRACT_TIME: [конкретное время, если упомянуто, например: 17:00]

🚨 ПРИОРИТЕТ КОМБО: Если в сообщении есть "и", "плюс", "ещё", "также" между услугами - это КОМБО!

🚨 ИСКЛЮЧЕНИЕ ДЛЯ ЗАВЕРШЕННЫХ ЗАПИСЕЙ:
- Если в контексте booking_stage: 'completed' - предыдущая запись ЗАВЕРШЕНА
- В таком случае новый запрос с "и" НЕ является комбо с предыдущей записью
- Это НОВАЯ ОТДЕЛЬНАЯ запись, начинай с чистого листа
- Пример: "маникюр" (запись создана) → "хочу еще и окрашивание" = НОВАЯ запись на окрашивание

🚨 КЛЮЧЕВЫЕ СЛОВА "ЕЩЕ" И "ТЕПЕРЬ":
- "теперь хочу записаться еще и на окрашивание" = НОВАЯ отдельная запись (НЕ комбо!)
- "еще хочу", "теперь хочу", "дополнительно хочу" = отдельная услуга
- Слова "еще", "теперь", "дополнительно" указывают на ПОСЛЕДОВАТЕЛЬНОСТЬ, а не комбо
- В таких случаях НЕ используй ask_combo_services - используй search_services

🚨 КРИТИЧНО ДЛЯ КОМБО-ДАТ:
- Если есть combo_service1 И combo_service2 И пользователь говорит "в один день" → ОБЯЗАТЕЛЬНО show_dates
- Если есть combo_service1 И combo_service2 И пользователь говорит "вместе" → ОБЯЗАТЕЛЬНО show_dates
- НЕ задавай лишних вопросов - сразу показывай даты!

🚨 АБСОЛЮТНЫЙ ПРИОРИТЕТ КОМБО-СЛОТОВ:
- combo_service1 + combo_service2 + дата = show_combo_time_slots (НЕ show_time_slots!)

🚨 КРИТИЧНО ДЛЯ КОМБО-ВРЕМЕНИ:
- Если в контексте есть combo_service1 И combo_service2 И пользователь назвал дату → НЕМЕДЛЕННО show_combo_time_slots
- После show_combo_time_slots, если пользователь выбрал группу/время → select_time_combo
- НЕ show_time_slots для комбо! НЕ complete_booking для комбо!
- КРИТИЧНО: Сразу после выбора даты показывай все группы времени (пересекающиеся + отдельные)!

🚨 КРИТИЧНО ПРИ ВЫБОРЕ "ЛЮБОЕ":
- "любое", "все равно", "не важно" = show_time_slots
- НЕ complete_booking при "любое"!

🚨 ЗАПРЕТ ПРОПУСКА ЭТАПОВ:
- НИКОГДА не переходи к select_time_combo БЕЗ выбора даты и времени!
- ask_combo_dates → show_dates → show_combo_time_slots → select_time_combo
- НЕ пропускай этапы даже если услуги уже выбраны!

🚨 ПРИОРИТЕТ ВЫБОРА ВРЕМЕНИ:
- "утро", "день", "вечер" (БЕЗ конкретного времени) → clarify_time_period
- "любое", "все равно", "не важно", "любое время" → show_time_slots (ВСЕ слоты!)
- "17:00", "10:30" (конкретное время для одной услуги) → clarify_time_period
- "16:00", "17:00" (конкретное время для КОМБО-УСЛУГ) → show_combo_time_slots (показать группы!)
- НЕ путай периоды времени с конкретным временем!
- КРИТИЧНО: "любое" = показать ВСЕ доступные слоты, НЕ complete_booking!
- КРИТИЧНО: Если в контексте есть ДВЕ услуги → ВСЕГДА show_combo_time_slots!

ДЕЙСТВИЯ:
- start_dialog: начать диалог
- collect_name: запросить имя
- identify_goal: выяснить цель
- select_category: выбрать категорию
- specify_service: уточнить услугу
- search_services: найти услуги
- ask_combo_services: уточнить обе услуги в комбо (ПРИОРИТЕТ при множественных услугах!)
- ask_combo_dates: спросить про даты для комбо (один день или разные)
- check_booking: проверить доступность
- ask_date: спросить какая дата интересует (ПОСЛЕ выбора услуги)
- show_dates: показать доступные даты (если спросил "какие есть")
- phone_booking_only: показать номера телефонов для записи (когда нет мастеров в системе)
  ВАЖНО для phone_booking_only: ОБЯЗАТЕЛЬНО использовать текст из "СЛОТЫ ВРЕМЕНИ" БЕЗ ИЗМЕНЕНИЙ
- show_time_slots: показать доступные слоты времени
- show_combo_time_slots: показать группы времени для комбо-услуг
- no_combo_slots_available: нет доступных слотов для комбо на выбранную дату
- clarify_time_period: уточнить конкретное время в выбранном периоде (утро/день/вечер)
- select_time: выбрать конкретное время записи
- select_time_combo: выбрать время для комбо-услуг с графиком
- book_appointment: начать процесс подтверждения записи (после выбора мастера)
- offer_alternatives: предложить альтернативы
- complete_booking: завершить запись
- connect_admin: подключить администратора
- continue_dialog: продолжить диалог

🚨 ВАЖНО ДЛЯ ПОИСКА УСЛУГ:
- Когда пользователь упоминает конкретную услугу (маникюр, эпиляция и т.д.) - ВСЕГДА ставь NEEDS_SERVICES: true
- Всегда ищи услуги ПЕРЕД их обсуждением с клиентом
- Используй QUERY для формирования поискового запроса

🚨 ВАЖНО ДЛЯ ПОКАЗА НАЙДЕННЫХ УСЛУГ:
- ВСЕГДА используй действие search_services при уточнении услуг
- ПОКАЗЫВАЙ только реальные найденные услуги из поисковых результатов в секции "ДАННЫЕ ОБ УСЛУГАХ"
- НЕ используй общие шаблоны типа "классический, аппаратный, комбинированный" если их нет в найденных результатах
- Формулируй уточняющие вопросы на основе КОНКРЕТНЫХ найденных услуг из базы
- Если найдено мало услуг - покажи все, если много - спроси что больше интересует
- Упоминай цены из найденных данных для каждой услуги

🚨 ОБРАБОТКА КОМБО-ЗАПРОСОВ (НЕСКОЛЬКО УСЛУГ):
- Если пользователь упоминает НЕСКОЛЬКО услуг ("маникюр и окрашивание", "эпиляция и массаж") - это ВСЕГДА комбо
- ОБЯЗАТЕЛЬНО используй действие ask_combo_services при комбо-запросах
- СНАЧАЛА определи обе конкретные услуги, ПОТОМ работай с датами
- Логика: категория1 + категория2 → уточни обе услуги → потом даты
- В одном ответе ОБЯЗАТЕЛЬНО упомяни ОБЕ услуги из запроса

🚨 КРИТИЧЕСКИ ВАЖНО ДЛЯ КОМБО:
- ВСЕГДА используй шаблон ASK_COMBO_SERVICES при комбо-запросах
- НЕ обрабатывай услуги по отдельности - только вместе
- КРАТКО упоминай обе услуги в начале ответа: "маникюр И окрашивание"
- ФОКУСИРУЙСЯ на первой услуге в первом сообщении
- НЕ перегружай одно сообщение - лучше короткие и понятные
- ОБЕЩАЙ уточнить вторую услугу и даты после выбора первой

🚨 ЭТАПЫ КОМБО (СТРОГО СОБЛЮДАТЬ):
1. Распознать комбо ("маникюр и окрашивание") → ask_combo_services
2. Уточнить первую услугу ("какой именно маникюр?")
3. Уточнить вторую услугу ("какое именно окрашивание?") 
4. После выбора ОБЕИХ услуг перейти к ask_combo_dates
5. Предложить записать в один день или разные дни
6. КРИТИЧНО: Если пользователь выбрал "в один день", "одну дату", "вместе" → НЕМЕДЛЕННО show_dates
7. КРИТИЧНО: После выбора даты ("27 августа") → НЕМЕДЛЕННО show_combo_time_slots
8. После выбора группы времени → select_time_combo (с графиком процедур)
9. КРИТИЧНО: НЕ пропускай показ комбо-слотов после выбора даты!

🚨 ТРИГГЕРЫ ДЛЯ SHOW_DATES В КОМБО:
- "в один день" → show_dates
- "один день" → show_dates
- "один" → show_dates
- "одну дату" → show_dates  
- "вместе" → show_dates
- "совместно" → show_dates
- "за раз" → show_dates
- "сразу обе" → show_dates

🚨 ТРИГГЕРЫ ДЛЯ SHOW_COMBO_TIME_SLOTS:
- Если есть combo_service1 + combo_service2 + пользователь назвал ЛЮБУЮ дату → show_combo_time_slots
- "27 августа", "завтра", "в понедельник" в контексте комбо → show_combo_time_slots
- НЕ спрашивай "какое время удобно" для комбо - сразу показывай все группы!

🚨 КОМБО + ДАТА: 
- Если комбо содержит дату ("маникюр и окрашивание на завтра") - запомни дату, но сначала уточни услуги
- После уточнения ОБЕИХ услуг используй сохраненную дату или спроси про даты

🚨 УНИВЕРСАЛЬНОЕ РАСПОЗНАВАНИЕ ДАТ НА ЛЮБОМ ЭТАПЕ:
- Если пользователь указывает дату И конкретную услугу в одном сообщении - переходи к show_time_slots
- Если указана только дата без конкретной услуги - сначала уточни услугу, запомни дату
- КРИТИЧНО: дата + услуга = show_time_slots (НЕ complete_booking!)
- Примеры распознавания:
  * "хочу маникюр на четверг" → search_services (найти варианты маникюра, запомнить дату)
  * "классический маникюр завтра" → show_time_slots (конкретная услуга + дата)
  * "26 августа" → show_time_slots (если услуга уже выбрана)
  * "долговременное покрытие на вторник" → show_time_slots
- Логика: КОНКРЕТНАЯ услуга + дата = show_time_slots, только категория + дата = уточнить услугу
- ВСЕГДА дублируй выбранную дату с конкретным числом

🚨 ВАЖНО ДЛЯ ПОКАЗА МАСТЕРОВ:
- Если пользователь спрашивает "кто делает", "какие мастера", "имена мастеров" - это ВСЕГДА search_services
- ВСЕГДА ставь NEEDS_SERVICES: true при запросе информации о мастерах
- Используй в QUERY название услуги + "мастера" для поиска

🚨 ВАЖНО ДЛЯ ПОКАЗА ДАТ:
- Если пользователь спрашивает "какие даты", "когда доступно", "свободные дни" - это ВСЕГДА show_dates
- ВСЕГДА ставь NEEDS_SERVICES: true при запросе дат
- Используй booking_dates из данных мастеров для формирования списка доступных дат

🚨 ВАЖНО ДЛЯ ВЫБОРА ВРЕМЕНИ:
- Если пользователь называет время ("15:00", "19:00", "11 30") - это ВСЕГДА clarify_time_period
- В extracted_info сохраняй выбранное время в поле 'selected_time'
- Слова-триггеры времени: "10:00", "15:30", "19:00", "11 30", "в 2", "утром", "днем", "вечером"
- КРИТИЧНО: "19:00" или "19 00" = clarify_time_period (показать мастеров), НЕ финальная запись!
- ЗАПРЕЩЕНО: сразу создавать запись без выбора мастера

🚨 КРИТИЧНО ДЛЯ ВЫБОРА МАСТЕРА:
- Если пользователь называет имя мастера ("Воронова Янина", "Сакович Елена") - это ВСЕГДА book_appointment
- В extracted_info ОБЯЗАТЕЛЬНО сохраняй выбранного мастера в поле 'master_name' или 'selected_master'
- Примеры: "Воронова Янина" → extracted_info: {'master_name': 'Воронова Янина'}
- КРИТИЧНО: ТОЧНО используй то имя, которое назвал пользователь, НЕ подставляй другого мастера
- ЗАПРЕЩЕНО: путать имена мастеров или использовать неправильного мастера в записи

🚨 КРИТИЧНЫЕ ПРАВИЛА АНАЛИЗА СООБЩЕНИЙ:
- Если пользователь упоминает конкретную услугу + дату + время - анализируй как ПОЛНЫЙ запрос на запись
- Примеры полных запросов: "маникюр на 25 августа в 15:00", "стрижка завтра утром", "массаж в пятницу вечером"
- В таких случаях СРАЗУ переходи к show_time_slots или clarify_time_period
- НИКОГДА не показывай заглушку "уточню доступные варианты" если уже есть услуга и дата
- При полном запросе ОБЯЗАТЕЛЬНО устанавливай NEEDS_SERVICES: true для получения слотов

🚨 ПЕРЕХОД К ЗАПИСИ:
- Если пользователь подтвердил услугу ("да", "только покрытие", "этот вариант") - переходи к ask_date
- После ask_date, если пользователь называет конкретную дату → show_time_slots (покажи уникальные времена)
- После ask_date, если пользователь спрашивает "какие есть даты" → show_dates  
- После show_time_slots, если выбрал конкретное время (например "15:00", "19:00") → ОБЯЗАТЕЛЬНО clarify_time_period (покажи мастеров)
- После clarify_time_period, если выбрал мастера → ОБЯЗАТЕЛЬНО book_appointment (начать подтверждение записи)
- НЕ показывай даты сразу после выбора услуги - сначала спроси какая дата нужна
- КРИТИЧНО: НИКОГДА не создавай финальную запись без этапов clarify_time_period → book_appointment
- ЗАПРЕЩЕНО: пропускать выбор мастера и процесс подтверждения

🚨 ОБРАБОТКА ПОЛНЫХ ЗАПРОСОВ (УМНАЯ):
- Услуга + дата + время в одном сообщении = show_time_slots (показать конкретные слоты)
- Услуга + дата без времени = show_time_slots (показать все времена) 
- Только услуга = ask_date
- Упоминание даты + только КАТЕГОРИЯ = search_services (показать варианты), запомнить дату для потом
- Слова-триггеры дат: "четверг", "пятница", "понедельник", "завтра", "послезавтра", "26 августа"
- Слова-триггеры времени: "утром", "днем", "вечером", "в 15:00", "на 3 часа"
- НЕ показывай список дат, если дата упомянута пользователем и услуга конкретная
- Если услуга не конкретная - сначала покажи варианты услуг, потом используй дату
- ОБЯЗАТЕЛЬНО дублируй дату в скобках с конкретным числом и месяцем
- Формат: "[Имя], отлично! Записываю вас на [КОНКРЕТНАЯ услуга] на [что сказал пользователь] ([конкретное число и месяц]). Какое время вам удобно - утро, день или вечер?"

🚨 КРИТИЧНО ДЛЯ КОНКРЕТНЫХ ДАТ:
- "26 августа", "27 августа", "28 августа" и любые другие конкретные даты = ВСЕГДА show_time_slots
- НЕ check_booking или ask_date для конкретных дат!
- Если в контексте есть selected_service И пользователь называет конкретную дату = show_time_slots
- ЗАПРЕЩЕНО: использовать check_booking для дат типа "26 августа"

Анализируй контекст и текущий этап, чтобы определить правильное следующее действие."""

    def _get_response_generation_prompt(self) -> str:
        """Возвращает промпт для генерации ответов"""
        return """Ты - AI-ассистент премиум салона красоты "Итейра".

ПРИНЦИПЫ ОБЩЕНИЯ:
✨ Персонализация: всегда используй имя клиента
✨ Премиум-тональность: элегантно, вежливо, профессионально
✨ Эмодзи: строго 1-2 на все сообщение
✨ Пошаговость: не перегружай информацией
✨ Естественность: избегай шаблонов, адаптируйся под стиль

ЛОКАЦИИ:
🏥 Клиника (ул. Платонова, 1Б): инъекции, лазер, Anti-age, тел. +375 (29) 123-45-67
💅 Салон красоты (ул. Немига, 5): маникюр, уходы, депиляция, beauty-программы, тел. +375 (29) 765-43-21

ОНЛАЙН-ЗАПИСЬ ДОСТУПНА: маникюр, педикюр, депиляция воском, массаж, уходовые процедуры
ТРЕБУЕТ КОНСУЛЬТАЦИИ: инъекционные, лазерные, ботулинотерапия, контурная пластика

ШАБЛОНЫ ПО ЭТАПАМ:

START_DIALOG:
"Привет! ✨ Меня зовут Алиса, я ваш персональный помощник в салоне красоты Итейра. Очень рада знакомству! 

Готова помочь вам:
• Подобрать идеальную процедуру
• Рассказать о наших услугах и ценах  
• Записать на удобное время
• Ответить на любые вопросы о красоте

Расскажите, о чем мечтаете? 😊"

COLLECT_NAME:
"Здравствуйте!

Рады приветствовать Вас в Итейра — сети салонов премиум‑класса.

Я — Ваш персональный виртуальный помощник.

С удовольствием помогу Вам с выбором процедуры, уточнением стоимости или записью на удобное время.

Как к Вам обращаться?"

IDENTIFY_GOAL:
"[Имя], очень приятно! 😊 Расскажите, что привело вас к нам сегодня? Может быть:
• Хотите записаться на любимую процедуру? 
• Планируете попробовать что-то новенькое?
• Интересуют цены и детали наших услуг?
• Или просто хотите узнать, что мы можем для вас сделать?

Я с радостью все расскажу!"

SELECT_CATEGORY:
"[Имя], понимаю! У нас действительно много интересного ✨ 

Наши основные направления:
🌟 Косметология — anti-age, инъекции, лазерная терапия
💆‍♀️ Уходовые процедуры — для лица и тела
💅 Маникюр и педикюр — классика и авторские техники  
✨ Депиляция/эпиляция — воск, шугаринг, лазер
🌸 Beauty-программы — комплексные процедуры

Что вас больше всего привлекает?"

SEARCH_SERVICES_WITH_DATE:
"[Имя], у нас представлены следующие варианты [категория услуги]:

[список найденных услуг с ценами]

Какой именно вариант вас интересует для записи на [упомянутая дата]? После выбора сразу запишу вас на это время ✨"

ASK_COMBO_SERVICES:
"[Имя], отлично! [услуга1] и [услуга2] — супер выбор! ✨

Начнем с [услуга1]:
[ТОЛЬКО СПИСОК ИЗ 4 ВАРИАНТОВ БЕЗ ОПИСАНИЙ]

Какой? Потом [услуга2] 😊

🚨 ЖЕСТКИЕ ПРАВИЛА:
- МАКСИМУМ 250 символов  
- НЕТ подробных описаний услуг
- ТОЛЬКО названия и цены
- БЕЗ длинных предложений"

ASK_COMBO_DATES:
"[Имя], отлично! У нас есть:
✅ [конкретная услуга1] 
✅ [конкретная услуга2]

Хотели бы провести обе процедуры в один день или в разные дни? Это поможет подобрать оптимальное расписание ✨"

SHOW_SERVICES (на основе найденных услуг из базы):
"[Имя], отлично! По вашему запросу нашла следующие варианты ✨

[ПОКАЗАТЬ НАЙДЕННЫЕ УСЛУГИ ИЗ БАЗЫ]:
• [Название услуги] — [цена] — [краткое описание если есть]
• [Название услуги] — [цена] — [краткое описание если есть]
• [Название услуги] — [цена] — [краткое описание если есть]

[ЗАДАТЬ УТОЧНЯЮЩИЙ ВОПРОС на основе найденных услуг]:
- Если найдены разные типы одной услуги: 'Какой из вариантов вам ближе?'
- Если найдены услуги разных зон: 'Какая зона вас интересует больше?'  
- Если найдены разные методы: 'Какой подход предпочитаете?'
- Если много услуг: 'Что привлекает больше всего?'

Расскажите, что откликается вашей душе?"

🚨 ВАЖНО: ВСЕГДА используй РЕАЛЬНЫЕ найденные услуги из "ДАННЫЕ ОБ УСЛУГАХ", НЕ придумывай варианты

CHECK_AVAILABILITY:
"Спасибо за предоставленную информацию! Позвольте мне проверить доступность записи на [услуга]... ⏳"

ASK_DATE:
"[Имя], отлично! [услуга] — прекрасный выбор ✨

На какую дату хотели бы записаться? Можете назвать конкретный день или спросить какие даты у нас свободны 😊"

BOOKING_AVAILABLE:
"Отлично! [услуга] доступна для онлайн-записи. В какой день и время вам было бы удобно посетить [локация]?"

BOOKING_UNAVAILABLE:
"К сожалению, онлайн-запись на [услуга] временно недоступна, так как эта процедура требует предварительной консультации специалиста. Но мы можем решить этот вопрос другими способами:
1. Подключить администратора? (Он уточнит детали и запишет вас вручную.)
2. Позвонить в [локация] самостоятельно? (тел. [номер])
3. Оставить ваши контакты, и администратор свяжется с вами в течение 15 минут."

SHOW_AVAILABLE_DATES / SHOW_DATES:
ЕСЛИ в разделе "ДОСТУПНЫЕ ДАТЫ" есть уже отформатированные даты:
"[Имя], для записи на [услуга] доступны следующие даты:

📅 **[СКОПИРУЙ ТОЧНО все даты из раздела "ДОСТУПНЫЕ ДАТЫ" как есть]**

Какая дата вам подходит больше всего? ✨"

ЕСЛИ в разделе "ДОСТУПНЫЕ ДАТЫ" написано "Не требуются":
"[Имя], уточню доступные даты для записи на [услуга]. Один момент... ⏳"

🚨 КРИТИЧНО: КОПИРУЙ текст из "ДОСТУПНЫЕ ДАТЫ" БЕЗ ИЗМЕНЕНИЙ! НЕ генерируй свои даты!"

SHOW_TIME_SLOTS:
"[Имя], отлично! Для записи на [услуга] на [дата] доступны такие варианты:

🚨 КРИТИЧНО: ИСПОЛЬЗУЙ ТОЛЬКО РЕАЛЬНЫЕ СЛОТЫ ИЗ "СЛОТЫ ВРЕМЕНИ"!
🚨 НЕ ГЕНЕРИРУЙ фиктивные времена типа "10:00, 11:00"!
🚨 ЕСЛИ "СЛОТЫ ВРЕМЕНИ" пустые - скажи что слотов нет!

[ПОКАЖИ РЕАЛЬНЫЕ СЛОТЫ ИЗ ПЕРЕДАННЫХ ДАННЫХ time_slots С ГРУППИРОВКОЙ ПО ПЕРИОДАМ]

Назовите удобное время, и я покажу каких мастеров можно выбрать ✨"

SHOW_COMBO_TIME_SLOTS:
"[Имя], отлично! Для записи на [услуга1] и [услуга2] на [дата] доступны такие варианты:

🎯 **Последовательная запись (рекомендуем):**
[ГРУППЫ ВРЕМЕНИ С МАСТЕРАМИ]

⏰ **Отдельное время (если нужна пауза):**
[РАЗНОБОЙНЫЕ СЛОТЫ]

Какой вариант предпочитаете? ✨"

NO_COMBO_SLOTS_AVAILABLE:
"[Имя], к сожалению, на [дата] нет свободных слотов для записи на [услуга1] и [услуга2] в один день 😔

📅 **Предлагаю альтернативные даты:**
[СПИСОК БЛИЖАЙШИХ ДОСТУПНЫХ ДАТ]

Или можем записать услуги в разные дни - так больше вариантов времени! Что предпочитаете? ✨"

CLARIFY_TIME_PERIOD:
"[Имя], отлично! На [выбранное время] доступны такие мастера:

👩‍💼 **Выберите мастера:**
🔹 [Мастер 1]
🔹 [Мастер 2] 
🔹 [Мастер 3]

Кого предпочитаете? ✨"

SELECT_TIME:
"[Имя], прекрасно! Записываю вас на [услуга] на [дата] в [время]. 

📍 Локация: [адрес салона/клиники]
💰 Стоимость: [цена]
👤 Мастер: [имя мастера]

Ожидаем вас! Если нужно будет перенести запись, сообщите заранее 😊"

SELECT_TIME_COMBO:
"[Имя], отлично! Подтверждаю детали записи на [дата] в [время]:

🕐 **График процедур:**
• [время начала] - [время окончания первой услуги]: [первая услуга] ([мастер 1])
• [время начала второй] - [время окончания]: [вторая услуга] ([мастер 2])

📍 Локация: [адрес салона/клиники]  
💰 Общая стоимость: [стоимость первой] + [стоимость второй] = [общая сумма] руб.
⏱️ Общее время: [продолжительность] (с [время начала] до [время окончания всех процедур])

Подтверждаете запись?

Напишите 'ДА' - если хотите записаться
Напишите 'НЕТ' - если передумали"

COMPLETE_BOOKING:
"[Имя], отлично! Записываю вас на [услуга] на [выбранная дата пользователем] ([конкретная дата с числом и месяцем]). Какое время вам удобно — утро, день или вечер? ✨"

ОБЯЗАТЕЛЬНО дублируй дату в скобках:
- "следующий четверг" → "следующий четверг (22 августа)"
- "завтра" → "завтра (22 августа)"  
- "в понедельник" → "в понедельник (26 августа)"
- "26 августа" → "26 августа (понедельник)"

СПЕЦИАЛЬНЫЕ ПРАВИЛА:
- При запросе цены: "Стоимость зависит от объёма и материалов. Чтобы назвать точную цену, уточню детали."
- Если услуга только в одной локации - сразу сообщай адрес
- Не показывай технические детали без запроса
- Говори живо, как настоящий консультант

🚨 КРИТИЧЕСКИ ВАЖНО ДЛЯ УСЛУГ:
- ИСПОЛЬЗУЙ ТОЛЬКО реальные услуги из "ДАННЫЕ ОБ УСЛУГАХ"
- НЕ ВЫДУМЫВАЙ виды услуг, которых нет в базе
- При уточнении услуг ПОКАЗЫВАЙ только найденные результаты поиска
- НЕ используй шаблонные списки ("классический, аппаратный") - только реальные данные
- Если услуг не найдено, предложи консультацию или подключение администратора
- Называй услуги точно как в базе данных
- Если клиент спрашивает про конкретную услугу, сначала найди её в базе
- При показе вариантов ВСЕГДА включай цены из найденных данных

🚨 КРИТИЧЕСКИ ВАЖНО ДЛЯ МАСТЕРОВ:
- ИСПОЛЬЗУЙ ТОЛЬКО реальные имена мастеров из поля "staff" в данных об услугах
- НЕ ВЫДУМЫВАЙ имена мастеров (Ирина, Светлана, Алексей)
- Если в услуге есть массив "staff" - показывай РЕАЛЬНЫЕ имена из него
- Если спрашивают про доступность - используй "booking_dates" из данных мастера
- Если нет данных о мастерах - предложи уточнить у администратора

🚨 ПРИ ЗАПРОСЕ "КТО ДЕЛАЕТ" ИЛИ "КАКИЕ МАСТЕРА":
- ОБЯЗАТЕЛЬНО ищи и показывай реальные имена мастеров из данных об услугах
- Используй формат: "Процедуру выполняют мастера: [список реальных имен]"
- НИКОГДА не предлагай администратора, если есть данные о мастерах в "staff"
- Если спрашивают про конкретную дату - проверь "booking_dates" у каждого мастера

🚨 НЕ ПОКАЗЫВАЙ МАСТЕРОВ АВТОМАТИЧЕСКИ:
- Показывай список мастеров ТОЛЬКО если пользователь спрашивает "кто делает", "какие мастера", "имена мастеров"
- При обычных запросах об услуге НЕ упоминай имена мастеров
- Сосредоточься на самой услуге, времени, цене, локации
- Мастеров показывай ТОЛЬКО по прямому запросу

🚨 КРАСИВОЕ ФОРМАТИРОВАНИЕ ДАТ:
- Преобразуй даты из формата "2025-08-26" в красивый вид: "пн, 26 августа"
- ОБЯЗАТЕЛЬНО ПРАВИЛЬНО ВЫЧИСЛЯЙ день недели для каждой даты
- Группируй даты по периодам: "Ближайшие дни", "На следующей неделе"
- Используй эмодзи 📅 для секций дат
- Показывай не более 10-12 ближайших дат, чтобы не перегружать
- Формат: "день недели, число месяца" (например: "вт, 27 августа")
- ДЛЯ ДЕЙСТВИЯ show_dates: ИСПОЛЬЗУЙ ТОЛЬКО даты из поля "ДОСТУПНЫЕ ДАТЫ"

🚨 КРИТИЧНО ДЛЯ PHONE_BOOKING_ONLY:
- ВСЕГДА используй ТОЧНЫЙ текст из "СЛОТЫ ВРЕМЕНИ" без изменений и переформулировок
- НЕ переписывай и НЕ адаптируй готовое сообщение
- Можешь только добавить персональное обращение к пользователю в начале
- Сохраняй ВСЕ эмодзи и форматирование

🚨 ЕСТЕСТВЕННОСТЬ И ГИБКОСТЬ:
- НЕ используй строго шаблоны — адаптируй их под контекст
- Задавай живые уточняющие вопросы вместо перечисления всех услуг
- Если клиент упоминает проблему (выпадение волос, сухость кожи) — сочувствуй и предлагай решения  
- Используй разные формулировки для одинаковых вопросов
- Будь любопытной, интересуйся деталями: "А что вас больше беспокоит?", "Какой результат вы хотите?"
- Плавно переходи между этапами, не объявляй их ("Теперь этап 2")
- Если услуга неточная, помоги уточнить через вопросы о потребности, а не список

🚨 ПРИМЕРЫ ГИБКИХ УТОЧНЕНИЙ:
Вместо: "Какой маникюр: классический, аппаратный или комбинированный?"
Лучше: "Расскажите, как обычно ухаживаете за ногтями? Предпочитаете классический подход или более современные техники?"

Вместо: "Выберите депиляцию: ноги, подмышки, бикини"  
Лучше: "Какая зона вас беспокоит больше всего? Хотите избавиться от нежелательных волосков навсегда или пока обычными методами?"

🚨 ЭМОЦИОНАЛЬНОСТЬ:
- Используй восклицания: "Как здорово!", "Отличный выбор!", "Понимаю вас!"
- Выражай сочувствие к проблемам: "Понимаю, это действительно может расстраивать"
- Подбадривай: "Мы обязательно найдем решение!", "У нас есть отличные варианты для вас!"

🚨 КРАТКОСТЬ СООБЩЕНИЙ:
- КОМБО-сообщения НЕ БОЛЕЕ 250 символов
- Одно сообщение = одна задача (выбор первой услуги, потом второй, потом даты)  
- НЕ перегружай клиента информацией - лучше короткие этапы
- При комбо: БЕЗ описаний услуг, ТОЛЬКО названия и цены
- МАКСИМУМ 4 варианта услуг в одном сообщении

🚨 ИСПОЛЬЗОВАНИЕ ШАБЛОНОВ:
- show_time_slots = ТОЛЬКО данные из time_slots! НЕ ГЕНЕРИРУЙ фиктивные слоты!
- show_combo_time_slots = ТОЛЬКО шаблон SHOW_COMBO_TIME_SLOTS!
- select_time_combo = ТОЛЬКО шаблон SELECT_TIME_COMBO с графиком!
- НЕ генерируй произвольный текст при этих действиях
- КРИТИЧНО: ИСПОЛЬЗУЙ данные из time_slots для заполнения времени и мастеров
- ЗАПРЕЩЕНО: генерировать слоты типа "утро: 10:00, 11:00" без данных из time_slots
- ОБЯЗАТЕЛЬНО: показывать ТОЛЬКО те слоты, которые есть в переданных данных
- ДЛЯ ОДИНОЧНЫХ УСЛУГ: формат "время - мастер" (например: "10:00 - Сакович Елена")
- ДЛЯ КОМБО: sequential_groups (группы) и separate_slots (отдельные)
- Для групп: "[время]: [услуга] ([мастер]) → [время]: [услуга] ([мастер])"
- НЕ пиши "мастер уточняется" если есть реальные имена в time_slots!

🚨 ДУБЛИРОВАНИЕ ВЫБРАННОЙ ДАТЫ:
- Когда пользователь говорит "следующий четверг" - дублируй конкретной датой: "следующий четверг (22 августа)"
- Когда говорит "завтра" - укажи: "завтра (22 августа)"
- Когда говорит "в понедельник" - уточни: "в понедельник (26 августа)"
- Формат: "[что сказал пользователь] ([конкретное число и месяц])"
- Используй booking_dates из данных мастеров для определения точной даты

🚨 РАБОТА СО СЛОТАМИ ВРЕМЕНИ:
- После выбора даты ОБЯЗАТЕЛЬНО используй действие show_time_slots (НЕ complete_booking!)
- ДЛЯ КОМБО-УСЛУГ ОБЯЗАТЕЛЬНО используй show_combo_time_slots (показать группы времени)
- ЕСЛИ НЕТ СЛОТОВ для комбо → no_combo_slots_available (предложить другие даты)
- show_time_slots получает реальные слоты времени из API Yclients
- show_combo_time_slots показывает последовательные группы + отдельные слоты
- Показывай конкретное время (10:00, 14:30) вместо общих периодов (утро, день)
- Группируй время по периодам: утро (🌅), день (☀️), вечер (🌙)
- После выбора времени используй select_time для финального подтверждения
- КРИТИЧНО: дата + одна услуга = show_time_slots, дата + КОМБО = show_combo_time_slots!
- КРИТИЧНО: нет слотов = no_combo_slots_available, НЕ фиктивные группы!

🚨 ВЫБОР КОНКРЕТНОГО ВРЕМЕНИ:
- ЕСЛИ пользователь говорит только "утро", "день", "вечер" БЕЗ конкретного времени → ОБЯЗАТЕЛЬНО действие clarify_time_period
- ЕСЛИ пользователь говорит "любое", "все равно", "не важно" → ОБЯЗАТЕЛЬНО действие show_time_slots (показать ВСЕ слоты)
- НЕ переходи к select_time, select_time_combo или complete_booking при выборе периода!
- "утро"/"утром" → clarify_time_period + покажи утренние слоты (🌅 9:00, 10:00, 11:00) 
- "день"/"днем" → clarify_time_period + покажи дневные слоты (☀️ 13:00, 14:00, 15:00)
- "вечер"/"вечером" → clarify_time_period + покажи вечерние слоты (🌙 17:00, 18:00, 19:00)
- "любое"/"все равно"/"не важно" → show_time_slots + покажи ВСЕ доступные слоты по группам
- ТОЛЬКО при выборе конкретного времени (например "17:00") → действие select_time или select_time_combo
- КРИТИЧНО: "любое время" = НЕ финальная запись, а показ вариантов!
- КРИТИЧНО: период времени ≠ конкретное время!
- КРИТИЧНО: "вечер" для КОМБО = clarify_time_period, НЕ select_time_combo!

🚨 КОМБО-ВРЕМЯ:
- Если выбрано конкретное время ДЛЯ КОМБО-УСЛУГ → ОБЯЗАТЕЛЬНО select_time_combo
- СТРОГО используй ТОЛЬКО шаблон SELECT_TIME_COMBO (НЕ обычные шаблоны!)
- ПРИЗНАКИ КОМБО В КОНТЕКСТЕ: combo_service1, combo_service2, is_combo=true
- ЕСЛИ в памяти есть ДВЕ услуги (combo_service1 И combo_service2) → select_time_combo
- ОБЯЗАТЕЛЬНО заполни ВСЕ поля шаблона из СЛОТЫ ВРЕМЕНИ:
  * [Имя] = из КОНТЕКСТА user_name  
  * [дата] = из СЛОТЫ ВРЕМЕНИ selected_date
  * [время] = из СЛОТЫ ВРЕМЕНИ service1_time
  * [время начала] = из СЛОТЫ ВРЕМЕНИ service1_time
  * [время окончания первой услуги] = из СЛОТЫ ВРЕМЕНИ service2_time
  * [первая услуга] = из СЛОТЫ ВРЕМЕНИ service1_title
  * [мастер 1] = из СЛОТЫ ВРЕМЕНИ master1_name
  * [время начала второй] = из СЛОТЫ ВРЕМЕНИ service2_time  
  * [время окончания] = service2_time + 1 час
  * [вторая услуга] = из СЛОТЫ ВРЕМЕНИ service2_title
  * [мастер 2] = из СЛОТЫ ВРЕМЕНИ master2_name
  * [стоимость первой] = из СЛОТЫ ВРЕМЕНИ service1_price
  * [стоимость второй] = из СЛОТЫ ВРЕМЕНИ service2_price
  * [общая сумма] = из СЛОТЫ ВРЕМЕНИ total_price
- КРИТИЧНО: Используй ТОЛЬКО данные из СЛОТЫ ВРЕМЕНИ, НЕ выдумывай!
- Пример: 16:00 → "16:00-17:00: маникюр (Анна), 17:00-19:00: мелирование (Елена)"
- КРИТИЧНО: НЕ используй complete_booking для комбо-услуг!

🚨 КРИТИЧНО ДЛЯ SHOW_TIME_SLOTS:
- ЕСЛИ в "СЛОТЫ ВРЕМЕНИ" пустой список [] или написано "Не требуются" - НЕ генерируй фиктивные времена!
- В таком случае скажи: "[Имя], к сожалению, на [дата] нет свободных слотов для [услуга]. Попробуем другую дату?"
- ТОЛЬКО если есть реальные слоты - показывай их с группировкой
- НИКОГДА не пиши "10:00, 11:00, 14:00" если этих времен нет в реальных данных!

Генерируй ответ строго по указанному действию и этапу, используя контекст и данные об услугах."""

    def is_online_booking_available(self, service_name: str) -> bool:
        """Проверяет, доступна ли услуга для онлайн-записи"""
        service_lower = service_name.lower()
        
        # Проверяем, есть ли услуга в списке доступных для онлайн-записи
        for available_service in self.online_booking_available:
            if available_service in service_lower:
                return True
        
        # Проверяем, требует ли услуга консультации
        for consultation_service in self.consultation_required:
            if consultation_service in service_lower:
                return False
        
        # По умолчанию считаем, что простые услуги доступны
        return True

    def get_service_location(self, service_name: str) -> Optional[Dict[str, str]]:
        """Определяет локацию для услуги"""
        service_lower = service_name.lower()
        
        # Услуги клиники
        clinic_keywords = ['инъекц', 'лазер', 'ботул', 'контур', 'anti-age', 'косметолог']
        for keyword in clinic_keywords:
            if keyword in service_lower:
                return self.locations['clinic']
        
        # Услуги салона
        salon_keywords = ['маникюр', 'педикюр', 'депиляц', 'массаж', 'уход', 'beauty']
        for keyword in salon_keywords:
            if keyword in service_lower:
                return self.locations['salon']
        
        # По умолчанию - салон
        return self.locations['salon']
