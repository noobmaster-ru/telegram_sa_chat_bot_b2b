import json
import io
import aiofiles
from pathlib import Path
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile, InputMediaPhoto,  Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.bot.states.user import UserState

from src.services.parsing_data import ParsingDataClass

router = Router()


@router.message(StateFilter(UserState.result_json), F.document)
async def handle_result_json(message: Message):
    await message.reply("Начинаю парсинг, подождите, пожалуйста")
    document = message.document
    telegram_id = message.from_user.id
    if not document.file_name.endswith(".json"):
        await message.answer("Пожалуйста, отправь файл в формате .json 😊")
        return

    file = await message.bot.get_file(document.file_id)
    file_path = file.file_path

    file_bytes = await message.bot.download_file(file_path)

    # Сохраняем временно файл
    temp_path = f"/app/{document.file_name}"
    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(file_bytes.getvalue())

    # Парсим JSON
    parsed_path = await ParsingDataClass.parse_telegram_export_async(temp_path, telegram_id)
    parsed_file = FSInputFile(parsed_path)
    await message.answer_document(parsed_file, caption="✅ Вот твой распаршенный файл")

@router.message(StateFilter(UserState.result_json))
async def handle_result_json_other_message(message: Message):
    await message.answer(
        "Пришлите, пожалуйста, файл *result\.json*",
        parse_mode="MarkdownV2"
    )