import asyncio
from src.service.tgbot import TelegramBotService

async def main():
    bot = TelegramBotService()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
