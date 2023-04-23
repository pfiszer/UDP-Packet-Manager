from multiprocessing import Process, freeze_support, Manager
import socket
import logging


def UDPSocket(sockport, map_ports):
    global m
    # Create a socket
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", sockport))
    print(f"Port: {sockport} is active.", flush=True)
    logging(f"Port: {sockport} is active.")
    while True:
        try:
            message, _ = sock.recvfrom(2048)
            for ip in map_ports[sockport]:
                for port in map_ports[sockport][ip]:
                    sock.sendto(message, (ip, port))
                    logging.debug(f"Message from {sockport} to {ip}:{port}")
        except WindowsError:
            pass
        except Exception as e:
            print(e, flush=True)
            logging.error(e)


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
            logging.debug("Loaded port %s", port)
            del delDict[ip]
            logging.debug(f"Deleted {ip} from {port}")
            map_ports[port] = delDict
            logging.debug(f"New dict for {port}: {delDict}")
        except KeyError:
            pass


def mapPort(fromPort: int, ip: str | None, toPort: int | None):
    global map_ports

    try:
        sharedDict = map_ports[fromPort]
        logging.debug(f"Port {fromPort} extracted")
    except KeyError:
        map_ports[fromPort] = dict()
        sharedDict = map_ports[fromPort]
        logging.debug(f"Port {fromPort} extracted after error")
    if ip == None or toPort == None:
        return

    try:
        sharedDict[ip] += [toPort]
        logging.debug(f"IP {ip} and port {toPort} added to {fromPort}")
    except KeyError:
        try:
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
            logging.debug(
                f"IP {ip} and port {toPort} added to {fromPort} after 1 error")
        except KeyError:
            sharedDict = dict()
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
            logging.debug(
                f"IP {ip} and port {toPort} added to {fromPort} after 2 errors")
    finally:
        map_ports[fromPort] = sharedDict
        logging.debug(f"{fromPort} updated with {sharedDict}")


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """
    manager = Manager()
    map_ports = manager.dict()
    incomingPort = 58212
    dynamicConfig = False
    CONFIG_FILE = []
    logging.basicConfig(filename='latest.log',
                        encoding='utf-8', level=logging.DEBUG, filemode="a", format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S')
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
    logging.info("CONFIG LOADED")
    ''' START PROGRAM '''
    for port in map_ports:
        processess.append(Process(target=UDPSocket, args=[
                          port, map_ports], daemon=True))
        processess[-1].start()
        logging.debug(f"Process for port {port} started.")
    logging.info("Listening processes started.")
    if dynamicConfig:
        ''' Listening for incoming config changes'''
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", incomingPort))
        print(f"Listening for config on port: {incomingPort}.", flush=True)
        logging.info(f"Dynamic config started at port {incomingPort}.")
        while True:
            try:
                message, addr = sock.recvfrom(16)
                ip = addr[0]
                ports = message.decode('utf-8').split('>')
                logging.debug(f"Message: {message} from address {addr}")
                if len(ports) > 1:
                    inPort, outPort = map(int, ports)
                elif ports[0] == "clear":
                    clearIP(ip)
                    print(f"IP address {ip} has been cleared")
                    logging.debug(f"IP address {ip} has been cleared")
                    continue
                else:
                    inPort = outPort = int(ports[0])
                mapPort(inPort, ip, outPort)
                logging.info(f"Port {inPort} mapped to {ip}:{outPort}")
                logging.debug(f"Current dict state: {map_ports}")
            except Exception as e:
                print(e)
                logging.error(e)

    for process in processess:
        process.join()
