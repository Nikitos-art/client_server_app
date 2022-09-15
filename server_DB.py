from pprint import pprint

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime as dt


class ServerStorage:
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = dt.datetime.now()
            self.id = None

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    # Users contacts table
    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Action history table
    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self):
        # Creating our db engine
        # echo=False - turns off sql-inquiry output on screen
        # pool_recycle - by default db connection is cut after 8 idle hours
        # for this not to happen we need to add pool_recycle=7200 (resetting
        #    connection every 2 hours)
        # connect_args={'check_same_thread': False}) avoding collisions
        # while accesing db from different threads: Server class thread and main thread
        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        # Creating MetaData object
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        # Creating users contacts table Создаём
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Creating users history table
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        # Creating tables
        self.metadata.create_all(self.database_engine)

        # Creating mappings. Joining class in ORM with corresponding table
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        # Creating session
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        # If there are any entries in active uses table then they should be deleted
        # When connecting, we also are clearing active useres table
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # Function executes when user enters, writes event of login into db
    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)
        # User table inquiry checks if there is a user with such name already. Name must be unique
        rez = self.session.query(self.AllUsers).filter_by(name=username)

        # If such user already exists in the table, then refresh the time of last login
        if rez.count():
            user = rez.first()
            user.last_login = dt.datetime.now()
        # Otherwise, create such user
        else:
            # Creating self.AllUsers class instance, through which we pass data into the table
            user = self.AllUsers(username)
            self.session.add(user)
            # Commit is needed here to create a new user whose id will be used for adding active users to table
            self.session.commit()
            # Adding to users history
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        # Now active users table entry can be created on the moment of ther login
        # Creating self.ActiveUsers class instance, through whih we pass on data into table
        new_active_user = self.ActiveUsers(user.id, ip_address, port, dt.datetime.now())
        self.session.add(new_active_user)

        # Creating self.LoginHistory class instance, through which we pass on data into table
        history = self.LoginHistory(user.id, dt.datetime.now(), ip_address, port)
        self.session.add(history)

        # Commiting changes
        self.session.commit()

    # This function records users logout
    def user_logout(self, username):
        # Inquiry the user who is disconnecting; receiving entry to table self.AllUsers
        user = self.session.query(self.AllUsers).filter_by(name=username).first()

        # Deleting him from active users table; deleting entry from table self.ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Commiting changes
        self.session.commit()

    # This function registers event of sending a message and writes that to db
    def process_message(self, sender, recipient):
        # Getting receivers and senders ID
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        # Requesting lines from history and increasing counters
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # This function adds contact for user
    def add_contact(self, user, contact):
        # Getting users IDs
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        # Checking if doubles and if one can be created (user field is UNIQUE)
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Creating an object and putting it in db
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # This function removes contact from db
    def remove_contact(self, user, contact):
        # Getting users IDs
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        # Checking if contact can exist (User field is UNIQUE)
        if not contact:
            return

        # Deleting what's needed
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    # This function returns a list of known users from the last entry time
    def users_list(self):
        # Lines inquiry from users table
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login
        )
        # Returning a list of sets
        return query.all()

    # This function returns a list of all active users
    def active_users_list(self):
        # Insquiring connection of tables and forming sets name, addres, port, time.
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        # Returning a list of sets
        return query.all()

    # This function returns login history by each user or all users at once
    def login_history(self, username=None):
        # Inquiring login history
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # If a name was given then filtering by this name
        if username:
            query = query.filter(self.AllUsers.name == username)
        # Returning a list of sets
        return query.all()

    # This function returns users contacts list
    def get_contacts(self, username):
        # Requesting a certaid user
        user = self.session.query(self.AllUsers).filter_by(name=username).one()

        # Requesting its contact list
        query = self.session.query(self.UsersContacts, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        # choosing only users names and returning them
        return [contact[1] for contact in query.all()]

    # This function returns the ammount of messages sent and received
    def message_history(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        # Returning list of tuples
        return query.all()


# Layout
if __name__ == '__main__':
    test_db = ServerStorage()
    # Making the "connection" of users
    test_db.user_login('lily', '192.168.1.4', 8080)
    test_db.user_login('nikita', '192.168.1.5', 8081)
    # Printing out a list of sets of all users
    print(' ---- test_db.active_users_list() ----')
    pprint(test_db.users_list())

    # Printing out a list of sets of active users
    print(' ---- test_db.active_users_list() ----')
    pprint(test_db.active_users_list())

    # Making the "disconnecting" of the user
    test_db.user_logout('client_1')
    # amd prinint out currently active users
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_users_list())

    # Inquirying login history for each user
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.login_history('client_1'))

    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.remove_contact('test1', 'test3')
    test_db.process_message('nikita', 'lily')
    pprint(test_db.message_history())
