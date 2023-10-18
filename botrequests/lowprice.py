import requests
import json
from config import HEADERS, logger_api
import datetime


class LowpriceHotel:
    """
    Класс поиска дешевых отелей
    Attributes:
        headers (dict): передается параметры https://rapidapi.com/
        url_city (str): ссылка на поиск id города
        url_hotels (str): ссылка для поиска отелей
        url_photo (str): ссылка для поиска фотографий п отелю
    """
    def __init__(self):
        self.headers = HEADERS
        self.url_city = 'https://hotels4.p.rapidapi.com/locations/v2/search'
        self.url_hotels = 'https://hotels4.p.rapidapi.com/properties/list'
        self.url_photo = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'

    @logger_api
    def receive_id(self, name_city: str) -> str:
        """
        Метод поиска id города по названию
        Args:
            name_city (str): передается название города
        :return: str - id города
        """
        querystring = {'query': name_city, 'locale': 'ru_RU'}
        response_id = requests.get(self.url_city, headers=self.headers, params=querystring)
        data_city = json.loads(response_id.text)
        if not data_city.get('suggestions')[0].get('entities'):
            return None
        else:
            return data_city.get('suggestions')[0].get('entities')[0].get('destinationId')

    @logger_api
    def output_hotel(self, argument: dict, count_search: str) -> list:
        """
        Метод поиска отелей по минимальной цене
        Ключ sortOrder со значением 'PRICE' переменной querystring (dict) (строки запроса)
        ищет в url_hotels (str) минимальное значение и сортирует от минимума к максимуму в
        зависимости от количества запросов в count_search (str)
        Args:
            id_city (str): передается id города
            count_search (str): передается количество отелей для поиска
        :return: hotels_ls - список отелей
        """
        querystring = dict(destinationId=argument['id_city'], pageSize=count_search,
                           checkIn=argument['date'][0], checkOut=argument['date'][1],
                           sortOrder='PRICE', locale='ru_RU', currency='RUB')
        response = requests.get(self.url_hotels, headers=self.headers, params=querystring)
        data = json.loads(response.text)
        hotels_ls = []
        city = {'location': data.get('data').get('body').get('header')}
        hotels = data.get('data').get('body').get('searchResults').get('results')
        for hotel in hotels:
            hotel_dct = {'id': None, 'location': None, 'name': None, 'address': None, 'center': None, 'price': None,
                         'all_price': None, 'nights': None}
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
                hotel_dct['center'] = hotel.get('landmarks')[0].get('distance')
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
                    int(hotel.get('ratePlan').get('price').get('exactCurrent') / int(hotel_dct['nights']))) + ' RUB'
            except AttributeError:
                hotel_dct['price'] = 'Цена за ночь не указана'
            try:
                hotel_dct['all_price'] = hotel.get('ratePlan').get('price').get('current')
            except AttributeError:
                hotel_dct['all_price'] = 'Цена за количество ночей не указана'
            hotels_ls.append(hotel_dct)
        return hotels_ls

    @logger_api
    def output_photo(self, id_hotel: str) -> list:
        """
        Метод поиска id города по названию
        Args:
            id_city (str): передается id города
        :return: list_photo - список доступных фотографий
        """
        querystring = {'id': id_hotel}
        response = requests.get(self.url_photo, headers=self.headers, params=querystring)
        data_hotel = json.loads(response.text)
        list_photo = []
        for photo in data_hotel.get('hotelImages'):
            result = photo.get('baseUrl').format(size='b')
            list_photo.append(result)
        return list_photo[:11]
