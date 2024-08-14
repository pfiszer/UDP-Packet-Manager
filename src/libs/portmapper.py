import logging

logger = logging.getLogger('__main__')


def clearIP(ip: str, map_ports):
    for port in map_ports:
        try:
            delDict = map_ports[port]
            logger.debug("Loaded port %s", port)
            del delDict[ip]
            logger.debug(f"Deleted {ip} from {port}")
            map_ports[port] = delDict
            logger.debug(f"New dict for {port}: {delDict}")
        except KeyError:
            pass


def mapPort(fromPort: int, ip: str | None, toPort: int | None, map_ports, stage=None):

    if (ip == None or toPort == None) and (stage != "config"):
        return

    try:
        sharedDict = map_ports[fromPort]
        logger.debug(f"Port {fromPort} extracted")
    except KeyError:
        map_ports[fromPort] = dict()
        sharedDict = map_ports[fromPort]
        logger.debug(f"Port {fromPort} extracted after error")

    if ip == None or toPort == None:
        return
    try:
        sharedDict[ip] += [toPort]
        logger.debug(f"IP {ip} and port {toPort} added to {fromPort}")
    except KeyError:
        try:
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
            logger.debug(
                f"IP {ip} and port {toPort} added to {fromPort} after 1 error")
        except KeyError:
            sharedDict = dict()
            sharedDict[ip] = []
            sharedDict[ip] += [toPort]
            logger.debug(
                f"IP {ip} and port {toPort} added to {fromPort} after 2 errors")
    finally:
        map_ports[fromPort] = sharedDict
        logger.debug(f"{fromPort} updated with {sharedDict}")


# def saveConfig():
#     cfg = f"""maxPacketSize = {maxPacketSize}
# ## Config for the dynamic config of the ports
# incomingPort = {incomingPort}
# dynamicConfig = {dynamicConfig}
# saveConfig = {save_config}
# debug = {debug}
# debugPort = {debugPort}
# sharedConfigPort = {sharedConfigPort}
# ~~~MAP PORTS~~~
# #Map ports to outgoing ips and ports
# #Use template: port_from>ip_to:port_to
# """
#     for port in map_ports:
#         cfg += f"{port}\n"
#         for ip in map_ports[port]:
#             for outport in map_ports[port][ip]:
#                 cfg += f"{port}>{ip}:{outport}\n"
#     with open("./config.cfg", "w+") as f:
#         f.write(cfg)
#     pass
