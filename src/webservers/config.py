import logging
import json
import os
from http.server import BaseHTTPRequestHandler

from libs.portmapper import mapPort, clearIP

logger = logging.getLogger(__name__)


class ConfigServer(BaseHTTPRequestHandler):
    map_ports = dict()

    def do_GET(self):
        ip = self.client_address[0]
        if os.path.exists("port_names.json"):
            with open("port_names.json", "r", encoding="utf-8") as configFile:
                port_names = json.loads(configFile.read())
        else:
            port_names = {}
        match self.path:
            case "/connect":
                try:
                    # Swap ports and names around for the client
                    message = json.dumps(
                        dict((v, int(k)) for k, v in port_names.items())).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                except Exception as e:
                    logger.error(e)
                    self.send_response(500)
                    message = b""
                self.end_headers()
                self.wfile.write(message)
                logger.info(f"{ip} connected to the server")
            case "/active":
                active = []
                for port in self.map_ports:
                    if ip in self.map_ports[port]:
                        for _outPort in self.map_ports[port][ip]:
                            if f"{port}" in port_names.keys():
                                active.append(
                                    (port_names[f"{port}"], _outPort))
                            else:
                                active.append((f"{port}", _outPort))

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                self.wfile.write(json.dumps(active).encode("utf-8"))
        return

    def do_POST(self):
        ip = self.client_address[0]
        print(ip)
        match self.path:
            case "/clear":
                clearIP(ip, self.map_ports)
                message = f"IP address {ip} has been cleared"
                logger.info(f"IP address {ip} has been cleared")
            case "/forward":
                request = json.loads(self.rfile.read(
                    int(self.headers.get('content-length'))).decode('utf-8'))
                mapPort(request["inPort"], ip,
                        request["outPort"], self.map_ports)
                logger.info(
                    f'ort {request["inPort"]} mapped to {ip}:{request["outPort"]}')
                logger.debug(f'Current dict state: {self.map_ports}')
                message = f'Port {request["inPort"]} mapped to {ip}:{request["outPort"]}'
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
        return
