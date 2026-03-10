# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import oracledb as cxo
from oracle_connection import getOracleConnection
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest
import requests

from django.utils import timezone


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
    def ord_listDemandas(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select dem.com_in_codigo,
                              pro.pro_st_descricao,
                              dem.apt_re_qtdeselecionada,
                              dem.mvs_st_loteforne,
                              mgadm.adm_pck_util.f_formatacaract(dem.mvs_st_referencia) as mvs_st_referencia_desc
                         from mgcustom.apt_apontademanda_estoque dem,
                              mgadm.est_produtos pro
                        where pro.pro_tab_in_codigo = dem.com_tab_in_codigo
                          and pro.pro_pad_in_codigo = dem.com_pad_in_codigo
                          and pro.pro_in_codigo = dem.com_in_codigo
                          and dem.ord_in_codigo     = :ord_in
                          and dem.com_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in,100,sysdate)''')
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
        v_params = []        
        con = getOracleConnection()
        cur = con.cursor()
        v_params.append(self.fil_in)
        v_params.append(self.ordem_in)
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
                         from mgman.pro_ordens ord,
                              mgman.pro_prog_ordem pgo
                        where ord.org_tab_in_codigo = pgo.org_tab_in_codigo
                          and ord.org_pad_in_codigo = pgo.org_pad_in_codigo
                          and ord.org_in_codigo = pgo.org_in_codigo
                          and ord.org_tau_st_codigo = pgo.org_tau_st_codigo
                          and ord.ord_tab_in_codigo = pgo.ord_tab_in_codigo
                          and ord.ord_seq_in_codigo = pgo.ord_seq_in_codigo
                          and ord.ord_in_codigo = pgo.ord_in_codigo
                          and pgo.plf_in_sqoperacao = (select min(po.plf_in_sqoperacao)
                                                         from mgman.pro_prog_ordem po
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
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(org_in_codigo = int(rs[2]),
                              ord_in_codigo = int(rs[6]),
                              pro_in_codigo = int(rs[9]),
                              plf_in_sqoperacao = rs[10]))
        operacoes= {}
        operacoes = json.dumps(lista)
        return operacoes

    def lista_ocorrencia(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select a.ati_tab_in_codigo,
                              a.ati_pad_in_codigo,
                              a.ati_in_codigo,
                              a.ati_st_nome
                         from mgman.pro_atividade a
                        where a.ati_ch_produtiva = 'I'
                              and a.ati_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in, 204, sysdate)
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
                               nvl(mgadm.adm_pck_util.f_formatacaract(apl.orl_st_referencia),'*') as mvs_st_referencia_desc,
                               apl.orl_st_referencia
                        from mgcustom.apt_apontaordem_lote apl,
                             mgadm.est_produtos pro
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
        cur.callproc('intprod.apt_intprod.apt_retornacaracteristica',(sparams))
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
        cur.callproc('intprod.apt_intprod.apt_retornaatributo',(sparams))
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
        cur.callproc('intprod.apt_intprod.apt_retornaitens',(sparams))
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
class TabPreco:
    def __init__(self,pparams):
        v_params = []
        v_params.append(pparams)
        for v_obj in v_params:
            self.pro_pad = int(v_obj[0])
            
    def lista_precos(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select det.pro_in_codigo,
                              translate(prod.pro_st_descricao,'áâãêéôôóúç','aaaeeooouc') pro_st_descricao,
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
        json_preco2= {}
        for rs in c_rs:
            lista.append({"codigo" : str(rs[0]),
                              "descricao": rs[1],
                              "custo": str(rs[2]),
                              "preco": str(rs[3]),
                              "dolar": str(rs[4])})
            '''lista.append(dict(codigo = int(rs[0]),
                              descricao = rs[1],
                              custo = float(rs[2]),
                              preco = float(rs[3]),
                              dolar = float(rs[4])))'''
            json_preco2.update({"codigo":str(rs[0]),
                              "descricao":rs[1],
                              "custo": str(rs[2]),
                              "preco": str(rs[3]),
                              "dolar": str(rs[4])})
        json_preco= {}
        json_preco = json.dumps(lista)
        myDictStr = json_preco
        myDictStr2 = myDictStr.replace('"',"'")
        #print(myDictStr2)
        myDict = {}
        #myDict.update({'lista': [json_preco2]})
        myDict.update({'lista': lista})
        mystring = myDict        
        #myDict = {}
        #myDict.update({'lista': myDictStr2})
        #mystring = myDict        
        #data = json.loads(mystring)        
        teste_json = {}
        teste_json = json.dumps(mystring)
        #print(teste_json)
        return mystring      
        #myDict = {}
        #myDict.update({'lista': json_preco})
        #json_retorno = {}
        #json_retorno = json.dumps(myDict)
        #json_retorno = myDict        
        #print(myDict)       
        #return json_retorno        	
        #return json_preco
class TabCliente:
    def __init__(self,pparams):
        v_params = []
        v_params.append(pparams)
        for v_obj in v_params:
            self.agn_pad = int(v_obj[0])            
    def lista_cliente(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select aid.agn_tab_in_codigo,
                              aid.agn_pad_in_codigo,
                              aid.agn_in_codigo,
                              aid.agn_st_codigoalt, 
                              replace(aid.agn_st_codigoalt,'ES','') codigo_appweb,
                              translate(agn.agn_st_fantasia,'áâãêéíôôóúçÁÂÃÊÉÍÔÔÓÚÇÖÕõÑÜ','aaaeeíoooucAAAEEIOOOUCOOoNU') agn_st_fantasia,
                              translate(agn.agn_st_nome,'áâãêéíôôóúçÁÂÃÊÉÍÔÔÓÚÇÖÕõÑÜ','aaaeeíoooucAAAEEIOOOUCOOoNU') agn_st_nome,
                              agn.agn_dt_ultimaatucad       
                         from mgglo.glo_agentes agn,
                              mgglo.glo_agentes_id aid
                        where agn.agn_tab_in_codigo = aid.agn_tab_in_codigo
                          and agn.agn_pad_in_codigo = aid.agn_pad_in_codigo
                          and agn.agn_in_codigo = aid.agn_in_codigo
                          and agn.agn_pad_in_codigo = :agn_pad
                          and rownum < 3
                          and aid.agn_st_codigoalt like 'ES%'
                          --and replace(aid.agn_st_codigoalt,'ES','') = :agn_cod
                          ''')
        cur.prepare(selectSQL)
        cur.execute(None, {'agn_pad': self.agn_pad})
        c_rs = cur.fetchall()
        cur.close
        con.close
        Cliente = []
        json_cliente= {}
        for rs in c_rs:
            Cliente.append({"codigo" : str(rs[2]),
                          "codigo_appweb": rs[4],
                          "agn_st_fantasia": rs[5],
                          "agn_st_nome": rs[6],
                          "agn_dt_ultimaatucad": str(rs[7])})            
        listaCliente = {}        
        listaCliente.update({'lista': Cliente})
        clientes = listaCliente        
        return listaCliente
    def grava_cliente(self, vparams):
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        texto = vparams
        sparams = (texto, ref_cursor)
        #print(sparams)
        cur.callproc('mgcustom.CLI_PCK_ECOMMERCE.p_testar_api',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
    def read_cliente(self):
        #file_directory = '/home/admin/myproject/controleweb/api/Clientes.json'
        #json_data=open(file_directory).read()            
        #print(json_data)
        #dados = json.loads(json_data)
        enviar = '''{
            "tipo2": "cliente",
            "id": 25,
            "nome": "Luciano Rodrigues",
            "UF_ST_SIGLA": "SP",
            "endereco": "Rua trinta",
            "cep": "13.465-340",
            "numero": "845",
            "complemento": "apto145B",
            "AGN_ST_REFERENCIA": "proxima a shopping",
            "bairro": "Vila Mariana",
            "cidade": "Americana",
            "tipo": "J",
            "cnpj_cpf": "11.416.214/0001-60",
            "isento": false,
            "ie": "165383689118",
            "data_emissao": "20/10/2020 09:45:32",
            "data_alteracao": "20/10/2020 09:45:32",
            "AGN_ST_EMAIL": "",
            "telefones" : [
            {            
                "TEA_ST_TELEFONE": "19-98199.5899",
                "TEA_ST_TIPO": "Celular"
            }
            ],
            "enderecos" : [
            {
                "UF_ST_SIGLA": "SP",
                "TEA_ST_CODIGO": "LOC", 
                "ENA_ST_LOGRADOURO": "Rua trinta", 
                "ENA_ST_NUMERO": "845", 
                "ENA_ST_BAIRRO": "Vila Mariana", 
                "ENA_ST_MUNICIPIO": "Americana", 
                "ENA_ST_CEP": "13.465-340",
                "ENA_ST_COMPLEMENTO": "apto145B",
                "ENA_ST_REFERENCIA": "proxima a shopping",
                "ENA_ST_IDORIGEM": "25-1"
            }
            ]
        }'''        
        send_data = json.loads(enviar)
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        texto = 'teste metodo post'
        yourdata= '[{"likes": 10, "comments": 0}, {"likes": 4, "comments": 23}]'
        sparams = (texto, ref_cursor)
        response = requests.post("http://192.168.0.32/api/yourView", data=yourdata)
        #print(response.status_code)
        cur.callproc('mgcustom.CLI_PCK_ECOMMERCE.p_testar_api',(sparams))
        c_rs = ref_cursor.fetchall()
        cur.close
        con.close
        #print(v3)
        #pastebin_url = response.text 
        #print("The pastebin URL is:%s"%pastebin_url) 
class GetDadosProducao:
    def __init__(self):
        self.org_in = None
        self.ord_seq = None
        self.ordem_in = None
        self.fil_in = None
        self.pro_in = None
    def get_integracao(self,pparams):
        if pparams[1] is None:
            selectSQL =('''select ord.org_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo
                         from intprod.int_pro_ordens ord
                        where ord.ord_ch_integrada = :ord_ch_integrada
                          and ord.org_in_codigo = :org_in_codigo
                          --and ord.ord_in_codigo = 58865
                        order by ord.ord_in_codigo
                          ''')
        else:
            selectSQL =('''select ord.org_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo
                         from intprod.int_pro_ordens ord
                        where ord.ord_ch_integrada = :ord_ch_integrada
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
                              ord.tpo_st_codigo_tipo
                         from mgman.pro_ordens ord
                        where ord.org_in_codigo = :org_in_codigo
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
                              TPO_ST_CODIGO_TIPO = rs[12]))
        json_getOrdens= {}
        json_getOrdens = json.dumps(lista)
        return json_getOrdens
    def put_pro_ordens(self,pparams):
        self.org_in = pparams[0]
        self.ord_seq = pparams[1]
        self.ordem_in = pparams[2]
        ExecSQL =('''update intprod.int_pro_ordens ord
                        set ord.ord_ch_integrada = 'S'
                        where ord.ord_ch_integrada = 'N'
                          and ord.org_in_codigo = :org_in_codigo
                          and ord.ord_seq_in_codigo = :ord_seq_in_codigo 
                          and ord.ord_in_codigo = :ord_in_codigo''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(ExecSQL)
            cur.execute(None, {'org_in_codigo':self.org_in,'ord_seq_in_codigo':self.ord_seq,'ord_in_codigo':self.ordem_in})
            cur.close
            con.commit()
            con.close
        except cxo.Error as error:
            pass
        return True
    def itn_referencias(self,pparams):
        self.fil_in = pparams[0]
        self.pro_in = pparams[1]
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.pro_in,ref_cursor)
        cur.callproc('intprod.apt_intprod.apt_retornacaracteristica',(sparams))
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
        cur.callproc('intprod.apt_intprod.apt_retornaatributo',(sparams))
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
        cur.callproc('intprod.apt_intprod.apt_retornaitens',(sparams))
        c_rs = ref_cursor.fetchall()
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
                              pro_st_madeira= rs[9]
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
        cur.callproc('intprod.apt_intprod.apt_retornaDemanda',(sparams))
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
    def get_centro_custos(self):
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
                         from mgcon.con_centro_custo cc
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
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:
            lista.append(dict(CUS_ID_CCUSTO = rs[0],
                              CUS_TAB_IN_CODIGO = int(rs[1]),
                              CUS_PAD_IN_CODIGO = int(rs[2]),
                              CUS_IDE_ST_CODIGO = rs[3],
                              CUS_IN_REDUZIDO = int(rs[4]),
                              CUS_ST_EXTENSO = rs[5],
                              CUS_ST_DESCRICAO = rs[6]))
        json_getCCusto= {}
        json_getCCusto = json.dumps(lista)
        return json_getCCusto
    def get_CadastroProdutos(self):
        selectSQL =('''select lpad(pro.pro_tab_in_codigo,3,0)||
                              lpad(pro.pro_pad_in_codigo,3,0)||
                              lpad(pro.pro_in_codigo,7,0) as PRO_ST_ID,       
                              pro.pro_tab_in_codigo,
                              pro.pro_pad_in_codigo,
                              pro.pro_in_codigo,
                              pro.pro_st_descricao,
                              pro.uni_st_unidade
                         from mgadm.est_produtos pro
                        where pro.pro_pad_in_codigo = :pro_pad_in_codigo
                        order by pro.pro_in_codigo''')
        try:
            con = getOracleConnection()
            cur = con.cursor()
            cur.prepare(selectSQL)
            cur.execute(None, {'pro_pad_in_codigo': 1})
            c_rs = cur.fetchall()
            cur.close
            con.close
        except cxo._Error as error:
            pass
        lista = []
        for rs in c_rs:
            lista.append(dict(BXI_ID_PRODUTO = rs[0],
                              PRO_TAB_IN_CODIGO = int(rs[1]),
                              PRO_PAD_IN_CODIGO = int(rs[2]),
                              PRO_IN_CODIGO = int(rs[3]),
                              PRO_ST_DESCRICAO = rs[4],
                              UNI_ST_UNIDADE = rs[5]))
        json_getCadItens= {}
        json_getCadItens = json.dumps(lista)
        return json_getCadItens
class IntegrarProducao:
    def __init__(self):
        self.org_in = None
        self.ord_seq = None
        self.ordem_in = None

    def apt_integrarlote(self, pparams):
        v_listlote = []
        v_listlote.append(pparams)
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        for v_obj in v_listlote:
            sparams = (int(v_obj[0]),int(v_obj[1]),int(v_obj[2]),int(v_obj[3]),v_obj[4],int(v_obj[5]),float(v_obj[6]),float(v_obj[7]),float(v_obj[8]),int(v_obj[9]),v_obj[10],v_obj[11],v_obj[12],int(v_obj[13]),v_obj[14],v_obj[15],v_obj[16],v_obj[17],ref_cursor)
            cur.callproc('intprod.apt_intprod.cli_p_lotes_ordem',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            if c_rs:
                for v_rs in c_rs:
                    lista.append(dict(sequencia = v_rs[0],
                                      mensagem = v_rs[1],
                                      mensagem_sub = v_rs[2]))
            else:
                lista.append(dict(sequencia = 0,
                                  mensagem = 'Erro',
                                  mensagem_sub = 'Erro'))
            v_retorno = {}
            v_retorno = json.dumps(lista)
        return v_retorno

    def apt_integrarDemanda(self, pparams):
        v_listDem = []
        v_listDem.append(pparams)
        for v_obj in v_listDem:
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,int(v_obj[0]),int(v_obj[1]),int(v_obj[2]),int(v_obj[3]),v_obj[4],int(v_obj[5]),str(v_obj[6]),float(v_obj[7]))
            cur.callproc('intprod.apt_intprod.p_inseredemanda_lotes',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            if c_rs:
                for v_rs in c_rs:
                    lista.append(dict(mensagem = v_rs[0],
                                      item = v_rs[1],
                                      Sequencia = v_rs[2]))
            else:
                lista.append(dict(mensagem =  'Erro',
                                  item = 0,
                                  Sequencia = 0))
            v_retorno = {}
            v_retorno = json.dumps(lista)
        return v_retorno
