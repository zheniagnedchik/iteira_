#!/usr/bin/env python3
"""
Telegram Bot module for Beauty Salon RAG System
Provides conversational interface with context support
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

from .config import config
from .logger import get_logger, log_operation
from .error_handler import handle_error, BeautySalonError
from .dialog_orchestrator import DialogOrchestrator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import BeautySalonRAG


# ConversationContext теперь заменен на DialogOrchestrator


class TelegramBot:
    """Telegram бот для RAG-системы салона красоты."""
    
    def __init__(self):
        """Инициализация бота."""
        self.logger = get_logger(__name__)
        self.rag_system = BeautySalonRAG()
        
        # Инициализируем оркестратор диалогов
        self.orchestrator = DialogOrchestrator(self.rag_system)
        
        # Получаем токен бота из конфигурации
        self.bot_token = config.get('telegram.bot_token')
        if not self.bot_token:
            raise ValueError("Telegram bot token not found. Set TELEGRAM_BOT_TOKEN environment variable.")
        
        # Настройки бота
        self.max_message_length = config.get('telegram.max_message_length', 4096)
        self.context_ttl_hours = config.get('telegram.context_ttl_hours', 24)
        
        self.logger.info("Telegram bot with dialog orchestrator initialized successfully")
    
    # Методы контекста теперь обрабатываются через оркестратор
    @log_operation("telegram_start_command")
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        user = update.effective_user
        user_id = user.id
        
        self.logger.info(f"User {user_id} ({user.first_name}) started bot")
        
        # Обрабатываем команду /start как приветствие через оркестратор
        response, metadata = self.orchestrator.process_message(
            user_id=user_id,
            message="привет",  # Имитируем приветствие
            user_name=user.first_name
        )
        
        await update.message.reply_text(response)
    
    @log_operation("telegram_help_command")
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        help_text = (
            "📋 Справка по использованию бота:\n\n"
            "🔍 Поиск процедур:\n"
            "• \"массаж лица\"\n"
            "• \"процедуры от морщин\"\n"
            "• \"что поможет от акне?\"\n\n"
            "💬 Консультации:\n"
            "• \"что такое RF-лифтинг?\"\n"
            "• \"противопоказания к ботоксу\"\n"
            "• \"как подготовиться к пилингу?\"\n\n"
            "📅 Запись к мастеру:\n"
            "• \"хочу записаться на массаж\"\n"
            "• \"какие мастера делают чистку?\"\n"
            "• \"когда можно записаться?\"\n\n"
            "🎯 Команды:\n"
            "/start - начать заново\n"
            "/help - эта справка\n"
            "/status - статус системы\n"
            "/clear - очистить историю\n\n"
            "💡 Я запоминаю наш разговор и могу отвечать на уточняющие вопросы!"
        )
        
        await update.message.reply_text(help_text)
    
    @log_operation("telegram_status_command")
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status."""
        try:
            # Получаем статус системы
            status = self.rag_system.get_system_status()
            
            status_text = "📊 Статус системы:\n\n"
            status_text += f"🔍 Поисковый модуль: {'✅' if status['search_module'] else '❌'}\n"
            status_text += f"💬 Консультационный модуль: {'✅' if status['consultation_module'] else '❌'}\n"
            status_text += f"🎭 Оркестратор диалогов: ✅\n"
            status_text += f"⚡ Общий статус: {'✅ Работает' if status['overall_status'] else '❌ Есть проблемы'}\n\n"
            
            # Добавляем информацию о пользователе из оркестратора
            user_id = update.effective_user.id
            user_stats = self.orchestrator.get_user_stats(user_id)
            
            if user_stats:
                status_text += f"👤 Ваш профиль:\n"
                status_text += f"   Имя: {user_stats.get('name', 'Не указано')}\n"
                status_text += f"   Состояние: {user_stats.get('state', 'unknown')}\n"
                status_text += f"   Сообщений: {user_stats.get('interaction_count', 0)}\n"
                status_text += f"   Контекст: {user_stats.get('context_messages', 0)} сообщений\n"
            
            # Добавляем общую статистику оркестратора
            orchestrator_stats = self.orchestrator.get_orchestrator_stats()
            status_text += f"\n📈 Статистика бота:\n"
            status_text += f"   Всего пользователей: {orchestrator_stats['total_users']}\n"
            status_text += f"   Активных диалогов: {orchestrator_stats['active_conversations']}\n"
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            error_msg = handle_error(e, context={"command": "status", "user_id": update.effective_user.id})
            await update.message.reply_text(f"❌ Ошибка получения статуса: {error_msg}")
    
    @log_operation("telegram_clear_command")
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /clear."""
        user_id = update.effective_user.id
        
        # Очищаем контекст через оркестратор
        self.orchestrator.clear_user_context(user_id)
        
        await update.message.reply_text(
            "🧹 История диалога очищена!\n"
            "Теперь мы начинаем общение с чистого листа."
        )
    
    @log_operation("telegram_button_callback")
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        if callback_data.startswith("quick_"):
            # Быстрые запросы
            quick_query = callback_data.replace("quick_", "")
            
            # Создаем фейковое сообщение для обработки
            fake_message = type('obj', (object,), {
                'text': quick_query,
                'from_user': query.from_user,
                'reply_text': query.message.reply_text
            })
            
            fake_update = type('obj', (object,), {
                'message': fake_message,
                'effective_user': query.from_user
            })
            
            await self.handle_message(fake_update, context)
    
    # Все сообщения теперь обрабатываются через GPT-оркестратор
    # Хардкод-методы удалены для полной GPT-driven архитектуры

    @log_operation("telegram_handle_message")
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        self.logger.info(f"Received message from user {user_id}: {message_text[:100]}...")
        
        try:
            # Показываем индикатор печати
            await update.message.chat.send_action("typing")
            
            # Обрабатываем сообщение через оркестратор
            response, metadata = self.orchestrator.process_message(
                user_id=user_id,
                message=message_text,
                user_name=user.first_name
            )
            
            # Разбиваем длинные сообщения
            messages = self._split_long_message(response)
            
            # Отправляем ответ
            for msg in messages:
                await update.message.reply_text(msg, parse_mode='Markdown')
                
                # Небольшая задержка между сообщениями
                if len(messages) > 1:
                    await asyncio.sleep(0.5)
            
            # Логируем метаданные для аналитики
            self.logger.info(f"Successfully processed message for user {user_id}, type: {metadata.get('type', 'unknown')}")
            
        except Exception as e:
            error_msg = handle_error(e, context={
                "user_id": user_id, 
                "message": message_text[:100],
                "operation": "handle_message"
            })
            
            await update.message.reply_text(
                f"😔 Извините, произошла ошибка при обработке вашего запроса.\n\n"
                f"Попробуйте переформулировать вопрос или обратитесь позже.\n\n"
                f"Детали: {error_msg}"
            )
    
    # Контекст теперь обрабатывается через оркестратор
    
    def _split_long_message(self, message: str) -> List[str]:
        """Разбивает длинные сообщения на части."""
        if len(message) <= self.max_message_length:
            return [message]
        
        messages = []
        current_message = ""
        
        # Разбиваем по абзацам
        paragraphs = message.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_message + paragraph + '\n\n') <= self.max_message_length:
                current_message += paragraph + '\n\n'
            else:
                if current_message:
                    messages.append(current_message.strip())
                    current_message = ""
                
                # Если абзац слишком длинный, разбиваем по предложениям
                if len(paragraph) > self.max_message_length:
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_message + sentence + '. ') <= self.max_message_length:
                            current_message += sentence + '. '
                        else:
                            if current_message:
                                messages.append(current_message.strip())
                            current_message = sentence + '. '
                else:
                    current_message = paragraph + '\n\n'
        
        if current_message:
            messages.append(current_message.strip())
        
        return messages
    
    @log_operation("telegram_error_handler")
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок бота."""
        self.logger.error(f"Telegram bot error: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "😔 Произошла техническая ошибка. Попробуйте позже или обратитесь к администратору."
            )
    
    def run(self):
        """Запускает бота."""
        self.logger.info("Starting Telegram bot...")
        
        # Создаем приложение
        application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        # Запускаем бота
        self.logger.info("Telegram bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция для запуска Telegram бота."""
    try:
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Failed to start bot: {e}")


if __name__ == "__main__":
    main()