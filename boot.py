import network

nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect("unchi", "unchidayo")
