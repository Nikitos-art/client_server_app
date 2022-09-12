import socket
import sys
import argparse
import logging
import threading

import select
import log.log_configs.server_log_config
from common.variables import *
from common.utils import *
from decorators import log
from descriptors import ServerSocketDescriptor
from metaclasses import ServerVerifier
from server_DB import ServerStorage

LOGGER = logging.getLogger('server')


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    listen_port = ServerSocketDescriptor()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.listen_port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        # Names and their sockets dict
        self.names = dict()
        super().__init__()

    def init_socket(self):
        LOGGER.info(
            f'Server is launched, connection port: {self.listen_port}, '
            f'connection address: {self.addr}. '
            f'If no address is provided, then any address will be ok.')
        # Initializing sockets
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  ### setting  options for socket
        transport.bind((self.addr, self.listen_port))
        transport.settimeout(0.5)

        # Starting to listen to sockets
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        # Initializing sockets
        self.init_socket()

        # Server programm main cycle
        while True:
            # Waiting for connection; exit if timeout and catching exceptions
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Connection is established with {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Checking for awaiting clients
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # accepting messages and if any errors then excluding the client
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        LOGGER.info(f'Client {client_with_message.getpeername()} disconnected from server.')
                        self.clients.remove(client_with_message)

            # If any messages, processing each one
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except Exception as e:
                    LOGGER.info(f'Connection with client '
                                f'{message[DESTINATION]} was lost, '
                                f' error {e}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and \
                self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(f'A message has been sent to user {message[DESTINATION]} '
                        f'from user {message[SENDER]}.')
        elif message[DESTINATION] in self.names \
                and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            LOGGER.error(
                f'User {message[DESTINATION]} is not registered'
                f'from server, sending a message is impossible.')

        # Client messages processor, accepts a dictionary - a message from client,
        # checks it correctness, sends a report-dictionary if necassary.

    def process_client_message(self, message, client):
        LOGGER.debug(f'Analysing clinet meesage : {message}')
        # If this message about presence, then accept and reply
        if ACTION in message and message[ACTION] == PRESENCE \
                and TIME in message and USER in message:
            # If such user is not registered, then register,
            # otherwise send a reply and closing connection.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'User name unavaliable.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # If this message, then adding it to message que. Reply not needed.
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # If client exits
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        # Otherwise returning Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Incorrect request.'
            send_message(client, response)
            return


def print_help():
    print('Supported commands:')
    print('users - shows users list')
    print('connected - shows users who connected')
    print('loghist - users entrance history')
    print('exit - close server.')
    print('help - show inquiry on suppoerted commands')


def main():
    # Command line arguments launch, if there are no parameters then use defaults
    listen_address, listen_port = arg_parser()


    database = ServerStorage()
    # Creating server class instance.
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()
    # server.main_loop()

    # server main cycle
    while True:
        command = input('Enter command: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            all_users = sorted(database.users_list())
            if all_users:
                for user in all_users:
                    print(f"User {user[0]}, last entered: {user[1]}")
            else:
                print('No data')
        elif command == 'connected':
            active_users = sorted(database.active_users_list())
            if active_users:
                for user in active_users:
                    print(f"User {user[0]}, connected: {user[1]}:{user[2]} , "
                          f"Connected at the following time: {user[3]}")
            else:
                print('No data')
        elif command == 'loghist':
            name = input("Enter username for viewing history."
                         "For viewing your own history press Enter: ")
            history = sorted(database.login_history(name))
            if history:
                for user in sorted(database.login_history(name)):
                    print(f"User: {user[0]}, enterance time: {user[1]}."
                          f"Enter from {user[2]}:{user[3]}")
            else:
                print('No data')
        else:
            print("Unknown command")


if __name__ == '__main__':
    main()
