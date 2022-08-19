import json
import requests
from datetime import datetime


class DataGetter:
    def __init__(self, period):
        self.PERIOD = period
        self.DATE = datetime.now().date()
        self.JSON_FILE_PATH = f"movies-{self.DATE}.json"

    @staticmethod
    def is_pushkin_card_allowed(movie):
        return movie["scheduleInfo"]["pushkinCardAllowed"]

    def get_data_dict(self):
        url = f"https://afisha.yandex.ru/api/events/rubric/cinema?limit=1&offset=0&hasMixed=0&" \
              f"date={self.DATE}&period={self.PERIOD}&city=saint-petersburg&_=1660756014055"

        response = requests.get(url)
        data = response.json()

        total = data["paging"]["total"]
        limit_max = 20

        pushkin_card_list = []
        for offset in range(0, total + 1, limit_max):
            url = f"https://afisha.yandex.ru/api/events/rubric/cinema?limit={limit_max}&offset={offset}&hasMixed=0&" \
                  f"date={self.DATE}&period={self.PERIOD}&city=saint-petersburg&_=1660756014055"
            response = requests.get(url)
            data = response.json()

            pushkin_card_list.extend(list(filter(self.is_pushkin_card_allowed, data['data'])))

        return pushkin_card_list

    def get_yandex_afisha_info(self):
        domain = "https://afisha.yandex.ru"
        pushkin_card_list = self.get_data_dict()

        movies_info_list = []
        for card in pushkin_card_list:
            movie_info_dict = {}

            movie_info_dict['image'] = card['event']['image']['sizes']['microdata']['url']
            movie_info_dict['title'] = card['event']['title']
            movie_info_dict['description'] = card['event']['argument']
            movie_info_dict['link'] = domain + card['event']['url']

            movie_released_year_str = card['event']['dateReleased']
            if movie_released_year_str:
                movie_info_dict['released_year'] = movie_released_year_str[:4]

            movie_info_dict['rating'] = 0
            rating_dict = card['event']['kinopoisk']
            if rating_dict:
                movie_info_dict['rating'] = rating_dict['value']

            movie_info_dict['content_rating'] = card['event']['contentRating']

            movie_info_dict['dates'] = card['scheduleInfo']['dates'][0].replace("-", ".")
            if len(card['scheduleInfo']['dates']) > 1:
                movie_info_dict['dates'] = ' - '.join(
                    (movie_info_dict['dates'], card['scheduleInfo']['dates'][-1].replace("-", ".")))

            movie_info_dict['min_price'] = None
            if card['scheduleInfo']['prices']:
                movie_prices = list(map(lambda x: x['value'] // 100, card['scheduleInfo']['prices']))
                movie_info_dict['min_price'] = min(movie_prices)

            movies_info_list.append(movie_info_dict)

        movies_info_list.sort(key=lambda movie: movie["rating"], reverse=True)

        self.write_data_to_json(movies_info_list, self.JSON_FILE_PATH)

    @staticmethod
    def write_data_to_json(list_of_dict, json_file_path):
        with open(json_file_path, "w", encoding='utf-8-sig') as file:
            json.dump(list_of_dict, file, ensure_ascii=False)


def main():
    PERIOD = 30
    data_getter = DataGetter(PERIOD)
    data_getter.get_yandex_afisha_info()


if __name__ == "__main__":
    main()
