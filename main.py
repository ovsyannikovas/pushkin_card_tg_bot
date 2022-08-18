import json
import time
from random import random

from datetime import datetime

from selenium import webdriver
import requests


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

        card_list_pushkin = []
        for offset in range(0, total + 1, limit_max):
            url = f"https://afisha.yandex.ru/api/events/rubric/cinema?limit={limit_max}&offset={offset}&hasMixed=0&" \
                  f"date={self.DATE}&period={self.PERIOD}&city=saint-petersburg&_=1660756014055"
            response = requests.get(url)
            data = response.json()

            card_list_pushkin.extend(list(filter(self.is_pushkin_card_allowed, data['data'])))

            time.sleep(random())

        return card_list_pushkin

    def get_yandex_afisha_info(self):
        domain = "https://afisha.yandex.ru"
        card_list_pushkin = self.get_data_dict()

        movies_info_list = []
        for card in card_list_pushkin:
            movie_image = card['event']['image']['sizes']['microdata']['url']
            movie_title = card['event']['title']
            movie_description = card['event']['argument']
            movie_link = domain + card['event']['url']
            movie_released_year = None
            movie_released_year_str = card['event']['dateReleased']
            if movie_released_year_str:
                movie_released_year = movie_released_year_str[:4]
            movie_rating = 0
            rating_dict = card['event']['kinopoisk']
            if rating_dict:
                movie_rating = rating_dict['value']
            movie_content_rating = card['event']['contentRating']

            movies_info_list.append({
                "image": movie_image,
                "title": movie_title,
                "rating": movie_rating,
                "description": movie_description,
                "content_rating": movie_content_rating,
                "released_year": movie_released_year,
                "link": movie_link
            })

        movies_info_list.sort(key=lambda movie: movie["rating"], reverse=True)

        self.write_data_to_json(movies_info_list, self.JSON_FILE_PATH)

    @staticmethod
    def write_data_to_json(list_of_dict, json_file_path):
        with open(json_file_path, "w", encoding='utf-8-sig') as file:
            json.dump(list_of_dict, file, ensure_ascii=False)


def main():
    PERIOD = 14
    data_getter = DataGetter(PERIOD)
    data_getter.get_yandex_afisha_info()


if __name__ == "__main__":
    main()
