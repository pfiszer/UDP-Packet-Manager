# UDP-Packet-Manager

## Overview

This is a simple UDP packet manager to redirect UDP packets to different ports and ips.

## Config file

After the first run of the app, the config file will be created.

```
#Always receives at localhost
~~~SEND IPS~~~
#Add ip addresses where to send traffic
#DO NOT add quotes or any unrelated characters
localhost
~~~MAP PORTS~~~
#Add port mappings for the program
#Use template: port_from>port_to
8080>80
```

---

In order to send traffic to a specific ip, add it under the `~~~SEND IPS~~~` section.

In order to allow traffic from one port to another add them to the `~~~MAP PORTS~~~` section using the template below.

`from>to`

**NOTE:** You cannot send to a port on localhost that is being used by this application
