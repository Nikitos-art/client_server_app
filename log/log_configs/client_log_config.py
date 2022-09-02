import logging
import os
###________________________________полноценный вариант______________________________________###
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, "../log_files/client_app.log")

logger = logging.getLogger('client')
### создать файловый обработчик логирования (можно задасть кодироваку) ###
formatter = logging.Formatter("%(asctime)-10s %(levelname)-10s %(module)-10s %(message)-s")
#file_handler = logging.FileHandler('../log_files/client_app.log', encoding='utf-8')
file_handler = logging.FileHandler(PATH, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
### добавить в логгер новый обработчки и установить уровень логирования ###
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    PARAMS = {'host': '127.0.0.1', 'port': 7777}
    logger.info("Параметры подключения: %(host)s, %(port)d", PARAMS)

###________________________________базовый вариант______________________________________###

# logging.basicConfig(
#     filename="client_app.log",
#     format="%(asctime)-30s %(levelname)-10s %(module)-25s %(message)-s",
#     level=logging.DEBUG
# )
#
# LOG = logging.getLogger('client.app')
# CRIT_HAND = logging.StreamHandler(sys.stderr)
# LOG.addHandler(CRIT_HAND)
# LOG.debug('Отладочная информация')
#
