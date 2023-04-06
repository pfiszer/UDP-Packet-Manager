from multiprocessing import Process, freeze_support, Manager
import socket


def UDPSocket(sockport, map_ports):
    global m
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
                for port in map_ports[sockport][ip]:
                    sock.sendto(message, (ip, port))
        except WindowsError:
            pass
        except Exception as e:
            print(e, flush=True)


def convertConfig(port_cfg: str):
    cfg = port_cfg.split(">")
    if len(cfg) == 1:
        return int(cfg[0]), None, None
    ip, port = cfg[1].split(":")
    return int(cfg[0]), ip, int(port)


def clearIP(ip: str):
    global map_ports
    for port in map_ports:
        try:
            delDict = map_ports[port]
            del delDict[ip]
            map_ports[port] = delDict
        except KeyError:
            pass


def mapPort(fromPort: int, ip: str | None, toPort: int | None):
    global map_ports

    try:
        sharedDict = map_ports[fromPort]
    except KeyError:
        map_ports[fromPort] = dict()
        sharedDict = map_ports[fromPort]
    if ip == None or toPort == None:
        return

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


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """
    manager = Manager()
    map_ports = manager.dict()
    incomingPort = 58212
    dynamicConfig = False
    CONFIG_FILE = []
    try:
        with open("./UDPSplitter.cfg", 'r') as f:
            CONFIG_FILE = f.readlines()
    except FileNotFoundError:
        with open("./UDPSplitter.cfg", 'w+') as f:
            f.write("""## Always receives at localhost
## Config for the dynamic config of the ports
#incomingPort = 58212
#dynamicConfig = True
~~~MAP PORTS~~~
#Map ports to outgoing ips and ports
#Use template: port_from>ip_to:port_to
#8080>localhost:80""")
        quit()

    processess = []

    stage = None
    for line in CONFIG_FILE:
        line = line.replace('\n', "")
        if line.startswith("#") or line == "":
            continue
        elif line == "~~~MAP PORTS~~~":
            stage = "mapPORT"
        elif line.startswith("incomingPort="):
            try:
                incomingPort = int(line.split("=")[1])
            except:
                pass
        elif line.startswith("dynamicConfig ="):
            try:
                match line.split("=")[1].strip():
                    case "True":
                        dynamicConfig = True
                    case "False":
                        dynamicConfig = False
            except:
                pass
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

    if dynamicConfig:
        ''' Listening for incoming config changes'''
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", incomingPort))
        print(f"Listening for config on port: {incomingPort}.", flush=True)
        while True:
            try:
                message, addr = sock.recvfrom(16)
                ip = addr[0]
                ports = message.decode('utf-8').split('>')
                if len(ports) > 1:
                    inPort, outPort = map(int, ports)
                elif ports[0] == "clear":
                    clearIP(ip)
                    print(f"IP address {ip} has been cleared")
                    continue
                else:
                    inPort = outPort = int(ports[0])
                mapPort(inPort, ip, outPort)
            except Exception as e:
                print(e)

    for process in processess:
        process.join()
