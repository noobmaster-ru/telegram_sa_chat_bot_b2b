from pathlib import Path
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile, InputMediaPhoto, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import insert

from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.bot.states.user import UserState
from src.services.string_converter import StringConverterClass
from src.db.models import TableORM

router = Router()

@router.message(StateFilter(UserState.google_sheet_handler))
async def handle_google_sheets_url(message: Message, state: FSMContext):
    table_url = message.text
    await state.update_data(table_url=table_url)
    await message.reply(
        f"{table_url}\n\nЭто ссылка на вашу гугл-таблицу?",
        reply_markup=get_yes_no_keyboard("google_sheets_url")
    )

@router.callback_query(F.data.startswith("google_sheets_url_"), StateFilter(UserState.google_sheet_handler))
async def callback_google_sheets_url(
    callback: CallbackQuery,
    state: FSMContext,
    db_session_factory: async_sessionmaker,
    service_account: str
):
    data = await state.get_data()
    answer = "yes" if callback.data.endswith("yes") else "no"
    table_url = data.get("table_url")

    if answer == "yes":
        try:
            table_id = StringConverterClass.extract_table_id(table_url)
            if not table_url.startswith("https://"):
                await callback.message.edit_text("Пришлите ссылку корректно, пожалуйста.")
                await state.set_state(UserState.google_sheet_handler)
                return
            
            async with db_session_factory() as session:
                stmt = insert(TableORM).values(
                    table_id=table_id,
                    supplier_id=None
                )
                await session.execute(stmt)
                await session.commit()
            await callback.message.edit_text("✅ Ссылка на таблицу записана!")
            await callback.message.answer("Отлично!")
            INSTRUCTION_PHOTOS_DIR = Path(__file__).resolve().parent.parent.parent / "resources"
            photo_path1 = INSTRUCTION_PHOTOS_DIR / "1_access_settings.png"
            photo_path2 = INSTRUCTION_PHOTOS_DIR / "2_search_bar.png"
            photo_path3 = INSTRUCTION_PHOTOS_DIR / "3_access_placa_tables_editor.png"
            photo_path4 = INSTRUCTION_PHOTOS_DIR / "4_placa_tables_service_account.png"

            caption_text = (
                f"Теперь *внимательно!*:\n\n"
                f"1. Откройте свою таблицу\n"
                f"2. В правом верхнем углу откройте настройки доступа *(фото1)*\n"
                f"3. В поисковой строке вбейте вот этот email *(фото2)*:\n\n*{service_account}*\n\n"
                f"4. Дайте доступ *Редактор* этому сервисному аккаунту Google *(фото3)*\n\n"
                f"Как сделаете, у вас должно получиться вот так, как на *(фото4)*"
            )
            safe_caption = StringConverterClass.escape_markdown_v2(caption_text) 
            media_group = [
                InputMediaPhoto(
                    media=FSInputFile(photo_path1), 
                    caption=safe_caption, 
                    parse_mode="MarkdownV2"
                ),
                InputMediaPhoto(media=FSInputFile(photo_path2)), 
                InputMediaPhoto(media=FSInputFile(photo_path3)),
                InputMediaPhoto(media=FSInputFile(photo_path4)),
            ]
            # Отправляем медиагруппу
            await callback.bot.send_media_group(
                chat_id=callback.message.chat.id,
                media=media_group
            )
            await callback.message.answer(
                f"Дали доступ *Редактор* нашему cервисному аккаунту Google?",
                reply_markup=get_yes_no_keyboard("service_account"),
                parse_mode="MarkdownV2"
            )
            await state.set_state(UserState.service_account_handler)
        except Exception:
            await callback.message.edit_text("Пришлите ссылку корректно, пожалуйста.")
            await state.set_state(UserState.google_sheet_handler)
    else:
        await state.clear()
        await callback.message.edit_text("Пришлите тогда ссылку на таблицу ещё раз.")
        await state.set_state(UserState.google_sheet_handler)