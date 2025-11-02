import os 
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from src.bot.handlers import (
    start_router,
    token_router,
    google_sheet_router,
    service_account_router,
    result_json_router
)

from src.db.base import on_shutdown, on_startup
from src.services.gemini_api import GeminiVertexClient
        
# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/bot.log", encoding="utf-8"),  # сохраняем в файл
        logging.StreamHandler(),  # выводим в консоль
    ],
)

async def main():
    load_dotenv()
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN_STR")
    GOOGLE_SHEETS_TEMPLATE_URL = os.getenv("GOOGLE_SHEETS_TEMPLATE_URL")
    SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")


    GEMINI_PROJECT_ID = os.getenv("GEMINI_PROJECT_ID")
    GEMINI_MODEL_NAME=os.getenv("GEMINI_MODEL_NAME")
    gemini_client = GeminiVertexClient(
        model_name=GEMINI_MODEL_NAME,
        project_id=GEMINI_PROJECT_ID,
    )
    
    bot = Bot(token=TG_BOT_TOKEN)
    dp = Dispatcher()
    
    # create poll connection to and close poll connection to db
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    dp.workflow_data.update({
        "google_sheet_template_url": GOOGLE_SHEETS_TEMPLATE_URL,
        "service_account": SERVICE_ACCOUNT,
        "gemini_client": gemini_client
    })
    dp.include_routers(start_router, token_router, google_sheet_router, service_account_router, result_json_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())