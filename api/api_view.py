# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import oracledb as cxo
from oracle_connection import getOracleConnection
import requests
from html import unescape

from django.utils import timezone

class IntApi:
    def __init__(self,pparams):
        self.fil_in = int(pparams.get('filial'))
        self.ordem_in = int(pparams.get('ordem'))
        c_operacoes = self.operacoes_ordem()
        for v_operacoes in c_operacoes:
            self.pro_in = v_operacoes['PRO_IN_CODIGO']
            self.org_in = v_operacoes['ORG_IN_CODIGO']
    def ord_demandas(self):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.ordem_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornademandadisp',(sparams))
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
    def ord_listDemandas(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select dem.com_in_codigo,
                              pro.pro_st_descricao,
                              dem.apt_re_qtdeselecionada,
                              dem.mvs_st_loteforne,
                              idp.adm_pck_util.f_formatacaract(dem.mvs_st_referencia) as mvs_st_referencia_desc
                         from idp.apt_apontademanda_estoque dem,
                              idp.est_produtos pro
                        where pro.pro_tab_in_codigo = dem.com_tab_in_codigo
                          and pro.pro_pad_in_codigo = dem.com_pad_in_codigo
                          and pro.pro_in_codigo = dem.com_in_codigo
                          and dem.ord_in_codigo     = :ord_in
                          and dem.com_pad_in_codigo = idp.pck_mega.achapadraodatabela(:fil_in,100,sysdate)''')
        cur.prepare(selectSQL)
        cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(com_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              apt_re_qtdeselecionada = float(rs[2]),
                              mvs_st_loteforne = rs[3],
                              mvs_st_referencia_desc = rs[4]))
        json_baixas= {}
        json_baixas = json.dumps(lista)
        return json_baixas

    def operacoes_ordem(self):
        json_operacoes = {}
        try:
            with getOracleConnection() as con:
                #print('Conexão estabelecida com sucesso!')
                with con.cursor() as cur:
                    #print('Cursor criado com sucesso!')
                    selectSQL =('''select ord.org_tab_in_codigo,
                                          ord.org_pad_in_codigo,
                                          ord.org_in_codigo,
                                          ord.org_tau_st_codigo,
                                          ord.ord_tab_in_codigo,
                                          ord.ord_seq_in_codigo,
                                          ord.ord_in_codigo,
                                          ord.pro_tab_in_codigo,
                                          ord.pro_pad_in_codigo,
                                          ord.pro_in_codigo,
                                          pgo.plf_in_sqoperacao
                                     from idp.pro_ordens ord,
                                          idp.pro_prog_ordem pgo
                                    where ord.org_tab_in_codigo = pgo.org_tab_in_codigo
                                      and ord.org_pad_in_codigo = pgo.org_pad_in_codigo
                                      and ord.org_in_codigo = pgo.org_in_codigo
                                      and ord.org_tau_st_codigo = pgo.org_tau_st_codigo
                                      and ord.ord_tab_in_codigo = pgo.ord_tab_in_codigo
                                      and ord.ord_seq_in_codigo = pgo.ord_seq_in_codigo
                                      and ord.ord_in_codigo = pgo.ord_in_codigo
                                      and pgo.plf_in_sqoperacao = (select min(po.plf_in_sqoperacao)
                                                                     from idp.pro_prog_ordem po
                                                                    where po.org_tab_in_codigo = pgo.org_tab_in_codigo
                                                                      and po.org_pad_in_codigo = pgo.org_pad_in_codigo
                                                                      and po.org_in_codigo     = pgo.org_in_codigo
                                                                      and po.org_tau_st_codigo = pgo.org_tau_st_codigo
                                                                      and po.ord_tab_in_codigo = pgo.ord_tab_in_codigo
                                                                      and po.ord_seq_in_codigo = pgo.ord_seq_in_codigo
                                                                      and po.ord_in_codigo     = pgo.ord_in_codigo
                                                                      and po.tmp_ch_aponta     = 'S'                                                          
                                                                    )
                                    and ord.fil_in_codigo = :fil_in
                                    and ord.ord_in_codigo = :ord_in''')
                    cur.prepare(selectSQL)
                    cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
                    columns = [col[0] for col in cur.description]
                    c_rs = [dict(zip(columns, row)) for row in cur.fetchall()]
                    '''columns = [col[0] for col in cur.description]
                    cur.rowfactory = lambda *args: dict(zip(columns, args))
                    c_rs = cur.fetchall()'''
                    
                    return c_rs
        except cxo.Error as e:
            print(f"Erro: {e}")
        return json_operacoes       
    def lista_ocorrencia(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select a.ati_tab_in_codigo,
                              a.ati_pad_in_codigo,
                              a.ati_in_codigo,
                              a.ati_st_nome
                         from idp.pro_atividade a
                        where a.ati_ch_produtiva = 'I'
                              and a.ati_pad_in_codigo = idp.pck_mega.achapadraodatabela(:fil_in, 204, sysdate)
                              order by a.ati_in_codigo''')
        cur.prepare(selectSQL)
        cur.execute(None, {'fil_in': self.fil_in})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(ati_tab_in_codigo = int(rs[0]),
                              ati_pad_in_codigo = int(rs[1]),
                              ati_in_codigo = int(rs[2]),
                              ati_st_nome = rs[3]))
        json_motivos = {}
        json_motivos = json.dumps(lista)
        return json_motivos
    def list_lotes(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =(''' select apl.pro_in_codigo,
                               pro.pro_st_descricao,
                               apl.orl_re_qtdlote,
                               apl.orl_re_unidade,
                               apl.orl_st_lotefabricacao,
                               nvl(idp.adm_pck_util.f_formatacaract(apl.orl_st_referencia),'*') as mvs_st_referencia_desc,
                               apl.orl_st_referencia
                        from idp.apt_apontaordem_lote apl,
                             idp.est_produtos pro
                       where pro.pro_tab_in_codigo = apl.pro_tab_in_codigo
                         and pro.pro_pad_in_codigo = apl.pro_pad_in_codigo
                         and pro.pro_in_codigo = apl.pro_in_codigo
                         and apl.ord_in_codigo = :ord_in
                         and apl.fil_in_codigo  = :fil_in
                         order by to_number(apl.orl_st_slotefabricacao)''')
        cur.prepare(selectSQL)
        cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pro_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              orl_re_qtdlote = float(rs[2]),
                              orl_re_unidade = rs[3],
                              orl_st_lotefabricacao = rs[4],
                              mvs_st_referencia_desc = rs[5],
                              orl_st_referencia = rs[6]))
        json_producao= {}
        json_producao = json.dumps(lista)
        return json_producao
    def itn_referencias(self):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.pro_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornacaracteristica',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(rat_in_codigo = int(rs[0]),
                              rat_st_opcoes = rs[1],
                              itn_desc = rs[2],
                              rat_desc = rs[3],
                              rat_ch_tipo = rs[4],
                              ref_rat_value = rs[5],
                              rfc_in_codigo = int(rs[6])))
        json_referencia= {}
        json_referencia = json.dumps(lista)
        return json_referencia

    def itn_atributos(self):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.pro_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornaatributo',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pai_rat_in_codigo = int(rs[0]),
                                  rat_in_codigo = int(rs[1]),
                                  rat_st_descricao = rs[2],
                                  rat_value = rs[3],
                                  rat_ch_tipo = rs[4]))
        json_atributo= {}
        json_atributo = json.dumps(lista)
        return json_atributo
    def itens_ordem(self):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams =(self.fil_in,self.ordem_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornaitens',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pro_in_codigo = int(rs[2]),
                             pro_st_descricao = rs[3],
                              uni_st_unidade = rs[4],
                             rfc_in_codigo = int(rs[5])
                             ))
        json_itens= {}
        json_itens = json.dumps(lista)
        #print(json_itens)
        return json_itens

class GetDadosProducao:
    def __init__(self):
        self.org_in = None
        self.ord_seq = None
        self.ordem_in = None
        self.fil_in = None
        self.pro_in = None
        self.pro_id = None
        self.umidade = None
        self.rfc_in_codigo = None
        self.param = None
        self.lote = None
        #print('Iniciando')
    def situacao_ordem(self,pparams):
        self.fil_in = pparams.get('filial')
        self.ord_in = pparams.get('ordem')
        v_retorno = {'situacao': 'AB'}
        try:
        #if 1==1:
            with getOracleConnection() as con:
                #print('Conexão estabelecida com sucesso!')
                with con.cursor() as cur:
                    #print('Cursor criado com sucesso!')
                    c_rs = cur.callfunc('apt_intprod2.f_valida_sitordem',str,[self.fil_in, self.ord_in])                                                
                    if c_rs:
                        #print(c_rs)
                        v_retorno['situacao'] = c_rs
                    else:
                        v_retorno['situacao'] =  'AB'
        except:
            v_retorno['situacao'] =  'AB'        
        return [v_retorno]
    def get_saldo(self,pparams):
        self.fil_in = pparams['filial']
        self.lote = pparams['lote']
        try:
            with getOracleConnection() as con:
                #print('Conexão estabelecida com sucesso!')
                with con.cursor() as cur:
                    #print('Cursor criado com sucesso!')
                    ref_cursor = con.cursor()
                    sparams = (self.fil_in, self.lote, ref_cursor)
                    cur.callproc('apt_intprod2.p_saldolote', sparams)
                    columns = [col[0] for col in ref_cursor.description]
                    c_rs = ref_cursor.fetchall()
                    json_saldo = [dict(zip(columns, row)) for row in c_rs]
                    '''for row in json_saldo:
                        print(row)'''
        except cxo.Error as e:
            print(f"Erro: {e}")       
        return json_saldo
    def get_integracao(self,pparams):
        #integrações
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
                                 (ord.ord_ch_modificada = :status)
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
                cur.execute(None, {'ord_ch_integrada': 'N','org_in_codigo':pparams[0],'status':pparams[3]})
            else:
                cur.execute(None, {'ord_ch_integrada': 'N',
                                   'fil_in_codigo': pparams[1],
                                   'ord_in_codigo': pparams[2],
                                   'status':pparams[3]
                                   })
            c_rs = cur.fetchall()
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
    def get_pro_ordens(self, pparams):
        self.org_in = pparams[0]
        self.ord_seq = pparams[1]
        self.ordem_in = pparams[2]        
        selectSQL =('''select ord.org_tab_in_codigo,
                              ord.org_pad_in_codigo,
                              ord.org_in_codigo,
                              ord.org_tau_st_codigo,
                              ord.ord_tab_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo,
                              ord.pro_tab_in_codigo,
                              ord.pro_pad_in_codigo,
                              ord.pro_in_codigo,
                              ord.ord_re_qtde_ordem,
                              ord.fil_in_codigo,
                              ord.tpo_st_codigo_tipo,
                              nvl(oce.ord_re_umidade,0) ord_re_umidade,
                              decode(oce.ord_re_estufa,
                                                  null,
                                                  null,
                                                  lpad(oce.ord_re_estufa,2,0)||'/'||
                                                  lpad(oce.ord_re_carga,2,0)||'/'||
                                                  decode(oce.ord_re_ano,
                                                                   null,
                                                                   to_char(sysdate,'yy'),
                                                                   lpad(oce.ord_re_ano,2,0))
                              ) as lote_ordem,
                              oce.ord_st_destino,
                              lpad(ord.org_tab_in_codigo,3,0)||
                              lpad(ord.org_pad_in_codigo,3,0)||
                              lpad(ord.org_in_codigo,7,0)||
                              lpad(ord.org_tau_st_codigo,3,0)||
                              lpad(ord.ord_tab_in_codigo,3,0)||
                              lpad(ord.ord_seq_in_codigo,3,0)||
                              lpad(ord.ord_in_codigo,20,0) as ord_st_id,
                              lpad(ord.pro_tab_in_codigo,3,0)||
                              lpad(ord.pro_pad_in_codigo,3,0)||
                              lpad(ord.pro_in_codigo,7,0) as pro_st_id,
                              lpad(ord.tpo_tab_in_codigo,3,0)||
                              lpad(ord.tpo_pad_in_codigo,3,0)||
                              lpad(ord.tpo_st_codigo_tipo,6,0) as tpo_st_id,
                              oce.ord_st_origem 
                         from pro_ordens ord,
                              pro_ordenscmpesp oce
                        where ord.org_tab_in_codigo = oce.org_tab_in_codigo (+)
                          and ord.org_pad_in_codigo = oce.org_pad_in_codigo (+)
                          and ord.org_in_codigo     = oce.org_in_codigo     (+)
                          and ord.org_tau_st_codigo = oce.org_tau_st_codigo (+)
                          and ord.ord_tab_in_codigo = oce.ord_tab_in_codigo (+)
                          and ord.ord_seq_in_codigo = oce.ord_seq_in_codigo (+)
                          and ord.ord_in_codigo     = oce.ord_in_codigo     (+)                     
                          and ord.org_in_codigo = :org_in_codigo
                          and ord.ord_seq_in_codigo = :ord_seq_in_codigo
                          and ord.ord_in_codigo = :ord_in_codigo
                        order by ord.ord_in_codigo''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'org_in_codigo': self.org_in,'ord_seq_in_codigo': self.ord_seq,'ord_in_codigo':self.ordem_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:            
            if rs[13] is None:
                self.umidade = 0
            else:
                self.umidade = int(rs[13])                
            lista.append(dict(ORG_TAB_IN_CODIGO = int(rs[0]),
                              ORG_PAD_IN_CODIGO = int(rs[1]),
                              ORG_IN_CODIGO = int(rs[2]),
                              ORG_TAU_ST_CODIGO = rs[3],
                              ORD_TAB_IN_CODIGO = int(rs[4]),
                              ORD_SEQ_IN_CODIGO = int(rs[5]),
                              ORD_IN_CODIGO = int(rs[6]),
                              PRO_TAB_IN_CODIGO = int(rs[7]),
                              PRO_PAD_IN_CODIGO = int(rs[8]),
                              PRO_IN_CODIGO = int(rs[9]),
                              ORD_RE_QTDE_ORDEM = float(rs[10]),
                              FIL_IN_CODIGO = int(rs[11]),
                              TPO_ST_CODIGO_TIPO = rs[12],
                              ORD_RE_UMIDADE = self.umidade,
                              LOTE_ORDEM = rs[14],
                              ORD_ST_DESTINO = rs[15],
                              PRO_ST_ID = rs[17],
                              ORD_ST_ID = rs[16],
                              TPO_ST_ID = rs[18],
                              ORD_ST_ORIGEM = rs[19]
                              ))        
        json_getOrdens= {}
        json_getOrdens = json.dumps(lista)
        return json_getOrdens
    def put_pro_ordens(self,pparams):
        v_return = False
        self.org_in = pparams[0]
        self.ord_seq = pparams[1]
        self.ordem_in = pparams[2]
        self.param = pparams[3]
        v_up = {'status':self.param,
                'org_in_codigo':self.org_in,
                'ord_seq_in_codigo':self.ord_seq,
                'ord_in_codigo':self.ordem_in}
        ExecSQL =('''update idp.int_pro_ordens ord
                        set ord.ord_ch_integrada = 'S',
                            ord.ord_ch_modificada = :status
                        where (
                                 (ord.ord_ch_integrada = 'N')or
                                 (ord.ord_ch_modificada <> :status)
                              )
                          and ord.org_in_codigo = :org_in_codigo
                          and ord.ord_seq_in_codigo = :ord_seq_in_codigo 
                          and ord.ord_in_codigo = :ord_in_codigo''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(ExecSQL)
            cur.execute(None, v_up)
            cur.close
            con.commit()
            con.close
            v_return = True
        except cxo.Error as error:
            v_return = False
        return v_return
    def itn_referencias(self,pparams):
        self.fil_in = pparams[0]
        self.pro_in = pparams[1]
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.pro_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornacaracteristica',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(rat_in_codigo = int(rs[0]),
                              rat_st_opcoes = rs[1],
                              itn_desc = rs[2],
                              rat_desc = rs[3],
                              rat_ch_tipo = rs[4],
                              ref_rat_value = rs[5],
                              rfc_in_codigo = int(rs[6])))
        json_referencia= {}
        json_referencia = json.dumps(lista)
        return json_referencia
    def itn_atributos(self,pparams):
        self.fil_in = pparams[0]
        self.pro_in = pparams[1]
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.pro_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornaatributo',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pai_rat_in_codigo = int(rs[0]),
                                  rat_in_codigo = int(rs[1]),
                                  rat_st_descricao = rs[2],
                                  rat_value = rs[3],
                                  rat_ch_tipo = rs[4]))
        json_atributo= {}
        json_atributo = json.dumps(lista)
        return json_atributo
    def itens_ordem(self,pparams):
        self.fil_in = pparams[0]
        self.ordem_in = pparams[1]
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams =(self.fil_in,self.ordem_in,ref_cursor)
        cur.callproc('idp.apt_intprod2.apt_retornaitens',(sparams))
        #columns = [col[0] for col in ref_cursor.description]
        #ref_cursor.rowfactory = lambda *args: dict(zip(columns, args))
        c_rs = ref_cursor.fetchall()
        #print(c_rs)
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pro_pad_in_codigo = int(rs[1]),
                              pro_in_codigo = int(rs[2]),
                              pro_st_descricao = rs[3],
                              uni_st_unidade = rs[4],
                              rfc_in_codigo = int(rs[5]),
                              pro_re_comprimento = rs[6],
                              pro_re_largura = rs[7],
                              pro_re_espessura = rs[8],
                              pro_st_madeira= rs[9],
                              mvs_st_referencia = rs[10],
                              pro_st_id = rs[11],
                              pro_re_perda = rs[13],
                              tipo_item = rs[14]
                             ))
        json_itens= {}
        json_itens = json.dumps(lista)
        #print(json_itens)
        return json_itens
    def demandas_ordem(self,pparams):
        self.org_in = pparams[0]
        self.ord_seq = pparams[1]
        self.ordem_in = pparams[2]
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams =(self.org_in,self.ord_seq,self.ordem_in,ref_cursor)
        cur.callproc('idp.apt_intprod.apt_retornaDemanda',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(com_in_codigo = int(rs[9]),
                              com_st_descricao = rs[12],
                              uni_st_unidade = rs[13]
                             ))
        json_itens= {}
        json_itens = json.dumps(lista)
        #print(json_itens)
        return json_itens
    def get_centro_custos(self,pParams):
        lista = []
        self.fil_in = pParams['filial']
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
                         from idp.con_centro_custo cc
                        where cc.cus_ch_tipo_conta = 'A'
                          and cc.cus_pad_in_codigo = idp.pck_mega.achapadraodatabela(:fil_in,2,sysdate)
                        order by cc.cus_in_reduzido''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.fil_in})
            c_rs = cur.fetchall()            
            cur.close
            con.close
            #print('Linha 742',c_rs)
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
    def get_CadastroProdutos(self,pParams):
        lista = []
        json_getCadItens= {}
        self.pro_id = pParams['id']
        self.fil_in = pParams['filial']        
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
                          and pro.pro_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in, 100, sysdate)
                          and (
                                   (lpad(pro.pro_tab_in_codigo,3,'0')||
                                    lpad(pro.pro_pad_in_codigo,3,'0')||
                                    lpad(pro.pro_in_codigo,7,'0') = :id_produto) 
                                or
                                   (pro.pro_in_codigo = :id_produto) 
                                or
                                   (:id_produto is null)
                               )                          
                          and nvl(pce.pro_ch_almoxarifado,'N') = 'N'
                          --and nvl(pce.pro_st_orialteracao,'M') = 'M'
                        order by pro.pro_in_codigo''')           
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in':self.fil_in,'id_produto': self.pro_id})                        
            c_rs = cur.fetchall()
            cur.close
            con.close
            if c_rs:
                for rs in c_rs:
                    lista.append(dict(BXI_ID_PRODUTO = rs[0],
                              PRO_TAB_IN_CODIGO = int(rs[1]),
                              PRO_PAD_IN_CODIGO = int(rs[2]),
                              PRO_IN_CODIGO = int(rs[3]),
                              PRO_ST_DESCRICAO = rs[4],
                              UNI_ST_UNIDADE = rs[5]))
                    #Carimba o item como itegrado
                    try:
                        con = getOracleConnection()
                        cur = con.cursor()                                        
                        ref_cursor = con.cursor()
                        sparams =(rs[0],rs[6],'S',rs[6],rs[7],ref_cursor)
                        cur.callproc('idp.apt_intprod2.apt_PutItens',(sparams))
                        c_rs2 = ref_cursor.fetchall()
                        cur.close
                        con.close
                    except:
                       pass                    
        #except cxo._Error as error:
        except:
            lista.append(dict(BXI_ID_PRODUTO = None,
                              PRO_TAB_IN_CODIGO = None,
                              PRO_PAD_IN_CODIGO = None,
                              PRO_IN_CODIGO = None,
                              PRO_ST_DESCRICAO = None,
                              UNI_ST_UNIDADE = None))
        json_getCadItens = json.dumps(lista)
        #print(json_getCadItens)
        return json_getCadItens
    def get_CaracteristicaPadrao(self,pparams):
        self.fil_in = pparams[0]
        self.pro_in = pparams[1]
        selectSQL =('''select rfc.mvs_st_referencia 
                         from cus_tb_estprodutoreferencia rfc
                        where t.pro_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 100, sysdate)
                          and t.pro_in_codigo     = :pro_in_codigo''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'pro_in_codigo': self.pro_in,'fil_in_codigo':self.fil_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:
            lista.append(dict(mvs_st_referencia = rs[0]))
        json_getrfc= {}
        json_getrfc = json.dumps(lista)
        return json_getrfc
    def get_Prouni(self,pparams):
        self.fil_in = pparams[0]
        self.pro_in = pparams[1]
        selectSQL =(''' select fu.*
                          from (select lpad(pun.pro_tab_in_codigo,3,0)||
                                       lpad(pun.pro_pad_in_codigo,3,0)||
                                       lpad(pun.pro_in_codigo,7,0)||
                                       lpad(pun.pun_in_sequencia,3,0) as pun_st_id,
                                       lpad(fmt.fmt_tab_in_codigo,3,0)||
                                       lpad(fmt.fmt_pad_in_codigo,3,0)||
                                       lpad(fmt.fmt_st_codigo,4,0) as fmt_st_id,
                                       lpad(pun.pro_tab_in_codigo,3,0)||
                                       lpad(pun.pro_pad_in_codigo,3,0)||       
                                       lpad(pun.pro_in_codigo,7,0) as pro_st_id,                                      
                                       fmt.fmt_st_codigo,
                                       fmt.fmt_st_nome,
                                       pun.uni_st_unidade,
                                       (select pfa.uni_st_formula 
                                          from est_fatorunidade pfa
                                         where pfa.fmt_tab_in_codigo = pun.fmt_tab_in_codigo
                                           and pfa.fmt_pad_in_codigo = pun.fmt_pad_in_codigo
                                           and pfa.fmt_st_codigo     = pun.fmt_st_codigo
                                           and pfa.uni_tab_in_codigo = pun.uni_tab_in_codigo
                                           and pfa.uni_pad_in_codigo = pun.uni_pad_in_codigo
                                           and pfa.un1_st_unidade    = pun.uni_st_unidade
                                           and pfa.un2_st_unidade    = pro.uni_st_unidade
                                       ) formula
                                  from est_prouni pun,
                                       est_produtos pro,
                                       est_formatos fmt
                                 where pun.pro_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 100, sysdate)
                                   and pun.pro_tab_in_codigo = pro.pro_tab_in_codigo
                                   and pun.pro_pad_in_codigo = pro.pro_pad_in_codigo
                                   and pun.pro_in_codigo     = pro.pro_in_codigo
                                   and pun.fmt_tab_in_codigo = fmt.fmt_tab_in_codigo
                                   and pun.fmt_pad_in_codigo = fmt.fmt_pad_in_codigo
                                   and pun.fmt_st_codigo     = fmt.fmt_st_codigo
                                   and pun.pro_in_codigo     = :pro_in_codigo or :pro_in_codigo = 0) fu
                                 where fu.formula is not null''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'pro_in_codigo': self.pro_in,'fil_in_codigo':self.fil_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:
            lista.append(dict(pun_st_id = rs[0],
                              fmt_st_id = rs[1],
                              pro_st_id = rs[2],
                              fmt_st_codigo = rs[3],
                              fmt_st_nome = rs[4],
                              uni_st_unidade = rs[5],
                              formula = rs[6]
                              ))
        json_getpun= {}
        json_getpun = json.dumps(lista)
        return json_getpun
    def get_configAponta(self,pdados):
        self.fil_in = pdados.get('filial')
        selectSQL =('''select lpad(cfg.ctr_tab_in_codigo,3,0)||
                              lpad(cfg.ctr_pad_in_codigo,3,0)||
                              lpad(cfg.ctr_in_codigo,7,0)||
                              lpad(cfg.cmaq_tab_in_codigo,3,0)||
                              lpad(cfg.cmaq_pad_in_codigo,3,0)||
                              lpad(cfg.cmaq_in_codigo,7,0)||
                              lpad(cfg.opr_tab_in_codigo,3,0)||
                              lpad(cfg.opr_pad_in_codigo,3,0)||
                              lpad(cfg.opr_in_codigo,7,0) as cfg_st_id,
                              lpad(cfg.ctr_tab_in_codigo,3,0)||
                              lpad(cfg.ctr_pad_in_codigo,3,0)||
                              lpad(cfg.ctr_in_codigo,7,0) as ctr_st_id,
                              lpad(cfg.cmaq_tab_in_codigo,3,0)||
                              lpad(cfg.cmaq_pad_in_codigo,3,0)||
                              lpad(cfg.cmaq_in_codigo,7,0) as cmaq_st_id,
                              lpad(cfg.opr_tab_in_codigo,3,0)||
                              lpad(cfg.opr_pad_in_codigo,3,0)||
                              lpad(cfg.opr_in_codigo,7,0) as opr_st_id,
                              cfg.cus_bo_naobaixademanda,
                              cfg.cus_bo_geraseqpallet,
                              cfg.cus_bo_conversor,
                              cfg.cus_bo_lotes
                         from apt_pro_maquina_config cfg,
                              pro_operacoes opr,
                              pro_maquina ctr,
                              pro_cadmaquinas cmq
                        where cfg.cmaq_tab_in_codigo = cmq.cmaq_tab_in_codigo
                          and cfg.cmaq_pad_in_codigo = cmq.cmaq_pad_in_codigo
                          and cfg.cmaq_in_codigo     = cmq.cmaq_in_codigo
                          and cfg.opr_tab_in_codigo  = opr.opr_tab_in_codigo
                          and cfg.opr_pad_in_codigo  = opr.opr_pad_in_codigo
                          and cfg.opr_in_codigo      = opr.opr_in_codigo
                          and cfg.ctr_tab_in_codigo  = ctr.maq_tab_in_codigo
                          and cfg.ctr_pad_in_codigo  = ctr.maq_pad_in_codigo
                          and cfg.ctr_in_codigo      = ctr.maq_in_codigo
                          and cfg.ctr_tab_in_codigo  = 207
                          and cfg.ctr_pad_in_codigo  = pck_mega.achapadraodatabela(:fil_in_codigo, 207, sysdate)
                          --and cfg.cus_bo_integraacb   = 'N'
                          ''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in_codigo':self.fil_in})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            #print(c_rs)
            #transformar QueryDict em dicionario;
            #print(c_rs.dict())
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
    def get_tipoOrdens(self,pdados):
        self.fil_in = pdados.get('filial')
        selectSQL =('''select lpad(tpo.tpo_tab_in_codigo,3,0)||
                              lpad(tpo.tpo_pad_in_codigo,3,0)||
                              lpad(tpo.tpo_st_codigo_tipo,5,0) as tpo_st_id,
                              tpo.tpo_st_codigo_tipo,
                              null as tpo_st_unidade,
                              'False' tpo_st_selconversor,
                              'N' as tpo_st_operacao,                              
                              tpo.tpo_st_nome
                         from pro_tipoordens tpo
                        where tpo.tpo_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 224, sysdate)
                          ''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in_codigo':self.fil_in})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
        pass
    def get_pro_conversor(self,pdados):
        self.fil_in = pdados.get('fil_in_codigo')
        self.pro_in = pdados.get('pro_in_codigo')
        selectSQL =('''select fmt.fmt_st_nome, 
                              fu.uni_st_formula,
                              fu.uni_st_fator
                         from est_fatorunidade fu,
                              est_formatos fmt,
                              (select pro.uni_st_unidade,
                                      pun.uni_st_unidade fmt_st_unidade,
                                      pun.fmt_tab_in_codigo,
                                      pun.fmt_pad_in_codigo,
                                      pun.fmt_st_codigo
                                 from est_prouni pun,
                                      est_produtos pro
                                where pun.pro_tab_in_codigo = pro.pro_tab_in_codigo
                                  and pun.pro_pad_in_codigo = pro.pro_pad_in_codigo
                                  and pun.pro_in_codigo     = pro.pro_in_codigo
                                  and pun.pro_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 100, sysdate)
                                  and pun.pro_in_codigo     = :pro_in_codigo) ci
                        where fu.fmt_tab_in_codigo = fmt.fmt_tab_in_codigo
                          and fu.fmt_pad_in_codigo = fmt.fmt_pad_in_codigo
                          and fu.fmt_st_codigo     = fmt.fmt_st_codigo
                          and ci.fmt_tab_in_codigo = fu.fmt_tab_in_codigo
                          and ci.fmt_pad_in_codigo = fu.fmt_pad_in_codigo
                          and ci.fmt_st_codigo     = fu.fmt_st_codigo
                          and ci.uni_st_unidade    = fu.un2_st_unidade
                          and ci.fmt_st_unidade    = fu.un1_st_unidade''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in_codigo':self.fil_in, 'pro_in_codigo': self.pro_in})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            cr_rs = cur.fetchall()
        except cxo._Error as error:
            pass
        return cr_rs
        pass
    def get_ref_atributos(self,pdados):
        self.fil_in = pdados.get('filial')
        self.rfc_in_codigo = pdados.get('referencia')
        selectSQL =('''select lpad(cr.rat_tab_in_codigo,3,'0')||
                              lpad(cr.rat_pad_in_codigo,3,'0')||
                              lpad(cr.rat_in_codigo,7,'0')||
                              lpad(cr.rfc_tab_in_codigo,3,'0')||
                              lpad(cr.rfc_pad_in_codigo,3,'0')||
                              lpad(cr.rfc_in_codigo,7,'0') as car_st_id, 
                              lpad(cr.rat_tab_in_codigo,3,'0')||
                              lpad(cr.rat_pad_in_codigo,3,'0')||
                              lpad(cr.rat_in_codigo,7,'0') as rat_st_id, 
                              lpad(cr.rfc_tab_in_codigo,3,'0')||
                              lpad(cr.rfc_pad_in_codigo,3,'0')||
                              lpad(cr.rfc_in_codigo,7,'0') as rfc_st_id, 
                              ar.pai_rat_in_codigo,
                              ar.rat_in_codigo,
                              ar.rat_st_descricao,
                              case 
                                 when ar.rat_ch_tipo = 'P' then
                                    lpad(ar.pai_rat_in_codigo,7,'0')||'='||ar.rat_in_codigo
                                  else 
                                    lpad(ar.rat_in_codigo,7,'0')||'='
                              end as rat_value,
                              ar.rat_ch_tipo,
                              cr.car_in_prioridade,
                              cr.rfc_in_codigo,
                              case when ar.pai_rat_in_codigo = ar.rat_in_codigo then 'S' else 'N' end as rat_bo_grupo_new,
                               ar.rat_bo_grupo,
                              cr.car_bo_obrigatorio,
                              pai.rat_st_descricao as pai_st_descricao
                         from est_atributoreferencia ar,
                              est_caracatributoreferencia cr,
                              est_atributoreferencia pai
                        where ar.rat_tab_in_codigo = cr.rat_tab_in_codigo
                          and ar.rat_pad_in_codigo = cr.rat_pad_in_codigo
                          and ar.rat_in_codigo = cr.rat_in_codigo
                          and pai.rat_tab_in_codigo = ar.rat_tab_in_codigo
                          and pai.rat_pad_in_codigo = ar.rat_pad_in_codigo
                          and pai.rat_in_codigo = ar.pai_rat_in_codigo
                          and cr.rfc_in_codigo = :rfc_in_codigo
                          and cr.rfc_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 141, sysdate)
                        order by cr.rfc_in_codigo,cr.car_in_prioridade''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in_codigo':self.fil_in,'rfc_in_codigo': self.rfc_in_codigo})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
        pass
    
class IntegrarProducao:
    def __init__(self):
        self.org_in = None
        self.ord_seq = None
        self.ordem_in = None
        self.cmaq_st_id = None
        self.ord_st_id = None
    def apt_integrarlote(self, pparams):
        v_listlote = pparams
        self.cmaq_st_id = v_listlote.get('cmaq_st_id')
        self.ord_st_id = v_listlote.get('ord_st_id')
        #transformar QueryDict em dicionario;
        #print(v_listlote.dict())
        lista = []
        if (1==1):
        #try:
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
        else:
        #except cxo._Error as e:
        #    error_obj, = e.args
            lista.append(dict(sequencia = 0,
                              mensagem = 'Erro',
                              mensagem_sub = 'Erro'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno
    def apt_integrarDemanda(self, pparams):
        lista = []
        v_retorno = {}
        v_listDem = pparams
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
    def apt_integraraponta(self, pparams):
        v_listlote = v_params = json.loads(pparams)
        lista = []
        self.cmaq_st_id = v_listlote.get('cmaq_st_id')
        self.ord_st_id = v_listlote.get('ord_st_id')
        #transformar QueryDict em dicionario;
        #print(v_listlote.dict())
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

        except cxo._Error as e:
            error_obj, = e.args
            lista.append(dict(sequencia = 0,
                              mensagem = 'Erro',
                              mensagem_sub = 'Erro'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno
    def apt_integrarBaixas(self, pparams):
        lista = []
        v_retorno = {}
        v_listDem = json.loads(pparams)
        #print(v_listDem)
        #if (1==1):
        try:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
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
                       str(v_listDem.get('ord_st_id'))
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
        #else:
        except:
            lista.append(dict(mensagem =  'Erro',
                              item = 0,
                               Sequencia = 0))
        v_retorno = json.dumps(lista)
        return v_retorno

class GetDadosMaquina:
    def __init__(self):
        self.org_in = None
        self.fil_in = None
        self.ord_seq = None
        self.ordem_in = None
        self.maq_in = None
        self.cmaq_in = None
    def apt_GetDadosMaquina(self):
        self.fil_in = 3
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.fil_in)
        cur.callproc('idp.apt_intprod.apt_GetDadosMaquina',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        if c_rs:
            for v_rs in c_rs:
                lista.append(dict(CTR_ST_ID = v_rs[0],
                                  CMAQ_ST_ID = v_rs[1],
                                  CTR_ST_NOME = v_rs[2],
                                  CMAQ_ST_NOME = v_rs[3],
                                  CMAQ_ST_CODIGO = v_rs[4]
                                  ))
        else:
            lista.append(dict(CTR_ST_ID = '0',
                                  CMAQ_ST_ID = '0',
                                  CTR_ST_NOME = '0',
                                  CMAQ_ST_NOME = '0',
                                  CMAQ_ST_CODIGO = '0'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno

    def apt_PutDadosMaquina(self, pparams):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor, pparams[0],pparams[1])
        cur.callproc('idp.apt_intprod.apt_PutDadosMaquina',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        if c_rs:
            for v_rs in c_rs:
                lista.append(dict(mensagem = v_rs[0]))
        else:
            lista.append(dict(mensagem = 'Não executado!'))
        v_retorno = {}
        v_retorno = json.dumps(lista)
        return v_retorno

class GetDadosRecebimento:
    def __init__(self):
        self.pdc_id = None
        self.pdi_id = None
        self.item_pdc_id = None
        self.mvl_st_loteini = None
        self.mvl_st_lotefim = None
    def get_recebimento(self,pdados):
        self.item_pdc_id = pdados.get('id')
        selectSQL =('''select avr.* 
                         from cus_vw_api_lotesavisoreceb avr
                        where avr.pdc_st_id||avr.pdi_st_id = :item_pdc_id''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'item_pdc_id':self.item_pdc_id})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
        pass
    def get_LotesReceb(self,pdados):
        v_sep = ';'
        self.avr_st_nota = pdados.get('nota')
        self.fil_in_codigo = pdados.get('filial')
        self.mvl_st_loteforne = pdados.get('lote')
        v_busca = self.mvl_st_loteforne.find(v_sep)
        #verificar se o lote é intervalo
        if v_busca > 0:
            self.mvl_st_loteini, self.mvl_st_lotefim = self.mvl_st_loteforne.split(v_sep)
        elif self.mvl_st_loteforne == '0':
            self.mvl_st_loteini = self.mvl_st_loteforne
        else:
            self.mvl_st_loteini = self.mvl_st_loteforne
            self.mvl_st_lotefim = self.mvl_st_loteforne
        
        selectSQL =('''select mvl.fil_in_codigo,
                              rci.pro_in_codigo,
                              rcb.avr_st_nota,
                              trunc(rcb.avr_dt_emissaonf)avr_dt_emissaonf,
                              trunc(rcb.avr_dt_entradanf)avr_dt_entradanf,
                              mvl.mvl_st_loteforne,
                              mvl.mvl_re_quantidade,
                              pro.pro_st_descricao,
                              substr(mvl.mvl_st_loteforne,17) sequencial,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Classificacao') classificacao,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Volume') volume,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Comprimento') comprimento,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Largura') largura,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Origem') origem,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Pilha') pilha
                         from est_itensavisorecebimento rci,
                              est_avisorecebimento rcb,
                              est_movtoaviso mav,
                              est_lotesmovimento mvl,
                              est_produtos pro
                        where rci.org_tab_in_codigo = rcb.org_tab_in_codigo
                          and rci.org_pad_in_codigo = rcb.org_pad_in_codigo
                          and rci.org_in_codigo = rcb.org_in_codigo
                          and rci.org_tau_st_codigo = rcb.org_tau_st_codigo
                          and rci.ser_tab_in_codigo = rcb.ser_tab_in_codigo
                          and rci.ser_in_sequencia = rcb.ser_in_sequencia
                          and rci.avr_in_codigo = rcb.avr_in_codigo
                          and rci.org_tab_in_codigo = mav.org_tab_in_codigo
                          and rci.org_pad_in_codigo = mav.org_pad_in_codigo
                          and rci.org_in_codigo = mav.org_in_codigo
                          and rci.org_tau_st_codigo = mav.org_tau_st_codigo
                          and rci.ser_tab_in_codigo = mav.avr_ser_tab_in_codigo
                          and rci.ser_in_sequencia = mav.avr_ser_in_sequencia
                          and rci.avr_in_codigo = mav.avr_in_codigo
                          and rci.iar_in_sequencia = mav.iar_in_sequencia
                           
                          and mav.org_tab_in_codigo = mvl.org_tab_in_codigo
                          and mav.org_pad_in_codigo = mvl.org_pad_in_codigo
                          and mav.org_in_codigo = mvl.org_in_codigo
                          and mav.org_tau_st_codigo = mvl.org_tau_st_codigo
                          and mav.ser_tab_in_codigo = mvl.ser_tab_in_codigo
                          and mav.ser_in_sequencia = mvl.ser_in_sequencia
                          and mav.mvt_in_lancam = mvl.mvt_in_lancam
                           
                          and pro.pro_tab_in_codigo = mvl.pro_tab_in_codigo
                          and pro.pro_pad_in_codigo = mvl.pro_pad_in_codigo
                          and pro.pro_in_codigo     = mvl.pro_in_codigo
                           
                          and rcb.avr_st_nota like '%'||:avr_st_nota
                          and rcb.fil_in_codigo = :fil_in_codigo
                          and (                              
                                  (to_number(substr(mvl.mvl_st_loteforne,17)) >= :mvl_st_loteini
                                    and to_number(substr(mvl.mvl_st_loteforne,17)) <= :mvl_st_lotefim
                                    and :mvl_st_loteini <>'0'
                                  )
                               or (:mvl_st_loteini = '0')                               
                              )                          
                          --and (mvl.mvl_st_loteforne like '%'||:mvl_st_loteforne or :mvl_st_loteforne ='0')
                          --and to_number(substr(mvl.mvl_st_loteforne,17)) > 749
                          --and to_number(substr(mvl.mvl_st_loteforne,17)) < 760
                        order by to_number(substr(mvl.mvl_st_loteforne,17))''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'avr_st_nota':self.avr_st_nota,'fil_in_codigo':self.fil_in_codigo, 'mvl_st_loteini':self.mvl_st_loteini,'mvl_st_lotefim':self.mvl_st_lotefim})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
        pass
    def get_LotesInventario(self,pdados):
        self.avr_st_nota = pdados.get('doc')
        self.fil_in_codigo = pdados.get('filial')
        self.mvl_st_loteforne = pdados.get('lote')
        selectSQL =('''select mvl.fil_in_codigo,
                              mvl.pro_in_codigo,
                              mvl.lot_in_sequencia as avr_st_nota,
                              mvl.lot_dt_movimento as AVR_DT_ENTRADANF,
                              mvl.mvl_st_loteforne,
                              mvl.mvl_re_quantidade as mvl_re_unidade,
                              mvl.mvl_re_quantmov as mvl_re_quantidade,
                              pro.pro_st_descricao,
                              substr(mvl.mvl_st_loteforne,17) sequencial,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Classificacao') classificacao,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Volume') volume,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Comprimento') comprimento,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Largura') largura,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Origem') origem,
                              adm_pck_utilidades.f_formatacaract(mvl.mvl_st_referencia,'Pilha') pilha
                         from cus_lotes_temp mvl,
                              est_produtos pro
                        where mvl.pro_tab_in_codigo = pro.pro_tab_in_codigo
                          and mvl.pro_pad_in_codigo = pro.pro_pad_in_codigo
                          and mvl.pro_in_codigo     = pro.pro_in_codigo
                           
                          and mvl.lot_in_sequencia = :lot_in_sequencia
                          and mvl.fil_in_codigo = :fil_in_codigo
                          and (mvl.mvl_st_loteforne like '%'||:mvl_st_loteforne or :mvl_st_loteforne ='0')
                          --and to_number(substr(mvl.mvl_st_loteforne,17)) > 1000
                          --and to_number(substr(mvl.mvl_st_loteforne,17)) <= 1001                          
                        order by to_number(substr(mvl.mvl_st_loteforne,17))''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'lot_in_sequencia':self.avr_st_nota,'fil_in_codigo':self.fil_in_codigo, 'mvl_st_loteforne':self.mvl_st_loteforne})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
        pass
    def get_cadOperadores(self, pParams):        
        self.fil_in_codigo = pParams['filial']
        try:
            self.opd_st_codigo = pParams['operador']
        except:
            pass
        selectSQL =('''select opd.opd_st_alternativo, 
                              opd.opd_st_descricao,
                              nvl(oce.prd_ch_acb,'N') prd_ch_acb
                         from pro_cadoperador opd,
                              pro_cadoperadorcmpesp oce
                        where opd.opd_tab_in_codigo  = oce.opd_tab_in_codigo (+)
                          and opd.opd_pad_in_codigo  = oce.opd_pad_in_codigo (+)
                          and opd.opd_in_codigo      = oce.opd_in_codigo     (+)
                          and opd.opd_pad_in_codigo  = pck_mega.achapadraodatabela(:fil_in_codigo,228,sysdate)
                          and (opd.opd_st_alternativo = :opd_st_alternativo or :opd_st_alternativo = 'all')''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in_codigo':self.fil_in_codigo, 'opd_st_alternativo':self.opd_st_codigo})
            columns = [col[0] for col in cur.description]
            cur.rowfactory = lambda *args: dict(zip(columns, args))
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        return c_rs
