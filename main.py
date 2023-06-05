from multiprocessing import Process, freeze_support, Manager
import socket
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info(f"{self.requestline} {self.path} {self.headers._headers}")
        global map_ports
        ports = dict(map_ports)
        match self.path:
            case "/ports":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                res = """<p><a href="/ports">Ports</a> <a href="/logs">Logs</a> <a href="/config">Config</a> <a href="/map-ports">Map Ports</a></p><br><table>
            <tr>
                <th>
                    Input port
                </th>
                <th>
                    IP
                </th>
                <th>
                    Output port
                </th>
            </tr>
            """
                try:
                    for inport in ports:
                        for ip in ports[inport]:
                            for outport in ports[inport][ip]:
                                res += f"""<tr>
                <td>
                    {inport}
                </td>
                <td>
                    {ip}
                </td>
                <td>
                    {outport}
                </td>
            </tr>
            """
                except Exception as e:
                    print(e)
                    res += f"{e}"
                res += "</table>"
                self.wfile.write(bytes(res, "utf-8"))

            case "/logs":
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                with open("latest.log", "r") as res:
                    self.wfile.write(
                        bytes(res.read(), "utf-8"))

            case "/config":
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                with open("UDPSplitter.cfg", "r") as res:
                    self.wfile.write(
                        bytes(res.read(), "utf-8"))

            case "/map-ports":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                res = """<p><a href="/ports">Ports</a> <a href="/logs">Logs</a> <a href="/config">Config</a> <a href="/map-ports">Map Ports</a></p><br><form action="/" method="post">
                    <label for="inport">In Port:</label>
                    <input type="text" id="inport" name="inport"><br>
                    <label for="outport">Out Port:</label>
                    <input type="text" id="outport" name="outport"><br>
                    <input type="submit" value="Submit">
                </form>"""
                self.wfile.write(bytes(res, "utf-8"))

            case "/map-ports-full":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                res = """<p><a href="/ports">Ports</a> <a href="/logs">Logs</a> <a href="/config">Config</a> <a href="/map-ports">Map Ports</a></p><br><form action="/" method="post">
                    <label for="inport">In Port:</label>
                    <input type="text" id="inport" name="inport"><br>
                    <label for="ip">IP:</label>
                    <input type="text" id="ip" name="ip"><br>
                    <label for="outport">Out Port:</label>
                    <input type="text" id="outport" name="outport"><br>
                    <input type="submit" value="Submit">
                </form>"""
                self.wfile.write(bytes(res, "utf-8"))

            case _:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes(
                    '<p><a href="/ports">Ports</a> <a href="/logs">Logs</a> <a href="/config">Config</a> <a href="/map-ports">Map Ports</a></p><br>', "utf-8"))

    def do_POST(self):
        logging.info(f"{self.requestline} {self.path} {self.headers._headers}")
        message = {'inport': None, 'ip': None, 'outport': None}
        length = int(self.headers.get('content-length'))
        for i in self.rfile.read(length).decode('utf-8').split('&'):
            var, val = i.split("=")
            message[var] = val

        try:
            message["inport"] = int(message["inport"])
            message["outport"] = int(message["outport"])
        except:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            res = """<form action="/" method="post">
                    <label for="inport">In Port:</label>
                    <input type="text" id="inport" name="inport"><br>"""
            res += f'<label for="ip">IP:</label><input type="text" id="ip" name="ip" value="{message["ip"]}" placeholder="{message["ip"]}"><br>' if message["ip"] != None else ""
            res += """<label for="outport">Out Port:</label>
                    <input type="text" id="outport" name="outport"><br>
                    <input type="submit" value="Submit">
                </form>"""
            self.wfile.write(bytes(res, "utf-8"))
            return
        if message["ip"] == None:
            message["ip"] = self.client_address[0]

        mapPort(message["inport"], message["ip"], message["outport"])
        self.send_response(302)
        self.send_header('Location', "/ports")
        self.end_headers()


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
        i += 1


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


def saveConfig():
    cfg = f"""maxPacketSize = {maxPacketSize}
## Config for the dynamic config of the ports
incomingPort = {incomingPort}
#dynamicConfig = {dynamicConfig}
#saveConfig = {saveConfig}
#debug = {debug}
~~~MAP PORTS~~~
#Map ports to outgoing ips and ports
#Use template: port_from>ip_to:port_to
"""
    for port in map_ports:
        cfg += f"{port}\n"
        for ip in map_ports[port]:
            for outport in map_ports[port][ip]:
                cfg += f"{port}>{ip}:{outport}\n"
    with open("./UDPSplitter.cfg", "w+") as f:
        f.write(cfg)
    pass


def mapPort(fromPort: int, ip: str | None, toPort: int | None):
    global map_ports

    if ip == None or toPort == None:
        return
    try:
        sharedDict = map_ports[fromPort]
        logging.debug(f"Port {fromPort} extracted")
    except KeyError:
        map_ports[fromPort] = dict()
        sharedDict = map_ports[fromPort]
        logging.debug(f"Port {fromPort} extracted after error")

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
        if saveConfig:
            saveConfig()


freeze_support()


if __name__ == '__main__':
    """ LOAD CONFIG """
    manager = Manager()
    map_ports = manager.dict()
    incomingPort = 53581
    dynamicConfig = False
    debug = False
    maxPacketSize = 2048
    saveConfig = False
    CONFIG_FILE = []
    logging.basicConfig(filename='latest.log', encoding='utf-8', level=logging.DEBUG if debug else logging.INFO, filemode="a", format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    try:
        with open("./UDPSplitter.cfg", 'r') as f:
            CONFIG_FILE = f.readlines()
    except FileNotFoundError:
        with open("./UDPSplitter.cfg", 'w+') as f:
            f.write("""#maxPacketSize = 2048
## Config for the dynamic config of the ports
#incomingPort = 58212
#dynamicConfig = False
#saveConfig = False
#debug = False
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
        elif line.startswith("debugPort="):
            try:
                incomingPort = int(line.split("=")[1])
            except:
                pass
        elif line.startswith("maxPacketSize ="):
            try:
                maxPacketSize = int(line.split("=")[1])
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
        elif line.startswith("saveConfig ="):
            try:
                match line.split("=")[1].strip():
                    case "True":
                        saveConfig = True
                    case "False":
                        saveConfig = False
            except:
                pass
        elif line.startswith("debug ="):
            try:
                match line.split("=")[1].strip():
                    case "True":
                        debug = True
                    case "False":
                        debug = False
            except:
                pass

        elif stage == "mapPORT":
            try:
                fromPort, toIP, toPort = convertConfig(line)
            except:
                continue
            mapPort(fromPort, toIP, toPort)
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.info("CONFIG LOADED")
    print("CONFIG LOADED")

    ''' START PROGRAM '''

    for port in map_ports:
        processess.append(Process(target=UDPSocket, args=[
                          port, map_ports, maxPacketSize], daemon=True))
        processess[-1].start()
        logging.debug(f"Process for port {port} started.")
    logging.info("Listening processes started.")

    if debug:
        webServer = HTTPServer(("0.0.0.0", incomingPort+1), MyServer)
        print(f"Debug on port: {incomingPort}.", flush=True)
        logging.info(f"Debug on port: {incomingPort}.")
        Thread(target=webServer.serve_forever).start()

    if dynamicConfig:

        ''' Listening for incoming config changes'''
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", incomingPort))
        print(f"Listening for config on port: {incomingPort}.", flush=True)
        logging.info(f"Dynamic config started at port {incomingPort}.")

        while True:
            message = ""
            inPort = outPort = None
            try:
                message, addr = sock.recvfrom(16)
                ip = addr[0]
                ports = message.decode('utf-8').split('>')
                logging.debug(f"Message: {message} from address {addr}")
                if len(ports) == 2:
                    inPort, outPort = map(int, ports)
                elif ports[0] == "clear":
                    clearIP(ip)
                    print(f"IP address {ip} has been cleared")
                    message = f"IP address {ip} has been cleared"
                    logging.debug(f"IP address {ip} has been cleared")
                elif ports[0] == "config":
                    try:
                        with open("default_config.txt", "rb") as configFile:
                            message = "⛭" + configFile.read()
                    except:
                        message = "⛭"
                else:
                    inPort = outPort = int(ports[0])
                if inPort not in map_ports and ports[0] not in ["clear", "config"]:
                    message = f"{inPort} is not a valid port"
                    inPort = None
                if None not in [inPort, outPort]:
                    mapPort(inPort, ip, outPort)
                    logging.info(f"Port {inPort} mapped to {ip}:{outPort}")
                    logging.debug(f"Current dict state: {map_ports}")
                    message = f"Port {inPort} mapped to {ip}:{outPort}"
            except ConnectionResetError:
                pass
            except Exception as e:
                print(e)
                logging.error(e)
                message = f"{e}"

            sock.sendto(bytes(message, "utf-8"), addr)
            print(message)
    for process in processess:
        process.join()
