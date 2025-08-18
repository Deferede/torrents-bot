import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from src.config.config import Config
from src.service.qbittorrent import QBittorrentService
from .middleware import MessageManager, AuthMiddleware
from .handler import CommandHandlers


class TelegramBotService:
    """Основной класс телеграм бота."""
    
    def __init__(self):
        # Инициализация конфигурации
        self.config = Config()
        
        # Инициализация зависимостей
        qb_config = self.config.get_qbittorrent_config()
        self.qb_service = QBittorrentService(**qb_config)
        
        # Инициализация middleware
        trusted_users = self.config.get_trusted_users()
        self.auth = AuthMiddleware(trusted_users)
        self.message_manager = MessageManager()
        
        # Инициализация обработчиков команд
        self.command_handlers = CommandHandlers(self)
        
        # Инициализация приложения телеграм
        self.app = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Настройка обработчиков
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений."""
        # Команды
        self.app.add_handler(CommandHandler("start", self.command_handlers.start_command))
        self.app.add_handler(CommandHandler("help", self.command_handlers.help_command))
        self.app.add_handler(CommandHandler("torrents", self.command_handlers.torrents_command))
        self.app.add_handler(CommandHandler("myid", self.command_handlers.my_id_command))
        
        # Обработчики
        self.app.add_handler(CallbackQueryHandler(self.command_handlers.button_callback))
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.command_handlers.handle_message
        ))
    
    async def run(self):
        """Запуск бота."""
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
