import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class ConfigServer(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            with open("default_config.json", "rb") as configFile:
                message = configFile.read()
        except:
            message = b""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(message)
