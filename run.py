import os 
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from src.bot.handlers import *

from src.db.base import on_shutdown, on_startup
        
async def main():
    load_dotenv()
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN_STR")
    GOOGLE_SHEETS_TEMPLATE_URL = os.getenv("GOOGLE_SHEETS_TEMPLATE_URL")
    SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")

    
    bot = Bot(token=TG_BOT_TOKEN)
    dp = Dispatcher()
    
    # create poll connection to and close poll connection to db
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    dp.workflow_data.update({
        "google_sheet_template_url": GOOGLE_SHEETS_TEMPLATE_URL,
        "service_account": SERVICE_ACCOUNT
    })
    dp.include_routers(start_router, token_router, google_sheet_router, service_account_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("starting bot!")
    asyncio.run(main())