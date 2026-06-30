# -*- encoding: utf-8 -*-
# api_producao.py
''' 
Cérebro. Fluxo FK: Busca Pai -> Busca Filhos -> INSERT Oracle -> UPDATE I
'''
import time, fcntl, os
import services
#from __future__ import unicode_literals
import sys
import json
import requests
import urllib3
import urllib as ul
import oracledb as cxo
from oracle_connection import getOracleConnection
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest
from datetime import datetime, date, timedelta
import json, requests
from unicodedata import normalize
from dateutil.relativedelta import *
from typing import List, Tuple
from collections import defaultdict
import services

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
v_dirlog = '/home/admin/prod/log'

GRAVAR_LOCAL = True
URL_LOCAL = 'localhost'
URL_REMOTO = '192.168.0.24'
URL_PRODUCAO = '192.168.0.24'
URL_SQLITE = '127.0.0.1:8000'

def trata_data(pDATA):
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
def trata_data_sqlite(pDATA):
    str_date = pDATA    
    if pDATA is not None:
        if pDATA == '0000-00-00':
            date = datetime.strptime('2021-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        else:            
            data_arquivo2 = str_date.replace('T',' ')
            str_date = data_arquivo2.replace('-03:00','')
            date = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')                                    
    else:
        date = str_date    
    return date

def separa_string(pString, vINI, vFIM):    
    return (pString[vINI:vFIM])

def separa_idordem(pparams):    
    list_ordem = [0,3,10,13]    
    fil_in_codigo = separa_string(pparams,list_ordem[0],list_ordem[1])
    ord_in_codigo = separa_string(pparams,list_ordem[1],list_ordem[2])
    plf_in_sqoperacao = separa_string(pparams,list_ordem[2],list_ordem[3])
    v_retorno =  {'fil_in_codigo':fil_in_codigo,'ord_in_codigo':ord_in_codigo,'plf_in_sqoperacao':plf_in_sqoperacao}
    return v_retorno
    
class integrador:
    def __init__(self,pParams):
        self.org_in = pParams[0]
        self.fil_in = pParams[1]
        self.ord_in = pParams[2]
        self.seq_in = pParams[3]
        self.cmaq_st_id = ''
        self.ord_st_extenso = None
        self.funcao = None
        self.get_urlapi = None
        self.get_urlapp = None
        self.get_urlprod = None
        self.payload = None
        self.row_now = datetime.now()
        self.str_now = self.row_now.strftime('%Y-%m-%d')        
        self.startDate = '2021-04-07'
        vdt_ret_new = self.row_now+relativedelta(days=+1)
        vdt_end = vdt_ret_new.strftime('%Y-%m-%d')        
        self.endDate = self.str_now
        self.grava_api = 'N'
        self.seq_arquivo = 1
    def encerra_ordens(self):
        tem_ordem = 'N'
        tem_demanda = 'N'
        self.funcao = 'controleApt/'
        self.get_urlprod = geturlprod(self.funcao)
        self.payload = {'fil_in_codigo': self.fil_in,'status': 'A'}
        try:
            #Busca os apontamentos em aberto                        
            v_rs = requests.get(self.get_urlprod, params=self.payload, verify=False).json()            
            for rs in v_rs:                                
                #Busca ordens pendentes de integração;
                self.funcao = 'apontamentos/'
                self.get_urlapp = geturlapp(self.funcao)                                
                self.payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
                #print(self.payload)
                try:                    
                    v_ordens = requests.get(self.get_urlapp, params=self.payload, verify=False).json()
                    print(requests.url)
                    if v_ordens:
                        tem_ordem = 'S'
                except:
                    pass
                #print(tem_ordem)
                self.funcao = 'demandas/'
                self.get_urlapp = geturlapp(self.funcao)
                self.payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
                try:
                    v_demanda = requests.get(self.get_urlapp, params=self.payload, verify=False).json()
                    if v_demanda:
                        tem_demanda = 'S'                        
                except:
                    pass
                #print(tem_demanda)
                if (tem_ordem =='N') and(tem_demanda =='N'):
                    self.payload = {'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'E'}
                    c_update = requests.put(self.get_urlprod, params=self.payload, verify=False)    
        except:
            pass                            
        
    def manutencao(self):
        #Busca as ordens pendentes no Mega;
        lista_conv = []
        self.funcao = 'GetOrdensPendentes'
        self.get_urlapi = geturlapi(self.funcao)
        if self.ord_in is None:
            self.payload = {'org_in_codigo': self.org_in}
        else:
            self.payload = {'org_in_codigo': self.org_in,'fil_in_codigo': self.fil_in,'ord_in_codigo': self.ord_in}        
        #try:        
        if 1==1:
            v_response = requests.get(self.get_urlapi, params=self.payload, verify=False).json()
            #Se encontrar ordem pendente segue continua;
            if v_response:
                for ord in v_response:                    
                    #busca dados das Ordens
                    self.funcao = 'GetManProOrdens/'
                    self.get_urlapi = geturlapi(self.funcao)
                    self.payload = {'org_in_codigo': ord['org_in_codigo'],
                                    'ord_seq_in_codigo': ord['ord_seq_in_codigo'],
                                    'ord_in_codigo': ord['ord_in_codigo']}
                    #try:
                    if 1==1:
                        c_getordens = requests.get(self.get_urlapi, params=self.payload).json()                        
                        #Se encontrar a ordem segue adiante;
                        if c_getordens:                            
                            for d_ord in c_getordens:                                
                                c_get_inf = {'umidade': d_ord['ORD_RE_UMIDADE'],'lote_ordem': d_ord['LOTE_ORDEM'],'destino': d_ord['ORD_ST_DESTINO'],'origem': d_ord['ORD_ST_ORIGEM']}                                
                                #Busca demandas da ordem;
                                self.funcao = 'get_demandaordens/'
                                self.get_urlapi = geturlapi(self.funcao)                                
                                c_get_demandas = requests.get(self.get_urlapi, params=self.payload).json()                                
                                #Busca Item da Ordem + Subprodutos;
                                self.funcao = 'itensordem/'
                                self.get_urlapi = geturlapi(self.funcao)
                                self.payload = {'ordem': d_ord['ORD_IN_CODIGO'],'filial': d_ord['FIL_IN_CODIGO']}                                
                                #try:
                                if 1==1:
                                    c_get_itens = requests.get(self.get_urlapi, params=self.payload).json()                                                                
                                    if c_get_itens:
                                        v_dados = {'ORG_TAB_IN_CODIGO':d_ord['ORG_TAB_IN_CODIGO'],
                                                          'ORG_PAD_IN_CODIGO':d_ord['ORG_PAD_IN_CODIGO'],
                                                          'ORG_IN_CODIGO':d_ord['ORG_IN_CODIGO'],
                                                          'ORG_TAU_ST_CODIGO':d_ord['ORG_TAU_ST_CODIGO'],
                                                          'ORD_TAB_IN_CODIGO':d_ord['ORD_TAB_IN_CODIGO'],
                                                          'ORD_SEQ_IN_CODIGO':d_ord['ORD_SEQ_IN_CODIGO'],
                                                          'ORD_IN_CODIGO':d_ord['ORD_IN_CODIGO'],
                                                          'PRO_TAB_IN_CODIGO':d_ord['PRO_TAB_IN_CODIGO'],
                                                          'PRO_PAD_IN_CODIGO':d_ord['PRO_PAD_IN_CODIGO'],
                                                          'PRO_IN_CODIGO':d_ord['PRO_IN_CODIGO'],
                                                          'ORD_RE_QTDE_ORDEM':d_ord['ORD_RE_QTDE_ORDEM'],
                                                          'FIL_IN_CODIGO':d_ord['FIL_IN_CODIGO'],
                                                          'TPO_ST_CODIGO':d_ord['TPO_ST_CODIGO_TIPO'],
                                                          'PRO_ST_ITENS':json.dumps(c_get_itens),
                                                          'PRO_ST_DEMANDAS':json.dumps(c_get_demandas),
                                                          'PRO_ST_INFOADIC':json.dumps(c_get_inf),
                                                          'PRO_ST_ID':d_ord['PRO_ST_ID'],
                                                          'ORD_ST_ID':d_ord['ORD_ST_ID'],
                                                          'TPO_ST_ID':d_ord['TPO_ST_ID']}                                                          
                                        #grava na tabela local => api => models.py man_pro_ordens                                        
                                        self.funcao = 'ordens/'                                        
                                        self.get_urlapp = geturlapp(self.funcao)
                                        self.payload = {'org_in_codigo': ord['org_in_codigo'],
                                                        'ord_seq_in_codigo': ord['ord_seq_in_codigo'],
                                                        'ord_in_codigo': ord['ord_in_codigo']}
                                        #Apaga as ordens
                                        c_verifica = requests.get(self.get_urlapp, params=self.payload).json()
                                        if c_verifica:
                                            c_apagaordem = requests.put(self.get_urlapp, params=self.payload)
                                        c_response = requests.post(self.get_urlapp, data=v_dados)
                                        # faz update nas ordens atualizadas;                                        
                                        v_update_ordem = data = {'ORG_IN_CODIGO': d_ord['ORG_IN_CODIGO'],
                                                                 'ORD_SEQ_IN_CODIGO': d_ord['ORD_SEQ_IN_CODIGO'],
                                                                 'ORD_IN_CODIGO': d_ord['ORD_IN_CODIGO']}
                                        self.funcao = 'GetOrdensPendentes/'
                                        self.get_urlapi = geturlapi(self.funcao)
                                        #do_response = requests.put(self.get_urlapi, data=v_update_ordem)
                                        #Busca Itens da ordem
                                        if c_get_itens:                                            
                                            for d_itens in c_get_itens:                                                
                                                pro_medidas = []
                                                pro_medidas.append(dict(PRO_RE_COMPRIMENTO = d_itens['pro_re_comprimento'],
                                                                        PRO_RE_LARGURA = d_itens['pro_re_largura'],
                                                                        PRO_RE_ESPESSURA = d_itens['pro_re_espessura']
                                                                       ))
                                                funcao = 'get_proconversor/'
                                                payload = {'fil_in_codigo': d_ord['FIL_IN_CODIGO'],'pro_in_codigo':d_itens['pro_in_codigo']}
                                                conv_url = geturlapi(funcao)
                                                pro_conversor =requests.get(conv_url, params=payload).json()
                                                if not(pro_conversor):
                                                    lista_conv = []
                                                    lista_conv.append(dict(CONVERSORES = None,))
                                                    pro_conversor =  json.dumps(lista_conv)
                                                if d_itens['rfc_in_codigo']!=0:
                                                    print('Iniciando')
                                                    #Busca atributos dos Itens
                                                    self.funcao = 'listaatributos/'
                                                    self.get_urlapi = geturlapi(self.funcao)
                                                    self.payload = {'item': d_itens['pro_in_codigo'],'filial': d_ord['FIL_IN_CODIGO']}
                                                    c_get_atrib = requests.get(self.get_urlapi, params=self.payload).json()
                                                    #Busca Características dos Itens
                                                    self.funcao = 'listareferencias/'
                                                    self.get_urlapi = geturlapi(self.funcao)
                                                    c_get_ref = requests.get(self.get_urlapi, params=self.payload).json()
                                                    #grava itens na tabela
                                                    lista_atrb = []
                                                    lista_atrb.append(dict(PRO_ST_ATRIBUTOS = None,))
                                                    lista_ref = []
                                                    lista_ref.append(dict(PRO_ST_REFERENCIA = None,))                                                    
                                                    '''v_dados_produtos = {'PRO_TAB_IN_CODIGO': 100,
                                                                               'PRO_PAD_IN_CODIGO': 312,
                                                                               'PRO_IN_CODIGO': 2,
                                                                               'PRO_ST_DESCRICAO': 'Lamina Torneada Seca de Pinus 1,7mm',
                                                                               'UNI_ST_UNIDADE': 'M3',
                                                                               'RFC_IN_CODIGO': '79',
                                                                               'PRO_ST_ATRIBUTOS': json.dumps(lista_atrb),
                                                                               'PRO_ST_REFERENCIA': json.dumps(lista_ref),
                                                                               'PRO_ST_MEDIDAS': json.dumps(pro_medidas),
                                                                               'MVS_ST_REFERENCIA': 'Indefinido',
                                                                               'PRO_ST_ID': '1003120000002',
                                                                               'PRO_ST_CONVERSOR':json.dumps(lista_conv)}'''
                                                    v_dados_produtos = {'PRO_TAB_IN_CODIGO': d_ord['PRO_TAB_IN_CODIGO'],
                                                                               'PRO_PAD_IN_CODIGO': d_ord['PRO_PAD_IN_CODIGO'],
                                                                               'PRO_IN_CODIGO': d_itens['pro_in_codigo'],
                                                                               'PRO_ST_DESCRICAO': d_itens['pro_st_descricao'],
                                                                               'UNI_ST_UNIDADE': d_itens['uni_st_unidade'],
                                                                               'RFC_IN_CODIGO': d_itens['rfc_in_codigo'],
                                                                               'PRO_ST_ATRIBUTOS': json.dumps(c_get_atrib),
                                                                               'PRO_ST_REFERENCIA': json.dumps(c_get_ref),
                                                                               'PRO_ST_MEDIDAS': json.dumps(pro_medidas),
                                                                               'MVS_ST_REFERENCIA': d_itens['mvs_st_referencia'],
                                                                               'PRO_ST_ID': d_itens['pro_st_id'],
                                                                               'PRO_ST_CONVERSOR':pro_conversor}
                                                    funcao = 'get_referencia/'
                                                    uri = geturlapi(funcao)
                                                    payload = {'filial': d_ord['FIL_IN_CODIGO'], 'referencia': d_itens['rfc_in_codigo']}
                                                    #busca no Mega as caracteristicas vinculadas ao item
                                                    itn_ref = requests.get(uri, params=payload).json()
                                                    if itn_ref:
                                                        for rs in itn_ref:
                                                            funcao = 'referencia/'
                                                            uri = geturlapp(funcao)
                                                            car_st_id = rs.get('CAR_ST_ID')
                                                            payload = {'car_st_id': car_st_id}
                                                            vget = requests.get(uri, params=payload).json()
                                                            if vget:
                                                                pass
                                                            else:
                                                                requests.post(uri, data=rs)                                        
                                                else:
                                                    lista_atrb = []
                                                    lista_atrb.append(dict(PRO_ST_ATRIBUTOS = None,))
                                                    lista_ref = []
                                                    lista_ref.append(dict(PRO_ST_REFERENCIA = None,))
                                                    v_dados_produtos = data = {'PRO_TAB_IN_CODIGO': d_ord['PRO_TAB_IN_CODIGO'],
                                                                               'PRO_PAD_IN_CODIGO': d_ord['PRO_PAD_IN_CODIGO'],
                                                                               'PRO_IN_CODIGO': d_itens['pro_in_codigo'],
                                                                               'PRO_ST_DESCRICAO': d_itens['pro_st_descricao'],
                                                                               'UNI_ST_UNIDADE': d_itens['uni_st_unidade'],
                                                                               'RFC_IN_CODIGO': d_itens['rfc_in_codigo'],
                                                                               'PRO_ST_ATRIBUTOS': json.dumps(lista_atrb),
                                                                               'PRO_ST_REFERENCIA': json.dumps(lista_ref),
                                                                               'PRO_ST_MEDIDAS': json.dumps(pro_medidas),
                                                                               'MVS_ST_REFERENCIA': d_itens['mvs_st_referencia'],
                                                                               'PRO_ST_ID': d_itens['pro_st_id'],
                                                                               'PRO_ST_CONVERSOR':pro_conversor
                                                                               }
                                                #verifica se existe o item cadastrado
                                                print(v_dados_produtos)
                                                self.funcao = 'itensOrdens/'
                                                self.get_urlapp = geturlapp(self.funcao)
                                                self.payload = {'pro_pad_in_codigo': d_itens['pro_pad_in_codigo'],
                                                                'pro_in_codigo': d_itens['pro_in_codigo'],
                                                                'rfc_in_codigo':d_itens['rfc_in_codigo']}
                                                c_appitens = requests.get(self.get_urlapp, params=self.payload).json()
                                                if c_appitens:
                                                    v_delete = requests.delete(self.get_urlapp, data=v_dados_produtos)
                                                respio = requests.post(self.get_urlapp, data=v_dados_produtos)
                                '''except:
                                    pass
                    except:
                        pass
        except:
            print('Não conectado')
            pass'''
    def integraOrdens(self):
        print('Bucando dados de controle')
        #busca Ordens Pendentes
        self.funcao = 'controleApt/'
        print('Linha 319',self.funcao)
        self.get_urlprod = geturlprod(self.funcao)
        if self.ord_in is not None:
            self.payload = {'fil_in_codigo': self.fil_in,'status': 'A', 'ord_in_codigo':self.ord_in}
        else:
            self.payload = {'fil_in_codigo': self.fil_in,'status': 'A'}        
        try:        
        #if 1==1:
            #Busca os apontamentos em aberto                        
            v_rs = requests.get(self.get_urlprod, params=self.payload, verify=False).json() 
            #print('Linha 330', v_rs)
            if v_rs:                
                for rs in v_rs:
                    print("Apontamentos", rs['ORD_IN_CODIGO'])
                    self.ord_in = rs['ORD_IN_CODIGO']
                    self.payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}                
                    #Busca a situação da ordem
                    v_sit = self.situacao_ordem()                    
                    if v_sit == 'EN':
                        print('Ordem encerrada! ',self.ord_in)
                        #Encerra a ordem;
                        self.payload = {'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'E'}
                        c_update = requests.put(self.get_urlprod, params=self.payload, verify=False)
                    else:
                        #print(self.ord_in)
                        self.ord_st_extenso = rs['ORD_ST_EXTENSO']                        
                        v_idordem = separa_idordem(self.ord_st_extenso)                        
                        self.seq_in = int(v_idordem.get('plf_in_sqoperacao'))
                        self.cmaq_st_id = rs['CMAQ_ST_ID']
                        v_dtapontamento = trata_data_sqlite(rs['CTL_DT_LOGIN'])                
                        str_now = v_dtapontamento.strftime('%Y-%m-%d')                
                        #Busca ordens pendentes de integração;
                        self.funcao = 'apontamentos/'
                        self.get_urlapp = geturlapp(self.funcao) 
                        print('Iniciando integração dos lotes!',self.get_urlapp)                                                   
                        try:
                        #if 1==1:
                            v_ordens = requests.get(self.get_urlapp, params=self.payload, verify=False).json()
                            if v_ordens:
                                print('Iniciando integração dos lotes!')
                                for r_ord in v_ordens:
                                    self.cmaq_st_id = r_ord['CMAQ_ST_ID']
                                    v_dadosProd = {'fil_in_codigo': r_ord['FIL_IN_CODIGO'],
                                               'ord_in_codigo': r_ord['ORD_IN_CODIGO'],
                                               'ctl_in_codigo': r_ord['CTL_IN_CODIGO'],
                                               'plf_in_sqoperacao': self.seq_in,
                                               'apt_dt_inclusao': str_now,
                                               'mvp_in_sequencia': r_ord['APT_IN_SEQUENCIA'],
                                               'apt_re_quantidade': r_ord['ORL_RE_QTDLOTE'],
                                               'apt_re_qtdeconvertida': r_ord['PRO_RE_QTDCONV'],
                                               'apt_re_qtderefugo': r_ord['PRO_RE_QTDREFUGO'],
                                               'pro_in_codigo': r_ord['PRO_IN_CODIGO'],
                                               'pro_st_obs': 'Lote integrado pelo ACB',
                                               'pro_st_docorigem': r_ord['PRO_ST_LOTEORI'],
                                               'pro_st_referencia': r_ord['ORL_ST_REFERENCIA'],
                                               'usu_in_codigo': 1,
                                               'pro_st_destino': 'I',
                                               'pro_st_lote': str(r_ord['PRO_ST_LOTE']),
                                               'pro_st_conversor': '0',
                                               'apt_dt_lote': r_ord['APT_DT_APONTAMENTO'],
                                               'cmaq_st_id': self.cmaq_st_id,
                                               'pro_st_id': r_ord['PRO_ST_ID'],
                                               'ord_st_id': r_ord['ORD_ST_ID'],
                                               'orl_re_qtdajustada': r_ord['ORL_RE_QTDAJUSTADA'],
                                               'ord_st_extenso' : rs['ORD_ST_EXTENSO'],
                                               'pro_st_fornecedor': r_ord['PRO_ST_FORNECEDOR']}                        
                                    self.funcao = 'post_producao/'                        
                                    self.get_urlapi = geturlapi(self.funcao)
                                    try:
                                    #if 1==1:
                                        # Grava os dados no Mega
                                        #print('Lote',v_dadosProd)
                                        resp_Prod = json.loads(self.apt_integrarlote(v_dadosProd))
                                        #resp_Prod = requests.post(self.get_urlapi, data=v_dadosProd).json()
                                        if resp_Prod:
                                            for rs_prod in resp_Prod:
                                                #(rs_prod)
                                                if (rs_prod['mensagem'] == 'Ok') and (rs_prod['mensagem_sub'] == 'Ok'):
                                                    #faz Update da transação da ordem;
                                                    self.funcao = 'apontamentos/'
                                                    self.get_urlapp = geturlapp(self.funcao)
                                                    self.payload = {'ctl_in_codigo': r_ord['CTL_IN_CODIGO'],'sequencia': r_ord['APT_IN_SEQUENCIA'],'status': 'I'}
                                                    c_update_prod = requests.put(self.get_urlapp, params=self.payload, verify=False)
                                    except:
                                        pass                                            
                        except:
                            pass
                        #busca demandas pendentes de integração para a ordem.                
                        self.funcao = 'demandas/'
                        self.get_urlapp = geturlapp(self.funcao)
                        self.payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
                        try:
                        #if 1==1:
                            v_demanda = requests.get(self.get_urlapp, params=self.payload, verify=False).json()
                            if v_demanda:
                                print('linha 403 => Iniciando integração das demandas!')
                                for r_dem in v_demanda:
                                    #print(f'linha 405 => Dados da demanda: {r_dem}')
                                    v_dadosDem = {'fil_in_codigo': r_dem['FIL_IN_CODIGO'],
                                              'ord_in_codigo': r_dem['ORD_IN_CODIGO'],
                                              'ctl_in_codigo': r_dem['CTL_IN_CODIGO'],
                                              'plf_in_sqoperacao': self.seq_in,
                                              'apt_dt_inclusao': str_now,
                                              'mvd_in_sequencia': r_dem['MOV_IN_SEQUENCIA'],
                                              'pro_st_lote': str(r_dem['PRO_ST_LOTE']),
                                              'pro_re_qtdlote': r_dem['PRO_RE_QTDLOTE'],
                                              'cmaq_st_id': self.cmaq_st_id,
                                              'ord_st_id': r_dem['ORD_ST_ID'],
                                              'ord_st_extenso' : rs['ORD_ST_EXTENSO']}
                                    self.funcao = 'post_demanda/'
                                    self.get_urlapi = geturlapi(self.funcao)
                                    try:
                                    #if 1==1:
                                        # Grava os dados no Mega                                                        
                                        #resp_Dem = requests.post(self.get_urlapi, data=v_dadosDem).json()
                                        
                                        resp_Dem = json.loads(self.apt_integrarDemanda(v_dadosDem))
                                        if resp_Dem:
                                            #print(f'linha 426 => Dados da resposta da demanda: {resp_Dem}')
                                            for rs_dem in resp_Dem:
                                                #print(rs_dem)
                                                if (rs_dem['mensagem'] == 'Ok'):
                                                    if (rs_dem['item'] == 'Não Encontrado!'):
                                                        self.payload = {'ctl_in_codigo': r_dem['CTL_IN_CODIGO'],'sequencia': r_dem['MOV_IN_SEQUENCIA'],'status': 'I', 'item': None}
                                                    else:
                                                        self.payload = {'ctl_in_codigo': r_dem['CTL_IN_CODIGO'],'sequencia': r_dem['MOV_IN_SEQUENCIA'],'status': 'I', 'item': rs_dem['item']}                        
                                                    #faz Update da transação de demanda;
                                                    #print(self.payload)
                                                    self.funcao = 'demandas/'
                                                    self.get_urlapp = geturlapp(self.funcao)                                                    
                                                    c_update_dem = requests.put(self.get_urlapp, params=self.payload, verify=False)                                                
                                    except:
                                        pass
                        except:
                            pass                                   
                #faz Update da transação;
                #self.payload = {'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'E'}
                #c_update = requests.put(self.get_urlprod, params=self.payload)
        except:
            pass
        print('Integração dos lotes e demandas finalizado!')
    def apt_integrarlote(self, pparams):
        #print(pparams)
        v_listlote = pparams
        self.cmaq_st_id = v_listlote.get('cmaq_st_id')
        self.ord_st_id = v_listlote.get('ord_st_id')
        #transformar QueryDict em dicionario;
        #print(v_listlote.dict())
        lista = []
        #if (1==1):
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (int(v_listlote.get('fil_in_codigo')),
                       int(v_listlote.get('ord_in_codigo')),
                       int(v_listlote.get('ctl_in_codigo')),
                       int(v_listlote.get('plf_in_sqoperacao')),
                       v_listlote.get('apt_dt_inclusao'),
                       int(v_listlote.get('mvp_in_sequencia')),
                       float(v_listlote.get('apt_re_quantidade')),
                       float(v_listlote.get('apt_re_qtdeconvertida')),
                       float(v_listlote.get('apt_re_qtderefugo')),
                       int(v_listlote.get('pro_in_codigo')),
                       v_listlote.get('pro_st_obs'),
                       v_listlote.get('pro_st_docorigem'),
                       v_listlote.get('pro_st_referencia'),
                       int(v_listlote.get('usu_in_codigo')),
                       v_listlote.get('pro_st_destino'),
                       v_listlote.get('pro_st_lote'),
                       v_listlote.get('pro_st_conversor'),
                       v_listlote.get('apt_dt_lote'),
                       v_listlote.get('cmaq_st_id'),
                       v_listlote.get('ord_st_id'),
                       v_listlote.get('pro_st_id'),
                       v_listlote.get('orl_re_qtdajustada'),
                       v_listlote.get('ord_st_extenso'),
                       v_listlote.get('pro_st_fornecedor'),
                       ref_cursor)
            cur.callproc('apt_intprod2.cli_p_lotes_ordem',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close            
            if c_rs:
                for v_rs in c_rs:
                    lista.append(dict(sequencia = v_rs[0],
                                      mensagem = v_rs[1],
                                      mensagem_sub = v_rs[2]))
        #else:
        except cxo._Error as e:
            pass
            #error_obj, = e.args
            lista.append(dict(sequencia = 0,
                              mensagem = 'Erro',
                              mensagem_sub = 'Erro'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno
    def apt_integrarDemanda(self, pparams):
        lista = []
        #print('linha 508 => Iniciando integração das demandas!',pparams)
        v_retorno = {}
        v_listDem = pparams
        if (self.ord_in == 1280):
            print(v_listDem)
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            v_params = []
            sparams = (ref_cursor,
                       int(v_listDem.get('fil_in_codigo')),
                       int(v_listDem.get('ord_in_codigo')),
                       int(v_listDem.get('ctl_in_codigo')),
                       int(v_listDem.get('plf_in_sqoperacao')),
                       v_listDem.get('apt_dt_inclusao'),
                       int(v_listDem.get('mvd_in_sequencia')),
                       str(v_listDem.get('pro_st_lote')),
                       float(v_listDem.get('pro_re_qtdlote')),
                       str(v_listDem.get('cmaq_st_id')),
                       str(v_listDem.get('ord_st_id')),
                       str(v_listDem.get('ord_st_extenso'))                       
                       )
            cur.callproc('apt_intprod2.p_inseredemanda_lotes',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            if c_rs:
                for v_rs in c_rs:
                    lista.append(dict(mensagem = v_rs[0],
                                      item = v_rs[1],
                                      Sequencia = v_rs[2]))
            else:
                lista.append(dict(mensagem =  'Erro',
                                  item = 0,
                                  Sequencia = 0))
        except:
            lista.append(dict(mensagem =  'Erro',
                              item = 0,
                               Sequencia = 0))
        v_retorno = json.dumps(lista)
        return v_retorno
    def situacao_ordem(self):
        lista = []
        v_retorno = 'AB'
        try:
        #if 1==1:
            con = getOracleConnection()
            cur = con.cursor()
            c_rs = cur.callfunc('apt_intprod2.f_valida_sitordem',str,[self.fil_in, self.ord_in])                        
            cur.close
            con.close            
            if c_rs:
                #print(c_rs)
                v_retorno = c_rs
            else:
                v_retorno =  'AB'
        except:
            v_retorno =  'AB'        
        return v_retorno
class IntegracaoProducao:
    def _now(self) -> str: return datetime.now().strftime("%H:%M:%S")

    def executar(self) -> int:
        start = time.time()
        try:
            controles = services.select_controles_pendentes()
            if not controles: print(f"[{self._now()}] Nada pra integrar."); return 0
            ctl_ids = [c['CTL_IN_CODIGO'] for c in controles]
            ordens, demandas = services.select_filhos_por_ctl(ctl_ids)
            print(f"[{self._now()}] {len(controles)} Controles, {len(ordens)} Ordens, {len(demandas)} Demandas")

            ord_map = defaultdict(list)
            dem_map = defaultdict(list)
            for o in ordens: ord_map[o['CTL_IN_CODIGO']].append(o)
            for d in demandas: dem_map[d['CTL_IN_CODIGO']].append(d)

            with services.oracle_tx() as con:
                cur = con.cursor()
                for d_ctl in controles:
                    services.processa_controle(cur, d_ctl, ord_map.get(d_ctl['CTL_IN_CODIGO'], []), dem_map.get(d_ctl['CTL_IN_CODIGO'], []))

            services.bulk_update_status_tudo(ctl_ids)
            print(f"[{self._now()}] OK FULL. {len(ctl_ids)} controles em {time.time()-start:.2f}s")
            return len(ctl_ids)
        except Exception as e:
            print(f"[{self._now()}] ROLLBACK TOTAL: {e}")
            return -1
if __name__ == '__main__':    
    contador = 1
    v_params = []
    v_params.append(2)
    v_params.append(3)
    #v_params.append(63207)
    v_params.append(None)
    v_params.append(None)
    init = integrador(v_params)
    #init.manutencao()
    init.integraOrdens()
    #ginit.encerra_ordens()
