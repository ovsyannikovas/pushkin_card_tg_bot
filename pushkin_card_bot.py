from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold, hlink
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from main import DataGetter
from cities import cities_dict
from asyncio import sleep
import json
import os

bot = Bot(token=os.getenv("TOKEN"), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


class UserInfoStatesGroup(StatesGroup):
    city = State()
    event_type = State()
    # filter_events = State()


@dp.message_handler(commands="start", state="*")
async def start(message: types.Message):
    await message.answer("Введите Ваш город.", reply_markup=types.ReplyKeyboardRemove())
    await UserInfoStatesGroup.city.set()


@dp.message_handler(lambda x: x.text.lower().replace(" ", "") == "поменятьгород", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start(message)


def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Кино", "Спектакли").add("Поменять город")
    return keyboard


@dp.message_handler(lambda x: x.text.lower().replace(' ', '') in cities_dict, state=UserInfoStatesGroup.city)
async def choose_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text

    await UserInfoStatesGroup.next()

    await message.answer("Выберите категорию мероприятия:", reply_markup=get_keyboard())


@dp.message_handler(state=UserInfoStatesGroup.city)
async def choose_city_fail(message: types.Message):
    await message.answer("Такого города нет в базе Яндекс Афиши. 😕 Проверьте на опечатки и попробуйте ввести еще раз.",
                         reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=UserInfoStatesGroup.event_type)
async def choose_event_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        city = data['city']
    event_type = message.text

    if not validate_message(message):
        await message.answer("Неверная команда.")
        await message.answer("Выберите категорию мероприятия:", reply_markup=get_keyboard())
    else:
        await receive_info(message, city, event_type)


# async def choose_filters():
#     ...


async def receive_info(message: types.Message, city, event_type):
    await message.answer("Сбор информации...", reply_markup=types.ReplyKeyboardRemove())
    data_getter = DataGetter(city, event_type)
    await data_getter.get_yandex_afisha_info()

    with open(data_getter.JSON_FILE_PATH, encoding='utf-8-sig') as file:
        data = json.load(file)

    data.sort(key=lambda movie: movie["rating"], reverse=True)
    rating_border = 7

    if len(data) == 0:
        await message.answer(
            f"В городе {hbold(city.capitalize())} нет мероприятий выбранного типа на ближайшее время. 😕",
            reply_markup=None)
        return

    for index, item in enumerate(data):
        if rating_border and item.get('rating') < rating_border:
            break

        arg_dict = {
            'Цена:': item.get('min_price'),
            'Рейтинг:': item.get('rating'),
            'Даты показа:': item.get('dates'),
            'Год выпуска:': item.get('released_year'),
            'Описание:': item.get('description'),
        }

        card = f"{hlink(item['title'], item['link'])}\n\n"

        for arg in arg_dict:
            if arg_dict[arg]:
                if arg == 'Цена:':
                    string = f"{hbold(arg)}  от {arg_dict[arg]} ₽\n"
                elif arg == 'Рейтинг:':
                    string = f"{hbold(arg)}  {arg_dict[arg]}★\n"
                elif arg == 'Описание:':
                    string = f"\n{hbold(arg)}  {arg_dict[arg]}.\n"
                else:
                    string = f"{hbold(arg)}  {arg_dict[arg]}\n"
                card = "".join((card, string))

        if index % 20 == 0:
            await sleep(1)

        await message.answer(card, reply_markup=None)
    await message.answer("Можете выбрать другой тип мероприятия или поменять город.", reply_markup=get_keyboard())


def validate_message(message: types.Message):
    return message.text.lower().replace(" ", "") in ("кино", "спектакли", "поменятьгород")


def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
