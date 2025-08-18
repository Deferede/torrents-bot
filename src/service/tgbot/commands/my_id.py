from telegram import Update
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class MyIdCommandHandler(BaseCommandHandler):
    """Обработчик команды /myid."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /myid."""
        chat_id = update.message.chat.id
        self.message_manager.update_user_message_id(chat_id, update.message.message_id)
        await self.message_manager.send_or_edit_message(
            update.message, context,
            f"🆔 Ваш Chat ID: `{update.message.chat.id}`",
            parse_mode='Markdown',
            force_new=True
        )
