# Системные импорты
import telebot
from telebot import types
from loguru import logger
import datetime
from datetime import date, timedelta

# Импорты пакетов TelebotApi
from telebot.types import InputMediaPhoto
from telegram_bot_calendar import DetailedTelegramCalendar

# Импорты пакетов API и конфигураций
from botrequests.lowprice import LowpriceHotel
from botrequests.highprice import HihgpriceHotel
from botrequests.bestdeal import BestdealHotel
from botrequests.history import Database
from config import BOT_TOKEN, logger_decorator, logger_handler

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
@logger.catch
@logger_decorator
def send_welcome(message: telebot.types.Message) -> None:
    """
    Метод для получения текстовых сообщений
    Он же запускает бота
    Args:
        message (list): после вводу сообщение '\start' выводит приветственное сообщение
    """
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton("/help")
    but2 = types.KeyboardButton("/lowprice")
    but3 = types.KeyboardButton("/highprice")
    but4 = types.KeyboardButton("/bestdeal")
    but5 = types.KeyboardButton("/history")
    keyboard.add(but1, but2, but3, but4, but5)
    if message.text == '/start':
        bot.reply_to(message,
                     'Здравствуйте, я телеграмм бот и готов помочь тебе выбрать подходящий отель.\n'
                     'Давайте для начала определимся какие команды я умею выполнять:\n'
                     'help — помощь по командам бота\n'
                     'lowprice — вывод самых дешёвых отелей в городе\n'
                     'highprice — вывод самых дорогих отелей в городе\n'
                     'bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра\n'
                     'history — вывод истории поиска отелей\n', reply_markup=keyboard)
        bot.register_next_step_handler(message, menu)
    else:
        bot.reply_to(message,
                     '/help — помощь по командам бота\n'
                     '/lowprice — вывод самых дешёвых отелей в городе\n'
                     '/highprice — вывод самых дорогих отелей в городе\n'
                     '/bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра\n'
                     '/history — вывод истории поиска отелей\n')
        bot.register_next_step_handler(message, menu)


@bot.message_handler(content_types=['text'])
@logger.catch
@logger_decorator
def menu(message: telebot.types.Message) -> None:
    """
    Метод обработки команд. Обрабатывает событие согласно выбранной команде команде
    Args:
        message (list): согласно выбранной команде осуществляется перенаправление на метод поиска id города
    """
    Database().delete_str(message.from_user.id)
    if message.chat.type == 'private':
        if message.text not in ['/help', '/history', '/lowprice', '/highprice', '/bestdeal']:
            msg = bot.send_message(message.from_user.id, 'Ошибка обработки сообщения.\n'
                                                         'Чтобы продолжить работать выберите команду.')
            send_welcome(msg)
        elif message.text == '/help':
            msg = bot.send_message(message.from_user.id, 'Давайте напомню что я умею.')
            send_welcome(msg)
        elif message.text == '/history':
            result = Database().read_history(message.from_user.id)
            bot.reply_to(message, result)
        elif message.text == '/lowprice' or '/highprice' or '/bestdeal':
            bot.send_message(message.from_user.id,
                             f'Вы выбрали команду {message.text}. Укажите город для поиска...')
            bot.register_next_step_handler(message, search_city, message.text)


@logger.catch
@logger_decorator
def search_city(message: telebot.types.Message, command: str) -> None:
    """
    Метод поиска id города. После получение через скрипт Lowprice_hotel вызывается метод поиска отелей.
    Args:
        message (list): message.text (str) -> возвращается id_города (str), после чего вызывается метод search_hotel
                        который обрабатывается условным оператором через значение введенной команды
        command (str): значение команды, которое ввел пользователь, для дальнейшей обработки и выбора методом
                        search_hotel скрипта для вывода результатов пользователя клиентом (telegram)
    """
    city = message.text
    id_city = LowpriceHotel().receive_id(city)
    parameter = {'id_user': message.from_user.id, 'id_city': id_city, 'command': command, 'date_on': 'xxx',
                 'date_off': 'zzz'}
    Database().record_search(parameter)
    if message.text in ['/help', '/history', '/lowprice', '/highprice', '/bestdeal']:
        menu(message)
    elif id_city is None:
        bot.send_message(message.from_user.id, f'Вы не верно указали город. Повторите поиск {command}')
    else:
        if command == '/lowprice' or command == '/highprice' or command == '/bestdeal':
            bot.send_message(message.from_user.id, f'Укажите дату заезда в отель')
            get_date(message, date.today())


@bot.message_handler(func=lambda message: True)
@logger.catch
@logger_decorator
def get_date(message: telebot.types.Message, my_day):
    """
    Метод запускает инлайн-календарь
    """
    calendar, step = DetailedTelegramCalendar(locale='ru', min_date=my_day).build()
    bot.send_message(message.chat.id,
                     "Укажите год...",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
@logger.catch
@logger_handler
def cal(call: telebot.types.Message):
    """
    Метод обрабатывает запросы инлайн-календаря и в зависимости от команды запускает методы поиска отеля
    или переходит на дополнение параметров поиска
    """
    my_day = None
    result_date = Database().return_date(call.from_user.id)
    if result_date[3] == 'xxx':
        my_day = date.today()
    elif result_date[3].isdigit():
        my_day = datetime.date(int(result_date[3][:4]), int(result_date[3][4:6]),
                               int(result_date[3][6:])) + timedelta(days=1)
    result, key, step = DetailedTelegramCalendar(locale='ru', min_date=my_day).process(call.data)
    if not result and key:
        seasons = {'y': 'год', 'm': 'месяц', 'd': 'день'}
        bot.edit_message_text(f"Укажите {seasons[step]}...",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        replace = result.strftime("%Y%m%d")
        Database().update_search(call.from_user.id, replace)
        my_dates = Database().return_date(call.from_user.id)
        bot.edit_message_text(f"Вы выбрали {result}",
                              call.message.chat.id,
                              call.message.message_id)
        if my_dates[4] == 'zzz':
            list_info = call.data.split('_')
            my_day = datetime.date(int(list_info[4]), int(list_info[5]), int(list_info[6]))
            msg = bot.send_message(call.from_user.id, f'Укажите дату выезда из отеля. Начало '
                                                      f'календаря берется от следующего дня после заезда.')
            get_date(msg, my_day)
        else:
            date_on = datetime.date(int(my_dates[3][:4]), int(my_dates[3][4:6]), int(my_dates[3][6:]))
            date_off = datetime.date(int(my_dates[4][:4]), int(my_dates[4][4:6]), int(my_dates[4][6:]))
            parameter = dict(id_user=my_dates[0], id_city=my_dates[1], command=my_dates[2],
                             date=[date_on.strftime('%Y-%m-%d'), date_off.strftime('%Y-%m-%d')])
            if parameter['command'] != '/bestdeal':
                message = bot.send_message(call.from_user.id, f'Укажите количество отелей для поиска (доступно 25)')
                bot.register_next_step_handler(message, search_hotel, parameter)
            elif parameter['command'] == '/bestdeal':
                message = bot.send_message(call.from_user.id, f'Укажите минимальную цену')
                bot.register_next_step_handler(message, get_minprice, parameter)


@logger.catch
@logger_decorator
def get_minprice(message: telebot.types.Message, parameter: dict) -> None:
    """
    Метод описывает параметры для команды /bestdeal. Добавляет в словарь parameter минимальную цену
    Args:
        message (list): данные сообщения от пользователя
        parameter (dict): параметры для поиска по команде
    """
    if message.text.isdigit():
        parameter['price'] = [message.text]
        bot.send_message(message.from_user.id, 'Укажите максимальную цену')
        bot.register_next_step_handler(message, get_maxprice, parameter)
    else:
        input_valid(message, get_minprice, parameter)


@logger.catch
@logger_decorator
def get_maxprice(message: telebot.types.Message, parameter: dict) -> None:
    """
    Метод описывает параметры для команды /bestdeal. Добавляет в словарь parameter максимальную цену
    Args:
        message (list): данные сообщения от пользователя
        parameter (dict): параметры для поиска по команде
    """
    if message.text.isdigit():
        parameter['price'].append(message.text)
        parameter['price'].sort()
        bot.send_message(message.from_user.id, 'Укажите минимальное расстояние до центра в метрах')
        bot.register_next_step_handler(message, get_mindist, parameter)
    else:
        input_valid(message, get_maxprice, parameter)


@logger.catch
@logger_decorator
def get_mindist(message: telebot.types.Message, parameter: dict) -> None:
    """
    Метод описывает параметры для команды /bestdeal. Добавляет в словарь parameter минимальное расстояние до центра
    Args:
        message (list): данные сообщения от пользователя
        parameter (dict): параметры для поиска по команде
    """
    if message.text.isdigit():
        parameter['dist'] = [str(int(message.text) / 1000)]
        bot.send_message(message.from_user.id, 'Укажите максимальное расстояние до центра в метрах')
        bot.register_next_step_handler(message, get_maxdist, parameter)
    else:
        input_valid(message, get_mindist, parameter)


@logger.catch
@logger_decorator
def get_maxdist(message: telebot.types.Message, parameter: dict) -> None:
    """
    Метод описывает параметры для команды /bestdeal. Добавляет в словарь parameter максимальное расстояние до центра
    Args:
        message (list): данные сообщения от пользователя
        parameter (dict): параметры для поиска по команде
    """
    if message.text.isdigit():
        parameter['dist'].append(str(int(message.text) / 1000))
        parameter['dist'].sort()
        text = f'Осуществляется поиск отелей по следующим параметрам:\nДата заезда: {parameter["date"][0]}' \
               f'\nДата выезда: {parameter["date"][1]}' \
               f'\nДиапазон цен: {parameter["price"][0]} руб. - {parameter["price"][1]} руб.' \
               f'\nДиапазон расстояния: {parameter["dist"][0]} км. - {parameter["dist"][1]} км.' \
               f'\nОжидайте.'
        bot.reply_to(message, text)
        result = BestdealHotel().all_hotels(parameter)
        parameter['hotels'] = result
        if len(result) == 0 or result is None:
            bot.send_message(message.from_user.id, 'По запросу ничего не найдено. '
                                                   'Повторите поиск, выбрав команду /bestdeal и изменив параметры поиска')
        else:
            bot.send_message(message.from_user.id,
                             f'Укажите количество отелей (доступно к просмотру {len(result)} отелей)...')
            bot.register_next_step_handler(message, search_hotel, parameter)
    else:
        input_valid(message, get_maxdist, parameter)


@logger.catch
@logger_decorator
def search_hotel(message: telebot.types.Message, parameter: dict) -> None:
    """
    Метод обработки введенной команды для перенаправления клиента на вызов скрипта из папки botrequests
    Возвращается вложенный список отелей, состоящий из параметров заключенных в словарь:
    dict = {'id': '', 'name: '', 'address': '', 'center': '', 'price': ''}
    Args:
        message (list): message.text (str) -> количество отеле для поиска
        parameter (dict): значения параметров необходимые для  поиска отелей
    """
    text = f'Осуществляется поиск отелей по следующим параметрам:\nДата заезда: {parameter["date"][0]}\n' \
           f'Дата выезда: {parameter["date"][1]}\nКоличество отелей для поиска: {message.text}\nОжидайте.'
    if message.text.isdigit():
        if parameter['command'] == '/lowprice':
            bot.reply_to(message, text)
            hotel_dict = LowpriceHotel().output_hotel(parameter, message.text)
            data_output(message, hotel_dict, parameter['command'])
        elif parameter['command'] == '/highprice':
            bot.reply_to(message, text)
            hotel_dict = HihgpriceHotel().output_hotel(parameter, message.text)
            data_output(message, hotel_dict, parameter['command'])
        elif parameter['command'] == '/bestdeal':
            if int(message.text) <= len(parameter['hotels']):
                hotel_dict = [parameter['hotels'][i] for i in range(int(message.text))]
                data_output(message, hotel_dict, parameter['command'])
            else:
                message.text = len(parameter['hotels'])
                hotel_dict = [parameter['hotels'][i] for i in range(int(message.text))]
                data_output(message, hotel_dict)
    else:
        input_valid(message, search_hotel, parameter)


@bot.message_handler(func=lambda message: True)
@logger.catch
@logger_decorator
def data_output(message: telebot.types.Message, hotels: str, command) -> None:
    """
    Метод, выводящий информацию о отелях, под каждым сообщением формирует инлайн-клавиатуру с информацией,
    которую можно загрузить (фотографии, сайт отеля). Данные поиска записываются в СУБД.
    Args:
        message (list): параметр сообщения введенного от пользователя
        hotels (str): название .json файла, в который записываются данные по отелям
        command (str): команда для записи в базу данных
    """
    bot.send_message(message.from_user.id, f'По вашему запросу в городе {hotels[0]["location"]}'
                                           f' найдены следующие отели')
    for key in hotels:
        result = [info for info in key.values()]
        Database().record_history(message.from_user.id, command, result)
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        text = f"Название отеля: {key['name']}\n" \
               f"Адрес: {key['address']}\n" \
               f"Цена за ночь: {key['price']}\n" \
               f"Общая стоимость за {key['nights']} дней: {key['all_price']}\n" \
               f"Расстояние до центра: {key['center']}"
        bot.send_message(message.from_user.id, text)
        photo = types.InlineKeyboardButton(text='Фотографии', callback_data=key['id'])
        site = types.InlineKeyboardButton(text='Сайт отеля', url=f'https://ru.hotels.com/ho{key["id"]}')
        keyboard.row(photo, site)
        bot.send_message(message.from_user.id, f'Выберите действие для отеля - {key["name"]}',
                         reply_markup=keyboard)
    menu_next = types.InlineKeyboardMarkup(row_width=3)
    next_step_menu = types.InlineKeyboardButton('Перейти в меню команд', callback_data='/help')
    menu_next.add(next_step_menu)
    bot.send_message(message.from_user.id, 'Если хотите продолжить поиск по командам, нажмите '
                                           'клавишу под этим сообщением', reply_markup=menu_next)


@bot.callback_query_handler(func=lambda call: True)
@logger.catch
@logger_handler
def callback(call: telebot.types.Message) -> None:
    """
    Метод обработки инлайн клавиатуры
        if call.data (str): Предлагает выбрать загрузки фотографии
        elif call.data == '/help': Предлагает перейти в меню команд
    Args:
        call (list): параметр инлайн-клавиатуры выбранная пользователем
    """

    if call.data.isdigit():
        result = Database().read_info(call.from_user.id, call.data)
        photo_list = LowpriceHotel().output_photo(call.data)
        msg = bot.send_message(call.from_user.id, f"Для отеля {result[4]} доступно {len(photo_list)} "
                                                  f"фотографий. Укажите количество фотографий")
        bot.register_next_step_handler(msg, photo_hotel, photo_list)
    elif call.data == '/help':
        bot.send_message(call.from_user.id, 'Выбери одну из нижеперечисленных команд:\n'
                                            '/help — помощь по командам бота\n'
                                            '/lowprice — вывод самых дешёвых отелей в городе\n'
                                            '/highprice — вывод самых дорогих отелей в городе\n'
                                            '/bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра\n'
                                            '/history — вывод истории поиска отелей\n')


@logger.catch
@logger_decorator
def photo_hotel(message: telebot.types.Message, photo_list: list) -> None:
    """
    Методы вывода сообщение в виде альбома фотографий клиентом по запросу пользователем
    Args:
        message (list): message.text (str) -> количество фотографий в альбоме
        photo_list(list): список фотографий в виде url-ссылок
    """
    if message.text.isdigit():
        count_photo = int(message.text)
        if count_photo >= len(photo_list):
            count_photo = len(photo_list)
        new_list = [InputMediaPhoto(photo_list[photo]) for photo in range(count_photo)]
        photo_show = [new_list[i:i + 10] for i in range(0, len(new_list), 10)]
        for media in photo_show:
            bot.send_media_group(message.chat.id, media)
    else:
        input_valid(message, photo_hotel, photo_list)


@logger.catch
@logger_decorator
def input_valid(message: telebot.types.Message, func, parameter: dict) -> None:
    """
    Метод обработки ввода значений поиска. Добавляется в словарь option_info минимальное расстояние до центра
    Args:
        message (list): данные сообщения от пользователя
        func (func): метод в которой произошла ошибка ввода
        parameter (dict): параметры для поиска по команде
    """
    if message.text in ['/help', '/history', '/lowprice', '/highprice', '/bestdeal']:
        menu(message)
    else:
        bot.reply_to(message, 'Неверный формат ввода. Укажите цифру')
        bot.register_next_step_handler(message, func, parameter)


if __name__ == '__main__':
    Database().create_table()
    bot.polling(none_stop=True, interval=0)
