import logging
import os.path
from logging import handlers
from common.variables import LOGGING_LEVEL
###_____________________________создаем формировщик логов____________________________________________###
import sys
#sys.path.append("../log_files")
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, "../log_files/server_app.log")

LOGGER = logging.getLogger('server')
SERVER_FORMATTER = logging.Formatter("%(asctime)-10s %(levelname)-10s %(module)-10s %(message)-s")

###___________________________________потоки вывода логов____________________________________________###
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(SERVER_FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1,
                                                     when='midnight')
LOG_FILE.setFormatter(SERVER_FORMATTER)

###______________________________создаем регистратор и настраиваем его_______________________________###
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

### отладка ###
if __name__ == "__main__":
    LOGGER.critical("Критическая ошибка")
    LOGGER.error("Ошибка")
    LOGGER.debug("Отладочная информация")
    LOGGER.info("Информационное есообщение")
