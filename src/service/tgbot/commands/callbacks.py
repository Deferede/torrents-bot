from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class CallbacksHandler(BaseCommandHandler):
    """Обработчик callback запросов (нажатий кнопок)."""
    
    def __init__(self, bot_service):
        super().__init__(bot_service)
        # Импортируем другие обработчики для использования их методов
        from .torrents import TorrentsCommandHandler
        from .messages import MessagesHandler
        
        self.torrents_handler = TorrentsCommandHandler(bot_service)
        self.messages_handler = MessagesHandler(bot_service)
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок."""
        query = update.callback_query
        await query.answer()
        
        if not self.auth.check_access(query.from_user.id):
            await query.message.reply_text(
                "❌ У вас нет доступа к этой функции\n"
                "Доступные команды:\n"
                "• /help - справка\n"
                "• /myid - ваш ID"
            )
            return
        
        if query.data == "torrents":
            # Сбрасываем состояние ожидания удаления при возврате к списку
            context.user_data.pop('pending_delete_hash', None)
            await self.torrents_handler.show_torrents(query.message, context)
        elif query.data.startswith("page_"):
            page = int(query.data.split("_")[1])
            await self.torrents_handler.show_torrents(query.message, context, page)
        elif query.data.startswith("delete_"):
            await self._handle_delete_request(query.message, context, query.data)
        elif query.data.startswith("confirm_delete_"):
            await self._handle_confirm_delete(query.message, context, query.data)
        elif query.data.startswith("cancel_delete_"):
            await self._handle_cancel_delete(query.message, context, query.data)
        elif query.data == "add_torrent":
            await self._request_category_selection(query.message, context)
        elif query.data == "category_films":
            await self.messages_handler.request_magnet_link(query.message, context, "/DATA/films")
        elif query.data == "category_series":
            await self.messages_handler.request_magnet_link(query.message, context, "/DATA/tvshows")
        elif query.data == "cancel":
            context.user_data['waiting_for_magnet'] = False
            context.user_data.pop('save_path', None)
            context.user_data.pop('pending_delete_hash', None)  # Сбрасываем и состояние удаления
            keyboard = [
                [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.message_manager.send_or_edit_message(
                query.message, context, "❌ Добавление торрента отменено", reply_markup
            )
    
    async def _request_category_selection(self, message, context: ContextTypes.DEFAULT_TYPE):
        """Запрашивает выбор категории для торрента."""
        keyboard = [
            [InlineKeyboardButton("🎬 Фильмы", callback_data="category_films")],
            [InlineKeyboardButton("📺 Сериалы", callback_data="category_series")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.message_manager.send_or_edit_message(
            message, context,
            "📂 Выберите категорию для торрента:",
            reply_markup
        )
    
    async def _handle_delete_request(self, message, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обрабатывает запрос на удаление торрента - показывает кнопки подтверждения."""
        # Проверяем права администратора
        if str(message.chat.id) != self.config.ADMIN_CHAT_ID:
            await message.reply_text("❌ У вас нет прав для удаления торрентов")
            return
        
        # Извлекаем hash торрента из callback_data
        hash_value = callback_data.replace("delete_", "")
        
        if not hash_value:
            await message.reply_text("❌ Не удалось определить торрент для удаления")
            return
        
        # Устанавливаем состояние ожидания подтверждения
        context.user_data['pending_delete_hash'] = hash_value
        
        # Перерисовываем список торрентов с кнопками подтверждения
        await self.torrents_handler.show_torrents(message, context)
    
    async def _handle_confirm_delete(self, message, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обрабатывает подтверждение удаления торрента."""
        # Проверяем права администратора
        if str(message.chat.id) != self.config.ADMIN_CHAT_ID:
            await message.reply_text("❌ У вас нет прав для удаления торрентов")
            return
        
        try:
            # Извлекаем hash торрента из callback_data
            hash_value = callback_data.replace("confirm_delete_", "")
            
            if not hash_value:
                await message.reply_text("❌ Не удалось определить торрент для удаления")
                return
            
            # Удаляем торрент и файлы
            success = self.qb_service.delete_torrent(hash_value, delete_files=True)
            
            # Сбрасываем состояние ожидания
            context.user_data.pop('pending_delete_hash', None)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                    [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self.message_manager.send_or_edit_message(
                    message, context,
                    "✅ Торрент успешно удален!\n"
                    "📁 Скачанные файлы также удалены для освобождения места на диске.",
                    reply_markup
                )
            else:
                await message.reply_text("❌ Не удалось удалить торрент")
                # Показываем список торрентов обратно
                await self.torrents_handler.show_torrents(message, context)
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка при удалении торрента: {str(e)}")
            # Сбрасываем состояние и показываем список торрентов
            context.user_data.pop('pending_delete_hash', None)
            await self.torrents_handler.show_torrents(message, context)
    
    async def _handle_cancel_delete(self, message, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Обрабатывает отмену удаления торрента."""
        # Сбрасываем состояние ожидания подтверждения
        context.user_data.pop('pending_delete_hash', None)
        
        # Перерисовываем список торрентов без кнопок подтверждения
        await self.torrents_handler.show_torrents(message, context)
