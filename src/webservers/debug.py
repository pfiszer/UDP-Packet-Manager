import logging
from http.server import BaseHTTPRequestHandler

from libs.portmapper import mapPort

logger = logging.getLogger('__main__')


class DebugServer(BaseHTTPRequestHandler):
    map_ports = dict()

    def do_GET(self):
        logging.info(f"{self.requestline} {self.path} {self.headers._headers}")
        ports = dict(self.map_ports)
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
                with open("UDPManager.log", "r") as res:
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

        mapPort(message["inport"], message["ip"],
                message["outport"], self.map_ports)
        self.send_response(302)
        self.send_header('Location', "/ports")
        self.end_headers()
