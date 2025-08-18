from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Optional


class MessageManager:
    """Управление состоянием сообщений для каждого чата."""
    
    def __init__(self):
        # Сохраняем ID последнего сообщения для каждого чата
        self.last_message_ids: Dict[int, int] = {}
        # Сохраняем ID последнего сообщения пользователя для каждого чата
        self.last_user_message_ids: Dict[int, int] = {}
    
    def update_user_message_id(self, chat_id: int, message_id: int):
        """Обновляет ID последнего сообщения пользователя."""
        self.last_user_message_ids[chat_id] = message_id
    
    async def send_or_edit_message(self, message, context: ContextTypes.DEFAULT_TYPE, 
                                 text: str, reply_markup=None, parse_mode=None, force_new=False):
        """Отправляет новое сообщение или редактирует существующее."""
        chat_id = message.chat.id
        
        # Если force_new=True или нет предыдущего сообщения бота, создаём новое
        if force_new or chat_id not in self.last_message_ids:
            sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            self.last_message_ids[chat_id] = sent_message.message_id
            return
        
        # Проверяем, старше ли сообщение бота последнего сообщения пользователя
        bot_message_id = self.last_message_ids[chat_id]
        last_user_message_id = self.last_user_message_ids.get(chat_id, 0)
        
        # Если сообщение бота старше последнего сообщения пользователя, создаём новое
        if bot_message_id <= last_user_message_id:
            sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            self.last_message_ids[chat_id] = sent_message.message_id
        else:
            # Пытаемся отредактировать существующее сообщение
            try:
                await context.bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    message_id=bot_message_id,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            except:
                # Если не удалось отредактировать, создаём новое
                sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                self.last_message_ids[chat_id] = sent_message.message_id


class AuthMiddleware:
    """Проверка доступа пользователей."""
    
    def __init__(self, trusted_users: Optional[list] = None):
        self.trusted_users = trusted_users or []
    
    def is_trusted_user(self, user_id: int) -> bool:
        """Проверяет является ли пользователь доверенным."""
        return user_id in self.trusted_users if self.trusted_users else True
    
    async def send_access_denied(self, message, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет сообщение об отказе в доступе."""
        await message.reply_text(
            "❌ У вас нет доступа к этой функции\n"
            "Доступные команды:\n"
            "• /help - справка\n"
            "• /myid - ваш ID"
        )
    
    def check_access(self, user_id: int) -> bool:
        """Проверяет доступ и возвращает результат."""
        return self.is_trusted_user(user_id)
