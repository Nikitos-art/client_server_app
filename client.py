"""Программа-клиент"""
import sys
import json
import socket
import threading
import time
import argparse
import logging
import log.log_configs.client_log_config
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS, \
    ACTION, TIME, USER, ACCOUNT_NAME, SENDER, PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT, EXIT, DESTINATION
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from decorators import log

# client logger initialisation
LOGGER = logging.getLogger('client')


@log
def create_exit_message(account_name):
    """Функция создаёт словарь с сообщением о выходе"""
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@log
def message_from_server(sock, my_username):
    """Function - processes server messages of other users"""
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                print(f'\nReceived username {message[SENDER]}:'
                      f'\n{message[MESSAGE_TEXT]}')
                LOGGER.info(f'MEssage recevived from user {message[SENDER]}:'
                            f'\n{message[MESSAGE_TEXT]}')
            else:
                LOGGER.error(f'Incorrect message from server received: {message}')
        except IncorrectDataRecivedError:
            LOGGER.error(f'Couldnt decorate received message.')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            LOGGER.critical(f'Disconnected from server.')
            break


@log
def create_message(sock, account_name='Guest'):
    """ Function asks for message and sender, then sends received data to server
    :param sock:
    :param account_name:
    :return:
    """
    to_user = input('Enter receiver name: ')
    message = input('Enter your message: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    LOGGER.debug(f'Formed message dictionary: {message_dict}')
    try:
        send_message(sock, message_dict)
        LOGGER.info(f'Message sent for user {to_user}')
    except:
        LOGGER.critical('Dicsonnected from server.')
        sys.exit(1)


@log
def user_interactive(sock, username):
    """USer intercation function. Asks for commands, sends messages"""
    print_help()
    while True:
        command = input('Enter you command: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Disconnected.')
            LOGGER.info('Ended process after user command.')
            # Small pause needed to avoid collision
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


@log
def create_presence(account_name='Guest'):
    """This function generates a request for client presence"""
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Formed {PRESENCE} message for user {account_name}')
    return out


def print_help():
    """Help inquiry function"""
    print('Supported commands:')
    print('message - send a message. To whom and text will be prompted later.')
    print('help - show commands help')
    print('exit - close programm')


@log
def process_response_ans(message):
    """
    This function parses server reply to presence message,
    returns 200 if everythign is ok or raises exception if there is an error
    """
    LOGGER.debug(f'Parse greetings message from server: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    """Creating comand line arguments parser
    and reading parameters, return 3 parameters
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # check port number is ok
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Client launch attempt with wrong port: {server_port}. '
            f'Addresses allowed from 1024 to 65535. Client is closing.')
        sys.exit(1)

    # check port
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Attempted launching client with wrong port number: {server_port}. '
            f'Allowed ports from 1024 to 65535. Closing the client.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    """INforming about launch"""
    print('Console manager. Client module.')

    # Launching command line parameters
    server_address, server_port, client_name = arg_parser()

    # If no client name was specified then asking for its input.
    if not client_name:
        client_name = input('Enter username: ')

    LOGGER.info(
        f'Launched client with parameters: server address: {server_address}, '
        f'port: {server_port}, name: {client_name}')

    # Socket initialisaztion and message to server about client presence
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        LOGGER.info(f'Connected to server. Server reply: {answer}')
        print(f'Connected to server.')
    except json.JSONDecodeError:
        LOGGER.error('Couldnt decorate received Json string.')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'While connecting, srver returned an error: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'Server reply is missing a field  {missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        LOGGER.critical(
            f'Couldnt connect to server {server_address}:{server_port}, '
            f'end computer refused request for connection.')
        sys.exit(1)
    else:
        # If connected to server successfully then launch client process of receiving messages
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        ### launching message sending and user interaction
        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug("Threads launched")

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
