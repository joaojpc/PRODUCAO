# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import requests
import urllib3
import urllib as ul
import time
from datetime import datetime, date, timedelta
import json, requests
from unicodedata import normalize
from dateutil.relativedelta import *
import oracledb as cxo
from oracle_connection import getOracleConnection
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
v_dirlog = '/home/admin/prod/log'

GRAVAR_LOCAL = True
URL_LOCAL = 'localhost'
URL_REMOTO = '192.168.50.8'
URL_PRODUCAO = '192.168.50.8'
URL_SQLITE = 'localhost:8000'
DATABASE = "/home/suporte/prod/producao.db"

class Baixas:
    def __init__(self):
        self.fil_in_codigo = None
        self.bxa_in_sequencia = None
        self.bxa_dt_apontamento = None
        self.bxa_st_usuario = None
        self.cus_id_ccusto = None
        self.bxa_ch_status = None
        self.req_in_sequencia = 0
        self.bxi_in_sequencia = None
        self.bxi_id_produto = None
        self.bxi_re_quantidade = None
        self.bxi_ch_status = None
        self.acao_in_codigo = None
    def apt_gerarBaixa(self,pparams):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.acao_in_codigo,self.fil_in_codigo,self.req_in_sequencia)
        cur.callproc('apt_intprod.p_Gera_BaixaRequisicao',(sparams))
        c_cursor = ref_cursor.fetchall()
        cur.close
        con.close
        for v_ret in c_cursor:
            result = v_ret[0]
        return result

    def apt_inserirItemReq(self, pparams):
        for v_rei in pparams:
            self.fil_in_codigo = int(v_rei['fil_in_codigo'])
            self.bxi_in_sequencia = int(v_rei['bxi_in_sequencia'])
            self.bxa_in_sequencia = int(v_rei['bxa_in_sequencia'])
            self.bxi_id_produto = v_rei['bxi_id_produto']
            self.bxi_re_quantidade = v_rei['bxi_re_quantidade']
            self.bxa_ch_status = v_rei['bxa_ch_status']
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.fil_in_codigo,self.req_in_sequencia,self.bxi_in_sequencia,
                   self.bxa_in_sequencia,self.bxi_id_produto, self.bxi_re_quantidade, self.bxi_ch_status)
        cur.callproc('apt_intprod.p_Insere_ItemRequisicao',(sparams))
        c_cursor = ref_cursor.fetchall()
        cur.close
        con.close
        for v_ret in c_cursor:
            result = v_ret[0]
        return result

    def apt_inserirRequisicao(self,pparams):
        #c_params = json.loads(pparams)
        #print(pparams)
        lista = []
        json_baixas= {}
        self.fil_in_codigo = int(pparams['FIL_IN_CODIGO'])
        self.bxa_in_sequencia = int(pparams['BXA_IN_SEQUENCIA'])
        self.bxa_dt_apontamento = pparams['BXA_DT_APONTAMENTO']
        self.bxa_st_usuario = pparams['BXA_ST_USUARIO']
        self.cus_id_ccusto = pparams['CUS_ID_CCUSTO']
        self.bxa_ch_status = pparams['BXA_CH_STATUS']
        #Busca Itens da requisição
        funcao = 'reqItem/'
        get_urlest = geturlest(funcao)
        payload = {'sequencia':self.bxa_in_sequencia,'seq_item':None}
        c_req = requests.get(get_urlest, params=payload).json()
        if c_req:
            try:
                con = getOracleConnection()
                cur = con.cursor()
                ref_cursor = con.cursor()
                sparams = (ref_cursor,self.fil_in_codigo,self.bxa_in_sequencia,self.bxa_dt_apontamento
                            ,self.bxa_st_usuario,self.cus_id_ccusto,self.bxa_ch_status)
                cur.callproc('intprod.apt_intprod.p_Insere_Requisicao',(sparams))
                c_cursor = ref_cursor.fetchall()
                cur.close
                con.close
                for v_ret in c_cursor:
                    self.req_in_sequencia = v_ret[0]
                #Busca os itens das requisições;
                for v_req in c_req:
                    #prepara a integração da requisição
                    self.bxi_in_sequencia = int(v_req['BXI_IN_SEQUENCIA'])
                    self.bxi_id_produto = v_req['BXI_ID_PRODUTO']
                    self.bxi_re_quantidade =float(v_req['BXI_RE_QUANTIDADE'])
                    self.bxi_ch_status = v_req['BXI_CH_STATUS']
                    try:
                        con = getOracleConnection()
                        cur = con.cursor()
                        ref_cursor = con.cursor()
                        sparams = (ref_cursor,self.fil_in_codigo,self.req_in_sequencia,self.bxi_in_sequencia, self.bxa_in_sequencia,
                                   self.bxi_id_produto,self.bxi_re_quantidade,self.bxi_ch_status)
                        cur.callproc('intprod.apt_intprod.p_Insere_ItemRequisicao',(sparams))
                        cur_req = ref_cursor.fetchall()
                        cur.close
                        con.close
                        for v_reqitn in cur_req:
                            #Carimba o item da requisição como baixado
                            payload = {'requisicao':v_reqitn[0],'item_req':v_reqitn[1],'sequencia':v_reqitn[2],'seq_item': v_reqitn[3],'status': 'B'}
                            c_encerra = requests.put(get_urlest, data=payload)
                    except:
                        pass
                    #print(v_req)
                lista.append(dict(req_in_sequencia =self.req_in_sequencia,
                                  bxa_in_sequencia =self.bxa_in_sequencia))
                json_baixas = json.dumps(lista)
                #print('linha 128',json_baixas)
            except:
                lista.append(dict(req_in_sequencia=self.req_in_sequencia,
                                  bxa_in_sequencia =0))
                json_baixas = json.dumps(lista)
        else:
            lista.append(dict(req_in_sequencia = self.req_in_sequencia,
                              bxa_in_sequencia =self.bxa_in_sequencia))
            json_baixas = json.dumps(lista)
        return json_baixas

