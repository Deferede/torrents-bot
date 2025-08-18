from abc import ABC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import TelegramBotService


class BaseCommandHandler(ABC):
    """Базовый класс для обработчиков команд."""
    
    def __init__(self, bot_service: 'TelegramBotService'):
        self.bot_service = bot_service
        self.qb_service = bot_service.qb_service
        self.config = bot_service.config
        self.auth = bot_service.auth
        self.message_manager = bot_service.message_manager
    
    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для Markdown."""
        special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def _get_status_emoji_and_text(self, status: str) -> tuple[str, str]:
        """Возвращает эмодзи и текст для статуса торрента."""
        status_map = {
            "downloading": ("⬇️", "Скачивается"),
            "uploading": ("⬆️", "Раздается"),
            "pausedDL": ("⏸️", "Приостановлено"),
            "pausedUP": ("⏸️", "Приостановлено"),
            "queuedDL": ("⏳", "В очереди"),
            "queuedUP": ("⏳", "В очереди"),
            "stalledDL": ("⚠️", "Зависло"),
            "stalledUP": ("⚠️", "Зависло"),
            "checkingDL": ("🔍", "Проверяется"),
            "checkingUP": ("🔍", "Проверяется"),
            "checkingResumeData": ("🔍", "Проверяется"),
            "metaDL": ("📋", "Метаданные"),
            "forcedDL": ("⚡", "Принудительно"),
            "forcedUP": ("⚡", "Принудительно"),
            "moving": ("📁", "Перемещается"),
            "missingFiles": ("❌", "Файлы отсутствуют"),
            "error": ("💥", "Ошибка"),
            "stoppedUP": ("⏹️", "Остановлено"),
        }
        return status_map.get(status, ("❓", status))
    
    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру главного меню."""
        keyboard = [
            [InlineKeyboardButton("📊 Торренты", callback_data="torrents")],
            [InlineKeyboardButton("➕ Добавить Торрент", callback_data="add_torrent")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def _show_main_menu(self, message, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False):
        """Показывает главное меню."""
        await self.message_manager.send_or_edit_message(
            message, context,
            "🤖 Torrents Bot активен!\n\n"
            "Используйте кнопки ниже:",
            self._get_main_menu_keyboard(),
            force_new=force_new
        )
