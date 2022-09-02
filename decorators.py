import sys
import logging
import log.log_configs.client_log_config
import log.log_configs.server_log_config
import inspect
from functools import wraps

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


###_____________________________________ функция декоратор ________________________________________________###
def log(func_to_log):
    """Функция декоратор. Фиксирует обращение к декорируемой функции, сохраняет ее имя и аргументы"""
    @wraps(func_to_log)
    def wrapper_log_saver(*args, **kwargs):
        wrapper_log_saver.calls_count += 1
        LOGGER.debug(
            f'Была вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}.'
            f'Количество вызовов (за одну сессию) : {wrapper_log_saver.calls_count}  '
            f' Вызов из модуля {func_to_log.__module__}.'
            f' Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
        return func_to_log(*args, **kwargs)

    wrapper_log_saver.calls_count = 0
    return wrapper_log_saver

###_________________________________ класс декоратор ____________________________________________________###

# class log: ### класс назван с маленькой буквы для удобства
#     def __init__(self, func):
#         self.func = func
#
#     def __call__(self, *args, **kwargs):
#         return_value = self.func(*args, **kwargs)
#         LOGGER.debug(
#             f'Была вызвана функция {self.func.__name__} с параметрами {args}, {kwargs}.'
#             f'Вызов из модуля {self.func.__module__}.'
#             # f'функции {traceback.format_stack()[0].strip().split()[-1]}.')
#             f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
#         return return_value
