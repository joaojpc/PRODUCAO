# -*- coding: utf-8 -*-
import socket
import threading
import sys
import time
import math

sys.path.append("/opt/pi4j/lib/pi4j-core.jar")
sys.path.append("/opt/pi4j/lib/pi4j-device.jar")
sys.path.append("/opt/pi4j/lib/pi4j-gpio-extension.jar")
sys.path.append("/opt/pi4j/lib/pi4j-encoder-read_final.jar")
sys.path.append("/home/pi/projetos/producao/lib/mysql-connector-java-5.1.46.jar")
sys.path.append("/home/pi/projetos/producao/lib/ojdbc6.jar")


#import com.idp.automacao.GpioListenAllExample as hig
import com.raspoid.examples.GipoTimerExit as hig


class medicoes:
    def __init__(self):        
        self.volta = 0        
    def never_stop(self):        
        lista=[]
        iniciar = hig(1)
        steste = iniciar.main(lista)
        
    def controle(self):
        time_started = time.time()
        X = 30
        t3 = threading.Thread(name='testeLeitura', target=self.never_stop)
        t3.start()
        while True:            
            if time.time() > time_started + X:                
                raise TimeoutException()
                return
        
if __name__ == '__main__':
    init = medicoes()
    init.never_stop()
