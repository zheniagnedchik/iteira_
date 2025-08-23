#!/usr/bin/env python3
"""
GPT-оркестратор диалогов для системы записи в салон красоты.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .gpt_client import GPTClient
from .logger import get_logger
from .error_handler import handle_error


@dataclass
class DialogAction:
    """Действие, которое должна выполнить система."""
    action_type: str  # show_services, confirm_service, show_dates, confirm_booking, etc.
    parameters: Dict[str, Any]  # параметры действия
    response_text: str  # текст ответа пользователю
    next_state: Optional[str] = None  # следующее состояние диалога


class GPTOrchestrator:
    """GPT-оркестратор для управления диалогами."""
    
    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.gpt_client = GPTClient()
        self.logger = get_logger(__name__)
        
        # Контекст пользователей
        self.user_contexts: Dict[int, Dict[str, Any]] = {}
        
        self.logger.info("GPT Orchestrator initialized successfully")
    
    def process_message(self, user_id: int, message: str, user_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сообщение пользователя через GPT-оркестратор."""
        try:
            # Получаем или создаем контекст пользователя
            context = self.get_user_context(user_id)
            
            # Если есть имя пользователя, сохраняем его
            if user_name:
                context['user_name'] = user_name
            
            # Добавляем сообщение в историю
            context['dialog_history'].append({
                'role': 'user',
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Получаем решение от GPT-оркестратора
            action = self._get_orchestrator_decision(user_id, message, context)
            
            # Выполняем действие
            response, metadata = self._execute_action(user_id, action, context)
            
            # Добавляем ответ в историю
            context['dialog_history'].append({
                'role': 'assistant',
                'message': response,
                'action': action.action_type,
                'timestamp': datetime.now().isoformat()
            })
            
            # Обновляем состояние
            if action.next_state:
                context['current_state'] = action.next_state
            
            return response, metadata
            
        except Exception as e:
            error_msg = handle_error(e, context={"user_id": user_id, "message": message})
            return "Извините, произошла ошибка. Попробуйте еще раз.", {"type": "error", "error": error_msg}
    
    def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Получает или создает контекст пользователя."""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                'user_id': user_id,
                'user_name': None,
                'visit_history': None,
                'current_state': 'initial',
                'dialog_history': [],
                'selected_services': [],
                'selected_service': None,
                'selected_date': None,
                'available_services': [],
                'created_at': datetime.now().isoformat()
            }
        
        return self.user_contexts[user_id]
    
    def _get_orchestrator_decision(self, user_id: int, message: str, context: Dict[str, Any]) -> DialogAction:
        """Получает решение от GPT-оркестратора о том, что делать дальше."""
        
        # Подготавливаем контекст для GPT-оркестратора
        dialog_context = {
            'user_name': context.get('user_name'),
            'current_state': context.get('current_state', 'initial'),
            'conversation_history': context.get('dialog_history', []),
            'selected_service': context.get('selected_service'),
            'available_services': context.get('available_services', [])
        }
        
        # Используем готовый метод orchestrate_dialog из GPTClient
        orchestration_result = self.gpt_client.orchestrate_dialog(message, dialog_context)
        
        # Преобразуем результат в DialogAction
        return DialogAction(
            action_type=orchestration_result.get('action', 'general_response'),
            parameters=orchestration_result.get('parameters', {}),
            response_text=orchestration_result.get('response', message),
            next_state=orchestration_result.get('next_state')
        )
    

    
    def _execute_action(self, user_id: int, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Выполняет действие, определенное GPT-оркестратором."""
        
        try:
            if action.action_type == 'greeting':
                return self._handle_greeting(context)
            
            elif action.action_type == 'collect_name':
                return self._handle_name_collection(action, context)
            
            elif action.action_type == 'ask_visit_history':
                return self._handle_visit_history(action, context)
            
            elif action.action_type == 'ask_service_clarification':
                return self._handle_service_clarification(action, context)
            
            elif action.action_type == 'show_services' or action.action_type == 'show_service_list':
                return self._handle_show_services(action, context)
            
            elif action.action_type == 'confirm_service' or action.action_type == 'confirm_service_selection':
                return self._handle_confirm_service(action, context)
            
            elif action.action_type == 'show_dates' or action.action_type == 'show_available_dates':
                # Принудительно используем наш метод, игнорируя текст от GPT
                return self._handle_show_dates(action, context)
            
            elif action.action_type == 'confirm_booking':
                return self._handle_confirm_booking(action, context)
            
            elif action.action_type == 'general_consultation':
                return self._handle_general_consultation(action, context)
            
            elif action.action_type == 'show_masters':
                return self._handle_show_masters(action, context)
            
            elif action.action_type == 'show_all_dates':
                return self._handle_show_all_dates(action, context)
            
            elif action.action_type in ['show_masters_info', 'show_staff', 'show_masters', 'masters_info']:
                return self._handle_show_masters(action, context)
            
            else:
                # Общий ответ
                return action.response_text, {"type": action.action_type}
                
        except Exception as e:
            self.logger.error(f"Error executing action {action.action_type}: {e}")
            return "Произошла ошибка при обработке запроса.", {"type": "error"}
    
    def _handle_greeting(self, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает приветствие."""
        response = (
            "Здравствуйте!\n\n"
            "Рады приветствовать Вас в Итейра — сети салонов премиум‑класса.\n\n"
            "Я — Ваш персональный виртуальный помощник.\n\n"
            "С удовольствием помогу Вам с выбором процедуры, уточнением стоимости или записью на удобное время.\n\n"
            "Как к Вам обращаться?"

        )
        context['current_state'] = 'collecting_name'
        return response, {"type": "greeting"}
    
    def _handle_name_collection(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сбор имени."""
        name = action.parameters.get('name')
        if name:
            context['user_name'] = name
            context['current_state'] = 'collecting_history'
            response = f"Приятно познакомиться, {name}! 😊\n\nВы уже были у нас в салоне или это будет первое посещение?"
            return response, {"type": "name_collected", "name": name}
        else:
            return action.response_text, {"type": "name_collection"}
    
    def _handle_visit_history(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает сбор информации о предыдущих посещениях."""
        user_name = context.get('user_name', '')
        message = action.response_text.lower()
        
        if any(word in message for word in ['была', 'был', 'посещал', 'посещала', 'раньше', 'да']):
            context['visit_history'] = 'returning_client'
            context['current_state'] = 'ready_for_service'
            response = f"Отлично! Тогда мы постараемся сделать ваше посещение еще лучше, чем в прошлый раз.\n\n"
            response += f"Чем вас порадовать сегодня? Возможно:\n"
            response += f"🔹 Премиальное окрашивание\n"
            response += f"🔹 Авторская стрижка\n"
            response += f"🔹 Комплексный уход\n"
            response += f"🔹 Или что-то другое?"
        else:
            context['visit_history'] = 'new_client'
            context['current_state'] = 'ready_for_service'
            response = f"Добро пожаловать в ITEIRA! 🌟\n\n"
            response += f"Мы рады, что вы выбрали наш салон для первого посещения.\n"
            response += f"Расскажите, какая процедура вас интересует?"
        
        return response, {"type": "visit_history_collected"}
    
    def _handle_service_clarification(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Задает уточняющие вопросы на основе найденных услуг."""
        service_query = action.parameters.get('service_query', '') or action.parameters.get('service_type', '')
        
        # Если нет запроса в параметрах, извлекаем из последнего сообщения пользователя
        if not service_query:
            dialog_history = context.get('dialog_history', [])
            if dialog_history:
                for msg in reversed(dialog_history):
                    if msg.get('role') == 'user':
                        service_query = msg.get('message', '')
                        break
        
        self.logger.debug(f"Creating clarification for query: '{service_query}'")
        
        # Получаем услуги по запросу
        available_services = self._get_services_with_masters(service_query)
        
        if not available_services:
            # Если услуг нет, возвращаем общий вопрос
            response = (
                "Чтобы подобрать для Вас наиболее подходящие процедуры, "
                "расскажите пожалуйста подробнее о том, что Вас беспокоит?\n\n"
                "Это поможет мне предложить именно те услуги, которые будут наиболее эффективны в Вашем случае."
            )
            return response, {"type": "service_clarification", "query": service_query}
        
        # Обновляем состояние и сохраняем найденные услуги
        context['current_state'] = 'clarifying_service'
        context['available_services'] = available_services
        context['original_query'] = service_query
        
        # Генерируем уточняющие вопросы на основе найденных услуг через GPT
        try:
            response = self._generate_clarification_questions(available_services, service_query)
        except Exception as e:
            self.logger.error(f"Failed to generate clarification questions: {e}")
            # Fallback к простому списку
            return self._handle_show_services(action, context)
        
        return response, {"type": "service_clarification", "query": service_query, "services_count": len(available_services)}
    
    def _generate_clarification_questions(self, services: List[Dict[str, Any]], query: str) -> str:
        """Генерирует уточняющие вопросы на основе найденных услуг через GPT."""
        
        # Подготавливаем данные об услугах для анализа
        services_summary = []
        categories = set()
        
        for service in services:
            title = service.get('title', '')
            category = service.get('category', '')
            price = service.get('price', 0)
            
            services_summary.append({
                'title': title,
                'category': category,
                'price': price
            })
            categories.add(category)
        
        # Создаем промпт для GPT
        services_data = {
            'query': query,
            'services': services_summary,
            'categories': list(categories),
            'total_count': len(services)
        }
        
        prompt = f"""
Ты - консультант салона красоты. Пользователь написал: "{query}"

Система нашла {len(services)} услуг в следующих категориях: {', '.join(categories)}

Твоя задача - создать 2-4 уточняющих вопроса, чтобы помочь пользователю выбрать наиболее подходящие услуги из найденных.

ВАЖНО:
- Вопросы должны быть основаны на РЕАЛЬНЫХ найденных услугах и их категориях
- НЕ придумывай категории, которых нет в списке
- Используй эмодзи для визуального оформления
- Сделай вопросы конкретными и понятными
- Добавь опцию "или опишите подробнее"

Найденные услуги:
{chr(10).join([f"- {s['title']} ({s['category']}) - {s['price']} руб." for s in services_summary[:10]])}

Формат ответа:
Понимаю Вашу проблему. Чтобы подобрать наиболее подходящее решение, уточните пожалуйста:

🔍 [Основной вопрос]
1️⃣ [Вариант 1]
2️⃣ [Вариант 2]
3️⃣ [Вариант 3]
[4️⃣ Вариант 4 - если нужен]

Или опишите свою проблему подробнее.
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Ты - эксперт по созданию уточняющих вопросов для салона красоты. Создавай вопросы только на основе предоставленных данных об услугах."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.gpt_client._make_request(messages, temperature=0.7)
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to generate clarification via GPT: {e}")
            raise
    
    def _filter_services_by_clarification(self, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Фильтрует уже найденные услуги на основе ответа пользователя на уточняющие вопросы."""
        
        available_services = context.get('available_services', [])
        original_query = context.get('original_query', '')
        
        # Получаем последний ответ пользователя
        dialog_history = context.get('dialog_history', [])
        user_clarification = ""
        if dialog_history:
            for msg in reversed(dialog_history):
                if msg.get('role') == 'user':
                    user_clarification = msg.get('message', '')
                    break
        
        self.logger.debug(f"Filtering {len(available_services)} services based on clarification: '{user_clarification}'")
        
        try:
            # Используем GPT для интеллектуальной фильтрации услуг
            filtered_services = self._filter_services_with_gpt(
                services=available_services,
                original_query=original_query,
                user_clarification=user_clarification
            )
            
            if not filtered_services:
                # Если фильтрация не дала результатов, показываем все найденные услуги
                self.logger.warning("Filtering returned no results, showing all services")
                filtered_services = available_services
            
            # Обновляем контекст
            context['available_services'] = filtered_services
            context['current_state'] = 'service_selection'  # Переходим к выбору услуги
            
            # Форматируем отфильтрованный список
            response = self.gpt_client.format_service_list(filtered_services, context)
            
            return response, {"type": "services_shown", "count": len(filtered_services), "filtered": True}
            
        except Exception as e:
            self.logger.error(f"Failed to filter services: {e}")
            # Fallback - показываем все найденные услуги
            response = self.gpt_client.format_service_list(available_services, context)
            return response, {"type": "services_shown", "count": len(available_services), "filtered": False}
    
    def _filter_services_with_gpt(self, services: List[Dict[str, Any]], original_query: str, user_clarification: str) -> List[Dict[str, Any]]:
        """Фильтрует услуги с помощью GPT на основе уточнения пользователя."""
        
        # Подготавливаем данные для GPT
        services_data = []
        for i, service in enumerate(services):
            services_data.append({
                'index': i,
                'id': service.get('id', ''),
                'title': service.get('title', ''),
                'category': service.get('category', ''),
                'price': service.get('price', 0),
                'description': service.get('description', '')[:200]  # Ограничиваем описание
            })
        
        prompt = f"""
Пользователь изначально спросил: "{original_query}"
Затем уточнил: "{user_clarification}"

Из предложенного списка услуг выбери 2-4 наиболее подходящих на основе уточнения пользователя.

Услуги:
{chr(10).join([f"{i}. {s['title']} ({s['category']}) - {s['price']} руб." for i, s in enumerate(services_data)])}

ВАЖНО:
- Анализируй уточнение пользователя и выбирай наиболее релевантные услуги
- Если пользователь выбрал номер (1, 2, 3), то учитывай соответствие этому номеру из предыдущих вопросов
- Если пользователь описал конкретные симптомы/предпочтения, выбирай подходящие услуги
- Верни ТОЛЬКО индексы выбранных услуг в JSON формате

Формат ответа:
{{"selected_indices": [0, 2, 3]}}
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "Ты - эксперт по фильтрации услуг салона красоты. Анализируй уточнения пользователя и выбирай наиболее подходящие услуги."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.gpt_client._make_request(messages, temperature=0.3)
            
            # Парсим JSON ответ
            import json
            result = json.loads(response)
            selected_indices = result.get('selected_indices', [])
            
            # Возвращаем отфильтрованные услуги
            filtered_services = []
            for index in selected_indices:
                if 0 <= index < len(services):
                    filtered_services.append(services[index])
            
            self.logger.info(f"GPT filtered services: {len(services)} → {len(filtered_services)}")
            return filtered_services
            
        except Exception as e:
            self.logger.error(f"GPT filtering failed: {e}")
            raise
    
    def _handle_show_services(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Показывает список доступных услуг."""
        service_query = action.parameters.get('service_query', '') or action.parameters.get('service_type', '')
        
        # КРИТИЧНО: Если мы в состоянии уточнения и есть уже найденные услуги - фильтруем их
        if context.get('current_state') == 'clarifying_service' and context.get('available_services'):
            self.logger.debug("Filtering existing services based on user clarification")
            return self._filter_services_by_clarification(context)
        
        # Если нет запроса в параметрах, попробуем извлечь из последнего сообщения пользователя
        if not service_query:
            dialog_history = context.get('dialog_history', [])
            if dialog_history:
                last_user_message = None
                for msg in reversed(dialog_history):
                    if msg.get('role') == 'user':
                        last_user_message = msg.get('message', '')
                        break
                if last_user_message:
                    service_query = last_user_message
        
        self.logger.debug(f"Searching services with query: '{service_query}'")
        
        # Получаем услуги с доступными мастерами
        available_services = self._get_services_with_masters(service_query)
        
        if not available_services:
            # Если нет доступных услуг, показываем контакты
            response = self._generate_no_services_message(service_query)
            return response, {"type": "no_services_available"}
        
        # Сохраняем услуги в контекст
        context['available_services'] = available_services
        
        # Используем GPT для красивого форматирования списка услуг
        try:
            response = self.gpt_client.format_service_list(available_services, context)
        except Exception as e:
            self.logger.error(f"GPT formatting failed, using fallback: {e}")
            # Fallback к базовому форматированию
            user_name = context.get('user_name', '')
            greeting = f"{user_name}, " if user_name else ""
            response = f"{greeting}отлично! Я нашла доступные услуги для записи:\n\n"
            
            for i, service in enumerate(available_services, 1):
                title = service.get('title', 'Услуга')
                price = service.get('price', 0)
                duration = self._format_duration(service.get('duration', 0))
                
                response += f"{i}. {title}\n"
                response += f"   💰 {price} руб. | ⏱ {duration}\n\n"
            
            response += "Напишите номер услуги (например, 1), чтобы выбрать её для записи."
        
        return response, {"type": "services_shown", "count": len(available_services)}
    
    def _handle_confirm_service(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Подтверждает выбор услуги."""
        service_number = action.parameters.get('service_number')
        available_services = context.get('available_services', [])
        
        if not service_number or service_number < 1 or service_number > len(available_services):
            return "Пожалуйста, укажите корректный номер услуги (например, 1, 2, 3...).", {"type": "invalid_service_number"}
        
        # Выбираем услугу
        selected_service = available_services[service_number - 1]
        context['selected_service'] = selected_service
        
        # Генерируем подтверждение
        user_name = context.get('user_name', '')
        greeting = f"{user_name}, с" if user_name else "С"
        
        title = selected_service.get('title', 'Услуга')
        price = selected_service.get('price', 0)
        duration = self._format_duration(selected_service.get('duration', 0))
        
        # Получаем описание и место проведения
        csv_fields = selected_service.get('csv_fields', {})
        description = csv_fields.get('Описание технологии', '') or csv_fields.get('Терапевтическая цель', '')
        location = csv_fields.get('Место оказания услуг', '')
        
        response = f"{greeting}пасибо! 🌸\n\n"
        response += f"Вы выбрали услугу:\n{title}\n\n"
        
        if description:
            short_description = description[:150] + "..." if len(description) > 150 else description
            response += f"📝 {short_description}\n\n"
        
        response += f"💰 Стоимость: {price} руб.\n"
        response += f"⏱ Длительность: {duration}\n"
        
        if location:
            response += f"📍 Место проведения: {location}\n"
        
        response += "\n"
        response += "Теперь выберите удобную дату:\n"
        response += "• Напишите конкретную дату (например, 20.08.2025)\n"
        response += "• Или напишите 'даты', чтобы посмотреть доступные варианты"
        
        return response, {"type": "service_confirmed", "service_id": selected_service.get('id'), "service_title": title}
    
    def _handle_show_dates(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Показывает доступные даты."""
        selected_service = context.get('selected_service')
        
        self.logger.debug(f"Show dates - selected_service: {selected_service}")
        self.logger.debug(f"Show dates - context keys: {list(context.keys())}")
        
        if not selected_service:
            return "Сначала выберите услугу для записи.", {"type": "no_service_selected"}
        
        # Получаем доступные даты
        available_dates = self._get_available_dates(selected_service)
        
        if not available_dates:
            return (
                "К сожалению, на данный момент нет доступных дат для записи.\n\n"
                "📞 Для уточнения расписания обратитесь к администратору:\n"
                "• Клиника: +375296080912\n"
                "• Салон: +375445903030"
            ), {"type": "no_dates_available"}
        
        service_title = selected_service.get('title', 'услугу')
        response = f"📅 Доступные даты для записи на {service_title}:\n\n"
        
        # Умное отображение дат
        self.logger.debug(f"Formatting {len(available_dates)} dates smartly")
        smart_dates = self._format_dates_smartly(available_dates)
        self.logger.debug(f"Smart dates result: {smart_dates[:100]}...")
        response += smart_dates
        
        response += "\n💡 Как записаться:\n"
        response += "• Напишите номер даты (например, 1, 2, 3...)\n"
        response += "• Или конкретную дату (например, 20.08.2025)\n"
        response += "• Или напишите 'все даты' для полного списка"
        
        return response, {"type": "dates_shown", "count": len(available_dates)}
    
    def _handle_confirm_booking(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Подтверждает запись."""
        selected_service = context.get('selected_service')
        selected_date = action.parameters.get('date')
        
        if not selected_service or not selected_date:
            return "Ошибка: не хватает данных для записи.", {"type": "booking_error"}
        
        # Сохраняем дату
        context['selected_date'] = selected_date
        
        # Генерируем итоговое сообщение
        user_name = context.get('user_name', '')
        greeting = f"{user_name}, " if user_name else ""
        
        title = selected_service.get('title', 'Услуга')
        price = selected_service.get('price', 0)
        duration = self._format_duration(selected_service.get('duration', 0))
        
        response = f"{greeting}отлично! 🎉\n\n"
        response += f"📋 Ваша запись:\n"
        response += f"🔸 Услуга: {title}\n"
        response += f"🔸 Дата: {selected_date}\n"
        response += f"🔸 Стоимость: {price} руб.\n"
        response += f"🔸 Длительность: {duration}\n\n"
        
        response += "📞 Для подтверждения записи обратитесь к администратору:\n"
        
        # Определяем тип услуги для правильных контактов
        title_lower = title.lower()
        clinical_keywords = ['мезотерапия', 'инъекции', 'ботокс', 'филлеры', 'плазмотерапия', 'биоревитализация']
        is_clinical = any(keyword in title_lower for keyword in clinical_keywords)
        
        if is_clinical:
            response += "• Клиника: +375296080912 (пн–сб 8:00–22:00, вс 10:00–18:00)\n"
        else:
            response += "• Салон: +375445903030 (пн–вс 9:00–21:00)\n"
        
        response += "\nАдминистратор подберет удобное время и подходящего мастера! ✨"
        
        return response, {"type": "booking_confirmed", "service": title, "date": selected_date}
    
    def _handle_general_consultation(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Обрабатывает общую консультацию."""
        query = action.parameters.get('query', '')
        
        # Используем RAG-систему для консультации
        try:
            response = self.rag_system.process_query(query)
            user_name = context.get('user_name')
            if user_name:
                response = f"{user_name}, {response}"
            return response, {"type": "consultation"}
        except Exception as e:
            self.logger.error(f"Error in general consultation: {e}")
            return "Извините, произошла ошибка при обработке запроса.", {"type": "error"}
    
    def _handle_show_masters(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Показывает информацию о мастерах для выбранной услуги."""
        selected_service = context.get('selected_service')
        
        if not selected_service:
            return "Сначала выберите услугу для записи.", {"type": "no_service_selected"}
        
        # Получаем мастеров для услуги
        masters_info = self._get_masters_for_service(selected_service)
        
        if not masters_info:
            return (
                "К сожалению, информация о мастерах недоступна.\n\n"
                "📞 Для уточнения обратитесь к администратору:\n"
                "• Клиника: +375296080912\n"
                "• Салон: +375445903030"
            ), {"type": "no_masters_info"}
        
        user_name = context.get('user_name', '')
        greeting = f"{user_name}, " if user_name else ""
        service_title = selected_service.get('title', 'услугу')
        
        response = f"{greeting}👩‍💼 Наши мастера по услуге \"{service_title}\":\n\n"
        
        # Показываем всех мастеров
        for i, master in enumerate(masters_info, 1):  # Показываем всех мастеров
            name = master.get('name', 'Мастер')
            available_dates = master.get('dates', [])
            
            response += f"�  {name}\n"
            
            if available_dates:
                # Показываем статус доступности
                if len(available_dates) >= 10:
                    status = "🟢 Много свободных дат"
                elif len(available_dates) >= 5:
                    status = "🟡 Есть свободные даты"
                else:
                    status = "🔴 Мало свободных дат"
                
                response += f"   {status} ({len(available_dates)} дат)\n"
                
                # Показываем ближайшие даты
                nearest_dates = available_dates[:3]
                if nearest_dates:
                    dates_text = ", ".join(nearest_dates)
                    response += f"   📅 Ближайшие: {dates_text}\n"
            else:
                response += f"   📅 Уточните расписание у администратора\n"
            
            response += "\n"
        
        # Добавляем общую информацию
        response += f"📊 Всего мастеров: {len(masters_info)}\n\n"
        
        response += "💡 Как записаться:\n"
        response += "• Выберите удобную дату из списка\n"
        response += "• Администратор подберет свободного мастера\n"
        response += "• Или укажите предпочтения по мастеру\n\n"
        response += "📞 Контакты для записи:\n"
        response += "• Салон: +375445903030 (пн–вс 9:00–21:00)"
        
        return response, {"type": "masters_shown", "count": len(masters_info)}
    
    def _handle_show_all_dates(self, action: DialogAction, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Показывает все доступные даты."""
        selected_service = context.get('selected_service')
        
        if not selected_service:
            return "Сначала выберите услугу для записи.", {"type": "no_service_selected"}
        
        # Получаем доступные даты
        available_dates = self._get_available_dates(selected_service)
        
        if not available_dates:
            return (
                "К сожалению, на данный момент нет доступных дат для записи.\n\n"
                "📞 Для уточнения расписания обратитесь к администратору:\n"
                "• Клиника: +375296080912\n"
                "• Салон: +375445903030"
            ), {"type": "no_dates_available"}
        
        service_title = selected_service.get('title', 'услугу')
        user_name = context.get('user_name', '')
        greeting = f"{user_name}, в" if user_name else "В"
        
        response = f"{greeting}от полный список дат для записи на {service_title}:\n\n"
        
        # Показываем все даты с красивым форматированием
        formatted_dates = self._format_dates_beautifully(available_dates)
        response += formatted_dates
        
        response += f"\n📊 Всего доступно: {len(available_dates)} дат\n\n"
        response += "💡 Напишите номер даты или дату в формате ДД.ММ.ГГГГ"
        
        return response, {"type": "all_dates_shown", "count": len(available_dates)}
    
    def _get_services_with_masters(self, query: str) -> List[Dict[str, Any]]:
        """Получает услуги с доступными мастерами."""
        try:
            # Используем поисковый модуль
            service_ids = self.rag_system.search_module.find_services(query)
            if not service_ids:
                return []
            
            # Получаем полную информацию об услугах
            services = self.rag_system.consultation_module.get_services_by_ids(service_ids)
            
            # Фильтруем услуги с мастерами
            services_with_masters = []
            for service in services:
                if self._has_available_masters(service):
                    services_with_masters.append(service)
            
            return services_with_masters[:5]
            
        except Exception as e:
            self.logger.error(f"Error getting services with masters: {e}")
            return []
    
    def _has_available_masters(self, service: Dict[str, Any]) -> bool:
        """Проверяет, есть ли у услуги доступные мастера."""
        companies = service.get('companies', [])
        
        # Если есть хотя бы одна компания, считаем услугу доступной
        if companies and len(companies) > 0:
            # Проверяем полную структуру с мастерами (если есть)
            for company in companies:
                if isinstance(company, dict):
                    staff = company.get('staff', [])
                    if staff and len(staff) > 0:
                        for staff_member in staff:
                            if isinstance(staff_member, dict):
                                booking_dates = staff_member.get('booking_dates', [])
                                if booking_dates and len(booking_dates) > 0:
                                    return True
                # Если компания задана как строка ID, считаем доступной
                elif isinstance(company, str):
                    return True
            
            # Если есть компании-объекты без мастеров, тоже считаем доступной
            return True
        
        return False
    
    def _get_available_dates(self, service: Dict[str, Any]) -> List[str]:
        """Получает доступные даты для услуги."""
        available_dates = set()
        companies = service.get('companies', [])
        
        for company in companies:
            if isinstance(company, dict):
                staff = company.get('staff', [])
                for staff_member in staff:
                    if isinstance(staff_member, dict):
                        booking_dates = staff_member.get('booking_dates', [])
                        if booking_dates:
                            available_dates.update(booking_dates)
        
        return sorted(list(available_dates))
    
    def _get_masters_for_service(self, service: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получает информацию о мастерах для услуги."""
        masters = []
        companies = service.get('companies', [])
        
        for company in companies:
            if isinstance(company, dict):
                staff = company.get('staff', [])
                for staff_member in staff:
                    if isinstance(staff_member, dict):
                        name = staff_member.get('name', 'Мастер')
                        booking_dates = staff_member.get('booking_dates', [])
                        
                        masters.append({
                            'name': name,
                            'dates': booking_dates,
                            'company': company.get('name', 'Салон')
                        })
        
        return masters
    
    def _format_duration(self, duration: int) -> str:
        """Форматирует длительность процедуры."""
        if not duration:
            return "не указано"
        
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
    
    def _format_dates_smartly(self, dates: List[str]) -> str:
        """Умно форматирует список дат с группировкой и сокращением."""
        if not dates:
            return ""
        
        self.logger.debug(f"Smart formatting {len(dates)} dates")
        from datetime import datetime, timedelta
        
        # Получаем сегодняшнюю дату
        today = datetime.now()
        
        # Группируем даты более гибко
        near_dates = []    # Ближайшие даты (первые 7)
        middle_dates = []  # Средние даты (следующие 5)
        later_dates = []   # Остальные даты
        
        for i, date_str in enumerate(dates):
            try:
                day, month, year = date_str.split('.')
                date_obj = datetime(int(year), int(month), int(day))
                days_diff = (date_obj - today).days
                
                if i < 7:  # Первые 7 дат - приоритетные
                    near_dates.append((date_str, date_obj, days_diff))
                elif i < 12:  # Следующие 5 дат
                    middle_dates.append((date_str, date_obj, days_diff))
                else:
                    later_dates.append((date_str, date_obj, days_diff))
            except:
                continue
        
        formatted = ""
        counter = 1
        
        # Ближайшие даты (приоритет)
        if near_dates:
            formatted += "🔥 Ближайшие варианты:\n"
            for date_str, date_obj, days_diff in near_dates:
                day_name = self._get_day_name(date_obj)
                if days_diff == 0:
                    day_info = "сегодня"
                elif days_diff == 1:
                    day_info = "завтра"
                elif days_diff <= 7:
                    day_info = f"{day_name}"
                else:
                    day_info = f"{day_name}"
                
                formatted += f"{counter}. 📅 {date_str} ({day_info})\n"
                counter += 1
            formatted += "\n"
        
        # Дополнительные даты
        if middle_dates:
            formatted += "📅 Дополнительные варианты:\n"
            for date_str, date_obj, days_diff in middle_dates:
                day_name = self._get_day_name(date_obj)
                formatted += f"{counter}. 📅 {date_str} ({day_name})\n"
                counter += 1
            formatted += "\n"
        
        # Если ничего не показали, показываем хотя бы первые даты
        if counter == 1:
            formatted += "🔥 Ближайшие варианты:\n"
            for i, date_str in enumerate(dates[:7], 1):
                try:
                    day, month, year = date_str.split('.')
                    date_obj = datetime(int(year), int(month), int(day))
                    day_name = self._get_day_name(date_obj)
                    formatted += f"{i}. 📅 {date_str} ({day_name})\n"
                except:
                    formatted += f"{i}. 📅 {date_str}\n"
            formatted += "\n"
            counter = 8
        
        # Показываем сколько еще дат доступно
        total_remaining = len(dates) - (counter - 1)
        if total_remaining > 0:
            formatted += f"📋 И еще {total_remaining} дат доступно\n"
        
        self.logger.debug(f"Smart formatting result: {formatted}")
        return formatted
    
    def _format_dates_beautifully(self, dates: List[str]) -> str:
        """Красиво форматирует список дат (старый метод для совместимости)."""
        if not dates:
            return ""
        
        formatted = ""
        for i, date in enumerate(dates, 1):
            # Добавляем эмодзи для дней недели
            day_emoji = self._get_day_emoji(date)
            formatted += f"{i}. {day_emoji} {date}\n"
            
            # Добавляем разделитель каждые 5 дат для лучшей читаемости
            if i % 5 == 0 and i < len(dates):
                formatted += "\n"
        
        return formatted
    
    def _get_day_name(self, date_obj) -> str:
        """Возвращает название дня недели на русском."""
        day_names = {
            0: "понедельник",
            1: "вторник", 
            2: "среда",
            3: "четверг",
            4: "пятница",
            5: "суббота",
            6: "воскресенье"
        }
        return day_names.get(date_obj.weekday(), "")
    
    def _get_day_emoji(self, date_str: str) -> str:
        """Возвращает эмодзи для дня недели."""
        try:
            from datetime import datetime
            # Парсим дату в формате ДД.ММ.ГГГГ
            day, month, year = date_str.split('.')
            date_obj = datetime(int(year), int(month), int(day))
            weekday = date_obj.weekday()
            
            day_emojis = {
                0: "📅",  # Понедельник
                1: "📅",  # Вторник
                2: "📅",  # Среда
                3: "📅",  # Четверг
                4: "📅",  # Пятница
                5: "📅",  # Суббота
                6: "📅"   # Воскресенье
            }
            return day_emojis.get(weekday, "📅")
        except:
            return "📅"
    
    def _generate_no_services_message(self, query: str) -> str:
        """Генерирует сообщение когда нет доступных услуг."""
        query_lower = query.lower()
        clinical_keywords = ['мезотерапия', 'инъекции', 'ботокс', 'филлеры', 'плазмотерапия', 'биоревитализация']
        is_clinical = any(keyword in query_lower for keyword in clinical_keywords)
        
        response = "Благодарю за ожидание, данная услуга доступна для записи только по телефону.\n\n📞 Для записи свяжитесь с нами:\n"
        
        if is_clinical:
            response += "• Клиника: +375296080912 (пн–сб 8:00–22:00, вс 10:00–18:00)"
        else:
            response += "• Салон: +375445903030 (пн–вс 9:00–21:00)"
        
        return response
    
