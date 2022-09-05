import subprocess
import threading
from ipaddress import ip_network, ip_address
from pprint import pprint
# from sys import platform
import platform
from tabulate import tabulate
from termcolor import colored

DICTS_LIST = []


def subnetting(ipv4_network_range):
    """This function gets hosts from the network object"""
    SUBNET = ip_network(ipv4_network_range, strict=False)
    ips = [str(ip) for ip in SUBNET.hosts()]
    return ips


def host_range_ping(host):
    """This function checks if given network nodes are avaliable"""
    try:
        ipv4 = ip_address(host)
    except Exception as e:
        pass
    else:
        ipv4 = host
    param = "-n" if platform.system().lower() == 'windows' else "-c"
    response = subprocess.Popen(["ping", param, "1", str(ipv4)], stdout=subprocess.PIPE)
    if response.wait() == 0:
        DICTS_LIST.append({"Avaliable subnets": ipv4})
    else:
        DICTS_LIST.append({"Unavaliable subnets": ipv4})


if __name__ == "__main__":
    ip_range = '208.67.222.222/28'
    subnets = subnetting(ip_range)
    threads = list()
    for ip in subnets:
        x = threading.Thread(target=host_range_ping, args=(ip,), daemon=True)
        threads.append(x)
        x.start()
    for index, thread in enumerate(threads):
        thread.join()
    pprint(tabulate(DICTS_LIST, headers='keys', tablefmt="pipe"))

