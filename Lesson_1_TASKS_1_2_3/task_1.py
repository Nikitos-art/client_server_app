import subprocess
import threading
from pprint import pprint
from subprocess import Popen, PIPE
import platform
import chardet
from ipaddress import ip_address
import os

result = {"Avaliable web resources": '', "Unavaliable web resources": ""}

DNULL = open(os.devnull, 'w')


def host_ping(host):
    """This function checks if given network nodes are avaliable"""
    try:
        ipv4 = ip_address(host)
    except Exception as e:
        ipv4 = host

    param = "-n" if platform.system().lower() == 'windows' else "-c"
    response = subprocess.Popen(["ping", param, "1", str(ipv4)], stdout=subprocess.PIPE)

    if response.wait() == 0:
        result['Avaliable web resources'] += f"{ipv4}\n"
    else:
        result['Unavaliable web resources'] += f"{ipv4}\n"
    return result


if __name__ == "__main__":
    hosts = ['212.58.114.9', '2.3.0.4', 'google.com', 'yandex.ru', '208.67.222.222', '192.168.0.1']
    threads = list()
    for i in hosts:
        x = threading.Thread(target=host_ping, args=(i,), daemon=True)
        threads.append(x)
        x.start()
    for thread in threads:
        thread.join()
    pprint(result)


