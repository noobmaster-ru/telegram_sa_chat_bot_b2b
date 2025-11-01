from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import insert
from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.bot.states.user import UserState
from src.db.models import WBTokenORM
from src.services.string_converter import StringConverterClass

router = Router()

@router.message(StateFilter(UserState.token_handler))
async def handle_token(message: Message, state: FSMContext):
    token_text = message.text or "-"
    token_text_clean = StringConverterClass.escape_markdown_v2(token_text)
    await state.update_data(wb_token=token_text_clean)
    await message.reply(
        f"*{token_text_clean}*\n\nЭто токен от вашего кабинета?",
        reply_markup=get_yes_no_keyboard("token"),
        parse_mode="MarkdownV2"
    )

@router.callback_query(F.data.startswith("token_"), StateFilter(UserState.token_handler))
async def callback_token(
    callback: CallbackQuery,
    state: FSMContext,
    google_sheet_template_url: str,
    db_session_factory: async_sessionmaker
):
    data = await state.get_data()
    answer = "yes" if callback.data.endswith("yes") else "no"
    wb_token = data.get("wb_token")

    if answer == "yes":
        async with db_session_factory() as session:
            stmt = insert(WBTokenORM).values(
                token=wb_token,
                scopes=["read", "write"]
            )
            await session.execute(stmt)
            await session.commit()

        await callback.message.edit_text("✅ Ваш токен записан!")
        await callback.message.answer(
            f"Сделайте, пожалуйста, копию этой таблицы:\n\n{google_sheet_template_url}\n\nи пришлите мне ссылку."
        )
        await state.set_state(UserState.google_sheet_handler)
    else:
        await state.clear()
        await callback.message.edit_text("Пришлите тогда токен ещё раз.")
        await state.set_state(UserState.token_handler)