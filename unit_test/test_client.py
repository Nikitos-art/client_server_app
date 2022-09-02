import unittest

from client import create_presence, process_ans
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR


class TestClient(unittest.TestCase):
    # общая проверка пристувия
    def test_presense(self):
        presense = create_presence()
        presense[TIME] = 1.1
        self.assertEqual(presense, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: "Guest"}})

    # проверяем 'присутствие' неверного клиента в сети
    def test_wrong_presense(self):
        presense = create_presence()
        presense[TIME] = 1.1
        self.assertNotEqual(presense, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: "Admin"}})

    # Ошибка если действие не изветсно
    def test_no_presense(self):
        presense = create_presence()
        presense[TIME] = 1.1
        self.assertNotEqual(presense, {ACTION: "", TIME: 1.1, USER: {ACCOUNT_NAME: "Guest"}})

    # Ошибка если штамп время отстувиет
    def test_presense_no_time_stamp(self):
        presense = create_presence()
        presense[TIME] = 1.1
        self.assertNotEqual(presense, {ACTION: PRESENCE, TIME: "", USER: {ACCOUNT_NAME: "Guest"}})

    # проверяем 200 от сервера
    def test_ok_ans(self):
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')

    # проверяем 400 от сервера
    def test_not_ok_ans(self):
        self.assertEqual(process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    # def test_no_response(self):
    #     """Тест исключения без поля RESPONSE"""
    #     self.assertRaises(ValueError, process_ans, {ERROR: 'Bad Request'})


if __name__ == "__main__":
    unittest.main()
