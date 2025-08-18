from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class TorrentsCommandHandler(BaseCommandHandler):
    """Обработчик команды /torrents и отображения торрентов."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /torrents."""
        if not self.auth.check_access(update.message.from_user.id):
            await self.auth.send_access_denied(update.message, context)
            return
            
        chat_id = update.message.chat.id
        self.message_manager.update_user_message_id(chat_id, update.message.message_id)
        await self.show_torrents(update.message, context, force_new=True)
    
    async def show_torrents(self, message, context: ContextTypes.DEFAULT_TYPE, page: int = 0, force_new: bool = False):
        """Показывает список торрентов с пагинацией."""
        try:
            torrents = self.qb_service.get_torrents()
            
            if not torrents:
                await self.message_manager.send_or_edit_message(
                    message, context, "📭 Торрентов нет", force_new=force_new
                )
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
            
            for torrent in current_torrents:
                speed = f"{torrent.current_speed:.1f} KB/s" if torrent.current_speed > 0 else "0 KB/s"
                eta_text = f"{torrent.eta//3600}ч {(torrent.eta%3600)//60}м" if torrent.eta > 0 else "∞"
                
                # Определяем статус и эмодзи
                status_emoji, status_text = self._get_status_emoji_and_text(torrent.status)
                
                # Определяем завершенность
                if torrent.status in ["uploading", "stalledUP", "checkingUP"]:
                    completion_emoji = "✅"
                else:
                    completion_emoji = "🔄"
                
                # Экранируем специальные символы для Markdown
                safe_name = self._escape_markdown(torrent.name)
                
                # Ограничиваем длину названия
                if len(safe_name) > 50:
                    safe_name = safe_name[:47] + "..."
                
                response += f"{completion_emoji} **{safe_name}**\n"
                response += f"   {status_emoji} {status_text}\n"
                response += f"   📊 Скорость: {speed}\n"
                response += f"   ⏱️ ETA: {eta_text}\n\n"
            
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
                # Проверяем, ожидается ли подтверждение удаления для какого-то торрента
                pending_delete_hash = context.user_data.get('pending_delete_hash')
                
                for torrent in current_torrents:
                    if pending_delete_hash == torrent.hash_value:
                        # Показываем кнопки подтверждения/отмены для этого торрента
                        keyboard.append([
                            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_delete_{torrent.hash_value}"),
                            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_delete_{torrent.hash_value}")
                        ])
                    else:
                        # Обычная кнопка удаления
                        keyboard.append([InlineKeyboardButton(
                            f"🗑️ {torrent.name[:30]}...", 
                            callback_data=f"delete_{torrent.hash_value}"
                        )])
            
            # Основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
                [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.message_manager.send_or_edit_message(
                message, context, response, reply_markup, 'Markdown', force_new=force_new
            )
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def delete_torrent(self, message, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
        """Удаляет торрент."""
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
                
                await self.message_manager.send_or_edit_message(
                    message, context,
                    "✅ Торрент успешно удален!\n"
                    "📁 Скачанные файлы также удалены для освобождения места на диске.",
                    reply_markup
                )
            else:
                await message.reply_text("❌ Не удалось удалить торрент")
            
        except Exception as e:
            await message.reply_text(f"❌ Ошибка при удалении торрента: {str(e)}")
