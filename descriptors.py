

class ServerSocketDescriptor:
    def __get__(self, instance, instance_type):
        return instance.__dict__[self.listen_port]

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError("Port number cannot be negative")
        elif not isinstance(value, int):
            raise ValueError("Port number must be an integer")
        else:
            instance.__dict__[self.listen_port] = value

    def __delete__(self, instance):
        del instance.__dict__[self.listen_port]

    def __set_name__(self, instance_type, listen_port):
        self.listen_port = listen_port
