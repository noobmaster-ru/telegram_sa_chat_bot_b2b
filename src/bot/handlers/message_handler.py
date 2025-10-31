from aiogram import Router,  F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message,   CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.states.user import User
from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.services.tools import ToolsClass
import asyncpg.pool


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
    google_sheet_template_url: str,
    db_pool: asyncpg.pool.Pool
):
    data = await state.get_data()
    
    answer = "yes" if callback.data.endswith("yes") else "no"
    username = callback.from_user.username
    telegram_id = callback.from_user.id
    wb_token = data.get("wb_token")
    
    if answer == "yes":
        # ---- insert wb_token to database ------
        async with db_pool.acquire() as connection:
            await connection.execute('''
                INSERT INTO users (telegram_id, username, wb_token)
                VALUES ($1, $2, $3)
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    wb_token = EXCLUDED.wb_token,
                    last_update = CURRENT_TIMESTAMP
            ''', telegram_id, username, wb_token)
            print(f"[INFO] insert into users wb_token from {telegram_id}")
        await callback.message.edit_text("✅ Ваш токен записан!")
        await callback.message.answer(
            f"Сделайте, пожалуйста, этой таблицы:\n\n{google_sheet_template_url}\n\nи пришлите ссылку на неё мне."
        )
        await state.set_state(User.waiting_for_google_sheets_url)
    else:
        # delete wb_token from state 
        await state.clear()
        await callback.message.edit_text("Пришлите тогда токен ещё раз.")
        await state.set_state(User.waiting_for_token)

@router.message(StateFilter(User.waiting_for_token))
async def handle_token(
    message: Message,
    state: FSMContext
):
    token_text = message.text if message.text else "-"
    token_text_clean = ToolsClass.escape_markdown_v2(token_text)
    await state.update_data(wb_token=token_text_clean)
    await message.reply(
        f"*{token_text_clean}*\n\n Это токен от вашего кабинета?",
        reply_markup=get_yes_no_keyboard("token"),
        parse_mode="MarkdownV2"
    )

       
@router.callback_query(F.data.startswith("google_sheets_url_"), StateFilter(User.waiting_for_google_sheets_url))
async def handle_google_sheets_url(
    callback: CallbackQuery,
    state: FSMContext,
    db_pool: asyncpg.pool.Pool
):
    data = await state.get_data()
    
    answer = "yes" if callback.data.endswith("yes") else "no"
    username = callback.from_user.username
    telegram_id = callback.from_user.id
    table_url = data.get("table_url")
    if answer == "yes":
        # ---- Запись ссылки на гугл-таблицу записана в БД ------
        async with db_pool.acquire() as connection:
            await connection.execute('''
                UPDATE users
                SET table_url = $1,
                    last_update = CURRENT_TIMESTAMP
                WHERE telegram_id = $2
            ''', table_url, telegram_id)
            print(f"[INFO] insert into table users table_url from {telegram_id}")
        await callback.message.edit_text("✅ Ссылка на вашу таблица записана")
        await callback.message.answer("Что дальше?")
    else:
        await state.clear()
        await callback.message.edit_text("Пришлите тогда ссылку на таблицу ещё раз.")
        await state.set_state(User.waiting_for_google_sheets_url)

@router.message(StateFilter(User.waiting_for_google_sheets_url))
async def handle_google_sheets_url(
    message: Message,
    state: FSMContext
):
    table_url = message.text
    await state.update_data(table_url=table_url)
    await message.reply(
        f"{table_url} \n\nЭто ссылка на вашу гугл-таблицу?",
        reply_markup=get_yes_no_keyboard("google_sheets_url")
    )
    