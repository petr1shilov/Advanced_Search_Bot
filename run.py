import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    FSInputFile,
)
from aiogram.utils.deep_linking import create_start_link

import config

# from bot.keyboards import kb, model_kb
from bot.states import UserStates
from bot.texts import *
from api import AnswerApi

TOKEN = config.bot_token

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(TOKEN)

api = AnswerApi()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        message_id = data["delete_messege"]
        await bot.delete_messages(chat_id=message.chat.id, message_ids=message_id)
    except KeyError:
        await message.answer(hello_message_text)
    await message.answer(start_message_text)
    messege_id = message.message_id
    message_excel = await message.answer(excel_message_text)
    user_id = message.from_user.id
    await state.update_data(delete_messege=[message_excel.message_id], user_id=user_id)
    await state.set_state(UserStates.get_excel)


@dp.message(UserStates.get_excel, F.content_type == "document")
async def get_excel_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    message_id = user_data["delete_messege"]
    user_id = user_data["user_id"]
    await bot.delete_messages(chat_id=message.chat.id, message_ids=message_id)

    file_id = message.document.file_id
    file_name = f"{str(user_id)}_{message.document.file_name}"
    await state.update_data(file_name=file_name)

    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, f"files/{file_name}")
    await message.answer(theme_message_text)
    messege_id = message.message_id
    await state.update_data(delete_messege=[messege_id + 1])
    await state.set_state(UserStates.get_theme)


@dp.message(StateFilter(UserStates.get_excel), F.content_type != "document")
async def warning_not_excel(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data["delete_messege"]
    message_id.append(message.message_id - 1)

    await bot.delete_messages(chat_id=message.chat.id, message_ids=message_id)
    answer_text = f"{warning_excel_message}\n\n{excel_message_text}"
    await message.answer(text=answer_text)
    messege_id = message.message_id
    await state.update_data(delete_messege=[messege_id, messege_id + 1])
    data = await state.get_data()
    message_id = data["delete_messege"]


@dp.message(UserStates.get_theme, F.content_type == "text")
async def get_theme_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    message_id = data["delete_messege"]
    await bot.delete_messages(chat_id=message.chat.id, message_ids=message_id)
    request = message.text.strip()
    await state.update_data(request=request)
    await send_file(message, state)


@dp.message(UserStates.get_theme, F.content_type != "text")
async def warning_not_theme(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    message_id = data["delete_messege"]
    message_id.append(message.message_id - 1)

    await bot.delete_messages(chat_id=message.chat.id, message_ids=message_id)
    answer_text = f"{warning_theme_message}\n\n{theme_message_text}"
    await message.answer(text=answer_text)
    messege_id = message.message_id
    await state.update_data(delete_messege=[messege_id, messege_id + 1])
    data = await state.get_data()
    message_id = data["delete_messege"]


async def send_file(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    file_name = user_data["file_name"]
    request = user_data["request"]
    path = f"files/{file_name[:-5]}_response.xlsx"

    msg = await message.answer(waiting_message)

    answer_test = api.api_answer(str(file_name), request)

    if not answer_test:
        message_id = msg.message_id
        await bot.delete_messages(chat_id=message.chat.id, message_ids=[message_id])
        text_error = await message.answer("error_text")
        await state.update_data(delete_messege=[text_error.message_id])
    else:
        message_id = msg.message_id
        await bot.delete_messages(chat_id=message.chat.id, message_ids=[message_id])
        await message.answer_document(FSInputFile(path))
        message_after = await message.answer(
            "Что бы запусть бота заново напишите /start"
        )
        await state.update_data(delete_messege=[message_after.message_id])
        await state.clear()


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
