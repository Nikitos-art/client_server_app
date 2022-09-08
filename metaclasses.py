import dis
from pprint import pprint


class ClientVerifier(type):
    ### we use __init__ instead of __new__ beacause we don't need to change anything
    def __init__(cls, name, bases, attrsdict):
        methods = []

        for func in attrsdict:
            try:
                ret = dis.get_instructions(attrsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        print(20 * '_', 'methods', 20 * '_')
        pprint(methods)
        print(50 * '_')
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Incorrect socket initialization.')
        super().__init__(name, bases, attrsdict)


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        methods_2 = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods_2:
                            methods_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        # print(20*'-', 'methods', 20*'-')
        # pprint(methods)
        # print(20*'-', 'methods_2', 20*'-')
        # pprint(methods_2)
        # print(20*'-', 'attrs', 20*'-')
        # pprint(attrs)
        # print(50*'-')
        if 'connect' in methods:
            raise TypeError('Method connect is not allowed in server class')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Incorrect socket initialization.')
        super().__init__(clsname, bases, clsdict)

