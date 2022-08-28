from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold, hlink
from aiogram.dispatcher.filters.state import State, StatesGroup
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


@dp.message_handler(commands="start", state=None)
async def start(message: types.Message):
    await UserInfoStatesGroup.city.set()
    await message.answer("Введите Ваш город.")


@dp.message_handler(commands=["Поменять_город"], state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await UserInfoStatesGroup.city.set()
    await message.answer("Введите Ваш город.")


@dp.message_handler(lambda x: x.text.lower().replace(' ', '') in cities_dict, state=UserInfoStatesGroup.city)
async def choose_city(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text

    await UserInfoStatesGroup.next()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Кино", "Спектакли").add("/Поменять_город")
    await message.answer("Выберите категорию:", reply_markup=keyboard)


@dp.message_handler(commands=["города"], state="*")  # not working
async def show_cities_list(message: types.Message):
    n = len(cities_dict)
    for i in range(n, 15):
        await message.answer(cities_dict.keys()[i:i + 15])


@dp.message_handler(state=UserInfoStatesGroup.city)
async def choose_city_fail(message: types.Message):
    await message.answer("Такого города нет в базе :( Проверьте на опечатки и попробуйте ввести еще раз "
                         f"или посмотрите в базе, набрав команду  {hbold('/города')} .")


@dp.message_handler(state=UserInfoStatesGroup.event_type)
async def choose_event_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        city = data['city']
    event_type = message.text

    # await state.finish()

    await receive_info(message, city, event_type)


# async def choose_filters():
#     ...


async def receive_info(message: types.Message, city, event_type):
    await message.answer("Сбор информации...")
    data_getter = DataGetter(city, event_type)
    await data_getter.get_yandex_afisha_info()
    rating_border = 7

    with open(data_getter.JSON_FILE_PATH, encoding='utf-8-sig') as file:
        data = json.load(file)

    if len(data) == 0:
        await message.answer(
            f"В городе {hbold(city.capitalize())} нет мероприятий выбранного типа на ближайшее время :(",
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
            await sleep(2)

        await message.answer(card, reply_markup=None)


def main():
    executor.start_polling(dp, skip_updates=True)

    # # information check
    # import asyncio
    # loop = asyncio.run()
    # data_getter = DataGetter("санкт-петербург", "кино")
    # loop.run_until_complete(data_getter.get_yandex_afisha_info())


if __name__ == "__main__":
    main()
