import configparser
import os
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
import socket
import sys
import os
import argparse
import json
import logging
import select
import time
import threading
import configparser   # https://docs.python.org/3/library/configparser.html
from errors import IncorrectDataRecivedError
from common.variables import *
from common.utils import *
from server_DB import ServerStorage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
LOGGER = logging.getLogger('server')

# Flag, to show that a new user was connected, is needed to ease things up for our db
# and avoid constant requests for refreshing
new_connection = False
conflag_lock = threading.Lock()

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
            except OSError as err:
                LOGGER.error(f'Socket error: {err}')

            # accepting messages and if any errors then excluding the client
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except OSError:
                        # Searching for client in client dict and deleting it from there and from db
                        LOGGER.info(f'Client {client_with_message.getpeername()} disconnected from server.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            # If any messages, processing each one
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    LOGGER.info(
                        f'Connection with client {message[DESTINATION]} was lost')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    # Function that sends a message to an addressed client. Accepts a dict:
    # message, list of registered users список and listening sockets. No return here.
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
        global new_connection
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
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'User name unavaliable.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # If this message, then adding it to message que. Reply not needed.
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(
                message[SENDER], message[DESTINATION])
            return

        # If client exits
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            LOGGER.info(
                f'Client {message[ACCOUNT_NAME]} disconnected from server correctly.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return
        # If it is request of contact list
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        # If it is adding a contact
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # If it is deleting a contact
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # If this is a request of known users
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

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
    # Loading server config file
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Command line arguments launch, if there are no parameters then use defaults
    listen_address, listen_port = arg_parser(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])
    # DB init
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    # Creating server class instance.
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()
    # server.main_loop()

    # Creating graphics environemnt for server:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Initialising window parameters
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # This function, renews list of connected users, check connection flag, and renews list if necessary
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # This function creates window with client stats
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # This function creates window with server settings
    def server_config():
        global config_window
        # Creating window and putting current parameters in it
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # This function saves settings
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Timer to refresh client list 1 time per second
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Linking button t oprocedures
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # launching GUI
    server_app.exec_()

    # server main cycle
    # while True:
    #     command = input('Enter command: ')
    #     if command == 'help':
    #         print_help()
    #     elif command == 'exit':
    #         break
    #     elif command == 'users':
    #         all_users = sorted(database.users_list())
    #         if all_users:
    #             for user in all_users:
    #                 print(f"User {user[0]}, last entered: {user[1]}")
    #         else:
    #             print('No data')
    #     elif command == 'connected':
    #         active_users = sorted(database.active_users_list())
    #         if active_users:
    #             for user in active_users:
    #                 print(f"User {user[0]}, connected: {user[1]}:{user[2]} , "
    #                       f"Connected at the following time: {user[3]}")
    #         else:
    #             print('No data')
    #     elif command == 'loghist':
    #         name = input("Enter username for viewing history."
    #                      "For viewing your own history press Enter: ")
    #         history = sorted(database.login_history(name))
    #         if history:
    #             for user in sorted(database.login_history(name)):
    #                 print(f"User: {user[0]}, enterance time: {user[1]}."
    #                       f"Enter from {user[2]}:{user[3]}")
    #         else:
    #             print('No data')
    #     else:
    #         print("Unknown command")


if __name__ == '__main__':
    main()
