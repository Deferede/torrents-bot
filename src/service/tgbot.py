import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from src.config.config import Config
from src.service.qbittorrent import QBittorrentService
from src.presenters.torrent_presenter import TorrentPresenter


class TelegramBotService:
    def __init__(self):
        self.config = Config()
        self.app = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        qb_config = self.config.get_qbittorrent_config()
        self.qb_service = QBittorrentService(**qb_config)
        self._setup_handlers()
        # Сохраняем ID последнего сообщения для каждого чата
        self.last_message_ids = {}
        # Сохраняем ID последнего сообщения пользователя для каждого чата
        self.last_user_message_ids = {}
    
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("torrents", self.torrents))
        self.app.add_handler(CommandHandler("myid", self.my_id))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Сохраняем ID последнего сообщения пользователя
        chat_id = update.message.chat.id
        self.last_user_message_ids[chat_id] = update.message.message_id
        await self._show_main_menu_force_new(update.message, context)
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Сохраняем ID последнего сообщения пользователя
        chat_id = update.message.chat.id
        self.last_user_message_ids[chat_id] = update.message.message_id
        
        keyboard = [
            [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
            [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_or_edit_message(
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
    
    async def torrents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Сохраняем ID последнего сообщения пользователя
        chat_id = update.message.chat.id
        self.last_user_message_ids[chat_id] = update.message.message_id
        await self._show_torrents(update.message, context, force_new=True)
    
    async def my_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Сохраняем ID последнего сообщения пользователя
        chat_id = update.message.chat.id
        self.last_user_message_ids[chat_id] = update.message.message_id
        await self._send_or_edit_message(
            update.message, context,
            f"🆔 Ваш Chat ID: `{update.message.chat.id}`",
            parse_mode='Markdown',
            force_new=True
        )
    
    async def _send_or_edit_message(self, message, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None, parse_mode=None, force_new=False):
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

    async def _show_torrents(self, message, context: ContextTypes.DEFAULT_TYPE, page: int = 0, force_new: bool = False):
        try:
            torrents = self.qb_service.get_torrents()
            
            if not torrents:
                await self._send_or_edit_message(message, context, "📭 Торрентов нет", force_new=force_new)
                return
            
            # Пагинация по 5 торрентов
            page_size = 5
            total_pages = (len(torrents) + page_size - 1) // page_size
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(torrents))
            
            current_torrents = torrents[start_idx:end_idx]
            
            response = f"📊 **Торренты:** (стр. {page + 1} из {total_pages})\n\n"
            
            # Создаем клавиатуру
            keyboard = []
            
            for i, torrent in enumerate(current_torrents):
                speed = f"{torrent.current_speed:.1f} KB/s" if torrent.current_speed > 0 else "0 KB/s"
                eta_text = f"{torrent.eta//3600}ч {(torrent.eta%3600)//60}м" if torrent.eta > 0 else "∞"
                
                # Определяем статус и эмодзи
                if torrent.status == "downloading":
                    status_emoji = "⬇️"
                    status_text = "Скачивается"
                elif torrent.status == "uploading":
                    status_emoji = "⬆️"
                    status_text = "Раздается"
                elif torrent.status == "pausedDL":
                    status_emoji = "⏸️"
                    status_text = "Приостановлено"
                elif torrent.status == "pausedUP":
                    status_emoji = "⏸️"
                    status_text = "Приостановлено"
                elif torrent.status == "queuedDL":
                    status_emoji = "⏳"
                    status_text = "В очереди"
                elif torrent.status == "queuedUP":
                    status_emoji = "⏳"
                    status_text = "В очереди"
                elif torrent.status == "stalledDL":
                    status_emoji = "⚠️"
                    status_text = "Зависло"
                elif torrent.status == "stalledUP":
                    status_emoji = "⚠️"
                    status_text = "Зависло"
                elif torrent.status == "checkingDL":
                    status_emoji = "🔍"
                    status_text = "Проверяется"
                elif torrent.status == "checkingUP":
                    status_emoji = "🔍"
                    status_text = "Проверяется"
                elif torrent.status == "checkingResumeData":
                    status_emoji = "🔍"
                    status_text = "Проверяется"
                elif torrent.status == "metaDL":
                    status_emoji = "📋"
                    status_text = "Метаданные"
                elif torrent.status == "forcedDL":
                    status_emoji = "⚡"
                    status_text = "Принудительно"
                elif torrent.status == "forcedUP":
                    status_emoji = "⚡"
                    status_text = "Принудительно"
                elif torrent.status == "moving":
                    status_emoji = "📁"
                    status_text = "Перемещается"
                elif torrent.status == "missingFiles":
                    status_emoji = "❌"
                    status_text = "Файлы отсутствуют"
                elif torrent.status == "error":
                    status_emoji = "💥"
                    status_text = "Ошибка"
                elif torrent.status == "stoppedUP":
                    status_emoji = "⏹️"
                    status_text = "Остановлено"
                else:
                    status_emoji = "❓"
                    status_text = torrent.status
                
                # Определяем завершенность
                if torrent.status in ["uploading", "stalledUP", "checkingUP"]:
                    completion_emoji = "✅"
                    completion_text = "Завершено"
                else:
                    completion_emoji = "🔄"
                    completion_text = "В процессе"
                
                # Экранируем специальные символы для Markdown
                safe_name = torrent.name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
                
                # Ограничиваем длину названия
                if len(safe_name) > 50:
                    safe_name = safe_name[:47] + "..."
                
                response += f"{completion_emoji} **{safe_name}**\n"
                response += f"   {status_emoji} {status_text}\n"
                response += f"   📊 Скорость: {speed}\n"
                response += f"   ⏱️ ETA: {eta_text}\n"
                
                response += "\n"
            
            # Добавляем пагинацию и основные кнопки
            
            # Кнопки навигации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{page+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # Кнопки удаления для администратора
            if str(message.chat.id) == self.config.ADMIN_CHAT_ID:
                for torrent in current_torrents:
                    keyboard.append([InlineKeyboardButton(f"🗑️ {torrent.name[:30]}...", callback_data=f"delete_{torrent.hash_value}")])
            
            # Основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_or_edit_message(message, context, response, reply_markup, 'Markdown', force_new=force_new)
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def _request_category_selection(self, message, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🎬 Фильмы", callback_data="category_films")],
            [InlineKeyboardButton("📺 Сериалы", callback_data="category_series")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_or_edit_message(
            message, context,
            "📂 Выберите категорию для торрента:",
            reply_markup
        )
    
    async def _request_magnet_link(self, message, context: ContextTypes.DEFAULT_TYPE, save_path: str):
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if "films" in save_path:
            category_name = "Фильмы"
        elif "tvshows" in save_path:
            category_name = "Сериалы"
        else:
            category_name = "Общее"
        
        await self._send_or_edit_message(
            message, context,
            f"🔗 Отправьте magnet ссылку для добавления торрента\n\n"
            f"Категория: {category_name}\n"
            f"Путь: `{save_path}`",
            reply_markup,
            parse_mode='Markdown'
        )
        
        # Сохраняем состояние ожидания magnet ссылки и путь сохранения
        context.user_data['waiting_for_magnet'] = True
        context.user_data['save_path'] = save_path
    
    async def _show_main_menu(self, message, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
            [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_or_edit_message(
            message, context,
            "🤖 Torrents Bot активен!\n\n"
            "Используйте кнопки ниже:",
            reply_markup
        )

    async def _show_main_menu_force_new(self, message, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
            [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_or_edit_message(
            message, context,
            "🤖 Torrents Bot активен!\n\n"
            "Используйте кнопки ниже:",
            reply_markup,
            force_new=True
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Сохраняем ID последнего сообщения пользователя
        chat_id = update.message.chat.id
        self.last_user_message_ids[chat_id] = update.message.message_id
        
        if context.user_data.get('waiting_for_magnet'):
            await self._add_torrent_from_magnet(update.message, context)
        else:
            # Сброс интерфейса - показываем главное меню (новое сообщение)
            await self._show_main_menu_force_new(update.message, context)
    
    async def _add_torrent_from_magnet(self, message, context: ContextTypes.DEFAULT_TYPE):
        magnet_link = message.text.strip()
        
        if not magnet_link.startswith('magnet:'):
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self._send_or_edit_message(
                message, context,
                "❌ Это не magnet ссылка. Отправьте корректную magnet ссылку.",
                reply_markup
            )
            return
        
        try:
            # Получаем сохраненный путь или используем по умолчанию
            save_path = context.user_data.get('save_path', '/DATA')
            
            # Добавляем торрент через magnet ссылку
            success = self.qb_service.add_torrent_from_magnet(magnet_link, save_path)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                    [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if "films" in save_path:
                    category_name = "Фильмы"
                elif "tvshows" in save_path:
                    category_name = "Сериалы"
                else:
                    category_name = "Общее"
                
                await self._send_or_edit_message(
                    message, context,
                    f"✅ Торрент успешно добавлен!\n"
                    f"Категория: {category_name}\n"
                    f"Путь: `{save_path}`\n"
                    f"Ссылка: {magnet_link[:50]}...",
                    reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await message.reply_text("❌ Не удалось добавить торрент. Проверьте ссылку.")
            
            # Сбрасываем состояние ожидания
            context.user_data['waiting_for_magnet'] = False
            context.user_data.pop('save_path', None)
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка при добавлении торрента: {str(e)}")
            context.user_data['waiting_for_magnet'] = False
            context.user_data.pop('save_path', None)
    
    async def _delete_torrent(self, message, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        # Проверяем права администратора
        if str(message.chat.id) != self.config.ADMIN_CHAT_ID:
            await message.reply_text("❌ У вас нет прав для удаления торрентов")
            return
        
        try:
            # Извлекаем hash торрента из callback_data
            hash_value = callback_data.replace("delete_", "")
            
            if not hash_value:
                await message.reply_text("❌ Не удалось определить торрент для удаления")
                return
            
            # Удаляем торрент и файлы
            success = self.qb_service.delete_torrent(hash_value, delete_files=True)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                    [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self._send_or_edit_message(
                    message, context,
                    "✅ Торрент успешно удален!\n"
                    "📁 Скачанные файлы также удалены для освобождения места на диске.",
                    reply_markup
                )
            else:
                await message.reply_text("❌ Не удалось удалить торрент")
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка при удалении торрента: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "torrents":
            await self._show_torrents(query.message, context)
        elif query.data.startswith("page_"):
            page = int(query.data.split("_")[1])
            await self._show_torrents(query.message, context, page)
        elif query.data.startswith("delete_"):
            await self._delete_torrent(query.message, context, query.data)
        elif query.data == "add_torrent":
            await self._request_category_selection(query.message, context)
        elif query.data == "category_films":
            await self._request_magnet_link(query.message, context, "/DATA/films")
        elif query.data == "category_series":
            await self._request_magnet_link(query.message, context, "/DATA/tvshows")
        elif query.data == "cancel":
            context.user_data['waiting_for_magnet'] = False
            context.user_data.pop('save_path', None)
            keyboard = [
                [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self._send_or_edit_message(query.message, context, "❌ Добавление торрента отменено", reply_markup)
    
    async def run(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
