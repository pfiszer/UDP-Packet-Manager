import socket
from multiprocessing import Process, freeze_support
freeze_support()


def UDPSocket(sockport):
    # Create a socket
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", sockport))
    print(f"Port: {sockport} is active.", flush=True)
    while True:
        try:
            message, _ = sock.recvfrom(2048)
            for ip in send_ips:
                for port in map_ports[sockport]:
                    sock.sendto(message, (ip, port))
        except Exception as e:
            pass


if __name__ == '__main__':
    """ LOAD CONFIG """

    CONFIG_FILE = []
    try:
        with open("./UDPSplitter.cfg", 'r') as f:
            CONFIG_FILE = f.readlines()
    except FileNotFoundError:
        with open("./UDPSplitter.cfg", 'w+') as f:
            f.write("""#Always receives at localhost
~~~SEND IPS~~~
#Add ip addresses where to send traffic
#DO NOT add quotes or any unrelated characters
localhost
~~~MAP PORTS~~~
#Add port mappings for the program
#Use template: port_from>port_to
8080>80""")
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
        processess[-1].start()

    for process in processess:
        process.join()
