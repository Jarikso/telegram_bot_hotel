import sqlite3
import datetime

from config import logger_api


class Database:
    """
    Класс работы с sqlite
    Attributes:
        con: команда для создания файла базы данных
        cursor_obj: устанавливает курсор
    """

    def __init__(self) -> None:
        self.con = sqlite3.connect('search_now.db')
        self.cursor_obj = self.con.cursor()

    @logger_api
    def create_table(self) -> None:
        """
        Метод создания таблиц в базе данных. Создаются:
        search_data - таблица хранящие временные данные о дате заезда
        Таблица содержит следующие колонки:
            id_user (str): id пользователя
            id_hotel (str): id отеля
            command (str): используемая команда в боте
            date_on (str): дата заезда
            date_off (str): дата выезда
        history - хранятся данные по просматриваемым запросам
        Таблицы содержат следующие колонки:
            id_user (str): id пользователя
            date_time (str): дату и время просмотра информации об отеле
            id_hotel (str): id отеля
            location (str): Город поиска
            name (str): Название отеля
            address (str): Адрес отеля
            center (str): Расстояние до центра
            price (str): Цена
        """
        try:
            self.cursor_obj.execute(
                'CREATE TABLE search_data (id_user TEXT, id_hotel TEXT, command TEXT, date_on TEXT, date_off TEXT)')
            self.cursor_obj.execute(
                'CREATE TABLE history (id_user INTEGER, date_time TEXT, id_hotel INTEGER, location TEXT, name TEXT,'
                'address TEXT, center TEXT, price TEXT, all_price TEXT, nights TEXT, command TEXT)')
            self.con.commit()
        except BaseException:
            return None

    @logger_api
    def record_search(self, search_dict: dict) -> None:
        """
        Методы аптейта колонок таблицы параметров для поиска
        Args:
            search_dict (dict): параметры поиска
        """
        data = [i for i in search_dict.values()]
        self.cursor_obj.execute(
            'INSERT INTO search_data (id_user, id_hotel, command, date_on, date_off)'
            'VALUES(?, ?, ?, ?, ?)', tuple(data))
        self.con.commit()

    @logger_api
    def update_search(self, id_user: str, date: str) -> None:
        """
        Методы аптейта колонок таблицы параметров для поиска
        Args:
            id_user (dict): id пользователя
            date (str): дата, один из параметров поиска
        """
        data = self.cursor_obj.execute(f'SELECT * FROM search_data WHERE id_user = {id_user}')
        if data.fetchone()[3] == 'xxx':
            self.cursor_obj.execute(f'UPDATE search_data SET date_on = {date} WHERE id_user = {id_user}')
            self.con.commit()
        else:
            self.cursor_obj.execute(f'UPDATE search_data SET date_off = {date} WHERE id_user = {id_user}')
            self.con.commit()

    @logger_api
    def return_date(self, id_user: str) -> tuple:
        """
        Метод возвращающий данные по дате, хранящиеся во временной СУБД
        Args:
            id_user (dict): id пользователя
        """
        data = self.cursor_obj.execute(f'SELECT * FROM search_data WHERE id_user = {id_user}')
        return data.fetchone()

    @logger_api
    def delete_str(self, id_user: str) -> None:
        """
        Метод очистки временной СУБД для хранения даты заезда
        Args:
            id_user (dict): id пользователя
        """
        try:
            self.cursor_obj.execute(f'DELETE FROM search_data WHERE id_user = {id_user}')
            self.con.commit()
        except BaseException:
            self.create_table()

    @logger_api
    def record_history(self, id_user: str, command: str, list_hotel: tuple) -> None:
        """
        Метод записи в таблицу history данных результата поиска отелей пользователем
        Args:
            id_user (str): id пользователя
            command (str): используемая команда в боте
            list_hotel (tuple): передается кортеж информацию об отеле, согласно колонкам таблицы
        """
        period = datetime.datetime.today()
        dt = period.strftime("%d/%m/%Y %H:%M")
        list_hotel.insert(0, id_user)
        list_hotel.insert(1, dt)
        list_hotel.append(command)
        self.cursor_obj.execute(
            'INSERT INTO history (id_user, date_time, id_hotel, location, name, address, center, price, all_price, nights, command)'
            'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', tuple(list_hotel))
        self.con.commit()

    @logger_api
    def read_history(self, user: str) -> str:
        """
        Метод выводящий историю просмотров пользователем отелей по запросу
        Args:
            user (str): id пользователя
        :return: text (str) - строка, содержащая ДАТА/ВРЕМЯ, ГОРОД, НАЗВАНИЕ ОТЕЛЯ
        """
        data = self.cursor_obj.execute(f'SELECT * FROM history')
        if data.fetchone() is None:
            return 'База данных еще не заполнена'
        else:
            data = self.cursor_obj.execute(f'SELECT * FROM history WHERE id_user={user}')
            text = ''
            for i in data:
                text += f'{i[10]}, {i[1]}, {i[3].split(",")[0]}, {i[4]}\n'
            return text

    @logger_api
    def read_info(self, id_user: str, id_hotel: str) -> str:
        """
        Метод выводящий историю просмотров пользователем отелей по запросу
        Args:
            id_user (str): id пользователя
        :return: text (str) - строка, содержащая ДАТА/ВРЕМЯ, ГОРОД, НАЗВАНИЕ ОТЕЛЯ
        """
        data = self.cursor_obj.execute(f'SELECT * FROM history WHERE id_user={id_user} AND id_hotel={id_hotel}')
        for i in data:
            return i
