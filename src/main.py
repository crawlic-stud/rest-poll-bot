import logging
from aiogram import types, Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import CommandStart
from aiogram.filters.callback_data import CallbackData

from settings import settings
from models import LocationPolls, Poll
from database import (
    add_new_poll,
    get_poll_by_location,
    has_at_least_one_poll,
    reset_and_add_new_poll,
)

bot = Bot(settings.TG_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())


class PollCallbackData(CallbackData, prefix="poll"):
    action: str
    where: str


SPB = "spb"
MOSCOW = "moscow"
REGIONS = "regions"
DONT_ADD = "dont_add"
SHOW_ACTION = "show"
ADD_ACTION = "add"
CHOICE_ADD = "choice_add"
CHOICE_RESET = "choice_reset"
CONTINUE = "continue"

poll_where_map = {SPB: "СПБ", MOSCOW: "Москва", REGIONS: "Регионы"}
polls_ram = {}


logging.basicConfig(level=logging.INFO)


@dp.message(F.poll, F.from_user.id == settings.ADMIN_ID)
async def register_new_poll(m: types.Message):
    m.from_user.id
    await m.reply(
        "Куда добавить этот опрос?",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[SPB],
                        callback_data=PollCallbackData(
                            action=ADD_ACTION, where=SPB
                        ).pack(),
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[MOSCOW],
                        callback_data=PollCallbackData(
                            action=ADD_ACTION, where=MOSCOW
                        ).pack(),
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[REGIONS],
                        callback_data=PollCallbackData(
                            action=ADD_ACTION, where=REGIONS
                        ).pack(),
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="Не добавлять", callback_data=DONT_ADD
                    )
                ],
            ]
        ),
    )
    poll = Poll(name=m.poll.question, chat_id=m.chat.id, message_id=m.message_id)
    if polls_ram.get(m.chat.id):
        polls_ram[m.chat.id].append(poll)
    else:
        polls_ram[m.chat.id] = [poll]


@dp.callback_query(F.data == DONT_ADD)
async def delete_message(query: types.CallbackQuery):
    await query.message.delete()


@dp.callback_query(PollCallbackData.filter(F.action == CHOICE_ADD))
async def add_poll(query: types.CallbackQuery, callback_data: PollCallbackData):
    return await add_poll_to_db(query, callback_data, reset=False)


@dp.callback_query(PollCallbackData.filter(F.action == CHOICE_RESET))
async def add_poll(query: types.CallbackQuery, callback_data: PollCallbackData):
    return await add_poll_to_db(query, callback_data, reset=True)


@dp.callback_query(PollCallbackData.filter(F.action == SHOW_ACTION))
async def show_poll_handler(
    query: types.CallbackQuery, callback_data: PollCallbackData
):
    return await show_poll(query, callback_data)


@dp.callback_query(PollCallbackData.filter(F.action == ADD_ACTION))
async def ask_for_add(query: types.CallbackQuery, callback_data: PollCallbackData):
    if await has_at_least_one_poll(callback_data.where):
        await show_poll(query, callback_data)

        await query.message.answer(
            "Вы хотите добавить к существующим или создать опросы заново?",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="Добавить к существующим",
                            callback_data=PollCallbackData(
                                action=CHOICE_ADD, where=callback_data.where
                            ).pack(),
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="Создать опросы заново",
                            callback_data=PollCallbackData(
                                action=CHOICE_RESET, where=callback_data.where
                            ).pack(),
                        )
                    ],
                ]
            ),
        )
    else:
        await add_poll_to_db(query, callback_data, reset=True)


async def add_poll_to_db(
    query: types.CallbackQuery, callback_data: PollCallbackData, reset: bool
):
    data = polls_ram.get(query.message.chat.id, [None])
    poll: Poll = data.pop()
    if poll is None:
        await query.message.answer("Сначала отправьте опрос!")
        return

    if reset:
        await reset_and_add_new_poll(callback_data.where, poll)
    else:
        await add_new_poll(callback_data.where, poll)
    await query.message.edit_text(
        f"Добавлено в {poll_where_map[callback_data.where]}!", reply_markup=None
    )


@dp.message(CommandStart())
async def show_where_polls(m: types.Message):
    await m.answer(
        "Привет! Вот простые инструкции о том, как проголосовать за любимый проект:\n"
        " 1 Вы можете голосовать за несколько проектов\n"
        " 2 Если в один день вы проголосовали за один проект, а в другой день вам хочется добавить голос ещё за другой проект, то необходимо: "
        "зажать сообщение с опросом ➡️ выбрать в выпадающем списке «отменить голос». После этого выбрать заново все заведения за которые хочется проголосовать.\n"
        "Enjoy!",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Продолжить", callback_data=CONTINUE)]
            ]
        ),
    )


@dp.callback_query(F.data == CONTINUE)
async def show_where_polls(query: types.CallbackQuery):
    await query.message.answer(
        "Где голосуете?",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[REGIONS],
                        callback_data=PollCallbackData(
                            action=SHOW_ACTION, where=REGIONS
                        ).pack(),
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[SPB],
                        callback_data=PollCallbackData(
                            action=SHOW_ACTION, where=SPB
                        ).pack(),
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=poll_where_map[MOSCOW],
                        callback_data=PollCallbackData(
                            action=SHOW_ACTION, where=MOSCOW
                        ).pack(),
                    )
                ],
            ]
        ),
    )


async def show_poll(query: types.CallbackQuery, callback_data: PollCallbackData):
    poll = await get_poll_by_location(callback_data.where)
    if poll is None:
        await query.message.answer("Опрос не найден :(")
        return

    await query.answer(f"Открываю {poll_where_map[callback_data.where]}...")
    polls: LocationPolls = LocationPolls(**poll)
    sent_messages = []
    for poll in polls.polls:
        poll_message = await bot.forward_message(
            query.message.chat.id, poll.chat_id, poll.message_id, protect_content=True
        )
        sent_messages.append(poll_message)
    return sent_messages


@dp.poll_answer()
async def succesfully_answered_to_poll(answer: types.PollAnswer):
    await bot.send_message(answer.voter_chat.id, "Спасибо, ваш ответ записан!")


if __name__ == "__main__":
    dp.run_polling(bot)
