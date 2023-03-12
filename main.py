import socket
from multiprocessing import Process


def UDPSocket(sockport):
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", sockport))
    while True:
        try:
            message, _ = sock.recvfrom(2048)
            print(message)
            for ip in send_ips:
                for port in map_ports[sockport]:
                    sock.sendto(message, (ip, port))
        except Exception as e:
            print(e)


""" LOAD CONFIG """

CONFIG_FILE = []
try:
    with open("./UDPSplitter.cfg", 'r') as f:
        CONFIG_FILE = f.readlines()
except FileNotFoundError:
    with open("./UDPSplitter.cfg", 'w+') as f:
        f.write("""~~~SEND IPS~~~
~~~MAP PORTS~~~""")
    quit()

send_ips = []
map_ports = dict()
processess = []

stage = None
for line in CONFIG_FILE:
    line = line.replace('\n', "")
    if line.startswith("#"):
        continue
    elif line == "~~~SEND IPS~~~":
        stage = "sendIP"
    elif line == "~~~MAP PORTS~~~":
        stage = "mapPORT"
    else:
        match stage:
            case "sendIP":
                send_ips.append(line)
            case "mapPORT":
                fromPort, toPort = map(int, line.split('>'))
                try:
                    map_ports[fromPort].append(toPort)
                except:
                    map_ports[fromPort] = [toPort]

for port in map_ports:
    processess.append(Process(target=UDPSocket, args=[port], daemon=True))
    processess[-1].run()
