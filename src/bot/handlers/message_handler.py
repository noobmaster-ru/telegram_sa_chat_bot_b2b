from aiogram import Router,  F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message,   CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import insert, select

from src.bot.states.user import UserState
from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.services.string_converter import StringConverterClass
from src.db.models import WBTokenORM, TableORM, UserORM


router = Router()

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    db_session_factory: async_sessionmaker
):
    telegram_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "no username"
    first_name = message.from_user.first_name if message.from_user.first_name else "no first_name"
    
    async with db_session_factory() as session:
        # Проверяем, есть ли пользователь
        result = await session.execute(
            select(UserORM).where(UserORM.telegram_id == telegram_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"user {telegram_id} already in 'users'")
        else:
            # Создаём нового пользователя
            new_user = UserORM(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
            )
            session.add(new_user)
            await session.commit()
            print(f"added {telegram_id} into 'users'")

    await message.answer("Здравствуйте! Пришлите,пожалуйста, свой токен от личного кабинета 😊")
    await state.set_state(UserState.waiting_for_token)

@router.callback_query(F.data.startswith("token_"), StateFilter(UserState.waiting_for_token))
async def callback_token(
    callback: CallbackQuery,
    state: FSMContext,
    google_sheet_template_url: str,
    db_session_factory: async_sessionmaker
):
    data = await state.get_data()
    
    answer = "yes" if callback.data.endswith("yes") else "no"
    username = callback.from_user.username
    telegram_id = callback.from_user.id
    wb_token = data.get("wb_token")
    
    if answer == "yes":
        # ---- insert wb_token to database ------
        async with db_session_factory() as session:
            stmt = insert(WBTokenORM).values(
                token=wb_token,
                scopes=["read", "write"]
            )
            await session.execute(stmt)
            await session.commit()

        await callback.message.edit_text("✅ Ваш токен записан!")
        await callback.message.answer(
            f"Сделайте, пожалуйста, этой таблицы:\n\n{google_sheet_template_url}\n\nи пришлите ссылку на неё мне."
        )
        await state.set_state(UserState.waiting_for_google_sheets_url)
    else:
        # delete wb_token from state 
        await state.clear()
        await callback.message.edit_text("Пришлите тогда токен ещё раз.")
        await state.set_state(UserState.waiting_for_token)

@router.message(StateFilter(UserState.waiting_for_token))
async def handle_token(
    message: Message,
    state: FSMContext
):
    token_text = message.text if message.text else "-"
    token_text_clean = StringConverterClass.escape_markdown_v2(token_text)
    await state.update_data(wb_token=token_text_clean)
    await message.reply(
        f"*{token_text_clean}*\n\n Это токен от вашего кабинета?",
        reply_markup=get_yes_no_keyboard("token"),
        parse_mode="MarkdownV2"
    )

       
@router.callback_query(F.data.startswith("google_sheets_url_"), StateFilter(UserState.waiting_for_google_sheets_url))
async def handle_google_sheets_url(
    callback: CallbackQuery,
    state: FSMContext,
    google_sheet_template_url: str,
    db_session_factory: async_sessionmaker
):
    data = await state.get_data()
    
    answer = "yes" if callback.data.endswith("yes") else "no"
    username = callback.from_user.username
    telegram_id = callback.from_user.id
    table_url = data.get("table_url")
    if answer == "yes":
        # ---- insert table_id to ------
        try:
            table_id = StringConverterClass.extract_table_id(table_url)
            async with db_session_factory() as session:
                stmt = insert(TableORM).values(
                    table_id=table_id,
                    supplier_id=None  
                )
                await session.execute(stmt)
                await session.commit()
                
            await callback.message.edit_text("✅ Ссылка на вашу таблица записана")
            await callback.message.answer("Что дальше?")
        except:
            await callback.message.edit_text("Пришлите вашу ссылку корректно, пожалуйста.")
            await state.set_state(UserState.waiting_for_google_sheets_url)
    else:
        await state.clear()
        await callback.message.edit_text("Пришлите тогда ссылку на таблицу ещё раз.")
        await state.set_state(UserState.waiting_for_google_sheets_url)

@router.message(StateFilter(UserState.waiting_for_google_sheets_url))
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
    