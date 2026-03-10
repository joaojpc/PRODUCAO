# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket

def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip

test = getEnderIP()
print(test)
