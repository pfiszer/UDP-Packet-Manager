# UDP-Packet-Manager

## **Overview**

This is a simple UDP packet manager to redirect UDP packets to different ports and ips.

## **Config file**

After the first run of the app, the example config file will be created.

```py
#maxPacketSize = 2048
## Config for the dynamic config of the ports
#incomingPort =
#dynamicConfig = False
#saveConfig = False
#debug = False
#debugPort =
#sharedConfigPort =
~~~MAP PORTS~~~
#Map ports to outgoing ips and ports
#Use template: port_from>ip_to:port_to
#161>localhost:616
```


### <ins>**Port Forwarding**</ins>

In order to allow traffic from one port to another add them under the `~~~MAP PORTS~~~` section using the template below. If a port is added, but there is no ip and outgoing port specified, the process for the port will be started, but it will not forward traffic to any other port/ip.

`port_from>ip_to:port_to`

### <ins>**Packet Size**
To specify the maximum packet size, change the `maxPacketSize` value to your desired value.

### <ins>**Dynamic Config**
To allow for better performance and customisation, you can use dynamic config to change which ports are forwarded to you when the `dynamicConfig` is enabled. The server will listen for communication from the client on the `incomingPort`. Only ports activated by the config file will be accepted.

#### <ins>**GUI Client**
To configure your manager instance dynamically you can use the client interface ([`./Client/client.py`] in the source). It will let you connect to the server, save, edit and delete frequently used configurations. Furthermore it will allow you to send a config to the sever without needing to save it using the quick connect button. It will show you which configurations are active, and all communications coming from the server.
\
<ins>Initial screen
\
![First screen](/readme/client1.png)
\
<ins>Screen when successfully connected
\
![Main screen](/readme/client2.png)
\
<ins>Add config popup
\
![Add config popup](/readme/client3.png)
\
<ins>Confirm config deletion
\
![Delete config popup](/readme/client4.png)
\
<ins>Quick connect
\
![Quick connect](/readme/client5.png)
\

##### ***Shared Config***
If you enable the `sharedConfigPort` and set it to a free port, when the client connects and does not have a saved configuration, it will try to connect to the http server to download the default client configuration saved in [`./default_config.json`].

GUI Client config is saved in a JSON file with the following structure:
```json
[
  {
    "name": "Name of the config, displayed in the config list",
    "serverPort": 161, // server port
    "clientPort": 616 // client port
  }
]

```

#### <ins>**Save Config**
If your instance of the program is restarted often, you can save the dynamic configuration if you set the `saveConfig` to `True`.

### <ins>**Debug**
If you set `debug` to `True`, logging level changes to `DEBUG` (default: `INFO`). In addition it allows you to set a `debugPort`, which creates a HTTP server that allows you to view logs, map ports to custom ips, and view the current full configuration. **USE ONLY IF YOU KNOW WHAT YOU'RE DOING**
