import json
import requests
from datetime import datetime
from cities import cities_dict


class DataGetter:
    def __init__(self, city, mode):
        self.PERIOD = 30
        self.DATE = datetime.now().date()
        self.CITY = cities_dict[city.strip().lower()]
        self.SITE_PATH = self.get_site_path(mode)
        self.JSON_FILE_PATH = "result.json"

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

    def get_data_list(self):
        url = f"https://afisha.yandex.ru/api/events/{self.SITE_PATH}?limit=1&offset=0&hasMixed=0&" \
              f"date={self.DATE}&period={self.PERIOD}&city={self.CITY}&_=1660756014055"

        response = requests.get(url)
        data = response.json()

        total = data["paging"]["total"]
        limit_max = 20

        pushkin_card_list = []
        for offset in range(0, total, limit_max):
            url = f"https://afisha.yandex.ru/api/events/{self.SITE_PATH}?limit={limit_max}&offset={offset}&hasMixed=0&" \
                  f"date={self.DATE}&period={self.PERIOD}&city={self.CITY}&_=1660756014055"
            response = requests.get(url)
            data = response.json()

            if self.SITE_PATH == "rubric/cinema":
                pushkin_card_list.extend(list(filter(self.is_pushkin_card_allowed, data['data'])))
            else:
                pushkin_card_list.extend(list(data['data']))

        return pushkin_card_list

    def get_yandex_afisha_info(self):
        domain = "https://afisha.yandex.ru"
        pushkin_card_list = self.get_data_list()

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
    data_getter = DataGetter("Москва", "спектакли")
    data_getter.get_yandex_afisha_info()


if __name__ == "__main__":
    main()
