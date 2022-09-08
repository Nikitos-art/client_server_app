import sys
import json
import socket
import threading
import time
import argparse
import logging
import log.log_configs.client_log_config
from common.variables import *
from common.utils import *
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from decorators import log

from metaclasses import ClientVerifier

LOGGER = logging.getLogger('client')


# User interaction class that forms and sends messages to server
class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # This function creates dictionary with an exit message about exit
    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    # Function requests sender info and the message itself, then sends received data to the server.
    def create_message(self):
        to = input('Enter who will receive your message: ')
        message = input('Enter the message to send: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Message dictionary formed: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            LOGGER.info(f'Message has been sent to user {to}')
        except:
            LOGGER.critical('Connection with server is lost.')
            exit(1)

    # User interaction function, requests commands, send messages
    def run(self):
        self.print_help()
        while True:
            command = input('Enter command: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print('Ending connection.')
                LOGGER.info('Task ended after user command.')
                # A small pause needed so message will have enough time to be sent
                time.sleep(0.5)
                break
            else:
                print('Uuknown command, try again. help - print out all commands.')

    # This function prints out all commands that can be used
    def print_help(self):
        print('Avaliable commands:')
        print('message - send a message. To who and the text will be requested later on.')
        print('help - prints out command tips and hints.')
        print('exit - exit the program')


# Receiver class. Receives message from server. Accepts a message and prints it in console
class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # Main cycle of receiver of massages, accepts message and prints it out. Closes if connection is lost.
    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nMessage received from user {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    LOGGER.info(f'Message received from user {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                else:
                    LOGGER.error(f'Incorrect message from server is recieved: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Couldnt decorate received message.')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Connection with server is lost.')
                break


# Function generates a request of clients presense
@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Formed {PRESENCE} , message for user {account_name}')
    return out


# Function analyzses server reply to presense message,
# returns 200 if all is OK and formes an exception if there is a mistake.
@log
def process_response_ans(message):
    LOGGER.debug(f'Analyzes hello message from server: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


# Парсер аргументов коммандной строки
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # check if port number is ok
    if not 1023 < server_port < 65536:
        LOGGER.critical(
            f'Attempted to launch server with wrong port number : {server_port}. Only ports 1024 - 65535 are allowed. Client is closing.')
        exit(1)

    return server_address, server_port, client_name


def main():
    print('Console manager. Client module.')
    # Loading comand line parameters
    server_address, server_port, client_name = arg_parser()

    # If no username was givenо, then prompt to enter one
    if not client_name:
        client_name = input('Enter user name: ')
    else:
        print(f'Client module is launched with a following name : {client_name}')

    LOGGER.info(
        f'Client is launched with parameters: server address: {server_address} , '
        f'port: {server_port}, user name: {client_name}')

    # Initialising socket and message to server about our presence
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_response_ans(get_message(transport))
        LOGGER.info(f'Connection with a server is established. Server reply: {answer}')
        print(f'Connection with a server is established.')
    except json.JSONDecodeError:
        LOGGER.error('Couldnt decorate Json string received.')
        exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'In servers reply there is a missing field {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Couldnt connect with server {server_address}:{server_port}, '
            f'end computer denied request for connection.')
        exit(1)
    else:
        # If server connection is correct, launching client process of message receving
        module_reciver = ClientReader(client_name, transport)
        module_reciver.daemon = True
        module_reciver.start()

        # after that we launch message sending and user interaction
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        LOGGER.debug('Processes are launched')

        # Watchdog main cycle, if one thread is finished, the nit means that either connection was lost or user
        # entered exit command. Because all events are handled in threads then just fnishing the cycle will be enough.
        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
