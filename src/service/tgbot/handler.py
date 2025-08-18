from telegram import Update
from telegram.ext import ContextTypes
from typing import TYPE_CHECKING

from .commands import (
    StartCommandHandler,
    HelpCommandHandler,
    MyIdCommandHandler,
    TorrentsCommandHandler,
    CallbacksHandler,
    MessagesHandler
)

if TYPE_CHECKING:
    from .bot import TelegramBotService


class CommandHandlers:
    """Координатор всех обработчиков команд телеграм бота."""
    
    def __init__(self, bot_service: 'TelegramBotService'):
        self.bot_service = bot_service
        
        # Инициализируем все обработчики
        self.start_handler = StartCommandHandler(bot_service)
        self.help_handler = HelpCommandHandler(bot_service)
        self.my_id_handler = MyIdCommandHandler(bot_service)
        self.torrents_handler = TorrentsCommandHandler(bot_service)
        self.callbacks_handler = CallbacksHandler(bot_service)
        self.messages_handler = MessagesHandler(bot_service)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        await self.start_handler.handle(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        await self.help_handler.handle(update, context)
    
    async def torrents_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /torrents."""
        await self.torrents_handler.handle(update, context)
    
    async def my_id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /myid."""
        await self.my_id_handler.handle(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        await self.messages_handler.handle(update, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок."""
        await self.callbacks_handler.handle(update, context)
    

    

    

    

    

    



    

