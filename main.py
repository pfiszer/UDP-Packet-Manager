import socket


""" LOAD CONFIG """

CONFIG_FILE = []
try:
    with open("./UDPSplitter.cfg", 'r') as f:
        CONFIG_FILE = f.readlines()
except FileNotFoundError:
    with open("./UDPSplitter.cfg", 'w+') as f:
        f.write("""~~~LISTEN IPS~~~
~~~LISTEN PORTS~~~
~~~SEND IPS~~~
~~~MAP PORTS~~~""")
    quit()

listen_ports = []
send_ips = []
map_ports = dict()

stage = None
for line in CONFIG_FILE:
    line = line.replace('\n', "")
    if line.startswith("#"):
        continue
    elif line == "~~~LISTEN PORTS~~~":
        stage = "listenPORT"
    elif line == "~~~SEND IPS~~~":
        stage = "sendIP"
    elif line == "~~~MAP PORTS~~~":
        stage = "mapPORT"
    else:
        match stage:
            case "listenPORT":
                listen_ports.append(line)
            case "sendIP":
                send_ips.append(line)
            case "mapPORT":
                fromPort, toPort = map(int, line.split('>'))
                try:
                    map_ports[fromPort].append(toPort)
                except:
                    map_ports[fromPort] = [toPort]
