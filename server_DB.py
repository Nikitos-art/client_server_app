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
        # Creating tables
        self.metadata.create_all(self.database_engine)

        # Creating mappings. Joining class in ORM with corresponding table
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)

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

    # Function returns a list of known users from the last entry time
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


# Layout
if __name__ == '__main__':
    test_db = ServerStorage()
    # Making the "connection" of users
    test_db.user_login('client_1', '192.168.1.4', 8080)
    test_db.user_login('client_2', '192.168.1.5', 7777)

    # Printing out a list of sets of active users
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_users_list())

    # Making the "disconnecting" of the user
    test_db.user_logout('client_1')
    # amd prinint out currently active users
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_users_list())

    # Inquirying login history for each user
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.login_history('client_1'))

    # and prining out list of known users
    print(' ---- test_db.users_list() ----')
    print(test_db.users_list())
