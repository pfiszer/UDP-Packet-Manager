from multiprocessing import Process, freeze_support
import socket
map_ports = dict()


def UDPSocket(sockport, map_ports):
    # Create a socket
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", sockport))
    print(f"Port: {sockport} is active.", flush=True)
    while True:
        try:
            message, _ = sock.recvfrom(2048)
            for ip in map_ports[sockport]:
                sock.sendto(message, (ip, map_ports[sockport][ip]))
        except Exception as e:
            pass


def convertConfig(port_cfg: str):
    inp, out = port_cfg.split(">")
    ip, port = out.split(":")
    return int(inp), ip, int(port)


def mapPort(fromPort: int, ip: str, toPort: int, resetIP=False):
    global map_ports
    if resetIP:
        for port in map_ports:
            try:
                del map_ports[port][ip]
            except KeyError:
                pass
    try:
        map_ports[fromPort][ip] += [toPort]
    except KeyError:
        try:
            map_ports[fromPort][ip] = []
            map_ports[fromPort][ip] += [toPort]
        except KeyError:
            map_ports[fromPort] = dict()
            map_ports[fromPort][ip] = []
            map_ports[fromPort][ip] += [toPort]


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """

    CONFIG_FILE = []
    try:
        with open("./UDPSplitter.cfg", 'r') as f:
            CONFIG_FILE = f.readlines()
    except FileNotFoundError:
        with open("./UDPSplitter.cfg", 'w+') as f:
            f.write("""#Always receives at localhost

~~~MAP PORTS~~~
#Map ports to outgoing ips and ports
#Use template: port_from>ip_to:port_to
8080>localhost:80""")
        quit()

    processess = []

    stage = None
    for line in CONFIG_FILE:
        line = line.replace('\n', "")
        if line.startswith("#") or line == "":
            continue
        elif line == "~~~MAP PORTS~~~":
            stage = "mapPORT"
        elif stage == "mapPORT":
            try:
                fromPort, toIP, toPort = convertConfig(line)
            except:
                continue
            mapPort(fromPort, toIP, toPort)
    ''' START PROGRAM '''
    for port in map_ports:
        processess.append(Process(target=UDPSocket, args=[
                          port, map_ports], daemon=True))
        processess[-1].start()

    for process in processess:
        process.join()
