import socket
import sys
import argparse
import logging
import select
import log.log_configs.server_log_config
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME, USER, \
    ACCOUNT_NAME, SENDER, PRESENCE, ERROR, MESSAGE, MESSAGE_TEXT, RESPONSE_200, RESPONSE_400, DESTINATION, \
    EXIT
from common.utils import get_message, send_message
from decorators import log

LOGGER = logging.getLogger('server')


class Server:
    def __init__(self):
        self.listen_socks = None
        self.message = None
        self.messages_list = None
        self.client = None
        self.clients = None
        self.names = None

    @log
    def process_client_message(self, message, messages_list, client, clients, names):
        self.message = message
        self.messages_list = messages_list
        self.client = client
        self.clients = clients
        self.names = names

        LOGGER.debug(f'Client message parse : {message}')
        # If this message about presence then accept and reply if success
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message:
            # If no such user then register this user. Otherwise, reply and disconnect.
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'User with this name already exists.'
                send_message(client, response)
                clients.remove(client)
                client.close()
            return

        # If this message, then add it to que. Reply not needed.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            messages_list.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            clients.remove(names[message[ACCOUNT_NAME]])
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return
        # Otherwise Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request.'
            send_message(client, response)
            return

    @log
    def process_message(self, message, names, listen_socks):
        """
        Function sends addressed message to a specific client. Receives dictionary reply,
        list of registered users and listens to sockets. Doesn't return anything.
        """
        self.message = message
        self.names = names
        self.listen_socks = listen_socks

        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
            send_message(names[message[DESTINATION]], message)
            LOGGER.info(f'Message has been sent to {message[DESTINATION]} '
                        f'from {message[SENDER]}.')
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            LOGGER.error(
                f'User {message[DESTINATION]} is not registerd on the server, '
                f'sending a message is forbidden.')

    @log
    def arg_parser(self):
        """Command line argumets parser"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-a', default='', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        listen_address = namespace.a
        listen_port = namespace.p

        # check correct port
        if not 1023 < listen_port < 65536:
            LOGGER.critical(
                f'Attempt launch server with incorrect port number '
                f'{listen_port}. Allowed ports from 1024 to 65535.')
            sys.exit(1)

        return listen_address, listen_port

    def main(self):
        """Comand line argumets launch, if no parameters, then default values are set"""
        listen_address, listen_port = self.arg_parser()

        LOGGER.info(
            f'Server is launched, connection port: {listen_port}, '
            f'address that receives connections: {listen_address}. '
            f'if no address is given, then any address will be ok.')

        # Getting sockets ready
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)

        # client list, message que
        clients = []
        messages = []

        # Dictionary containing users' names and their sockets.
        names = dict()

        # Listening port
        transport.listen(MAX_CONNECTIONS)
        # Server programm main cycle
        while True:
            # Waiting for connection, if timeout then exit, catching an exception.
            try:
                client, client_address = transport.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Established connection with client {client_address}')
                clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Checking for waiting clients
            try:
                if clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
            except OSError:
                pass

            # receiving messages and if there are messages there then
            # we put them in a dictionary, if error, excluding the client.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    messages, client_with_message, clients, names)
                    except Exception:
                        LOGGER.info(f'Client {client_with_message.getpeername()} '
                                    f'disconnected from server.')
                        clients.remove(client_with_message)

            # If there are messages to send and awating clients then send them message.
            for message in messages:
                try:
                    self.process_message(message, names, send_data_lst)
                except Exception:
                    LOGGER.info(f'Connection with client {message[DESTINATION]} was lost')
                    clients.remove(names[message[DESTINATION]])
                    del names[message[DESTINATION]]
            messages.clear()


if __name__ == '__main__':
    Server()
