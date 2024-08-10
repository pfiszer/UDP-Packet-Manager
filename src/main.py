from multiprocessing import Process, freeze_support, Manager
import socket
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from http.server import HTTPServer
from threading import Thread

from libs.configparser import parse
from libs.portmapper import mapPort, clearIP
from webservers.debug import DebugServer


def UDPSocket(sockport, map_ports, packetSize):
    # Create a socket
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", sockport))
    print(f"Port: {sockport} is active.", flush=True)
    while True:
        try:
            message, _ = sock.recvfrom(packetSize)
            for ip in map_ports[sockport]:
                for port in map_ports[sockport][ip]:
                    sock.sendto(message, (ip, port))
        except WindowsError:
            pass
        except Exception as e:
            print(e, flush=True)


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """
    manager = Manager()
    map_ports = manager.dict()

    config = {
        "debug": False,
        "debugPort": 53582,
        "maxPacketSize": 2048,
        "dynamicConfig": False,
        "dynamicConfigPort": 53581,
        "saveConfig": False}

    # Log to file and terminal
    logger = logging.getLogger(__name__)

    formatter = logging.Formatter(
        '[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger.setLevel(logging.INFO)
    logname = "UDPManager.log"
    file_handler = TimedRotatingFileHandler(
        logname, when="S", interval=30, backupCount=30, encoding='utf-8')
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    term_handler = logging.StreamHandler(
        sys.stdout)
    term_handler.setFormatter(formatter)
    logger.addHandler(term_handler)

    # Load config
    CONFIG_FILE = []
    try:
        with open("./config.cfg", 'r') as f:
            CONFIG_FILE = f.readlines()
    except FileNotFoundError:
        with open("./config.cfg", 'w+') as f:
            f.write("# maxPacketSize = 2048 \n## Dynamic config of ports\n#dynamicConfig = False\n#dynamicConfigPort =\n#saveConfig = False\n#debug = False\n#debugPort =\n#Map ports to outgoing ips and ports\n#Use template: port_from>ip_to:port_to\n#161>localhost:616")
        logger.error("No config found.")
        quit()

    CONFIG = parse(CONFIG_FILE)
    del CONFIG_FILE
    [mapPort(f, i, t, map_ports=map_ports)
     for f, i, t in [j for j in CONFIG["ports"]]]

    processess = []

    ''' START PROGRAM '''

    for port in map_ports:
        processess.append(Process(target=UDPSocket, args=[
                          port, map_ports, CONFIG["maxPacketSize"] if CONFIG["maxPacketSize"] else config["maxPacketSize"]], daemon=True))
        processess[-1].start()
        logger.debug(f"Process for port {port} started.")
    logger.info("Listening processes started.")

    if CONFIG["debug"]:
        webServer = HTTPServer(("0.0.0.0", CONFIG["debugPort"]), DebugServer)
        logger.info(f'Debug on port: {CONFIG["debugPort"]}.')
        Thread(target=webServer.serve_forever, daemon=True).start()

    if CONFIG["dynamicConfig"]:
        cfgServer = HTTPServer(
            ("0.0.0.0", CONFIG["sharedConfigPort"]), ConfigServer)
        logger.info(f'Client config on port: {CONFIG["sharedConfigPort"]}.')
        Thread(target=cfgServer.serve_forever, daemon=True).start()

        ''' Listening for incoming config changes'''
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", CONFIG["sharedConfigPort"]))
        logger.info(
            f'Dynamic config started at port {CONFIG["sharedConfigPort"]}.')

        while True:
            message = ""
            inPort = outPort = None
            try:
                message, addr = sock.recvfrom(16)
                ip = addr[0]
                ports = message.decode('utf-8').split('>')
                logger.debug(f"Message: {message} from address {addr}")
                if len(ports) == 2:
                    inPort, outPort = map(int, ports)
                elif ports[0] == "clear":
                    clearIP(ip, map_ports)
                    message = f"IP address {ip} has been cleared"
                    logger.debug(f"IP address {ip} has been cleared")
                elif ports[0] == "config":
                    message = f'⛭{CONFIG["sharedConfigPort"]}' if CONFIG["sharedConfigPort"] != None else "⛭"
                elif ports[0] == "connect":
                    message = "connected"
                elif ports[0] == "active":
                    message = "|"
                    for port in map_ports:
                        if ip in map_ports[port]:
                            for _outPort in map_ports[port][ip]:
                                message += f"{port}>{_outPort}|"
                else:
                    inPort = outPort = int(ports[0])
                if inPort not in map_ports and ports[0] not in ["clear", "config", "connect", "active"]:
                    message = f"{inPort} is not a valid port"
                    inPort = None
                if None not in [inPort, outPort]:
                    mapPort(inPort, ip, outPort)
                    logger.info(f"Port {inPort} mapped to {ip}:{outPort}")
                    logger.debug(f"Current dict state: {map_ports}")
                    message = f"Port {inPort} mapped to {ip}:{outPort}"
            except ConnectionResetError:
                pass
            except Exception as e:
                logger.error(e)
                message = f"{e}"

            sock.sendto(bytes(message, "utf-8"), addr)
            print(message)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        quit()
