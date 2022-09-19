import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('client_dist')


# Choose contact for adding
class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Choose contact for adding:')
        # Delete dialogue, if windwow was cloes before time
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Making this window modal (on top of other windows)
        self.setModal(True)

        self.selector_label = QLabel('Choose contact for adding:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Refresh list', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Add', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        # Filling in possible contacts list
        self.possible_contacts_update()
        # Refresh utton action assingment
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    # Filling in list of possible contacts
    def possible_contacts_update(self):
        self.selector.clear()
        # Sets of all contacts amd clients contacts
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        # Delete ourselves from users list, so we couldn't add outselves
        users_list.remove(self.transport.username)
        # Add list of possible contacts
        self.selector.addItems(users_list - contacts_list)

    # Refreshing table of known users (taking em from server),
    # this content of supposed contacts
    def update_possible_contacts(self):
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Refreshing users list from server is done')
            self.possible_contacts_update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from database import ClientDatabase
    database = ClientDatabase('test1')
    from transport import ClientTransport
    transport = ClientTransport(7777, '127.0.0.1', database, 'test1')
    window = AddContactDialog(transport, database)
    window.show()
    app.exec_()
