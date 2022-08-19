from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import hbold, hlink, hide_link
from main import DataGetter
import json
import os

# print(os.getenv("TOKEN"))
bot = Bot(token=os.getenv("TOKEN"), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    start_buttons = ["Кино", "Спектакли"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer("Выберите категорию", reply_markup=keyboard)


@dp.message_handler(Text(equals="Кино"))
async def get_discount_sneakers(message: types.Message):
    await message.answer("Сбор информации...")

    period = 30
    data_getter = DataGetter(period)
    # data_getter.get_yandex_afisha_info()

    with open(f"movies-{data_getter.DATE}.json", encoding='utf-8-sig') as file:
        data = json.load(file)

    for item in data:
        card = f"{hlink(item['title'], item['link'])}\n\n" \
               f"{hbold('Цена: ')} от {item['min_price']} ₽\n\n" \
               f"{hbold('Год выпуска: ')} {item['released_year']}\n\n" \
               f"{hbold('Рейтинг: ')} {item['rating']}\n\n" \
               f"{hbold('Даты показа: ')} {item['dates']}\n\n" \
               f"{hbold('Описание: ')} {item['description']}"

        await message.answer(card)


def main():
    executor.start_polling(dp)


if __name__ == "__main__":
    main()
