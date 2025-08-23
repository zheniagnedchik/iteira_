#!/usr/bin/env python3
"""
Unified GPT-driven orchestrator for Beauty Salon RAG System
Все решения и ответы генерируются через GPT
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .gpt_client import GPTClient
from .logger import get_logger
from .error_handler import handle_error


class UnifiedGPTOrchestrator:
    """Полностью GPT-driven оркестратор диалогов без хардкода."""
    
    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.gpt_client = GPTClient()
        self.logger = get_logger(__name__)
        
        # Контекст пользователей
        self.user_contexts: Dict[int, Dict[str, Any]] = {}
        
        self.logger.info("Unified GPT Orchestrator initialized successfully")
    
    def process_message(self, user_id: int, message: str, user_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Обрабатывает сообщение пользователя полностью через GPT.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            user_name: Имя пользователя (опционально)
            
        Returns:
            Tuple[str, Dict]: Ответ и метаданные
        """
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
            
            # ШАГ 1: GPT принимает решение о том, что делать
            decision = self._get_gpt_decision(user_id, message, context)
            action_type = decision.get('action', 'general_chat')
            action_parameters = decision.get('parameters', {})
            
            # ШАГ 2: Получаем необходимые данные на основе решения GPT
            services_data = []
            if action_type in ['show_service_list', 'service_consultation', 'ask_service_clarification', 'show_masters']:
                # Для всех действий, связанных с услугами, загружаем данные
                # GPT использует эту информацию для формирования умных вопросов и информации о мастерах
                services_data = self._get_services_for_action(action_type, action_parameters, message)
            
            # ШАГ 3: GPT генерирует финальный ответ
            if decision.get('response') == 'gpt_generated':
                # Генерируем ответ через GPT
                response = self._generate_gpt_response(
                    user_message=message,
                    dialog_context=context,
                    action_type=action_type,
                    action_parameters=action_parameters,
                    services_data=services_data
                )
            else:
                # Используем ответ из решения оркестратора (для обратной совместимости)
                response = decision.get('response', 'Спасибо за ваше сообщение!')
            
            # Обновляем контекст на основе действия
            self._update_context_after_action(context, action_type, action_parameters)
            
            # Добавляем ответ в историю
            context['dialog_history'].append({
                'role': 'assistant',
                'message': response,
                'action': action_type,
                'timestamp': datetime.now().isoformat()
            })
            
            # Обновляем состояние
            if decision.get('next_state'):
                context['current_state'] = decision['next_state']
            
            return response, {
                "type": action_type,
                "action_parameters": action_parameters,
                "services_count": len(services_data)
            }
            
        except Exception as e:
            error_msg = handle_error(e, context={"user_id": user_id, "message": message})
            return "Извините, произошла ошибка. Попробуйте еще раз.", {"type": "error", "error": error_msg}
    
    def _get_gpt_decision(self, user_id: int, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Получает решение от GPT о том, какое действие выполнить."""
        
        # Подготавливаем контекст для GPT-оркестратора
        dialog_context = {
            'user_name': context.get('user_name'),
            'current_state': context.get('current_state', 'initial'),
            'conversation_history': context.get('dialog_history', []),
            'selected_service': context.get('selected_service'),
            'available_services': context.get('available_services', []),
            'visit_history': context.get('visit_history')
        }
        
        # Используем готовый метод orchestrate_dialog из GPTClient
        try:
            return self.gpt_client.orchestrate_dialog(message, dialog_context)
        except Exception as e:
            self.logger.error(f"GPT decision failed: {e}")
            # Fallback к общему чату
            return {
                'action': 'general_chat',
                'parameters': {},
                'response': 'fallback_handled_by_gpt',
                'next_state': None
            }
    
    def _get_services_for_action(self, action_type: str, action_parameters: Dict[str, Any], user_message: str) -> List[Dict[str, Any]]:
        """Получает данные об услугах, если они нужны для действия."""
        
        if action_type in ['show_service_list', 'ask_service_clarification']:
            try:
                # Извлекаем запрос для поиска услуг
                service_query = (
                    action_parameters.get('service_type') or 
                    action_parameters.get('service_query') or 
                    user_message
                )
                
                if service_query:
                    # Используем поисковый модуль
                    service_ids = self.rag_system.search_module.find_services(service_query)
                    if service_ids:
                        # Получаем полную информацию об услугах
                        services = self.rag_system.consultation_module.get_services_by_ids(service_ids)
                        return services[:10]  # Ограничиваем количество
                
            except Exception as e:
                self.logger.error(f"Failed to get services for action {action_type}: {e}")
        
        return []
    
    def _generate_gpt_response(self, user_message: str, dialog_context: Dict[str, Any], 
                              action_type: str, action_parameters: Dict[str, Any],
                              services_data: List[Dict[str, Any]]) -> str:
        """Генерирует финальный ответ через GPT."""
        
        try:
            return self.gpt_client.generate_contextual_response(
                user_message=user_message,
                dialog_context=dialog_context,
                action_type=action_type,
                action_parameters=action_parameters,
                services_data=services_data
            )
        except Exception as e:
            self.logger.error(f"GPT response generation failed: {e}")
            # Fallback к базовому ответу
            return self._generate_fallback_response(action_type, dialog_context)
    
    def _generate_fallback_response(self, action_type: str, dialog_context: Dict[str, Any]) -> str:
        """Генерирует fallback ответ, если GPT недоступен."""
        user_name = dialog_context.get('user_name', '')
        greeting = f"{user_name}, " if user_name else ""
        
        fallback_responses = {
            'greeting': f"Здравствуйте! Рады приветствовать Вас в Итейра. Как к Вам обращаться?",
            'collect_name': f"Приятно познакомиться! Расскажите, чем могу помочь?",
            'show_service_list': f"{greeting}покажу Вам доступные услуги для записи.",
            'service_consultation': f"{greeting}с удовольствием проконсультирую по нашим услугам.",
            'general_chat': f"{greeting}как дела? Чем могу помочь?"
        }
        
        return fallback_responses.get(action_type, "Спасибо за ваше сообщение! Чем могу помочь?")
    
    def _update_context_after_action(self, context: Dict[str, Any], action_type: str, action_parameters: Dict[str, Any]):
        """Обновляет контекст пользователя после выполнения действия."""
        
        # Обновляем имя пользователя
        if action_type == 'collect_name' and 'name' in action_parameters:
            context['user_name'] = action_parameters['name']
        
        # Обновляем историю посещений
        if action_type == 'ask_visit_history':
            # GPT может указать тип клиента в параметрах
            visit_type = action_parameters.get('visit_type')
            if visit_type:
                context['visit_history'] = visit_type
        
        # Сохраняем этап уточнения услуг
        if action_type == 'ask_service_clarification':
            context['current_state'] = 'clarifying_service'
            context['clarification_topic'] = action_parameters.get('service_query', '')
            # НЕ сохраняем услуги на этапе уточнения - только задаем вопросы
        
        # Сохраняем выбранную услугу
        if action_type == 'confirm_service_selection':
            service_number = action_parameters.get('service_number', 0)
            available_services = context.get('available_services', [])
            if 0 < service_number <= len(available_services):
                context['selected_service'] = available_services[service_number - 1]
        
        # Сохраняем выбранную дату
        if action_type == 'confirm_date_selection':
            selected_date = action_parameters.get('date')
            if selected_date:
                context['selected_date'] = selected_date
    
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
    
    def clear_user_context(self, user_id: int):
        """Очищает контекст пользователя."""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
        self.logger.info(f"Cleared context for user {user_id}")
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя."""
        context = self.get_user_context(user_id)
        return {
            "user_id": user_id,
            "name": context.get('user_name'),
            "state": context.get('current_state', 'initial'),
            "interaction_count": len(context.get('dialog_history', [])),
            "context_messages": len(context.get('dialog_history', [])),
            "selected_service": context.get('selected_service', {}).get('title') if context.get('selected_service') else None,
            "created_at": context.get('created_at')
        }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Получает общую статистику оркестратора."""
        return {
            "total_users": len(self.user_contexts),
            "active_conversations": len(self.user_contexts)
        }
