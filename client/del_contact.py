import sys
import logging

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('client_dist')


# Dialgue box for deleting a contact
class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Select contact for deleting:')
        # Delete dialogue, if window is closed beforehand
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Making this window modal
        self.setModal(True)

        self.selector_label = QLabel('Select contact for deleting:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)
        # fill contacts for deleting
        self.selector.addItems(sorted(self.database.get_contacts()))

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from database import ClientDatabase
    database = ClientDatabase('test1')
    window = DelContactDialog(database)
    # with connection contacts are deleted, then added from server
    # thats why for checking add contact manual by ourselves for making a deleteing list
    database.add_contact('test1')
    database.add_contact('test2')
    print(database.get_contacts())
    window.selector.addItems(sorted(database.get_contacts()))
    window.show()
    app.exec_()
