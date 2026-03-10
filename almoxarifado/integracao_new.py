#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import requests
import urllib3
import urllib as ul
import cx_Oracle
import time
from datetime import datetime, date, timedelta
import json, requests
from unicodedata import normalize
from dateutil.relativedelta import *
import cx_Oracle as cxo
from api_view_oracle import *
from api_almoxa_oracle import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#from api_view import *
import requests
GRAVAR_LOCAL = True
URL_LOCAL = 'localhost'
URL_REMOTO = '192.168.0.43'
URL_PRODUCAO = '192.168.0.158'
#URL_SQLITE = 'localhost:8000'
URL_SQLITE = '192.168.0.158'

def geturlapp(funcao):
    url_remoto = URL_SQLITE
    url_principal = 'http://'+url_remoto+'/app/'+funcao
    return url_principal
def geturlapi(funcao):
    url_remoto = URL_SQLITE
    url_principal = 'http://'+url_remoto+'/api/'+funcao
    return url_principal
def geturlprod(funcao):
    url_remoto = URL_SQLITE
    url_principal = 'http://'+url_remoto+'/prod/'+funcao
    return url_principal
def geturlest(funcao):
    url_remoto = URL_SQLITE
    url_principal = 'http://'+url_remoto+'/est/'+funcao
    return url_principal

class integrador:
    def __init__(self,pParams):
        self.org_in = pParams[0]
        self.fil_in = pParams[1]
        self.pad_in = pParams[2]
    def Buscar_CentroCusto(self):
        print('Iniciando integração de centro de custos!')
        ini_get = GetDadosProducao()
        c_rs = json.loads(ini_get.get_centro_custos())
        if c_rs:
            for c_a in c_rs:
                funcao = 'centrocustos/'
                get_urlest = geturlest(funcao)
                get_urlest = geturlest(funcao)
                payload = {'id_centrocusto': c_a['CUS_ID_CCUSTO']}
                #Verificar se o Item ainda não foi cadastrado
                c_custo= requests.get(get_urlest, params=payload).json()
                #print(c_a['CUS_ID_CCUSTO'])
                if not c_custo:
                    dados = c_a
                    response = requests.post(get_urlest, data=dados)
                else:
                    pass
                    print(c_a['CUS_ID_CCUSTO'])
        print('Integração de centro de custos finalizada!')
    def Buscar_CadastroProdutos(self,pParam):
        print('Iniciando integração de Itens!')
        ini_get = GetDadosProducao()
        c_rs = json.loads(ini_get.get_CadastroProdutos())        
        if c_rs:
            for c_a in c_rs:
                funcao = 'produtos/'
                get_urlest = geturlest(funcao)
                payload = {'item': c_a['BXI_ID_PRODUTO']}
                #Verificar se o Item ainda não foi cadastrado
                c_prod = requests.get(get_urlest, params=payload).json()                
                if not c_prod:
                    #Grava integração do Item;                    
                    dados = c_a
                    response = requests.post(get_urlest, data=dados)
                else:
                    pass
                    print(c_a['BXI_ID_PRODUTO'])
        print('Integração de Itens finalizada!')
    def Integrarequisicao(self,pParam):
        # Busca requisições em aberto
        print('Iniciando integração de requisições!')
        funcao = 'requisicao/'
        get_urlest = geturlest(funcao)
        payload = {'sequencia':None,'status': 'A'}
        c_req = requests.get(get_urlest, params=payload).json()
        if c_req:
            for v_req in c_req:
                #prepara a integração da requisição
                ini_get = Baixas()                
                #grava a integração da requisição
                c_respReq = json.loads(ini_get.apt_inserirRequisicao(v_req))                
                #faz update no status da requisição
                for v_res in c_respReq:
                    payload = {'requisicao':v_res['req_in_sequencia'],'sequencia':v_res['bxa_in_sequencia'],'status': 'B'}
                    c_encerra = requests.put(get_urlest, data=payload)
        print('Integração de requisições finalizada!')
if __name__ == '__main__':
    contador = 1
    v_params = []
    v_params.append(2)
    v_params.append(3)
    v_params.append(1)
    init = integrador(v_params)
    init.Buscar_CentroCusto()
    init.Buscar_CadastroProdutos(1)
    init.Integrarequisicao(1)
