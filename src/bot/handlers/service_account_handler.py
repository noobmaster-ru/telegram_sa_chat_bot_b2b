from pathlib import Path
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile, InputMediaPhoto,  Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.keyboards.yes_no_keyboard import get_yes_no_keyboard
from src.bot.states.user import UserState
from src.services.string_converter import StringConverterClass

router = Router()

@router.message(StateFilter(UserState.service_account_handler))
async def handle_google_sheets_url(message: Message):
    await message.reply(
        f"Дали доступ *Редактор* нашему cервисному аккаунту Google?",
        reply_markup=get_yes_no_keyboard("service_account"),
        parse_mode="Markdownv2"
    )

@router.callback_query(F.data.startswith("service_account_"), StateFilter(UserState.service_account_handler))
async def callback_google_sheets_url(
    callback: CallbackQuery,
    state: FSMContext,
    db_session_factory: async_sessionmaker,
    service_account: str
):
    answer = "yes" if callback.data.endswith("yes") else "no"

    if answer == "yes":
        # тут можно добавить запись в бд
        await callback.message.edit_text("Отлично!")
        await callback.message.answer("Теперь пришлите файл со всеми вашими переписками с покупателями.")
        caption_text = f"Для этого необходимо:\n1. Cкачать Desktop версию Telegram\n\nhttps://desktop.telegram.org/\n\n2. Зайти в настройки *(settings)* ,затем расширенные настройки *(advanced)*, промотать в самый низ и зайти в раздел *Export Telegram Data*.\n3. Далее нажать галочки на *Personal chats* , *Machine-readable JSON*.\n4. Скачать себе на компьютер в удобную директорию\n5. Прислать мне сюда файл *result.json*\n\n\n(Следуйте указателям на фотографиях)"
        safe_caption = StringConverterClass.escape_markdown_v2(caption_text) 
        
        INSTRUCTION_PHOTOS_DIR = Path(__file__).resolve().parent.parent.parent / "resources"
        photo_path1 = INSTRUCTION_PHOTOS_DIR / "5_settings_tg.png"
        photo_path2 = INSTRUCTION_PHOTOS_DIR / "6_advanced.png"
        photo_path3 = INSTRUCTION_PHOTOS_DIR / "7_export_telegram_data.png"
        photo_path4 = INSTRUCTION_PHOTOS_DIR / "8_settings.png"
        photo_path5 = INSTRUCTION_PHOTOS_DIR / "9_personal_chats.png"
        photo_path6 = INSTRUCTION_PHOTOS_DIR / "10_media_export_settings.png"
        photo_path7 = INSTRUCTION_PHOTOS_DIR / "11_other.png"
        photo_path8 = INSTRUCTION_PHOTOS_DIR / "12_location_and_format.png"
        photo_path9 = INSTRUCTION_PHOTOS_DIR / "13_result_json.png"

        media_group = [
            InputMediaPhoto(
                media=FSInputFile(photo_path1), 
                caption=safe_caption, 
                parse_mode="MarkdownV2"
            ),
            InputMediaPhoto(media=FSInputFile(photo_path2)), 
            InputMediaPhoto(media=FSInputFile(photo_path3)),
            InputMediaPhoto(media=FSInputFile(photo_path4)),
            InputMediaPhoto(media=FSInputFile(photo_path5)),
            InputMediaPhoto(media=FSInputFile(photo_path6)),
            InputMediaPhoto(media=FSInputFile(photo_path7)),
            InputMediaPhoto(media=FSInputFile(photo_path8)),
            InputMediaPhoto(media=FSInputFile(photo_path9)),
        ]
        # Отправляем медиагруппу
        await callback.bot.send_media_group(
            chat_id=callback.message.chat.id,
            media=media_group
        )
        safe_question = StringConverterClass.escape_markdown_v2(f"Теперь пришлите файл *result.json*")
        await callback.message.answer(
            text=safe_question,
            parse_mode="MarkdownV2"
        )
        await state.set_state(UserState.data_export_telegram)
    else:
        await state.clear()
        try:
            await callback.message.edit_text(
                f"Дали доступ *Редактор* нашему cервисному аккаунту Google?",
                reply_markup=get_yes_no_keyboard("service_account"),
                parse_mode="MarkdownV2"
            )
        except:
            await callback.message.edit_text(
                f"Без доступа *Редактор* мы не сможем записывать данные в вашу гугл таблицу",
                reply_markup=get_yes_no_keyboard("service_account"),
                parse_mode="MarkdownV2"
            )
        await state.set_state(UserState.service_account_handler)