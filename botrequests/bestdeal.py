import requests
import json
from config import HEADERS, logger_api
import datetime


def format_str(data: str) -> (int, float):
    """
    Метод форматирования строки (str) в число (int) или число с плавающей точкой(float)
    Args:
        id_city (str): передается id города
        count_search (str): передается количество отелей для поиска
    :return: int или float - расстояние до центра
    """
    if data.split(','):
        return float('.'.join(data.split(',')))
    else:
        return int(data)


class BestdealHotel:
    """
    Класс поиска отелей по заданным параметрам
    Attributes:
        headers (dict): передается параметры https://rapidapi.com/
        url_hotels (str): ссылка для поиска отелей
    """

    def __init__(self):
        self.headers = HEADERS
        self.url_hotels = 'https://hotels4.p.rapidapi.com/properties/list'

    @logger_api
    def all_hotels(self, dict_param: dict) -> list:
        """
        Метод форматирование списка
        Args:
            param (dict): передается словарь, содержащий параметры для поиска (id, priceMin, priceMax)
        :return: end_hotel - список отелей
        """
        count = 1
        sort_hotels = []
        while True:
            hotel = self.output_hotel(dict_param, count)
            if hotel is None:
                break
            if len(sort_hotels) >= 10:
                break
            else:
                for info in hotel:
                    sort_hotels.append(info)
                count += 1
        sort_hotels.sort(key=lambda data: data['center'], reverse=False)
        end_hotel = [hotel for hotel in sort_hotels if
                     float(dict_param['dist'][0]) <= float(hotel['center']) <= float(dict_param['dist'][1])]
        return end_hotel

    def output_hotel(self, argument: dict, count_page: int) -> list:
        """
        Метод поиска отелей по минимальной цене
        Ключ priceMin переменной querystring (dict) (строки запроса) ищет в url_hotels (str) минимальное значение
        и сортирует от минимума к максимуму в зависимости от количества запросов в count_search (str)
        Args:
            id_city (str): передается id города
            count_search (str): передается номер страницы поиска
        :return: list_hotels - список отелей
        """
        querystring = dict(destinationId=argument['id_city'], pageNumber=str(count_page), pageSize='25',
                           priceMin=argument['price'][0], priceMax=argument['price'][1], sortOrder='PRICE',
                           locale='ru_RU', currency='RUB')
        response = requests.get(self.url_hotels, headers=self.headers, params=querystring)
        data = json.loads(response.text)
        try:
            if int(data['data']['body']['searchResults']['pagination']['currentPage']) != count_page:
                return None
            else:
                hotels_ls = []
                city = {'location': data.get('data').get('body').get('header')}
                hotels = data.get('data').get('body').get('searchResults').get('results')
                for hotel in hotels:
                    hotel_dct = {'id': None, 'location': None, 'name': None, 'address': None, 'center': None,
                                 'price': None, 'all_price': None, 'nights': None}
                    try:
                        hotel_dct['id'] = str(hotel.get('id'))
                    except AttributeError:
                        hotel_dct['id'] = 'Данные по id отеля не найдены'
                    try:
                        hotel_dct['location'] = city.get('location').split(',')[0]
                    except AttributeError:
                        hotel_dct['location'] = 'Неизвестный город'
                    try:
                        hotel_dct['name'] = hotel.get('name')
                    except AttributeError:
                        hotel_dct['name'] = 'Название отеля не известно'
                    try:
                        hotel_dct['address'] = hotel.get('address').get('streetAddress')
                    except AttributeError:
                        hotel_dct['address'] = 'Адрес отеля не найден'
                    try:
                        hotel_dct['center'] = format_str(hotel.get('landmarks')[0].get('distance').split()[0])
                    except AttributeError:
                        hotel_dct['center'] = 'Расстояние до центра не указано'
                    try:
                        on = argument['date'][0].split('-')
                        off = argument['date'][1].split('-')
                        date_1 = datetime.date(int(on[0]), int(on[1]), int(on[2]))
                        date_2 = datetime.date(int(off[0]), int(off[1]), int(off[2]))
                        all_day = str((date_1 - date_2) * (-1)).split()[0]
                        hotel_dct['nights'] = all_day
                    except AttributeError:
                        hotel_dct['nights'] = 'Количество ночей не указана'
                    try:
                        hotel_dct['price'] = str(
                            int(hotel.get('ratePlan').get('price').get('exactCurrent') / int(
                                hotel_dct['nights']))) + ' RUB'
                    except AttributeError:
                        hotel_dct['price'] = 'Цена за ночь не указана'
                    try:
                        hotel_dct['all_price'] = hotel.get('ratePlan').get('price').get('current')
                    except AttributeError:
                        hotel_dct['all_price'] = 'Цена за количество ночей не указана'
                    hotels_ls.append(hotel_dct)
                return hotels_ls
        except KeyError:
            return None
