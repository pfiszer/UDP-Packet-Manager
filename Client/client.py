from nicegui import app, ui, Client
from threading import Thread
import socket
from random import randint
import requests
import time
import json
import asyncio
app.native.window_args['resizable'] = True
app.native.start_args['debug'] = False


try:
    ipcfg = open("./startupcfg","r+")
    ip, port = ipcfg.read().split("|")
    port = int(port)

except Exception as e:
    ipcfg = open("./startupcfg","w")
    ip = ""
    port = 0

cfgJSON = []
cfg = {}

def setIP(text):
    global ip
    ip = text


def setPort(text):
    global port
    try:
        port = int(text)
    except:
        pass

def connect():
    ipcfg.seek(0)
    ipcfg.write(f"{ip}|{port}")
    ipcfg.truncate()
    ui.open("/connection")

buttonCSS = "flex:1;margin:5px;padding-right:10px;padding-left:10px;border:1px solid #BBB; background-color: transparent !important;border-radius:5px;"

ui.query('.nicegui-content').style("align-items:center;")
ui.query('.nicegui-content>div').style("width:50%;height:90vh;")

with ui.element("div").style("display:flex;flex-direction:column;border: 1px white solid; border-radius: 5px; padding: 15px;position: relative;display: flex; flex-direction:column;justify-content: space-evenly;"):
    _ipinp = ui.input(label='IP', placeholder='',
             on_change=lambda e: setIP(e.value))
    _portinp = ui.input(label='Port', placeholder='',
             on_change=lambda e: setPort(e.value),
             validation={
                'Invalid Port': lambda value: value.isdigit(),
                'Port too low': lambda value: value.isdigit() and int(value) > 0,
                'Port too high': lambda value: value.isdigit() and int(value) < 65536
                })
    _ipinp.set_value(ip)
    if port != 0:
        _portinp.set_value(f"{port}")
    with ui.button(on_click=connect).style("padding-right:10px;padding-left:10px;border:1px solid #999; background-color: transparent !important;border-radius:5px;margin-right:10px;margin-left:10px"):
        ui.icon("lan").style("margin-right:5px;")
        ui.label("Connect")


@ui.page("/connection")
async def connection():
    global cfgJSON

    class Request:
        def __init__(self, svPort: int | None | str, cliPort: int | None | str):
            self.svPort = svPort
            self.cliPort = cliPort


        def send(self):
            message = f"{self.svPort}>{self.cliPort}" if self.cliPort is not None else f"{self.svPort}"
            message = message.encode("utf-8")
            sock.sendto(message, (ip,port))
            return True


    def load_config(cfgJSON):
        global cfg
        opts = []
        for entry in cfgJSON:
            name = entry["name"]
            svPort = entry["serverPort"]
            cliPort = entry["clientPort"]
            cfg[name] = Request(svPort,cliPort)
            opts.append(name)
        confs.options = opts
        confs.update()

    def add_option(name,svPort,cliPort):
        global cfg
        global cfgJSON
        changed = False
        for i,opt in enumerate(cfgJSON):
            if opt["name"] == name:
                cfgJSON[i]["serverPort"] = svPort
                cfgJSON[i]["clientPort"] = cliPort
                changed = True
                break
        if not changed:
            cfgJSON.append({"name":name, "serverPort":svPort, "clientPort":cliPort})
        cfg[name] = Request(svPort,cliPort)
        if name not in confs.options:
            confs.options.append(name)
            confs.update()
        with open("config.json", "w") as f:
            f.write(json.dumps(cfgJSON))

        _nameInput.value = ""
        _svportInput.value = ""
        _cliportInput.value = ""
        addOption.close()
    def del_option(name):
        global cfg
        global cfgJSON
        del cfg[name]
        confs.options.remove(name)
        for i,opt in enumerate(cfgJSON):
            if opt["name"] == name:
                cfgJSON.pop(i)
                break
        with open("config.json", "w") as f:
            f.write(json.dumps(cfgJSON))
        delOption.close()


    def listen(socket):
        global cfg
        while True:
            try:
                message, _ = socket.recvfrom(2048)
                msg = message.decode("utf-8")
                if msg.startswith("⛭") and len(msg) > 1:
                    try:
                        response = requests.get(url=f"http://{ip}:{msg[1:]}")
                        if response.status_code == 200:
                            global cfgJSON
                            cfgJSON += response.json()
                            load_config(cfgJSON)
                            with open("./config.json","w") as f:
                                f.write(json.dumps(cfgJSON))
                    except Exception as e:
                        pass
                elif msg.startswith("|"):
                    current.clear()
                    if len(msg) == 1:
                        current.push("None")
                    else:
                        try:
                            msg = msg[1:-1]
                            activePorts = msg.split("|")
                            for _confg in activePorts:
                                _svport, _cliport = _confg.split(">")
                                found = False
                                for _config in cfg:
                                    if str(cfg[_config].svPort)== _svport and str(cfg[_config].cliPort)== _cliport:
                                        found = True
                                        current.push(f"{_config} | {_svport} > {_cliport}")
                                if not found:
                                    current.push(f"{_svport} > {_cliport}")
                        except Exception as e:
                            print(e)
                    continue
                elif msg == "connected":
                    connected.set()
                try:
                    comms.push(msg)
                except:
                    pass
            except:
                pass

    def removeConfirm():
        delOption.open()
        _confirmation.set_text(f"Do you want to delete \"{confs.value}\" ?")

    def quicksend(svPort,cliPort):
        message = f"{svPort}>{cliPort}" if cliPort is not None else f"{svPort}"
        message = message.encode("utf-8")
        sock.sendto(message, (ip,port))
        quickConnect.close()


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    portInc = randint(1, 65535)

    connected = asyncio.Event()



    while True:
        try:
            sock.bind(("0.0.0.0", portInc))
            break
        except:
            portInc = randint(0, 65535)
    Thread(target=listen, args=[sock], daemon=True).start()

    sock.sendto(b'connect',(ip,port))

    await connected.wait()


    ui.query('.nicegui-content').style("align-items:center;")
    ui.query('.nicegui-content>div').style("width:90%;height:90vh;")

    with ui.element("div").style("display:flex;flex-direction:row;border: 1px white solid; border-radius: 5px; padding: 15px;position: relative;display: flex; flex-direction:row"):
        with ui.element("div").style("display:flex;width:60%;height:100%;flex-direction:column;margin:5px"):
            with ui.element("div").style("display:flex;flex-direction:row;flex:1"):
                confs = ui.select([]).style(
                    "flex:14;margin:15px")
                with ui.dialog() as addOption, ui.card().style("max-width: 1000px !important;display:flex,flex-direction:column"):
                    _nameInput = ui.input("Name")
                    _svportInput = ui.input("Server port",
                                            validation={
                        'Invalid Port': lambda value: value.isdigit(),
                        'Port too low': lambda value: value.isdigit() and int(value) > 0,
                        'Port too high': lambda value: value.isdigit() and int(value) < 65536
                        })
                    _cliportInput = ui.input("Client Port",
                                             validation={
                        'Invalid Port': lambda value: value.isdigit(),
                        'Port too low': lambda value: value.isdigit() and int(value) > 0,
                        'Port too high': lambda value: value.isdigit() and int(value) < 65536
                        })
                    with ui.element("div"):
                        with ui.button(on_click=lambda e: add_option(
                            _nameInput.value,_svportInput.value,_cliportInput.value)).style(buttonCSS):
                            ui.icon("add")
                            ui.label("Add")
                        with ui.button(on_click=addOption.close).style(buttonCSS):
                            ui.icon("close")
                            ui.label("Cancel")
                    pass
                with ui.button(on_click=addOption.open).style("flex:1;aspect-ratio:1;padding-right:10px;padding-left:10px;border:1px solid #BBB; background-color: transparent !important;border-radius:5px;margin:15px"):
                    ui.icon("add")

                with ui.dialog() as delOption, ui.card().style("max-width: 1000px !important;display:flex,flex-direction:column"):
                    _confirmation = ui.label()
                    with ui.element("div"):
                        with ui.button(on_click=lambda e: del_option(confs.value)).style(buttonCSS):
                            ui.icon("delete")
                            ui.label("Delete")
                        with ui.button(on_click=delOption.close).style(buttonCSS):
                            ui.icon("close")
                            ui.label("Cancel")

                with ui.button(on_click=removeConfirm).style("flex:1;aspect-ratio:1;padding-right:10px;padding-left:10px;border:1px solid #BBB; background-color: transparent !important;border-radius:5px;margin:15px"):
                    ui.icon("remove")

            with ui.element("div").style("display:flex;flex-direction:row;flex:1"):
                with ui.button(on_click=lambda e: sock.sendto(b'clear',(ip,port))).style(buttonCSS):
                    ui.icon("delete").style("margin-right:5px;")
                    ui.label("Clear")
                with ui.button(on_click=lambda e: cfg[confs.value].send()).style(buttonCSS):
                    ui.icon("add_circle_outline").style("margin-right:5px;")
                    ui.label("Select")

            with ui.dialog() as quickConnect, ui.card().style("max-width: 1000px !important;display:flex,flex-direction:column"):
                    _svportQuickInput = ui.input("Server port",
                                            validation={
                        'Invalid Port': lambda value: value.isdigit(),
                        'Port too low': lambda value: value.isdigit() and int(value) > 0,
                        'Port too high': lambda value: value.isdigit() and int(value) < 65536
                        })
                    _cliportQuickInput = ui.input("Client Port",
                                             validation={
                        'Invalid Port': lambda value: value.isdigit(),
                        'Port too low': lambda value: value.isdigit() and int(value) > 0,
                        'Port too high': lambda value: value.isdigit() and int(value) < 65536
                        })
                    with ui.element("div"):
                        with ui.button(
                            on_click=lambda e: quicksend(_svportQuickInput.value,_cliportQuickInput.value)).style(buttonCSS):
                            ui.icon("send")
                            ui.label("Send")
                        with ui.button(on_click=quickConnect.close).style(buttonCSS):
                            ui.icon("close")
                            ui.label("Cancel")
            with ui.element("div").style("display:flex;flex-direction:row;flex:0.5"):
                with ui.button(on_click=quickConnect.open).style("flex:1;margin:5px;padding-right:10px;padding-left:10px;border:1px solid #BBB; background-color: transparent !important;border-radius:5px;"):
                    ui.icon("cable").style("margin-right:5px;")
                    ui.label("Quick Connect")
                with ui.button(on_click=lambda e: sock.sendto(b'active', (ip,port))).style("flex:1;margin:5px;padding-right:10px;padding-left:10px;border:1px solid #BBB; background-color: transparent !important;border-radius:5px;"):
                    ui.icon("refresh").style("margin-right:5px;")
                    ui.label("Get active connections")
            with ui.element("div").style("display:flex;flex-direction:row;flex:4;border: 1px #BBB solid; border-radius: 5px; padding: 15px;"):
                current = ui.log(max_lines=30).style(
                "width:100%;height:100%;color:#FFF;background-color:transparent;border:transparent")
        with ui.element("div").style("display:flex;width:40%;height:100%;border: 1px #555 solid; border-radius: 5px; padding: 15px;margin:5px"):
            comms = ui.log(max_lines=100).style(
                "width:100%;height:100%;color:#FFF;background-color:transparent;border:transparent")
            pass

    try:
        with open("./config.json", "r") as config:
            cfgJSON += json.loads(config.read())
            load_config(cfgJSON)

    except Exception as e:
        sock.sendto(b'config',(ip,port))

@app.exception_handler(500)
async def exception_handler_500(request, exception):
    with Client(ui.page('')) as client:
        with ui.element("div").classes(
                "bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative").style("flex:1;display:flex;flex-direction:row;height:10vh!important;width:100%"):
            ui.label("COULD NOT CONNECT TO THE SERVER").style(
                "flex: 14;align-self: center")
            with ui.button(on_click=lambda e: ui.open(
                    "/")).style("aspect-ratio:1;flex:1;background-color:#990000!important"):
                ui.icon("close")
    return client.build_response(request, 500)


ui.run(dark=True, native=True, window_size=(1080, 700), fullscreen=False)
