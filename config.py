from dotenv import dotenv_values
from loguru import logger

config = dotenv_values(".env")
BOT_TOKEN = config['BOT_TOKEN']
API_TOKEN = config['API_TOKEN']

HEADERS = {
    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
    'x-rapidapi-key': API_TOKEN
}

# logger.remove()
logger.add('bot.log', format="{time} {level} {message}", level='DEBUG', rotation='1000 KB', compression='zip')


def logger_decorator(func):
    """
     Декоратор логирующий методы Telebotapi
    """
    def wrap_log(*args, **kwargs):
        func(*args, **kwargs)
        result = args[0]
        logger.info(f'Пользователь {result.from_user.id} вызывает {func.__name__}, вводит сообщение {result.text}')

    return wrap_log


def logger_handler(func):
    """
     Декоратор логирующий методы инлайн-клавиатур Telebotapi
    """
    def wrap_log(*args, **kwargs):
        func(*args, **kwargs)
        result = args[0]
        logger.info(f'Пользователь {result.from_user.id} вызывает {func.__name__}, вводит сообщение {result.data}')

    return wrap_log


def logger_api(func):
    """
     Декоратор логирующий методы для Hotelapi
    """
    def wrap_log(self, *args, **kwargs):
        logger.info(f'Метод: {func.__name__} -> Файл: {func.__module__} -> Аргументы: {args}')
        return func(self, *args, **kwargs)

    return wrap_log
