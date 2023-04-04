from multiprocessing import Process, freeze_support, Manager
import socket


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
                delDict = map_ports[port]
                del delDict[ip]
                map_ports[port] = delDict
            except KeyError:
                pass
    try:
        sharedDict = map_ports[fromPort]
    except KeyError:
        map_ports[fromPort] = dict()
        sharedDict = map_ports[fromPort]

    try:
        sharedDict[ip] += [toPort]
    except KeyError:
        try:
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
        except KeyError:
            sharedDict = dict()
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
    finally:
        map_ports[fromPort] = sharedDict
        print(map_ports)


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """
    map_ports = Manager().dict()
    incomingPort = 58212
    dynamicConfig = True
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
            mapPort(fromPort, toIP, toPort, True)
        elif line.startswith("incomingPort="):
            try:
                incomingPort = int(line.split("=")[1])
            except:
                pass
    ''' START PROGRAM '''
    for port in map_ports:
        processess.append(Process(target=UDPSocket, args=[
                          port, map_ports], daemon=True))
        processess[-1].start()

    if dynamicConfig:
        ''' Listening for incoming config changes'''
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", incomingPort))
        print(f"Listening for config on port: {incomingPort}.", flush=True)
        while True:
            try:
                message, ip = sock.recvfrom(16)
                print(message, ip)
            except Exception as e:
                pass

    for process in processess:
        process.join()
