import json
import os
import time
from random import uniform

from bs4 import BeautifulSoup
from datetime import datetime

from selenium import webdriver
import requests

# def get_html_cards(movies, date):
#     with WebDriver() as driver:
#         if not os.path.exists(f"src/{date}"):
#             os.makedirs(f"src/{date}/pages")
#             os.makedirs(f"src/{date}/cards")
#
#         for index, movie in enumerate(movies):
#             driver.get(movie["link"])
#             html = driver.page_source
#
#             with open(f"src/{date}/cards/card_{index + 1}.html", "w", encoding='utf-8-sig') as file:
#                 file.write(html)
#
#             print(f"[INFO] Обработано {index + 1}/29")
#             time.sleep(uniform(2, 4))
#
#
# def add_card_details(movies_num, date):
#     for index, movie in enumerate(movies_num):
#         with open(f"src/{date}/cards/card_{index + 1}.html", encoding='utf-8-sig') as file:
#             html = file.read()
#             soup = BeautifulSoup(html, "lxml")
#             rows_list = soup.select("dl.event-attributes__inner > div")
#             for div in rows_list:
#                 if div.select_one(".event-attributes__category").text == "Год производства":
#                     movie["release_year"] = div.select_one(".event-attributes__category-value").text
#                     break


class WebDriver:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        self.driver = webdriver.Chrome(options=options)

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


class DataGetter:
    def __init__(self, period):
        self.PERIOD = period
        self.DATE = datetime.now().date()
        self.PAGES_NUM = self.get_pages_num()
        self.JSON_FILE_PATH = f"movies-{self.DATE}.json"

    def get_pages_num(self):
        url = f"https://afisha.yandex.ru/api/events/rubric/cinema?" \
              f"limit=12&offset=12&hasMixed=0&date={self.DATE}&period={self.PERIOD}&city=saint-petersburg&_=1660756014055"

        response = requests.get(url)
        data = response.json()

        return data["paging"]["total"] // data["paging"]["limit"] + 1

    def get_html_pages(self):
        pages_num, period, date = self.PAGES_NUM, self.PERIOD, self.DATE

        if not os.path.exists(f"src/{date}"):
            os.makedirs(f"src/{date}/pages")
            # os.makedirs(f"src/{date}/cards")

        with WebDriver() as driver:
            for i in range(1, pages_num + 1):
                driver.get(
                    f"https://afisha.yandex.ru/saint-petersburg/cinema?source=menu"
                    f"&date={date}&period={period}&page={i}")
                html = driver.page_source
                # html = requests.get(
                #     f"https://afisha.yandex.ru/saint-petersburg/cinema?source=menu"
                #     f"&date={date}&period={period}&page={i}").text
                # print(html)

                while html.startswith("<html prefix=\"og: http://ogp.me/ns#\">"):
                    print(f"page {i} is doing")
                    time.sleep(180)
                    driver.get(
                        f"https://afisha.yandex.ru/saint-petersburg/cinema?source=menu"
                        f"&date={date}&period={period}&page={i}")
                    html = driver.page_source

                with open(f"src/{date}/pages/page_{i}.html", "w", encoding='utf-8-sig') as file:
                    file.write(html)

                print(f"[INFO] Обработано {i}/{pages_num}")
                time.sleep(uniform(8, 10))

    def get_yandex_afisha_info(self):
        pages_num, date = self.PAGES_NUM, self.DATE

        self.get_html_pages()

        card_list_pushkin = []
        for i in range(1, pages_num + 1):
            with open(f"src/{date}/pages/page_{i}.html", encoding='utf-8-sig') as file:
                html = file.read()
                soup = BeautifulSoup(html, "lxml")
                cards_list_all = soup.find_all("div", class_="event events-list__item yandex-sans")
                card_list_pushkin += list(
                    filter(lambda x: x.find("div", class_="_2SFScJ AaVfFN") is not None, cards_list_all))

        movies_info_list = []
        for card in card_list_pushkin:
            div_with_data = card.find("div", class_="i-react event-card-react i-bem event-card-react_js_inited")
            card_str_info = div_with_data.get("data-bem")
            json_acceptable_card_str = card_str_info.replace("'", "\"")
            card_dict_info = json.loads(json_acceptable_card_str)

            movie_image = card_dict_info['event-card-react']['props']['image']['url']
            movie_title = card_dict_info['event-card-react']['props']['title']
            movie_link = "https://afisha.yandex.ru" + card_dict_info['event-card-react']['props']['link']
            movie_rating = 0
            rating_dict = card_dict_info['event-card-react']['props']['rating']
            if rating_dict:
                movie_rating = rating_dict['value']

            movies_info_list.append({
                "image": movie_image,
                "title": movie_title,
                "rating": movie_rating,
                # "release_year": None,
                "link": movie_link
            })

        # get_html_cards(movies_info, DATE)

        # add_card_details(movies_info, DATE)

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
