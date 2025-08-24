#!/usr/bin/env python3
"""
Упрощенный NewDialogOrchestrator - обертка вокруг DialogAssistant
"""

from typing import Dict, Any
from .dialog_assistant import DialogAssistant
from .gpt_client import GPTClient
from .modules.search_module import SearchModule
from .logger import get_logger


class NewDialogOrchestrator:
    """Упрощенный оркестратор для новой системы диалогов"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config
        
        # Инициализируем компоненты
        self.gpt_client = GPTClient()
        self.search_module = SearchModule()
        self.dialog_assistant = DialogAssistant(self.gpt_client, self.search_module)
        
        # Контексты пользователей
        self.user_contexts = {}
        
        self.logger.info("NewDialogOrchestrator инициализирован с DialogAssistant")

    def process_message(self, user_id: str, message: str) -> str:
        """
        Обрабатывает сообщение пользователя через DialogAssistant
        
        Args:
            user_id: Идентификатор пользователя
            message: Текст сообщения
            
        Returns:
            str: Ответ бота
        """
        try:
            # Получаем или создаем контекст пользователя
            context = self.get_user_context(user_id)
            context['last_message'] = message
            
            # Обрабатываем сообщение через DialogAssistant
            result = self.dialog_assistant.process_message(
                user_id=user_id,
                message=message,
                context=context
            )
            
            # Обновляем контекст пользователя
            self.user_contexts[user_id] = result['context']
            
            # Возвращаем ответ
            return result['response']
            
        except Exception as e:
            self.logger.error(f"Ошибка в NewDialogOrchestrator: {e}")
            return "Извините, произошла техническая ошибка. Попробуйте ещё раз."

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Получает контекст пользователя или создает новый"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                'dialog_stage': 'start',
                'conversation_history': []
            }
        return self.user_contexts[user_id].copy()

    def clear_user_context(self, user_id: str):
        """Очищает контекст пользователя"""
        if user_id in self.user_contexts:
            self.user_contexts.pop(user_id)
            self.logger.info(f"Контекст пользователя {user_id} очищен")

    def reset_user_context(self, user_id: str):
        """Сбрасывает контекст пользователя (алиас для clear_user_context)"""
        self.clear_user_context(user_id)
        self.logger.info(f"Контекст пользователя {user_id} сброшен")
