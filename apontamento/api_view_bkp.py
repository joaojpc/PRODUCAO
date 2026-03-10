# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import requests
from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite, Login_inicial_sqlite
from producao import settings
from datetime import datetime, date, timedelta

from django.utils import timezone

def geturlapi(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/api/'+funcao
    #print (url_principal)
    return url_principal
def geturlapp(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/app/'+funcao
    #print (url_principal)
    return url_principal
def geturl_local(funcao):
    url_local = settings.URL_SQLITE
    url_principal = 'http://'+url_local+'/producao/'+funcao
    #print (url_principal)
    return url_principal

def geturl_producao(funcao):
    url_producao = settings.URL_SQLITE
    url_principal = 'http://'+url_producao+'/prod/'+funcao
    #print (url_principal)
    return url_principal

def geturl_sqlite(funcao):
    url_producao = settings.URL_SQLITE
    url_principal = 'http://'+url_producao+'/app/'+funcao
    #print (url_principal)
    return url_principal
def geturl_api_sqlite(funcao):
    url_producao = settings.URL_SQLITE
    url_principal = 'http://'+url_producao+'/api/'+funcao
    #print (url_principal)
    return url_principal
def trata_data_sqlite(pDATA):
    str_date = pDATA
    if pDATA is not None:
        if pDATA == '0000-00-00':
            date = datetime.strptime('2021-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        else:
            data_arquivo2 = str_date.replace('T',' ')
            str_date = data_arquivo2.replace('Z','')
            date = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
    else:
        date = str_date
    return date

class IntAPI:
    def __init__(self):
        self.equip_logado = 'N'
        self.dbname = 'Producao.db'
        v_lista = Listar_opcoes_sqlite()
        c_controle = json.loads(v_lista.lis_controle_sqlite())
        for v_controle in c_controle:
            self.fil_in = v_controle['eqp_in_filial']
            self.ordem_in = v_controle['ord_in_codigo']
            self.usuario = v_controle['ctl_in_usuario']
            self.seq_controle = v_controle['ctl_in_codigo']
            self.maquina = v_controle['maq_in_codigo']
            self.equip_logado = 'S'
        if (self.equip_logado == 'S'):
            c_operacoes = json.loads(self.operacoes_ordem())
            for v_operacoes in c_operacoes:
                self.pro_in = v_operacoes['pro_in_codigo']
                self.org_in = v_operacoes['org_in_codigo']

    def operacoes_ordem(self):
        self.funcao = 'oper_ordem'
        self.uri = geturlapi(self.funcao)        
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        #print(payload)
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        #print(vRes_json)
        operacoes= {}
        operacoes = json.dumps(vRes_json)
        return operacoes

    def ordem_demandas(self):
        self.funcao = 'get_demandas'
        self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        #print(vresponse.url)
        #print(vRes_json)
        json_demandas= {}
        json_demandas = json.dumps(vRes_json)
        #print(json_demandas)
        return json_demandas

    def listar_ocorencias(self):
        self.funcao = 'listarocorrencias'
        self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_motivos = {}
        json_motivos = json.dumps(vRes_json)
        return json_motivos
    
    def reg_ocorencias(self):
        self.funcao = 'ocorrencias/'
        self.uri = geturl_local(self.funcao)        
        payload = {'ordem': self.ordem_in}
        vresponse = requests.get(self.uri, params=payload)
        #vresponse = requests.get('http://localhost/producao/ocorrencias/?ordem=50602')        
        vRes_json = vresponse.content
        #for resultado in json.loads(vRes_json):
        #    print(resultado['ATI_IN_TEMPO'])                        
        #json_ocorencias = {}
        #json_ocorencias = json.dumps(resultado)
        return vRes_json
    
    def reg_producao(self):
        self.funcao = 'apontamentos/'
        self.uri = geturlapp(self.funcao)
        payload = {'ordem': self.ordem_in}
        vresponse = requests.get(self.uri, params=payload)
        #print(vresponse2.url)
        #vresponse2 = requests.get('http://localhost/producao/apontamentos/?ordem=50602')        
        vRes_json = vresponse.content        
        return vRes_json

    def listar_producao(self,pParams):
        self.funcao = 'apontamentos'
        self.uri = geturlapp(self.funcao)
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_producao= {}
        json_producao = json.dumps(vRes_json)
        return json_producao

    def empenho_demanda(self):
        if settings.GRAVAR_LOCAL:
            self.funcao = 'demandas/'
            self.uri = geturl_local(self.funcao)
        else:
            self.funcao = 'empenhodemandas'
            self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)        
        if settings.GRAVAR_LOCAL:
            #print (vresponse.url)
            vRes_json = vresponse.content
            return vRes_json
        else:
            vRes_json = json.loads(vresponse.content)
            json_baixas= {}
            json_baixas = json.dumps(vRes_json)
            return json_baixas

    def itens_ordem(self):
        self.funcao = 'itensordem'
        self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_baixas= {}
        json_baixas = json.dumps(vRes_json)
        return json_baixas

    def itens_referencia(self):
        self.funcao = 'listareferencias'
        self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_baixas= {}
        json_baixas = json.dumps(vRes_json)
        return json_baixas

    def itens_atributo(self):
        self.funcao = 'listaatributos'
        self.uri = geturlapi(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_baixas= {}
        json_baixas = json.dumps(vRes_json)
        return json_baixas
    
    def gravar_ocorrencia(self,v_params):
        funcao = 'ocorrencias'
        #print('Passou aqui linha 160')

        api_ocorrencia = geturl_local(funcao)
        c_lista = []
        c_lista.append(v_params[0])
        c_lista.append(v_params[1])
        c_lista.append(v_params[2])        
        v_iniseq = Listar_opcoes_sqlite()
        c_seqati = json.loads(v_iniseq.seq_ocor_sqlite())
        for r_seq in c_seqati:
            c_lista.append(r_seq['sequencia'])
            c_lista.append(r_seq['usuario'])
            c_lista.append(r_seq['ordem'])
        dados = {u'ATI_IN_ORDEM': 50602, u'ATI_IN_CODIGO': 103, u'ATI_DT_INCLUSAO': '2019-12-16 15:49:08', u'ATI_IN_TEMPO': 4, u'ATI_IN_SEQUENCIA': 111, u'ATI_USU_INCLUSAO': u'0000041873'}
        '''dados = {"ATI_IN_SEQUENCIA": c_lista[3],
                            "ATI_IN_CODIGO": c_lista[0],
                            "ATI_DT_INCLUSAO": c_lista[2],
                            "ATI_USU_INCLUSAO": c_lista[4],
                            "ATI_IN_ORDEM": c_lista[5],
                            "ATI_IN_TEMPO": c_lista[1]}'''
        response = requests.post('http://192.168.0.250/producao/ocorrencias', dados)
