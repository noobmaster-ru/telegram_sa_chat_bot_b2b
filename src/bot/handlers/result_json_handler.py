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
from src.services.string_converter import StringConverterClass

from src.services.parse_telegram_data import parse_telegram_export

router = Router()


@router.message(StateFilter(UserState.result_json), F.document)
async def handle_result_json(message: Message):
    document = message.document

    if not document.file_name.endswith(".json"):
        await message.answer("Пожалуйста, отправь файл в формате .json 😊")
        return

    file = await message.bot.get_file(document.file_id)
    file_path = file.file_path

    file_bytes = await message.bot.download_file(file_path)

    # Сохраняем временно файл
    temp_path = f"/tmp/{document.file_name}"
    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(file_bytes.getvalue())

    # Парсим JSON
    parsed_path = parse_telegram_export(temp_path)
    parsed_file = FSInputFile(parsed_path)
    await message.answer_document(parsed_file, caption="✅ Вот твой распарсенный файл")

@router.callback_query(F.data.startswith("result_json_"), StateFilter(UserState.result_json))
async def callback_result_json(
    callback: CallbackQuery,
    state: FSMContext,
    db_session_factory: async_sessionmaker,
    service_account: str
):
    answer = "yes" if callback.data.endswith("yes") else "no"

    if answer == "yes":
        await callback.message.answer("Начинаю парсинг данных, подождите пожалуйста")
        await state.set_state(UserState.parsing_data)
    else:
        await state.clear()
        try:
            await callback.message.edit_text(
                f"Пришлите файл *result.json*",
                reply_markup=get_yes_no_keyboard("service_account"),
                parse_mode="MarkdownV2"
            )
        except:
            await callback.message.edit_text(
                f"Мне нужен ваш файл *result.json*",
                reply_markup=get_yes_no_keyboard("service_account"),
                parse_mode="MarkdownV2"
            )
        await state.set_state(UserState.result_json)