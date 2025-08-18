from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseCommandHandler


class MessagesHandler(BaseCommandHandler):
    """Обработчик текстовых сообщений."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        if not self.auth.check_access(update.message.from_user.id):
            await self.auth.send_access_denied(update.message, context)
            return
            
        chat_id = update.message.chat.id
        self.message_manager.update_user_message_id(chat_id, update.message.message_id)
        
        if context.user_data.get('waiting_for_magnet'):
            await self.add_torrent_from_magnet(update.message, context)
        else:
            await self._show_main_menu(update.message, context, force_new=True)
    
    async def request_magnet_link(self, message, context: ContextTypes.DEFAULT_TYPE, save_path: str):
        """Запрашивает magnet ссылку для добавления торрента."""
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        category_name = "Фильмы" if "films" in save_path else "Сериалы" if "tvshows" in save_path else "Общее"
        
        await self.message_manager.send_or_edit_message(
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
    
    async def add_torrent_from_magnet(self, message, context: ContextTypes.DEFAULT_TYPE):
        """Добавляет торрент по magnet ссылке."""
        magnet_link = message.text.strip()
        
        if not magnet_link.startswith('magnet:'):
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.message_manager.send_or_edit_message(
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
                
                category_name = "Фильмы" if "films" in save_path else "Сериалы" if "tvshows" in save_path else "Общее"
                
                await self.message_manager.send_or_edit_message(
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
