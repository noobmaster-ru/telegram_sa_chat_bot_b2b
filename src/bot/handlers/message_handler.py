import re
import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.states.user import User
from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.services.tools import ToolsClass


router = Router()

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext
):
    await message.answer("Здравствуйте! Пришлите,пожалуйста, свой токен от личного кабинета 😊")
    await state.set_state(User.waiting_for_token)

@router.callback_query(F.data.startswith("token_"), StateFilter(User.waiting_for_token))
async def callback_token(
    callback: CallbackQuery,
    state: FSMContext,
    google_sheet_template_url: str
):
    answer = "yes" if callback.data.endswith("yes") else "no"
    if answer == "yes":
        # ---- Запись токена в БД ------
        await callback.message.edit_text("✅ Ваш токен записан!")
        await callback.message.answer(f"Сделайте, пожалуйста , копию таблицы: \n\n {google_sheet_template_url}")
        await state.set_state(User.waiting_for_google_sheets_url)
    else:
        await callback.message.edit_text("Пришлите тогда токен ещё раз.")
        await state.set_state(User.waiting_for_token)

@router.message(StateFilter(User.waiting_for_token))
async def handle_token(
    message: Message,
    state: FSMContext
):
    token_text = message.text if message.text else "-"
    token_text_clean = ToolsClass.escape_markdown_v2(token_text)
    await message.reply(
        f"*{token_text_clean}*\n\n Это токен от вашего кабинета?",
        reply_markup=get_yes_no_keyboard("token"),
        parse_mode="MarkdownV2"
    )

       
@router.callback_query(F.data.startswith("google_sheets_url_"), StateFilter(User.waiting_for_google_sheets_url))
async def handle_google_sheets_url(
    callback: CallbackQuery,
    state: FSMContext
):
    answer = "yes" if callback.data.endswith("yes") else "no"
    if answer == "yes":
        # ---- Запись ссылки на гугл-таблицу записана в БД ------
        await callback.message.edit_text("✅ Ссылка на вашу таблица записана")
        await callback.message.answer("Что дальше?")
    else:
        await callback.message.edit_text("Пришлите тогда ссылку на таблицу ещё раз.")
        await state.set_state(User.waiting_for_google_sheets_url)

@router.message(StateFilter(User.waiting_for_google_sheets_url))
async def handle_google_sheets_url(
    message: Message,
    state: FSMContext
):
    url_text = message.text
    await message.reply(
        f"{url_text} \n\nЭто ссылка на вашу гугл-таблицу?",
        reply_markup=get_yes_no_keyboard("google_sheets_url")
    )
    