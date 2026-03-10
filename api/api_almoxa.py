# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import requests
import urllib3
import urllib as ul
import oracledb as cxo
from oracle_connection import getOracleConnection
import time
from datetime import datetime, date, timedelta
import json, requests
from unicodedata import normalize
from dateutil.relativedelta import *
import oracledb as cxo
from oracle_connection import getOracleConnection
from producao import settings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
v_dirlog = '/home/admin/prod/log'

GRAVAR_LOCAL = True
URL_LOCAL = 'localhost'
URL_REMOTO = '192.168.0.24'
URL_PRODUCAO = '192.168.0.24'
URL_SQLITE = 'localhost:8000'


def geturlest(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/est/'+funcao
    return url_principal

def geturlinv(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/inv/'+funcao
    return url_principal

class Baixas:
    def __init__(self):
        self.fil_in_codigo = None
        self.bxa_in_sequencia = None
        self.bxa_dt_apontamento = None
        self.bxa_st_usuario = None
        self.cus_id_ccusto = None
        self.bxa_ch_status = None
        self.req_in_sequencia = 0
        self.rei_in_sequencia = 0
        self.bxi_in_sequencia = None
        self.bxi_id_produto = None
        self.bxi_re_quantidade = None
        self.bxi_ch_status = None
        self.acao_in_codigo = None
        self.bxi_id_almoxa = None
        self.os_st_id = None
    def apt_gerarBaixa(self,pparams):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.acao_in_codigo,self.fil_in_codigo,self.req_in_sequencia)
        cur.callproc('apt_intprod2.p_Gera_BaixaRequisicao',(sparams))
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
        cur.callproc('apt_intprod2.p_Insere_ItemRequisicao',(sparams))
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
        try:
            self.os_st_id = pparams['OS_ST_ID']
        except:
            pass
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
                            ,self.bxa_st_usuario,self.cus_id_ccusto,self.bxa_ch_status,self.os_st_id)
                cur.callproc('idp.apt_intprod2.p_Insere_Requisicao',(sparams))
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
                    self.bxi_id_almoxa = v_req['BXI_ID_ALMOXA']
                    try:
                        con = getOracleConnection()
                        cur = con.cursor()
                        ref_cursor = con.cursor()
                        sparams = (ref_cursor,self.fil_in_codigo,self.req_in_sequencia,self.bxi_in_sequencia, self.bxa_in_sequencia,
                                   self.bxi_id_produto,self.bxi_re_quantidade,self.bxi_ch_status,self.bxi_id_almoxa)
                        cur.callproc('idp.apt_intprod2.p_Insere_ItemRequisicao',(sparams))
                        cur_req = ref_cursor.fetchall()
                        cur.close
                        con.close
                        for v_reqitn in cur_req:
                            self.rei_in_sequencia = v_reqitn[1]                            
                        #Carimba o item da requisição como baixado
                        payload = {'requisicao':self.req_in_sequencia,'item_req':self.rei_in_sequencia,'sequencia':self.bxa_in_sequencia,'seq_item': self.bxi_in_sequencia,'status': 'B'}                        
                        c_encerra = requests.put(get_urlest, data=payload)
                    except:
                        pass                    
                    #print('linha 128',json_baixas)
                lista.append(dict(req_in_sequencia =self.req_in_sequencia,

                                  bxa_in_sequencia =self.bxa_in_sequencia))
                json_baixas = json.dumps(lista)                
                #Baixa requisição em aberto
                try:
                    con = getOracleConnection()
                    cur = con.cursor()
                    ref_cursor = con.cursor()
                    sparams = (ref_cursor,self.fil_in_codigo)
                    cur.callproc('idp.apt_intprod2.p_Gera_BaixaRequisicao',(sparams))
                    c_cursor = ref_cursor.fetchall()
                    cur.close
                    con.close
                except:
                    pass
            except:
                lista.append(dict(req_in_sequencia=self.req_in_sequencia,
                                  bxa_in_sequencia =0))
                json_baixas = json.dumps(lista)
        else:
            lista.append(dict(req_in_sequencia = self.req_in_sequencia,
                              bxa_in_sequencia =self.bxa_in_sequencia))
            json_baixas = json.dumps(lista)
        return json_baixas

class Consulta:
    def __init__(self):
        self.fil_in_codigo = None
        self.id_produto = None
    def lista_saldo(self, id):
        lista = []
        json_saldo = {}
        self.id_produto = id['id']
        self.fil_in_codigo = id['filial']
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =(''' select mvs.pro_tab_in_codigo,
                               mvs.pro_pad_in_codigo,
                               mvs.pro_in_codigo,
                               pro.pro_st_descricao,
                               sum(mvs.mvs_re_quantidade)mvs_re_quantidade
                          from idp.est_movsumarizado mvs,
                               idp.est_produtos pro
                         where pro.pro_tab_in_codigo = mvs.pro_tab_in_codigo
                           and pro.pro_pad_in_codigo = mvs.pro_pad_in_codigo
                           and pro.pro_in_codigo     = mvs.pro_in_codigo
                           and mvs.fil_in_codigo     = :fil_in
                           and (   
                                   (mvs.pro_pad_in_codigo = 1 and mvs.alm_in_codigo||mvs.loc_in_codigo=11)
                                or (mvs.pro_pad_in_codigo <> 1)
                               )
                           and mvs.pro_pad_in_codigo = idp.pck_mega.achapadraodatabela(:fil_in,100,sysdate)
                           and ((lpad(mvs.pro_tab_in_codigo,3,'0')||
                               lpad(mvs.pro_pad_in_codigo,3,'0')||
                               lpad(mvs.pro_in_codigo,7,'0') = :id_produto) or
                               (mvs.pro_in_codigo = :id_produto))    
                         group by mvs.pro_tab_in_codigo,
                               mvs.pro_pad_in_codigo,
                               mvs.pro_in_codigo,
                               pro.pro_st_descricao''')
        cur.prepare(selectSQL)        
        cur.execute(None, {'id_produto': self.id_produto, 'fil_in':self.fil_in_codigo})
        c_rs = cur.fetchall()
        cur.close
        con.close
        for rs in c_rs:
            lista.append(dict(pro_tab_in_codigo = int(rs[0]),
                              pro_pad_in_codigo = rs[1],
                              pro_in_codigo = rs[2],
                              pro_st_descricao = rs[3],
                              mvs_re_quantidade = float(rs[4])))
        json_producao= {}
        json_saldo = json.dumps(lista)
        return json_saldo
    
    #Cadastro de localizações do produto;
    def get_CadastroProdLocal(self, p_params):
        self.fil_in_codigo = p_params[0]
        self.status = p_params[1]
        self.id_produto = p_params[2]
        lista = []
        json_retorno = {}
        selectSQL =('''select lpad(loc.pro_tab_in_codigo,3,0)||
                              lpad(loc.pro_pad_in_codigo,3,0)||
                              lpad(loc.pro_in_codigo,7,0)||
                              lpad(loc.alm_tab_in_codigo,3,0)||
                              lpad(loc.alm_pad_in_codigo,3,0)||
                              lpad(loc.alm_in_codigo,6,0)||
                              lpad(loc.loc_in_codigo,6,0)||
                              lpad(loc.fil_in_codigo,7,0) as LOC_ID_PROALMFIL,
                              lpad(loc.alm_tab_in_codigo,3,0)||
                              lpad(loc.alm_pad_in_codigo,3,0)||
                              lpad(loc.alm_in_codigo,6,0)||
                              lpad(loc.loc_in_codigo,6,0) as LOC_ID_ALMOXA,
                              lpad(loc.org_tab_in_codigo,3,0)||
                              lpad(loc.org_pad_in_codigo,3,0)||
                              lpad(loc.org_in_codigo,7,0)||
                              lpad(loc.org_tau_st_codigo,3,0) as LOC_ID_ORG,
                              lpad(loc.pro_tab_in_codigo,3,0)||
                              lpad(loc.pro_pad_in_codigo,3,0)||
                              lpad(loc.pro_in_codigo,7,0) as LOC_ID_PRODUTO,                                                                   
                              loc.fil_in_codigo,
                              loc.alm_in_codigo,
                              loc.loc_in_codigo,
                              alm.alm_st_almoxar,
                              loc.loc_st_nome
                         from cus_tb_api_almoxloc pce,
                              adm_vw_prodalmoxlocal loc,
                              est_almoxarifado alm
                        where loc.alm_tab_in_codigo = alm.alm_tab_in_codigo
                          and loc.alm_pad_in_codigo = alm.alm_pad_in_codigo
                          and loc.alm_in_codigo     = alm.alm_in_codigo
                          and lpad(loc.pro_tab_in_codigo,3,0)||
                              lpad(loc.pro_pad_in_codigo,3,0)||
                              lpad(loc.pro_in_codigo,7,0)||
                              lpad(loc.alm_tab_in_codigo,3,0)||
                              lpad(loc.alm_pad_in_codigo,3,0)||
                              lpad(loc.alm_in_codigo,6,0)||
                              lpad(loc.loc_in_codigo,6,0)||
                              lpad(loc.fil_in_codigo,7,0) = pce.LOC_ID_PROALMFIL(+)                          
                          and loc.fil_in_codigo     = :fil_in_codigo
                          and (nvl(pce.pro_ch_almoxarifado,'N') = :status or :status = 'T')
                          and (lpad(loc.pro_tab_in_codigo,3,0)||
                              lpad(loc.pro_pad_in_codigo,3,0)||
                              lpad(loc.pro_in_codigo,7,0) = :pro_id or :pro_id = '0') 
                        order by loc.pro_in_codigo''')        
        con = getOracleConnection()
        cur = con.cursor()
        cur.prepare(selectSQL)
        try:
            cur.execute(None, {'fil_in_codigo': self.fil_in_codigo,'status':self.status,'pro_id':self.id_produto})
            c_rs = cur.fetchall()            
            cur.close
            con.close
            if c_rs:
                for rs in c_rs:
                    lista.append(dict(LOC_ID_PROALMFIL = rs[0],
                                      LOC_ID_ALMOXA = rs[1],
                                      LOC_ID_ORG = rs[2],
                                      LOC_ID_PRODUTO = rs[3],
                                      LOC_IN_FILIAL = int(rs[4]),
                                      ALM_IN_CODIGO = int(rs[5]),
                                      LOC_IN_CODIGO = int(rs[6]),
                                      ALM_ST_DESCRICAO = rs[7],
                                      LOC_ST_DESCRICAO = rs[8]))                    
                
        except:
            cur.close
            con.close
            lista.append(dict(LOC_ID_PROALMFIL = self.id_produto))
        json_retorno = json.dumps(lista)
        return json_retorno
    def put_CadastroProdlocal(self, pParams):
        #Carimba a licalização como sincronizada;
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (pParams[0],'S',ref_cursor)
            cur.callproc('idp.apt_intprod2.apt_put_itemalmoxa',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
        except:
            pass
        lista = []
        if c_rs:
            for v_rs in c_rs:
                lista.append(dict(mensagem = v_rs[0]))
        else:
            lista.append(dict(mensagem = 'Não executado!'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno
            
class Inventario:
    def __init__(self):
        self.fil_in_codigo = None
        self.id_produto = None
        self.inv_in_sequencia = None
        self.inv_dt_movimento = None
        self.inv_id_produto = None
        self.inv_re_quantidade = None
        self.inv_ch_status = None
        self.mov_in_sequencia = None
        self.inv_id_usuario = None
        self.iti_in_sequencia = None
        self.iti_ch_status = None
        self.moi_in_sequencia = None
        self.iti_st_tipomov = None
        self.mov_st_mensagem = None
    def apt_inserirInventario(self,pparams):
        self.fil_in_codigo = int(pparams['FIL_IN_CODIGO'])
        self.inv_in_sequencia = int(pparams['INV_IN_SEQUENCIA'])
        self.inv_dt_movimento = pparams['INV_DT_MOVIMENTO'].replace('-','/')
        self.inv_id_usuario = pparams['INV_ST_USUARIO']
        self.inv_ch_status = pparams['INV_CH_STATUS']
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,self.fil_in_codigo,self.inv_in_sequencia,self.inv_id_usuario,
                       self.inv_dt_movimento,self.inv_ch_status)
            cur.callproc('idp.apt_intprod2.p_Insere_Inventario',(sparams))
            c_cursor = ref_cursor.fetchall()
            cur.close
            con.close
            for v_ret in c_cursor:
                self.mov_in_sequencia = v_ret[1]
        except:
            pass
        if self.mov_in_sequencia > 0:
            #Integra itens
            # Busca Itens em aberto;
            funcao = 'invItem/'
            get_urlest = geturlinv(funcao)
            payload = {'status':'A','inventario':self.inv_in_sequencia,'item':self.inv_id_produto}
            c_itn = requests.get(get_urlest, params=payload).json()
            if c_itn:
                for r_itn in c_itn:
                    self.iti_in_sequencia = r_itn['ITI_IN_SEQUENCIA']
                    self.inv_id_produto = r_itn['ITI_ID_PRODUTO']
                    self.inv_re_quantidade = float(r_itn['ITI_RE_QUANTIDADE'])
                    self.iti_ch_status = r_itn['ITI_CH_STATUS']
                    self.iti_st_tipomov = r_itn['ITI_ST_TIPOMOV']
                    con = getOracleConnection()
                    cur = con.cursor()
                    ref_cursor = con.cursor()
                    sparams = (ref_cursor,self.fil_in_codigo,self.inv_in_sequencia,self.iti_in_sequencia
                                    ,self.inv_id_produto,self.inv_re_quantidade,self.iti_ch_status,self.mov_in_sequencia,self.iti_st_tipomov)
                    try:
                        cur.callproc('idp.apt_intprod2.p_Insere_ItemInventario',(sparams))
                        c_cursor = ref_cursor.fetchall()
                        cur.close
                        con.close
                        for v_itn in c_cursor:
                            self.moi_in_sequencia = v_itn[3]
                            #Atualiza o item do inventário
                            payload = {'status':'B','sequencia':self.iti_in_sequencia,'item':self.inv_id_produto,
                                   'mov':self.mov_in_sequencia,'moi':self.moi_in_sequencia,
                                   'quantidade':self.inv_re_quantidade}                        
                            c_itn = requests.put(get_urlest, data=payload).json()
                    except:
                        cur.close
                        con.close
        #Gera movimento de Inventário no Mega
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,self.fil_in_codigo)
            cur.callproc('idp.apt_intprod2.p_Gera_MovimentoInventario',(sparams))
            c_cursor = ref_cursor.fetchall()
            cur.close
            con.close
            for v_ret in c_cursor:
                self.mov_st_mensagem = v_ret[0]
        except:
            pass                    
        c_retorno = {'movimento': self.mov_in_sequencia}
        return c_retorno
