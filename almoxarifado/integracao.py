# -*- coding: utf-8 -*-
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
from ..oracle_connection import getOracleConnection
from ..url_projeto import geturlapp, geturlapi, geturlprod, geturlest, geturlinv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#from api_view import *
import requests
GRAVAR_LOCAL = True
URL_LOCAL = 'localhost'
URL_REMOTO = '192.168.0.24'
URL_PRODUCAO = '192.168.0.24'
#URL_SQLITE = 'localhost:8000'
URL_SQLITE = '192.168.0.24'

class integrador:
    def __init__(self,pParams):
        self.org_in = pParams[0]
        self.fil_in = pParams[1]
        self.pad_in = pParams[2]
        self.pro_id = pParams[3]
        self.bxa_in_sequencia = None
        self.bxa_dt_apontamento = None
        self.bxa_st_usuario = None
        self.cus_id_ccusto = None
        self.bxa_ch_status = None
        self.os_st_id = None
        self.req_in_sequencia = 0
        self.rei_in_sequencia = 0
        self.bxi_in_sequencia = None
        self.bxi_id_produto = None
        self.bxi_re_quantidade = None
        self.bxi_ch_status = None
        self.acao_in_codigo = None
        self.bxi_id_almoxa = None
        self.url_req = None
        self.url_reqItn = None
        self.fil_in_codigo = None
        
    def Buscar_CentroCusto(self):
        print('Iniciando integração de centro de custos!')
        funcao = 'GetCentroCustos/'
        get_urlapi = geturlapi(funcao)
        #print(get_urlapi)
        payload = {'filial': self.fil_in}
        c_rs = requests.get(get_urlapi, params=payload).json()
        #print(c_rs)
        if c_rs:
            for c_a in c_rs:
                funcao = 'centrocustos/'
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
                    #print(c_a['CUS_ID_CCUSTO'])
        print('Integração de centro de custos finalizada!')
    def get_CadastroProdutos(self):
        selectSQL =('''select lpad(pro.pro_tab_in_codigo,3,0)||
                              lpad(pro.pro_pad_in_codigo,3,0)||
                              lpad(pro.pro_in_codigo,7,0) as PRO_ST_ID,       
                              pro.pro_tab_in_codigo,
                              pro.pro_pad_in_codigo,
                              pro.pro_in_codigo,
                              pro.pro_st_descricao,
                              pro.uni_st_unidade,
                              nvl(pce.pro_ch_acb,'N') pro_ch_acb,
                              nvl(pce.pro_ch_almoxarifado,'N') pro_ch_almoxarifado
                         from idp.est_produtos pro,
                              idp.est_produtoscmpesp pce
                        where pro.pro_tab_in_codigo = pce.pro_tab_in_codigo (+)
                          and pro.pro_pad_in_codigo = pce.pro_pad_in_codigo (+)
                          and pro.pro_in_codigo     = pce.pro_in_codigo (+)
                          and pro.pro_pad_in_codigo = :pro_pad_in_codigo
                          and nvl(pce.pro_ch_almoxarifado,'N') = 'N'
                          and nvl(pce.pro_st_orialteracao,'M') = 'M'
                        order by pro.pro_in_codigo''')
        lista = []
        json_getCadItens= {}
        if 1==1:
        #try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'pro_pad_in_codigo': self.pad_in})            
            c_rs = cur.fetchall()
            #print(c_rs)
            cur.close
            con.close
            if c_rs:                
                for rs in c_rs:                    
                    lista.append(dict(BXI_ID_PRODUTO = rs[0],
                              PRO_TAB_IN_CODIGO = int(rs[1]),
                              PRO_PAD_IN_CODIGO = int(rs[2]),
                              PRO_IN_CODIGO = int(rs[3]),
                              PRO_ST_DESCRICAO = rs[4],
                              UNI_ST_UNIDADE = rs[5],
                              PRO_CH_ACB = str(rs[6]),
                              PRO_CH_ALMOXARIFADO = str(rs[7])))                    
        #except cxo._Error as error:
        '''except:
            pass'''
        json_getCadItens = json.dumps(lista)        
        return json_getCadItens
    def Buscar_CadastroProdutos(self):
        print('Iniciando integração de Itens!')
        funcao = 'GetCadastroItens/'
        get_urlapi = geturlapi(funcao)        
        payload = {'id': self.pro_id,'filial': self.fil_in}        
        c_rs = requests.get(get_urlapi, params=payload).json()        
        #c_rs = json.loads(self.get_CadastroProdutos())        
        print(c_rs)
        if c_rs:
            for c_a in c_rs:
                print(c_a)
                funcao = 'produtos/'
                get_urlest = geturlest(funcao)
                #print(get_urlest)
                payload = {'item': c_a['BXI_ID_PRODUTO']}
                #print(get_urlest,payload)
                #Verificar se o Item ainda não foi cadastrado
                c_prod = requests.get(get_urlest, params=payload).json()                
                if not c_prod:                    
                    #Grava integração do Item;                    
                    dados = c_a
                    response = requests.post(get_urlest, data=dados)
                #busca local de estoque configurado no item
                funcao = 'GetItenslocalizacao/'                
                get_urlapi = geturlapi(funcao)                
                payload = {'id': c_a['BXI_ID_PRODUTO']}
                c_prl = requests.get(get_urlapi, params=payload).json()
                if c_prl:
                    for r_prl in c_prl:
                        dados = r_prl
                        funcao = 'ItemAlmoxa/'
                        get_urlest = geturlest(funcao)
                        payload = {'item_almoxa': r_prl['LOC_ID_PROALMFIL']}
                        c_pl = requests.get(get_urlest, params=payload).json()
                        #print(c_pl)
                        if not c_pl:
                            try:
                                #print(c_a['BXI_ID_PRODUTO'])
                                c_respReq = requests.post(get_urlest, data=dados).json()
                            except:
                                print('Erro ',c_rs['BXI_ID_PRODUTO'])
                else:
                    pass
                #Carimba o item como itegrado                
                '''try:
                    con = getOracleConnection()
                    cur = con.cursor()
                    ref_cursor = con.cursor()                    
                    sparams =(c_a['BXI_ID_PRODUTO'],c_a['PRO_CH_ACB'],'S',c_a['PRO_CH_ACB'],c_a['PRO_CH_ALMOXARIFADO'],ref_cursor)
                    #sparams1 =(rs[0],rs[6],'S',rs[6],rs[7])
                    #print(sparams1)                
                    cur.callproc('apt_intprod2.apt_PutItens',(sparams))
                    c_rs2 = ref_cursor.fetchall()
                    print('Carimbado',c_a['BXI_ID_PRODUTO'])
                except:
                    print('Erro ',c_a['BXI_ID_PRODUTO'])
                cur.close
                con.close'''
                #print(c_a['BXI_ID_PRODUTO'])
        print('Integração de Itens finalizada!')
    
    def Integrarequisicao(self):
        v_encerra = 'S'
        # Busca requisições em aberto
        print('Iniciando integração de requisições!')
        funcao = 'requisicao/'
        self.url_req = geturlest(funcao)        
        payload = {'filial':self.fil_in,'status': 'L'}
        #print(payload)
        c_req = requests.get(self.url_req, params=payload).json()
        #print(c_req)
        if c_req:            
            for v_req in c_req:
                #print(v_req)
                funcao = 'reqItem/'                        
                self.url_reqItn = geturlest(funcao)
                payload = {'filial':self.fil_in,'sequencia':v_req['BXA_IN_SEQUENCIA']}                
                c_reqItem = requests.get(self.url_reqItn, params=payload).json()                
                #se a requisição não tiver item excluir
                if c_reqItem:
                    #prepara a integração da requisição
                    dados = v_req                
                    c_respReq = self.apt_inserirRequisicao(dados)                
                    if c_respReq:
                        for rs_req in c_respReq:
                            self.req_in_sequencia = rs_req[0]                        
                            # Busca Itens em aberto;
                            if c_reqItem:
                                for rs_itn in c_reqItem:
                                    #print('Itens',rs_itn)
                                    c_retItn = self.apt_inserirItemReq(rs_itn)
                                    
                                    #print('voltou',c_retItn)
                                    if c_retItn:
                                        for v_ret in c_retItn:                                        
                                            self.rei_in_sequencia = v_ret[1]                                        
                                            #encerra o item da requisição                                        
                                            if v_encerra == 'S':
                                                #print(v_encerra)
                                                payload = {'requisicao':self.req_in_sequencia,'item_req': self.rei_in_sequencia,'sequencia':self.bxa_in_sequencia,
                                                           'seq_item':self.bxi_in_sequencia,'status': 'B', 'filial':self.fil_in}                                            
                                                c_encerra = requests.put(self.url_reqItn, data=payload)
                                                #print('encerrar Item',c_encerra)
                
                    #encerra a requisição
                    if v_encerra == 'S':
                        payload = {'requisicao':self.req_in_sequencia,'sequencia':self.bxa_in_sequencia,'status': 'B', 'filial':self.fil_in}                        
                        c_encerra = requests.put(self.url_req, data=payload)
                        #print('encerrar req',c_encerra)
                else:
                    #print('requisição não encontrada!')
                    payload = {'filial':v_req['FIL_IN_CODIGO'], 'sequencia':v_req['BXA_IN_SEQUENCIA']}                    
                    c_delete = requests.delete(self.url_req, data=payload)
        print('Integração de requisições finalizada!')
    def apt_inserirRequisicao(self,pparams):        
        #print(pparams)
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
        #return pparams
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,self.fil_in_codigo,self.bxa_in_sequencia,self.bxa_dt_apontamento
                      ,self.bxa_st_usuario,self.cus_id_ccusto,self.bxa_ch_status,self.os_st_id)            
            cur.callproc('idp.apt_intprod2.p_Insere_Requisicao',(sparams))            
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close            
        except cxo._Error as error:
            pass
        return c_rs    
    def apt_inserirItemReq(self, pparams):
        self.fil_in_codigo = int(pparams['FIL_IN_CODIGO'])        
        self.bxi_in_sequencia = int(pparams['BXI_IN_SEQUENCIA'])
        self.bxa_in_sequencia = int(pparams['BXA_IN_SEQUENCIA'])
        self.bxi_id_produto = pparams['BXI_ID_PRODUTO']
        self.bxi_re_quantidade = float(pparams['BXI_RE_QUANTIDADE'])
        if pparams['BXI_CH_STATUS'] == 'B':
            self.bxi_ch_status = 'A'
        else:
            self.bxi_ch_status = pparams['BXI_CH_STATUS']
        try:
            self.bxi_id_almoxa = pparams['BXI_ID_ALMOXA']
        except:
           self.bxi_id_almoxa = None
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,self.fil_in_codigo,self.req_in_sequencia,self.bxi_in_sequencia, self.bxa_in_sequencia,
                                   self.bxi_id_produto,self.bxi_re_quantidade,self.bxi_ch_status,self.bxi_id_almoxa)            
            cur.callproc('idp.apt_intprod2.p_Insere_ItemRequisicao',(sparams))            
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            if c_rs:
                v_return = c_rs
            else:
                v_return = (None)                
        except cxo._Error as error:
            v_return = (None)            
        return v_return
    def apt_geraBaixaRequisicao(self):
        print('Iniciando a baixa de requisição')        
        #Baixa requisição em aberto
        v_baixa = False
        try:
            con = getOracleConnection()
            cur = con.cursor()            
            ref_cursor = con.cursor()            
            sparams = (ref_cursor,self.fil_in)            
            cur.callproc('idp.apt_intprod2.p_Gera_BaixaRequisicao',(sparams))
            c_cursor = ref_cursor.fetchall()
            cur.close
            con.close
            v_baixa = True            
        except:
            pass
        print('Encerrando a baixa de requisição')
        return v_baixa
        
    def IntegraInventario(self):        
        # Busca inventários em Aberto
        print('Iniciando integração de inventario!')
        funcao = 'gravarinventario/'        
        get_urlinv = geturlinv(funcao)        
        payload = {'status':'A','filial':self.fil_in}
        c_inv = requests.get(get_urlinv, params=payload).json()
        if c_inv:
            for r_inv in c_inv:
                dados = r_inv
                funcao = 'geraInventario/'
                get_urlapi = geturlapi(funcao)
                # Busca Itens em aberto;
                funcao = 'invItem/'
                get_urlest = geturlinv(funcao)
                payload = {'status':'A','inventario':r_inv['INV_IN_SEQUENCIA']}
                c_itn = requests.get(get_urlest, params=payload).json()
                if c_itn:
                    #grava a integração do inventário            
                    c_respReq = requests.post(get_urlapi, data=dados).json()
                    if c_respReq['movimento'] is not None:
                        funcao = 'gravarinventario/'
                        get_urlest = geturlinv(funcao)
                        payload = {'sequencia':r_inv['INV_IN_SEQUENCIA'],'movimento':c_respReq['movimento'],'status': 'B'}
                        c_encerra = requests.put(get_urlest, data=payload)                        
        print('Integração de inventario finalizada!')
    def get_centro_custos(self):
        lista = []
        #print('Linha 701')
        selectSQL =('''select lpad(cc.cus_tab_in_codigo,3,0)|| 
                              lpad(cc.cus_pad_in_codigo,3,0)||
                              lpad(cc.cus_ide_st_codigo,5,0)|| 
                              lpad(cc.cus_in_reduzido,7,0) as CUS_ID_CCUSTO,
                              cc.cus_tab_in_codigo, 
                              cc.cus_pad_in_codigo, 
                              cc.cus_ide_st_codigo , 
                              cc.cus_in_reduzido, 
                              cc.cus_st_extenso, 
                              cc.cus_st_descricao 
                         from con_centro_custo cc
                        where cc.cus_ch_tipo_conta = 'A'
                          and cc.cus_pad_in_codigo = :cus_pad_in_codigo
                        order by cc.cus_in_reduzido''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'cus_pad_in_codigo': 1})
            c_rs = cur.fetchall()            
            cur.close
            con.close
            print('Linha 724',c_rs)
            for rs in c_rs:
                lista.append(dict(CUS_ID_CCUSTO = rs[0],
                              CUS_TAB_IN_CODIGO = int(rs[1]),
                              CUS_PAD_IN_CODIGO = int(rs[2]),
                              CUS_IDE_ST_CODIGO = rs[3],
                              CUS_IN_REDUZIDO = int(rs[4]),
                              CUS_ST_EXTENSO = rs[5],
                              CUS_ST_DESCRICAO = rs[6]))
        except cxo._Error as error:
            pass                
        json_getCCusto= {}
        json_getCCusto = json.dumps(lista)
        return json_getCCusto
    def get_integracao(self,pparams):
        if pparams[1] is None:
            selectSQL =('''select ord.org_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo
                         from idp.int_pro_ordens ord
                        where ord.ord_ch_integrada = :ord_ch_integrada
                          and ord.org_in_codigo = :org_in_codigo
                          --and ord.ord_in_codigo = 58865
                        order by ord.ord_in_codigo
                          ''')
        else:
            selectSQL =('''select ord.org_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo
                         from idp.int_pro_ordens ord
                        where ((ord.ord_ch_integrada = :ord_ch_integrada) or
                                 (ord.ord_ch_modificada <> 'N')
                              )
                          and ord.fil_in_codigo = :fil_in_codigo
                          and ord.ord_in_codigo = :ord_in_codigo                          
                        order by ord.ord_in_codigo
                          ''')

        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            if pparams[1] is None:
                cur.execute(None, {'ord_ch_integrada': 'N','org_in_codigo': pparams[0]})
            else:
                cur.execute(None, {'ord_ch_integrada': 'N',
                                   'fil_in_codigo': pparams[1],
                                   'ord_in_codigo': pparams[2]
                                   })
            c_rs = cur.fetchall()
            print(c_rs)
            cur.close
            con.close
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:
            lista.append(dict(org_in_codigo = int(rs[0]),
                              ord_seq_in_codigo = int(rs[1]),
                              ord_in_codigo = int(rs[2])))
        json_getOrdens= {}
        json_getOrdens = json.dumps(lista)
        return json_getOrdens
    def Buscar_CadastroProdLocal(self,Param):
        print('Iniciando integração de Localização dos itens!')
        if Param is not None:
            funcao = 'GetItenslocalizacao/'                
            get_urlapi = geturlapi(funcao)                
            payload = {'id': Param}
            c_prl = requests.get(get_urlapi, params=payload).json()
            for r_prl in c_prl:
                dados = r_prl
                funcao = 'ItemAlmoxa/'
                get_urlest = geturlest(funcao)
                payload = {'item_almoxa': r_prl['LOC_ID_PROALMFIL']}
                c_pl = requests.get(get_urlest, params=payload).json()
                 #print(c_pl)
                if not c_pl:
                    try:
                        print(dados)
                        c_respReq = requests.post(get_urlest, data=dados).json()
                    except:
                        print('Erro ',c_rs['BXI_ID_PRODUTO'])
                #Carimba a localização como sincronizada;
                try:
                    con = getOracleConnection()
                    cur = con.cursor()
                    ref_cursor = con.cursor()
                    sparams =(r_prl['LOC_ID_PROALMFIL'],'S',ref_cursor)
                    cur.callproc('apt_intprod2.apt_put_itemalmoxa',(sparams))
                    c_rs2 = ref_cursor.fetchall()
                    cur.close
                    con.close
                    print('Carimbado',r_prl['LOC_ID_PROALMFIL'])
                except:
                    print('Erro ',r_prl['LOC_ID_PROALMFIL'])                 
            
        funcao = 'produtos/'
        get_urlest = geturlest(funcao)
        payload = {'item': None}
        #Verificar se o Item ainda não foi cadastrado
        c_prod = requests.get(get_urlest, params=payload).json()
        if c_prod:
            for c_rs in c_prod:                
                funcao = 'GetItenslocalizacao/'                
                get_urlapi = geturlapi(funcao)                
                payload = {'id': c_rs['BXI_ID_PRODUTO']}
                c_prl = requests.get(get_urlapi, params=payload).json()                
                for r_prl in c_prl:
                    dados = r_prl
                    funcao = 'ItemAlmoxa/'
                    get_urlest = geturlest(funcao)
                    payload = {'item_almoxa': r_prl['LOC_ID_PROALMFIL']}
                    c_pl = requests.get(get_urlest, params=payload).json()                    
                    if not c_pl:
                        try:
                            print(dados)
                            c_respReq = requests.post(get_urlest, data=dados).json()
                        except:
                            print('Erro ',c_rs['BXI_ID_PRODUTO'])
                    else:
                        print('Cadastrado ',r_prl['LOC_ID_PROALMFIL'])
                    #Carimba a localização como sincronizada;
                    try:
                        con = getOracleConnection()
                        cur = con.cursor()
                        ref_cursor = con.cursor()                    
                        sparams =(r_prl['LOC_ID_PROALMFIL'],'S',ref_cursor)                        
                        cur.callproc('apt_intprod2.apt_put_itemalmoxa',(sparams))
                        c_rs2 = ref_cursor.fetchall()
                        cur.close
                        con.close
                        print('Carimbado',r_prl['LOC_ID_PROALMFIL'])
                    except:
                        print('Erro ',r_prl['LOC_ID_PROALMFIL'])                    
        print('Integração de Itens finalizada!')
    def Buscar_Operadores(self):
        print('Iniciando integração de operadores!')
        funcao = 'get_operadores/'
        get_urlapi = geturlapi(funcao)
        payload = {'filial': self.fil_in, 'operador':'all'}
        c_rs = requests.get(get_urlapi, params=payload).json()
        if c_rs:
            for rs in c_rs:                
                funcao = 'operador/'
                get_urlest = geturlprod(funcao)                
                payload = {'operador': rs.get('OPD_ST_ALTERNATIVO'), 'filial': self.fil_in}
                #Verificar se o Item ainda não foi cadastrado
                c_opd= requests.get(get_urlest, params=payload).json()
                #print(c_a['c_opd'])
                if not c_opd:                    
                    dados = {"OPD_ST_CRACHA": rs.get('OPD_ST_ALTERNATIVO'),
                             "OPD_ST_NOME": rs.get('OPD_ST_DESCRICAO'),
                             "FIL_IN_CODIGO": self.fil_in}
                    response = requests.post(get_urlest, data=dados)
                else:
                    print(print(rs))
                    pass
                    #print(c_a['CUS_ID_CCUSTO'])'''
        print('Integração de operadores finalizada!')
    def sincronizaLocal(self):
        print('Iniciando!')
        funcao = 'produtos/'
        get_urlest = geturlest(funcao)
        #print(get_urlest)
        payload = {}
        #print(get_urlest,payload)
        #Verificar se o Item ainda não foi cadastrado
        c_prod = requests.get(get_urlest, params=payload).json()
        for c_a in c_prod:
            print(c_a)
            #busca local de estoque configurado no item
            '''funcao = 'GetItenslocalizacao/'                
            get_urlapi = geturlapi(funcao)                
            payload = {'id': c_a['BXI_ID_PRODUTO'], 'filial':self.fil_in}
            c_prl = requests.get(get_urlapi, params=payload).json()            
            if c_prl:
                for r_prl in c_prl:
                    dados = r_prl
                    funcao = 'ItemAlmoxa/'
                    get_urlest = geturlest(funcao)
                    payload = {'item_almoxa': r_prl['LOC_ID_PROALMFIL']}
                    c_pl = requests.get(get_urlest, params=payload).json()
                    #print(c_pl)
                    if not c_pl:
                        try:
                            #print(c_a['BXI_ID_PRODUTO'])
                            c_respReq = requests.post(get_urlest, data=dados).json()
                        except:
                            print('Erro ',c_rs['BXI_ID_PRODUTO'])
                    else:
                        pass
                    #Carimba o item como itegrado                
                    try:
                        con = getOracleConnection()
                        cur = con.cursor()
                        ref_cursor = con.cursor()                    
                        sparams =(c_a['BXI_ID_PRODUTO'],c_a['PRO_CH_ACB'],'S',c_a['PRO_CH_ACB'],c_a['PRO_CH_ALMOXARIFADO'],ref_cursor)
                        #sparams1 =(rs[0],rs[6],'S',rs[6],rs[7])
                        #print(sparams1)                
                        cur.callproc('apt_intprod2.apt_PutItens',(sparams))
                        c_rs2 = ref_cursor.fetchall()
                        print('Carimbado',c_a['BXI_ID_PRODUTO'])
                except:
                    print('Erro ',c_a['BXI_ID_PRODUTO'])
                cur.close
                con.close
                #print(c_a['BXI_ID_PRODUTO'])
        print('Integração de Itens finalizada!') '''       
if __name__ == '__main__':
    contador = 1
    v_params = []
    v_params.append(2)
    v_params.append(3)
    v_params.append(1)
    #v_params.append('1003020000785')
    v_params.append('')
    init = integrador(v_params)
    #init.Buscar_Operadores()
    #init.sincronizaLocal()
    try:
        init.Integrarequisicao()
    except:
        pass
    try:
        init.apt_geraBaixaRequisicao()
    except:
        pass
    #retorno = init.get_centro_custos()
    #retorno = init.get_integracao(v_params)
    #init.Buscar_CentroCusto()
    #try:
    #init.Buscar_CadastroProdutos()
    #except:
        #pass
    '''try:
        init.Buscar_CadastroProdLocal(v_params[3])
    except:
        pass
    #init.IntegraInventario()
    try:
        init.Integrarequisicao()
    except:
        pass'''
