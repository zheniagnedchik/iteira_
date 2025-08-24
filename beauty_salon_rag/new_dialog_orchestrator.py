"""
Новый оркестратор диалогов для салона красоты "Итейра"
Использует DialogAssistant для структурированного ведения диалогов
и существующий поисковик для получения данных об услугах
"""

from typing import Dict, Any
from .dialog_assistant import DialogAssistant
from .gpt_client import GPTClient
from .modules.search_module import SearchModule
from .modules.data_loader import DataLoader
from .error_handler import ErrorHandler
from .logger import get_logger


class NewDialogOrchestrator:
    """Новый оркестратор для управления диалогами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # Инициализируем компоненты
        self.gpt_client = GPTClient()
        self.data_loader = DataLoader()  # Используем базовый путь по умолчанию
        self.search_module = SearchModule()  # Используем базовый путь по умолчанию
        
        # Создаем новый DialogAssistant
        self.dialog_assistant = DialogAssistant(
            gpt_client=self.gpt_client,
            search_module=self.search_module
        )
        
        # Хранилище контекстов пользователей
        self.user_contexts = {}

    def process_message(self, user_id: str, message: str) -> str:
        """
        Обрабатывает сообщение пользователя через новую систему диалогов
        
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
            
            # Обрабатываем сообщение через DialogAssistant (теперь синхронный)
            result = self.dialog_assistant.process_message(
                user_id=user_id,
                message=message,
                context=context
            )
            
            # Проверяем, нужно ли запустить процесс подтверждения после select_time_combo
            if result['context'].get('needs_booking_confirmation'):
                self.logger.info("Запускаем процесс подтверждения записи после select_time_combo")
                result['context'].pop('needs_booking_confirmation', None)  # Убираем флаг
                
                # Подготавливаем детали записи для подтверждения
                booking_details = self._prepare_combo_booking_details(result['context'])
                response_text, updated_context = self.dialog_assistant.booking_confirmation.start_booking_confirmation(booking_details)
                result['context'].update(updated_context)
                result['response'] = response_text
            
            # Обновляем контекст пользователя
            self.user_contexts[user_id] = result['context']
            
            # Логируем диалог
            self.logger.info(
                f"Диалог с пользователем {user_id}: "
                f"этап={result['context'].get('dialog_stage', 'unknown')}, "
                f"действие={result.get('action', 'unknown')}"
            )
            
            return result['response']
            
        except Exception as e:
            self.logger.error(f"Ошибка в NewDialogOrchestrator: {e}")
            # Для ошибок возвращаем простой fallback
            return "Извините, произошла техническая ошибка. Попробуйте позже или обратитесь к администратору."

    def _prepare_combo_booking_details(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает детали комбо-записи для подтверждения"""
        try:
            combo_service1 = context.get('combo_service1', {})
            combo_service2 = context.get('combo_service2', {})
            
            # Базовые детали
            booking_details = {
                'service_title': f"{combo_service1.get('title', '')} + {combo_service2.get('title', '')}",
                'date': context.get('selected_date'),
                'time': context.get('selected_time'),
                'location': 'ул. Немига, 5',
                'is_combo': True,
                'combo_service1': combo_service1,
                'combo_service2': combo_service2,
                'price': (combo_service1.get('price', 0) + combo_service2.get('price', 0))
            }
            
            # Добавляем информацию о мастерах из last_time_slots
            last_time_slots = context.get('last_time_slots', [])
            if last_time_slots and len(last_time_slots) > 0:
                slot = last_time_slots[0]
                booking_details['master1_name'] = slot.get('master1_name', 'уточняется')
                booking_details['master2_name'] = slot.get('master2_name', 'уточняется')
                booking_details['service1_time'] = slot.get('service1_time', context.get('selected_time'))
                booking_details['service2_time'] = slot.get('service2_time', context.get('selected_time'))
            
            self.logger.info(f"Подготовлены детали комбо-записи: {booking_details}")
            return booking_details
            
        except Exception as e:
            self.logger.error(f"Ошибка при подготовке деталей комбо-записи: {e}")
            # Возвращаем базовые данные
            return {
                'service_title': 'Комбо-услуги',
                'date': context.get('selected_date'),
                'time': context.get('selected_time'),
                'location': 'ул. Немига, 5',
                'is_combo': True,
                'price': 0
            }

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Получает контекст пользователя или создает новый
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Dict[str, Any]: Контекст пользователя
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                'dialog_stage': 'start',
                'user_name': None,
                'goal': None,
                'service_category': None,
                'selected_service': None,
                'location': None,
                'conversation_history': [],
                'created_at': None,
                'last_activity': None
            }
        
        return self.user_contexts[user_id].copy()

    def reset_user_context(self, user_id: str) -> None:
        """
        Сбрасывает контекст пользователя (начинает диалог заново)
        
        Args:
            user_id: Идентификатор пользователя
        """
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
        
        self.logger.info(f"Контекст пользователя {user_id} сброшен")

    def get_dialog_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по диалогам
        
        Returns:
            Dict[str, Any]: Статистика диалогов
        """
        total_users = len(self.user_contexts)
        
        # Подсчитываем пользователей по этапам
        stages_count = {}
        completed_dialogs = 0
        
        for context in self.user_contexts.values():
            stage = context.get('dialog_stage', 'unknown')
            stages_count[stage] = stages_count.get(stage, 0) + 1
            
            if stage in ['completion', 'completed']:
                completed_dialogs += 1
        
        return {
            'total_users': total_users,
            'completed_dialogs': completed_dialogs,
            'stages_distribution': stages_count,
            'completion_rate': completed_dialogs / total_users if total_users > 0 else 0
        }

    def handle_admin_connection(self, user_id: str) -> str:
        """
        Обрабатывает запрос на подключение администратора
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            str: Сообщение о подключении администратора
        """
        context = self.get_user_context(user_id)
        user_name = context.get('user_name', 'Клиент')
        
        # В реальной системе здесь была бы интеграция с CRM/системой уведомлений
        self.logger.info(f"Запрос на подключение администратора от пользователя {user_id}")
        
        # Обновляем контекст
        context['dialog_stage'] = 'admin_connected'
        context['admin_requested'] = True
        self.user_contexts[user_id] = context
        
        return (
            f"Сейчас подключаю администратора, {user_name}. "
            "Пожалуйста, подождите немного... "
            "Вам придет сообщение от администратора в этом чате. 📞"
        )

    def handle_phone_callback(self, user_id: str, phone_number: str) -> str:
        """
        Обрабатывает запрос на обратный звонок
        
        Args:
            user_id: Идентификатор пользователя
            phone_number: Номер телефона для обратного звонка
            
        Returns:
            str: Подтверждение запроса на звонок
        """
        context = self.get_user_context(user_id)
        user_name = context.get('user_name', 'Клиент')
        
        # Валидация номера телефона (упрощенная)
        if not phone_number or len(phone_number) < 10:
            return "Пожалуйста, укажите корректный номер телефона в формате +375XXYYYYYYY"
        
        # В реальной системе здесь была бы отправка в CRM
        self.logger.info(f"Запрос на обратный звонок: {user_id} -> {phone_number}")
        
        # Обновляем контекст
        context['phone_number'] = phone_number
        context['callback_requested'] = True
        context['dialog_stage'] = 'callback_requested'
        self.user_contexts[user_id] = context
        
        return (
            f"Спасибо, {user_name}! Администратор свяжется с вами по номеру {phone_number} "
            "в течение 15 минут. Если у вас есть срочные вопросы, звоните напрямую: "
            "+375 (29) 123-45-67 (клиника) или +375 (29) 765-43-21 (салон). 📞"
        )

    def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """
        Очищает старые контексты пользователей
        
        Args:
            max_age_hours: Максимальный возраст контекста в часах
            
        Returns:
            int: Количество удаленных контекстов
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        old_contexts = []
        for user_id, context in self.user_contexts.items():
            last_activity = context.get('last_activity', 0)
            if current_time - last_activity > max_age_seconds:
                old_contexts.append(user_id)
        
        # Удаляем старые контексты
        for user_id in old_contexts:
            del self.user_contexts[user_id]
        
        if old_contexts:
            self.logger.info(f"Удалено {len(old_contexts)} старых контекстов пользователей")
        
        return len(old_contexts)
