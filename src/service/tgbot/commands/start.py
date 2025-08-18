from telegram import Update
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class StartCommandHandler(BaseCommandHandler):
    """Обработчик команды /start."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        if not self.auth.check_access(update.message.from_user.id):
            await self.auth.send_access_denied(update.message, context)
            return
            
        chat_id = update.message.chat.id
        self.message_manager.update_user_message_id(chat_id, update.message.message_id)
        await self._show_main_menu(update.message, context, force_new=True)
