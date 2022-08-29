import json
from datetime import datetime
from cities import cities_dict
import asyncio
import aiohttp


class DataGetter:
    def __init__(self, city, event_type):
        self.PERIOD = 30
        self.DATE = datetime.now().date()
        self.CITY = cities_dict[city.replace(' ', '').lower()]
        self.SITE_PATH = self.get_site_path(event_type)
        self.JSON_FILE_PATH = "result.json"
        self.pushkin_card_list = []

    @staticmethod
    def get_site_path(string):
        string = string.strip().lower()
        if string == "кино":
            return "rubric/cinema"
        elif string == "спектакли":
            return "selections/pushkin-card-theatre"

    @staticmethod
    def is_pushkin_card_allowed(movie):
        return movie["scheduleInfo"]["pushkinCardAllowed"]

    async def get_page_data(self, session, offset, max_limit):
        url = f"https://afisha.yandex.ru/api/events/{self.SITE_PATH}?limit={max_limit}&offset={offset}&hasMixed=0&" \
              f"date={self.DATE}&period={self.PERIOD}&city={self.CITY}&_=1660756014055"
        async with session.get(url) as response:
            data = await response.json()

        if self.SITE_PATH == "rubric/cinema":
            self.pushkin_card_list.extend(list(filter(self.is_pushkin_card_allowed, data['data'])))
        else:
            self.pushkin_card_list.extend(list(data['data']))

    async def gather_data(self):
        async with aiohttp.ClientSession() as session:
            url = f"https://afisha.yandex.ru/api/events/{self.SITE_PATH}?limit=1&offset=0&hasMixed=0&" \
                  f"date={self.DATE}&period={self.PERIOD}&city={self.CITY}&_=1660756014055"
            response = await session.get(url)
            data = await response.json()
            total, max_limit = data["paging"]["total"], 20

            tasks = []

            for offset in range(0, total, max_limit):
                task = asyncio.create_task(self.get_page_data(session, offset, max_limit))
                tasks.append(task)

            await asyncio.gather(*tasks)

    async def get_yandex_afisha_info(self):
        domain = "https://afisha.yandex.ru"
        await self.gather_data()
        pushkin_card_list = self.pushkin_card_list

        movies_info_list = []
        for card in pushkin_card_list:
            movie_info_dict = {
                'title': card['event']['title'],
                'description': card['event']['argument'],
                'link': domain + card['event']['url']}

            movie_released_year_str = card['event']['dateReleased']
            if movie_released_year_str:
                movie_info_dict['released_year'] = movie_released_year_str[:4]

            movie_info_dict['rating'] = 0
            if self.SITE_PATH == "rubric/cinema":
                rating_dict = card['event']['kinopoisk']
            else:
                rating_dict = card['event']['userRating']['overall']
            if rating_dict:
                movie_info_dict['rating'] = rating_dict['value']

            movie_info_dict['content_rating'] = card['event']['contentRating']

            movie_info_dict['dates'] = datetime.strptime(card['scheduleInfo']['dates'][0],
                                                         '%Y-%m-%d').strftime('%d.%m.%Y')
            if len(card['scheduleInfo']['dates']) > 1:
                movie_info_dict['dates'] = ' - '.join(
                    (movie_info_dict['dates'],
                     datetime.strptime(card['scheduleInfo']['dates'][-1], '%Y-%m-%d').strftime('%d.%m.%Y')))

            movie_info_dict['min_price'] = None
            if card['scheduleInfo']['prices']:
                movie_prices = list(map(lambda x: x['value'] // 100, card['scheduleInfo']['prices']))
                movie_info_dict['min_price'] = min(movie_prices)

            movies_info_list.append(movie_info_dict)

        self.write_data_to_json(movies_info_list, self.JSON_FILE_PATH)

    @staticmethod
    def write_data_to_json(list_of_dict, json_file_path):
        with open(json_file_path, "w", encoding='utf-8-sig') as file:
            json.dump(list_of_dict, file, ensure_ascii=False)
