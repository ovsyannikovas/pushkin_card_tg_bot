from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import hbold, hlink, hide_link
from main import DataGetter
import json
import os

bot = Bot(token=os.getenv("TOKEN"), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    start_buttons = ["Кино", "Спектакли"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer("Выберите категорию", reply_markup=keyboard)


@dp.message_handler(Text(equals=["Кино", "Спектакли"]))
async def get_info(message: types.Message):
    await message.answer("Сбор информации...")

    if message.text == "Кино":
        path = "rubric/cinema"
    else:
        path = "selections/pushkin-card-theatre"

    period = 30
    data_getter = DataGetter(period)
    data_getter.get_yandex_afisha_info(path)
    rating_border = 7

    with open(data_getter.JSON_FILE_PATH, encoding='utf-8-sig') as file:
        data = json.load(file)

    for item in data:
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

        await message.answer(card)


def main():
    executor.start_polling(dp)


if __name__ == "__main__":
    main()
