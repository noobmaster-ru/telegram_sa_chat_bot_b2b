import os 
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from src.bot.handlers import message_router

from src.db.base import on_shutdown, on_startup
        
async def main():
    load_dotenv()
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN_STR")
    GOOGLE_SHEETS_TEMPLATE_URL = os.getenv("GOOGLE_SHEETS_TEMPLATE_URL")
    
    bot = Bot(token=TG_BOT_TOKEN)
    dp = Dispatcher()
    
    # create poll connection to and close poll connection to db
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    dp.workflow_data.update({
        "google_sheet_template_url": GOOGLE_SHEETS_TEMPLATE_URL
    })
    dp.include_router(message_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("starting bot!")
    asyncio.run(main())