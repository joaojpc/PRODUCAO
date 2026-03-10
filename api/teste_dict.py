# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import cx_Oracle as cxo

def getOracleConnection():
    username = 'mgcustom'
    password = 'supcustom'
    server   = '@192.168.0.8:1521/'
    databaseName = 'megag'
    try:
        conn = cxo.connect(username+'/'+password+server+databaseName)
        #print ('Conectado: \n')
    except cxo.DatabaseError:
        print ('Falha ao conectar no banco de dados: \n')
        exit (1)
    return conn;

class TabPreco:
    def __init__(self):
        #v_params = []
        #v_params.append(pparams)
        #for v_obj in v_params:
        self.pro_pad = 1
            
    def lista_precos(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select det.pro_in_codigo,
                              prod.pro_st_descricao,
                              round(det.prt_re_custo,2)prt_re_custo,
                              det.prt_re_preco,
                              det.tpp_re_vlmoeda            
                         from mgcli.cli_tb_tipoprecodetalhe det,
                              mgadm.est_produtos prod
                        where det.pro_tab_in_codigo = prod.pro_tab_in_codigo
                          and det.pro_pad_in_codigo = prod.pro_pad_in_codigo
                          and det.pro_in_codigo     = prod.pro_in_codigo
                          and det.tpr_pad_in_codigo = :pro_pad                         
                         order by pro_in_codigo''')
        cur.prepare(selectSQL)
        cur.execute(None, {'pro_pad': self.pro_pad})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        json_preco2={}
        for rs in c_rs:
            lista.append(dict(codigo = str(rs[0]),
                              descricao = rs[1],
                              custo = str(rs[2]),
                              preco = str(rs[3]),
                              dolar = str(rs[4])))
            json_preco2.update({"codigo":str(rs[0]),
                              "descricao":rs[1],
                              "custo": str(rs[2]),
                              "preco": str(rs[3]),
                              "dolar": str(rs[4])})
        #print(json_preco2)
        #lista2 = append(lista)        
        json_preco= {}
        json_preco = json.dumps(lista)
        myDictStr = json_preco
        myDictStr2 = myDictStr.replace('"',"'")
        #print(myDictStr2)        
        myDict = {}
        myDict.update({'lista': json_preco})
        mystring = myDict
        #mystring3 = mystring.replace('"','')
        #data = json.loads(mystring)
        #mystring.replace("\","")        
        teste_json = {}
        teste_json = json.dumps(mystring)
        print(teste_json)
        return teste_json        	
        #return teste_json
        
c_ini = TabPreco()
c_ini2 = c_ini.lista_precos()
