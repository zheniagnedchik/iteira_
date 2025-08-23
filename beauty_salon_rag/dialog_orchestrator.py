#!/usr/bin/env python3
"""
Dialog Orchestrator for Beauty Salon RAG System
Управление диалогами с возможностью выбора между старой и новой системами
"""

import os
from typing import Dict, Any, Tuple, Optional

from .unified_gpt_orchestrator import UnifiedGPTOrchestrator
from .new_dialog_orchestrator import NewDialogOrchestrator
from .logger import get_logger, log_operation
from .error_handler import handle_error


class DialogOrchestrator:
    """Оркестратор диалогов с поддержкой старой и новой систем."""
    
    def __init__(self, rag_system):
        """
        Инициализация оркестратора.
        
        Args:
            rag_system: Экземпляр RAG-системы
        """
        self.logger = get_logger(__name__)
        self.rag_system = rag_system
        
        # Определяем, какую систему использовать
        use_new_system = os.getenv('USE_NEW_DIALOG_SYSTEM', 'false').lower() == 'true'
        
        if use_new_system:
            # Новая система с шаблоном диалога - используем глобальный config
            from .config import Config
            config_obj = Config()
            self.new_orchestrator = NewDialogOrchestrator(config_obj._config)
            self.gpt_orchestrator = None
            self.system_type = 'new'
            self.logger.info("New structured dialog system initialized")
        else:
            # Старая unified GPT-система
            self.gpt_orchestrator = UnifiedGPTOrchestrator(rag_system)
            self.new_orchestrator = None
            self.system_type = 'legacy'
            self.logger.info("Legacy unified GPT-driven dialog orchestrator initialized")
    
    @log_operation("orchestrator_process_message")
    def process_message(self, user_id: int, message: str, user_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Обрабатывает сообщение пользователя через выбранную систему.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            user_name: Имя пользователя из Telegram (опционально)
            
        Returns:
            Tuple[str, Dict]: Ответ и метаданные
        """
        self.logger.info(f"Processing message from user {user_id} with {self.system_type} system")
        
        try:
            if self.system_type == 'new':
                # Новая система - теперь синхронная
                response = self.new_orchestrator.process_message(str(user_id), message)
                metadata = {
                    "type": "new_system_response",
                    "system": "structured_dialog"
                }
                return response, metadata
            else:
                # Старая система
                response, metadata = self.gpt_orchestrator.process_message(user_id, message, user_name)
                metadata["system"] = "legacy_unified_gpt"
                return response, metadata
            
        except Exception as e:
            error_msg = handle_error(e, context={"user_id": user_id, "message": message})
            
            # Обрабатываем ошибку через соответствующую систему
            try:
                if self.system_type == 'new' and self.new_orchestrator:
                    # Для новой системы
                    return (
                        "Извините, произошла техническая ошибка. Могу подключить администратора?",
                        {"type": "error", "error": error_msg, "system": "new"}
                    )
                elif self.gpt_orchestrator:
                    # Для старой системы
                    error_response = self.gpt_orchestrator._generate_fallback_response('error_handling', {
                        'user_name': user_name,
                        'error_context': error_msg
                    })
                    return error_response, {"type": "error", "error": error_msg, "system": "legacy"}
                else:
                    raise Exception("No orchestrator available")
            except:
                # Только если обе системы недоступны
                return "Извините, временно недоступен. Попробуйте позже.", {"type": "critical_error"}
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя."""
        if self.system_type == 'new':
            context = self.new_orchestrator.get_user_context(str(user_id))
            return {
                "user_id": user_id,
                "name": context.get('user_name'),
                "state": context.get('dialog_stage', 'start'),
                "dialog_history_count": len(context.get('conversation_history', [])),
                "selected_service": context.get('selected_service'),
                "system": "new_structured"
            }
        else:
            context = self.gpt_orchestrator.get_user_context(user_id)
            return {
                "user_id": user_id,
                "name": context.get('user_name'),
                "state": context.get('current_state', 'initial'),
                "dialog_history_count": len(context.get('dialog_history', [])),
                "selected_service": context.get('selected_service', {}).get('title') if context.get('selected_service') else None,
                "created_at": context.get('created_at'),
                "system": "legacy_unified"
            }
    
    def clear_user_context(self, user_id: int):
        """Очищает контекст пользователя."""
        if self.system_type == 'new':
            self.new_orchestrator.reset_user_context(str(user_id))
        else:
            if user_id in self.gpt_orchestrator.user_contexts:
                del self.gpt_orchestrator.user_contexts[user_id]
        
        self.logger.info(f"Cleared context for user {user_id}")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Получает общую статистику оркестратора."""
        if self.system_type == 'new':
            stats = self.new_orchestrator.get_dialog_statistics()
            stats["system"] = "new_structured"
            return stats
        else:
            return {
                "total_users": len(self.gpt_orchestrator.user_contexts),
                "active_conversations": len(self.gpt_orchestrator.user_contexts),
                "system": "legacy_unified"
            }
    
    def handle_admin_connection(self, user_id: int) -> str:
        """Обрабатывает запрос на подключение администратора."""
        if self.system_type == 'new':
            return self.new_orchestrator.handle_admin_connection(str(user_id))
        else:
            # Для старой системы - базовая обработка
            return "Подключаю администратора. Ожидайте сообщения в этом чате."
    
    def handle_phone_callback(self, user_id: int, phone_number: str) -> str:
        """Обрабатывает запрос на обратный звонок."""
        if self.system_type == 'new':
            return self.new_orchestrator.handle_phone_callback(str(user_id), phone_number)
        else:
            # Для старой системы - базовая обработка
            return f"Спасибо! Администратор свяжется с вами по номеру {phone_number} в течение 15 минут."