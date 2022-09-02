import unittest
import sys
import os
# sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from server_select import process_client_message


class TestServer(unittest.TestCase):
    err_dict = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }
    ok_dict = {RESPONSE: 200}

    # проверка на бездействие
    def test_no_action(self):
        self.assertEqual(process_client_message(
            {TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    # проверка на правильность действия
    def test_wrong_action(self):
        self.assertEqual(process_client_message(
            {ACTION: 'Wrong', TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    # проверка штампа времени
    def test_no_time(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.err_dict)

    # проверка есть ли пользователь
    def test_no_user(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1}), self.err_dict)

    # Проверка имени пользователя
    def test_unknown_user(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Admin'}}), self.err_dict)

    # Ошибка если имя пользователя не введено
    def test_empty_string_user(self):
        self.assertNotEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: ''}}), self.ok_dict)

    # Ошибка если за место имени пользователя введено число
    def test_user_digits(self):
        self.assertNotEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 123}}), self.ok_dict)

    # Ошибка если дейсвие не известно
    def test_no_presense_user(self):
        self.assertNotEqual(process_client_message({ACTION: "", TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}),
                            self.ok_dict)

        # # Проверка запроса на корректность
        # def test_ok_check(self):
        #     self.assertEqual(process_client_message(
        #         {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.ok_dict)

        if __name__ == '__main__':
            unittest.main()
