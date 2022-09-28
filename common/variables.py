import logging

DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'
LOGGING_LEVEL = logging.DEBUG

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
SERVER_DATABASE = 'sqlite:///server_base.db3'
# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
# Словари - ответы:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
DESTINATION = 'to'
EXIT = 'exit'
### ascii art ###
SERVER_IS_UP = """
 _____                            _       _   _______
/  ___|                          (_)     | | | | ___ \
\ `--.  ___ _ ____   _____ _ __   _ ___  | | | | |_/ /
 `--. \/ _ \ '__\ \ / / _ \ '__| | / __| | | | |  __/
/\__/ /  __/ |   \ V /  __/ |    | \__ \ | |_| | |
\____/ \___|_|    \_/ \___|_|    |_|___/  \___/\_|
"""
