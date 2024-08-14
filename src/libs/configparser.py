import logging

logger = logging.getLogger('__main__')


def parse(configFile: dict[str]):
    config = {"ports": [],
              "debug": False,
              "debugPort": None,
              "maxPacketSize": None,
              "dynamicConfig": False,
              "dynamicConfigPort": None,
              "saveConfig": False}
    for line in configFile:
        line = line.replace('\n', "")
        line = line.replace(" ", '')
        if line.startswith("#") or line == "":
            continue

        elif line.startswith("debugPort="):
            try:
                config["debugPort"] = int(line.split("=")[1])
            except:
                pass
        elif line.startswith("maxPacketSize="):
            try:
                config["maxPacketSize"] = int(line.split("=")[1])
            except:
                pass
        elif line.startswith("dynamicConfig="):
            try:
                match line.split("=")[1].strip().lower():
                    case "true":
                        config["dynamicConfig"] = True
                    case "false":
                        config["dynamicConfig"] = False
            except:
                pass
        elif line.startswith("dynamicConfigPort="):
            try:
                config["dynamicConfigPort"] = int(line.split("=")[1])
            except:
                pass
        elif line.startswith("saveConfig="):
            try:
                match line.split("=")[1].strip().lower():
                    case "true":
                        config["saveConfig"] = True
                    case "false":
                        config["saveConfig"] = False
            except:
                pass
        elif line.startswith("debug="):
            try:
                match line.split("=")[1].strip().lower():
                    case "true":
                        config["debug"] = True
                    case "false":
                        config["debug"] = False
            except:
                pass

        else:
            try:
                config["ports"].append((convertConfig(line)))
            except Exception:
                continue

    logger.setLevel(logging.DEBUG if config["debug"] else logging.INFO)
    logger.info("CONFIG LOADED")
    logger.debug("DEBUG ENABLED")
    return config


def convertConfig(port_cfg: str):
    cfg = port_cfg.split(">")
    if len(cfg) == 1:
        return int(cfg[0]), None, None
    ip, port = cfg[1].split(":")
    return int(cfg[0]), ip, int(port)
