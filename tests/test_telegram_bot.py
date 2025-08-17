"""
Тесты для Telegram бота RAG-системы салона красоты.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from beauty_salon_rag.telegram_bot import TelegramBot, ConversationContext


class TestConversationContext:
    """Тесты класса ConversationContext."""
    
    def test_init(self):
        """Тест инициализации контекста."""
        user_id = 12345
        context = ConversationContext(user_id)
        
        assert context.user_id == user_id
        assert context.messages == []
        assert context.last_services == []
        assert context.user_preferences == {}
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.last_activity, datetime)
    
    def test_add_message(self):
        """Тест добавления сообщения в контекст."""
        context = ConversationContext(12345)
        
        context.add_message("user", "Привет!")
        
        assert len(context.messages) == 1
        assert context.messages[0]["role"] == "user"
        assert context.messages[0]["content"] == "Привет!"
        assert "timestamp" in context.messages[0]
        assert context.messages[0]["metadata"] == {}
    
    def test_add_message_with_metadata(self):
        """Тест добавления сообщения с метаданными."""
        context = ConversationContext(12345)
        metadata = {"command": "start"}
        
        context.add_message("system", "Начало диалога", metadata)
        
        assert len(context.messages) == 1
        assert context.messages[0]["metadata"] == metadata
    
    def test_message_limit(self):
        """Тест ограничения количества сообщений."""
        context = ConversationContext(12345)
        
        # Добавляем 25 сообщений (больше лимита в 20)
        for i in range(25):
            context.add_message("user", f"Сообщение {i}")
        
        # Должно остаться только 20 последних сообщений
        assert len(context.messages) == 20
        assert context.messages[0]["content"] == "Сообщение 5"  # Первые 5 удалены
        assert context.messages[-1]["content"] == "Сообщение 24"
    
    def test_get_context_summary_empty(self):
        """Тест получения резюме пустого контекста."""
        context = ConversationContext(12345)
        
        summary = context.get_context_summary()
        
        assert summary == ""
    
    def test_get_context_summary_with_messages(self):
        """Тест получения резюме контекста с сообщениями."""
        context = ConversationContext(12345)
        
        context.add_message("user", "Хочу массаж лица")
        context.add_message("assistant", "Рекомендую классический массаж лица...")
        context.add_message("user", "А сколько это стоит?")
        
        summary = context.get_context_summary()
        
        assert "Пользователь: Хочу массаж лица" in summary
        assert "Ассистент: Рекомендую классический массаж лица" in summary
        assert "Пользователь: А сколько это стоит?" in summary
    
    def test_get_context_summary_long_message(self):
        """Тест сокращения длинных сообщений в резюме."""
        context = ConversationContext(12345)
        
        long_message = "А" * 300  # Длинное сообщение
        context.add_message("assistant", long_message)
        
        summary = context.get_context_summary()
        
        assert "..." in summary  # Сообщение должно быть сокращено
        assert len(summary) < len(long_message)
    
    def test_is_expired_fresh(self):
        """Тест проверки свежего контекста."""
        context = ConversationContext(12345)
        
        assert not context.is_expired(24)  # Свежий контекст не истек
    
    def test_is_expired_old(self):
        """Тест проверки истекшего контекста."""
        context = ConversationContext(12345)
        
        # Устанавливаем старую дату последней активности
        context.last_activity = datetime.now() - timedelta(hours=25)
        
        assert context.is_expired(24)  # Контекст истек


class TestTelegramBot:
    """Тесты класса TelegramBot."""
    
    @pytest.fixture
    def mock_config(self):
        """Мок конфигурации."""
        with patch('beauty_salon_rag.telegram_bot.config') as mock:
            mock.get.return_value = "test_token"
            mock.get_telegram_config.return_value = {
                'max_message_length': 4096,
                'context_ttl_hours': 24,
                'max_context_messages': 20
            }
            yield mock
    
    @pytest.fixture
    def mock_rag_system(self):
        """Мок RAG-системы."""
        with patch('beauty_salon_rag.telegram_bot.BeautySalonRAG') as mock:
            mock_instance = Mock()
            mock_instance.process_query.return_value = "Тестовый ответ"
            mock_instance.get_system_status.return_value = {
                'search_module': True,
                'consultation_module': True,
                'overall_status': True
            }
            mock.return_value = mock_instance
            yield mock_instance
    
    def test_init_success(self, mock_config, mock_rag_system):
        """Тест успешной инициализации бота."""
        bot = TelegramBot()
        
        assert bot.bot_token == "test_token"
        assert bot.max_message_length == 4096
        assert bot.context_ttl_hours == 24
        assert bot.contexts == {}
    
    def test_init_no_token(self, mock_config, mock_rag_system):
        """Тест инициализации без токена."""
        mock_config.get.return_value = None
        
        with pytest.raises(ValueError, match="Telegram bot token not found"):
            TelegramBot()
    
    def test_get_or_create_context_new(self, mock_config, mock_rag_system):
        """Тест создания нового контекста."""
        bot = TelegramBot()
        user_id = 12345
        
        context = bot.get_or_create_context(user_id)
        
        assert user_id in bot.contexts
        assert context.user_id == user_id
        assert len(context.messages) == 0
    
    def test_get_or_create_context_existing(self, mock_config, mock_rag_system):
        """Тест получения существующего контекста."""
        bot = TelegramBot()
        user_id = 12345
        
        # Создаем контекст
        context1 = bot.get_or_create_context(user_id)
        context1.add_message("user", "Тест")
        
        # Получаем тот же контекст
        context2 = bot.get_or_create_context(user_id)
        
        assert context1 is context2
        assert len(context2.messages) == 1
    
    def test_cleanup_expired_contexts(self, mock_config, mock_rag_system):
        """Тест очистки истекших контекстов."""
        bot = TelegramBot()
        
        # Создаем свежий контекст
        fresh_context = bot.get_or_create_context(12345)
        
        # Создаем истекший контекст
        expired_context = bot.get_or_create_context(67890)
        expired_context.last_activity = datetime.now() - timedelta(hours=25)
        
        # Запускаем очистку
        bot._cleanup_expired_contexts()
        
        # Свежий контекст должен остаться, истекший - удалиться
        assert 12345 in bot.contexts
        assert 67890 not in bot.contexts
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_config, mock_rag_system):
        """Тест команды /start."""
        bot = TelegramBot()
        
        # Мокаем объекты Telegram
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.first_name = "Тест"
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_update = Mock()
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        # Вызываем команду
        await bot.start_command(mock_update, mock_context)
        
        # Проверяем, что ответ был отправлен
        mock_message.reply_text.assert_called_once()
        
        # Проверяем, что контекст создан
        assert 12345 in bot.contexts
        
        # Проверяем содержание ответа
        call_args = mock_message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Добро пожаловать, Тест!" in message_text
        assert "консультант салона красоты" in message_text
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_config, mock_rag_system):
        """Тест команды /help."""
        bot = TelegramBot()
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_update = Mock()
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        await bot.help_command(mock_update, mock_context)
        
        mock_message.reply_text.assert_called_once()
        
        call_args = mock_message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Справка по использованию бота" in message_text
        assert "/start" in message_text
        assert "/help" in message_text
    
    @pytest.mark.asyncio
    async def test_status_command(self, mock_config, mock_rag_system):
        """Тест команды /status."""
        bot = TelegramBot()
        
        mock_user = Mock()
        mock_user.id = 12345
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_update = Mock()
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        await bot.status_command(mock_update, mock_context)
        
        mock_message.reply_text.assert_called_once()
        
        call_args = mock_message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Статус системы" in message_text
        assert "✅" in message_text  # Система работает
    
    @pytest.mark.asyncio
    async def test_clear_command(self, mock_config, mock_rag_system):
        """Тест команды /clear."""
        bot = TelegramBot()
        
        user_id = 12345
        
        # Создаем контекст с сообщениями
        context = bot.get_or_create_context(user_id)
        context.add_message("user", "Тест")
        
        mock_user = Mock()
        mock_user.id = user_id
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        mock_update = Mock()
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        await bot.clear_command(mock_update, mock_context)
        
        # Проверяем, что контекст удален
        assert user_id not in bot.contexts
        
        # Проверяем ответ
        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args
        message_text = call_args[0][0]
        assert "История диалога очищена" in message_text
    
    @pytest.mark.asyncio
    async def test_handle_message(self, mock_config, mock_rag_system):
        """Тест обработки текстового сообщения."""
        bot = TelegramBot()
        
        mock_user = Mock()
        mock_user.id = 12345
        
        mock_message = Mock()
        mock_message.text = "Хочу массаж лица"
        mock_message.reply_text = AsyncMock()
        mock_message.chat.send_action = AsyncMock()
        
        mock_update = Mock()
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        await bot.handle_message(mock_update, mock_context)
        
        # Проверяем, что RAG-система была вызвана
        mock_rag_system.process_query.assert_called_once()
        
        # Проверяем, что ответ был отправлен
        mock_message.reply_text.assert_called_once()
        
        # Проверяем, что контекст обновлен
        user_context = bot.contexts[12345]
        assert len(user_context.messages) == 2  # Вопрос пользователя + ответ
        assert user_context.messages[0]["role"] == "user"
        assert user_context.messages[0]["content"] == "Хочу массаж лица"
        assert user_context.messages[1]["role"] == "assistant"
    
    def test_enhance_query_with_context_empty(self, mock_config, mock_rag_system):
        """Тест улучшения запроса без контекста."""
        bot = TelegramBot()
        context = ConversationContext(12345)
        
        query = "Хочу массаж"
        enhanced = bot._enhance_query_with_context(query, context)
        
        assert enhanced == query  # Без контекста запрос не изменяется
    
    def test_enhance_query_with_context_with_history(self, mock_config, mock_rag_system):
        """Тест улучшения запроса с контекстом."""
        bot = TelegramBot()
        context = ConversationContext(12345)
        
        # Добавляем историю
        context.add_message("user", "Хочу массаж лица")
        context.add_message("assistant", "Рекомендую классический массаж")
        
        query = "А сколько это стоит?"
        enhanced = bot._enhance_query_with_context(query, context)
        
        assert "Контекст предыдущего разговора:" in enhanced
        assert "Хочу массаж лица" in enhanced
        assert "А сколько это стоит?" in enhanced
    
    def test_split_long_message_short(self, mock_config, mock_rag_system):
        """Тест разбиения короткого сообщения."""
        bot = TelegramBot()
        
        message = "Короткое сообщение"
        parts = bot._split_long_message(message)
        
        assert len(parts) == 1
        assert parts[0] == message
    
    def test_split_long_message_long(self, mock_config, mock_rag_system):
        """Тест разбиения длинного сообщения."""
        bot = TelegramBot()
        bot.max_message_length = 100  # Устанавливаем маленький лимит для теста
        
        # Создаем длинное сообщение
        message = "Первый абзац.\n\nВторой абзац.\n\nТретий абзац."
        parts = bot._split_long_message(message)
        
        assert len(parts) > 1
        assert all(len(part) <= bot.max_message_length for part in parts)


class TestTelegramBotIntegration:
    """Интеграционные тесты Telegram бота."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Мокаем все зависимости."""
        with patch('beauty_salon_rag.telegram_bot.config') as mock_config, \
             patch('beauty_salon_rag.telegram_bot.BeautySalonRAG') as mock_rag:
            
            mock_config.get.return_value = "test_token"
            mock_config.get_telegram_config.return_value = {
                'max_message_length': 4096,
                'context_ttl_hours': 24,
                'max_context_messages': 20
            }
            
            mock_rag_instance = Mock()
            mock_rag_instance.process_query.return_value = "Тестовый ответ"
            mock_rag_instance.get_system_status.return_value = {
                'search_module': True,
                'consultation_module': True,
                'overall_status': True
            }
            mock_rag.return_value = mock_rag_instance
            
            yield mock_config, mock_rag_instance
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, mock_dependencies):
        """Тест полного потока разговора."""
        mock_config, mock_rag = mock_dependencies
        
        bot = TelegramBot()
        user_id = 12345
        
        # Создаем моки для Telegram объектов
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.first_name = "Тест"
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        mock_message.chat.send_action = AsyncMock()
        
        mock_update = Mock()
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        mock_context = Mock()
        
        # 1. Команда /start
        await bot.start_command(mock_update, mock_context)
        
        # Проверяем, что контекст создан
        assert user_id in bot.contexts
        user_context = bot.contexts[user_id]
        assert len(user_context.messages) == 1  # Системное сообщение о начале
        
        # 2. Первый вопрос пользователя
        mock_message.text = "Хочу массаж лица"
        await bot.handle_message(mock_update, mock_context)
        
        # Проверяем обновление контекста
        assert len(user_context.messages) == 3  # start + вопрос + ответ
        
        # 3. Уточняющий вопрос
        mock_message.text = "А сколько это стоит?"
        await bot.handle_message(mock_update, mock_context)
        
        # Проверяем, что контекст передается в RAG-систему
        assert len(user_context.messages) == 5  # Все сообщения сохранены
        
        # Проверяем, что последний вызов RAG содержал контекст
        last_call = mock_rag.process_query.call_args[0][0]
        assert "Контекст предыдущего разговора:" in last_call
        assert "Хочу массаж лица" in last_call
    
    @pytest.mark.asyncio
    async def test_context_cleanup_on_new_user(self, mock_dependencies):
        """Тест очистки контекстов при создании нового пользователя."""
        mock_config, mock_rag = mock_dependencies
        
        bot = TelegramBot()
        
        # Создаем истекший контекст
        old_context = ConversationContext(11111)
        old_context.last_activity = datetime.now() - timedelta(hours=25)
        bot.contexts[11111] = old_context
        
        # Создаем нового пользователя
        new_context = bot.get_or_create_context(22222)
        
        # Проверяем, что старый контекст удален
        assert 11111 not in bot.contexts
        assert 22222 in bot.contexts
        assert new_context.user_id == 22222