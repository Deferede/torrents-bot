from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class HelpCommandHandler(BaseCommandHandler):
    """Обработчик команды /help."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        chat_id = update.message.chat.id
        self.message_manager.update_user_message_id(chat_id, update.message.message_id)
        
        keyboard = [
            [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
            [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.message_manager.send_or_edit_message(
            update.message, context,
            "📋 **Команды бота:**\n\n"
            "• /start - запуск бота\n"
            "• /help - эта справка\n"
            "• /myid - показать ваш Chat ID\n\n"
            "Или используйте кнопки:",
            reply_markup,
            parse_mode='Markdown',
            force_new=True
        )
