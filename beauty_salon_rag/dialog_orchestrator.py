#!/usr/bin/env python3
"""
Dialog Orchestrator for Beauty Salon RAG System
Manages conversation flow using GPT orchestrator
"""

from typing import Dict, Any, Tuple, Optional

from .gpt_orchestrator import GPTOrchestrator
from .logger import get_logger, log_operation
from .error_handler import handle_error


class DialogOrchestrator:
    """Упрощенный оркестратор диалогов, использующий GPT-оркестратор."""
    
    def __init__(self, rag_system):
        """
        Инициализация оркестратора.
        
        Args:
            rag_system: Экземпляр RAG-системы
        """
        self.logger = get_logger(__name__)
        self.rag_system = rag_system
        
        # GPT-оркестратор для умного управления диалогами
        self.gpt_orchestrator = GPTOrchestrator(rag_system)
        
        self.logger.info("Dialog orchestrator initialized successfully")
    
    @log_operation("orchestrator_process_message")
    def process_message(self, user_id: int, message: str, user_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Обрабатывает сообщение пользователя через GPT-оркестратор.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            user_name: Имя пользователя из Telegram (опционально)
            
        Returns:
            Tuple[str, Dict]: Ответ и метаданные
        """
        self.logger.info(f"Processing message from user {user_id} with GPT orchestrator")
        
        try:
            # Используем GPT-оркестратор для обработки сообщения
            response, metadata = self.gpt_orchestrator.process_message(user_id, message, user_name)
            
            return response, metadata
            
        except Exception as e:
            error_msg = handle_error(e, context={"user_id": user_id, "message": message})
            response = (
                "Извините, произошла ошибка при обработке вашего сообщения.\n\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
            return response, {"type": "error", "error": error_msg}
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя."""
        context = self.gpt_orchestrator.get_user_context(user_id)
        return {
            "user_id": user_id,
            "name": context.get('user_name'),
            "state": context.get('current_state', 'initial'),
            "dialog_history_count": len(context.get('dialog_history', [])),
            "selected_service": context.get('selected_service', {}).get('title') if context.get('selected_service') else None,
            "created_at": context.get('created_at')
        }
    
    def clear_user_context(self, user_id: int):
        """Очищает контекст пользователя."""
        if user_id in self.gpt_orchestrator.user_contexts:
            del self.gpt_orchestrator.user_contexts[user_id]
        
        self.logger.info(f"Cleared context for user {user_id}")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Получает общую статистику оркестратора."""
        return {
            "total_users": len(self.gpt_orchestrator.user_contexts),
            "active_conversations": len(self.gpt_orchestrator.user_contexts)
        }