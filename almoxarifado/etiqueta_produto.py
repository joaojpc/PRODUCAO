# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import  socket
import os
import json

from django.template.defaultfilters import upper


class gera_etiqueta:
    def __init__(self):
        self.v_texto1 = None
        self.v_texto2 = None
        self.imprimir = True
    def trata_None(self, param):
        if not (param is None):
            retorno = param
        else:
            retorno =''
        return retorno
    def etiqueta_item(self,pparams):
        label5 = None
        v_id_item = pparams[2]
        v_descr = pparams[3]
        label5 = r'^XA'+'\n'
        label5 += r'^MMT'+'\n'
        label5 += r'^CI28'+'\n'
        label5 += r'^PW799'+'\n'
        label5 += r'^LL0144'+'\n'
        #margem largura
        label5 += r'^LS0'+'\n'
        #Margem altura
        label5 += r'^LT15'+'\n'
        label5 += r'^FT16,12^A0N,28,32^FH\^FD'+v_descr+'^FS'+'\n'
        label5 += r'^BY2,3,72'+'\n'
        label5 += r'^FO20,25^BCN,N,N,N^FD'+v_id_item+'^FS'+'\n'
        label5 += r'^FT120,119^A0N,23,28^FH\^FD'+v_id_item+'^FS'+'\n'
        label5 += r'^PQ1,0,1,Y^XZ'+'\n'
        v_print = upper(label5)
        #print(v_print)
        if self.imprimir:
            try:
                TCP_IP = '192.168.1.192'
                TCP_PORT = 9100
                BUFFER_SIZE = 1024
                #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #s.connect((TCP_IP, TCP_PORT))
                mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                host = "192.168.1.192"
                port = 9100
                zpl = """
                        ^XA
                        ^FO150,40^BY3
                        ^BCN,110,Y,N,N
                        ^FD123456^FS
                        ^XZ
                        """
                try:
                    mysocket.connect((host, port))
                    #connecting to host
                    mysocket.send(bytes(v_print, "utf-8"))
                except:
                    pass
                s.close()
            except:
                pass
    def etiqueta_Operador(self,pparams):
        label5 = None
        v_id_item = pparams[2]
        v_descr = pparams[3]
        label5 = r'^XA'+'\n'
        label5 += r'^MMT'+'\n'
        label5 += r'^CI28'+'\n'
        label5 += r'^PW799'+'\n'
        label5 += r'^LL0144'+'\n'
        #margem largura
        label5 += r'^LS0'+'\n'
        #Margem altura
        label5 += r'^LT15'+'\n'
        #label5 += r'^FT16,12^A0N,28,32^FH\^FD'+v_descr+'^FS'+'\n'
        label5 += r'^BY2,3,72'+'\n'
        label5 += r'^FO20,25^BCN,N,N,N^FD'+v_id_item+'^FS'+'\n'
        label5 += r'^FT120,119^A0N,23,28^FH\^FD'+v_id_item+'^FS'+'\n'
        label5 += r'^PQ1,0,1,Y^XZ'+'\n'
        v_print = upper(label5)
        #print(v_print)
        if self.imprimir:
            try:
                TCP_IP = '192.168.1.211'
                TCP_PORT = 9100
                BUFFER_SIZE = 1024
                #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #s.connect((TCP_IP, TCP_PORT))
                mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                host = "192.168.1.192"
                port = 9100
                zpl = """
                        ^XA
                        ^FO150,40^BY3
                        ^BCN,110,Y,N,N
                        ^FD123456^FS
                        ^XZ
                        """
                try:
                    mysocket.connect((host, port))
                    #connecting to host
                    mysocket.send(bytes(v_print, "utf-8"))
                except:
                    pass
                s.close()
            except:
                pass
