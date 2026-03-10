# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

#from django.test import TestCase

# Create your tests here.

import socket
import json
import sys
import sqlite3
import cx_Oracle as cxo
import requests

from django.utils import timezone

def getOracleConnection():
    username = 'mgcustom'
    password = 'supcustom'
    server   = '@10.101.235.105:1521/'
    databaseName = 'mega'
    try:
        conn = cxo.connect(username+'/'+password+server+databaseName)
        #print ('Conectado: \n')
    except cxo.DatabaseError:
        print ('Falha ao conectar no banco de dados: \n')
        exit (1)
    return conn;

class IntApi:
    def __init__(self,pparams):
        v_params = []
        v_params.append(pparams)
        for v_obj in v_params:
            self.fil_in = int(v_obj[0])
            self.ordem_in = int(v_obj[1])
        c_operacoes = json.loads(self.operacoes_ordem())
        for v_operacoes in c_operacoes:
            self.pro_in = v_operacoes['pro_in_codigo']
            self.org_in = v_operacoes['org_in_codigo']
    def ord_demandas(self):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.ordem_in,ref_cursor)
        cur.callproc('intprod.apt_intprod.apt_retornademandadisp',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pro_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              mvs_re_quantidade = rs[2],
                              mvs_st_loteforne = rs[3],
                              mvs_st_referenciadesc = rs[4],
                              conversor = float(rs[5]),
                              mvs_st_referencia = rs[6]))
        json_demandas= {}
        json_demandas = json.dumps(lista)
        return json_demandas

if __name__ == '__main__':
    v_params = []
    v_params.append(3)
    v_params.append(56656)
    ini_prod = IntApi(v_params)
    c_ocorrencias = json.loads(ini_prod.itens_ordem())
    print(c_ocorrencias)
