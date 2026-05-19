# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import requests
from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite
from producao import settings
from datetime import datetime, date, timedelta
from apontamento.Etiqueta_precorte import gera_etiqueta
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest

from django.utils import timezone
import pandas as pd
from pandas import json_normalize

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

def monta_produto(pparams):
    v_tab = str(pparams[0])
    v_pad = str(pparams[1])
    v_cod   = str(pparams[2])
    v_retorno =  v_tab.zfill(3)+ v_pad.zfill(3)+v_cod.zfill(7)
    return (v_retorno)

def monta_ordem(pparams):
    org_tab = str(pparams[0])
    org_pad = str(pparams[1])
    org_cod = str(pparams[2])
    org_tau = pparams[3]
    ord_tab = str(pparams[4])
    ord_seq = str(pparams[5])
    ord_cod = str(pparams[6])
    v_retorno =  org_tab.zfill(3)+ org_pad.zfill(3)+org_cod.zfill(7)+org_tau.zfill(3)+ord_tab.zfill(3)+ord_seq.zfill(3)+ord_cod.zfill(20)
    return (v_retorno)

def separa_string(pString, vINI, vFIM):
    return (pString[vINI:vFIM])

def separa_ordem(pparams):
    list_ordem = [0,3,6,13,16,19,22,42]          
    org_tab = separa_string(pparams,list_ordem[0],list_ordem[1])    
    org_pad = separa_string(pparams,list_ordem[1]+list_ordem[2])
    org_cod = separa_string(pparams,list_ordem[2]+list_ordem[3])
    org_tau = separa_string(pparams,list_ordem[3]+list_ordem[4])
    ord_tab = separa_string(pparams,list_ordem[4]+list_ordem[5])
    ord_seq = separa_string(pparams,list_ordem[5]+list_ordem[6])
    ord_cod = separa_string(pparams,list_ordem[6]+list_ordem[7])
    v_retorno =  {'org_tab':org_tab,'org_pad':org_pad,'org_cod':org_cod,'org_tau':org_tau,'ord_tab':ord_tab,'ord_seq':ord_seq,'ord_cod':ord_cod}
    return (v_retorno)

def separa_produto(pparams):
    list_ordem = [0,3,6,13]
    pro_tab = separa_string(pparams,list_ordem[0],list_ordem[1])
    pro_pad = separa_string(pparams,list_ordem[1]+list_ordem[2])
    pro_in = separa_string(pparams,list_ordem[2]+list_ordem[3])
    v_retorno =  {'pro_tab':pro_tab,'pro_pad':pro_pad,'pro_in':pro_in}
    return (v_retorno)

def converter_unidade(pParams):
    v_qtdeConv = pParams[4]
    if pParams[5] == 3:
        if pParams[0] == 'OP003':
            v_qtdeConv = pParams[4]
            if pParams[2] > 0:
                v_qtdeConv = round(pParams[4]*(pParams[2]/1000),3)
        else:
            v_qtdeConv = pParams[4]
    #Zk Laminadora
    elif pParams[5] == 312:
        v_qtdeConv = round(pParams[4]*((pParams[1]/1000)*(pParams[2]/1000)*(pParams[3]/1000)),3)
    else:
        v_qtdeConv = pParams[4]
    return v_qtdeConv

def formatar_caracteristicas(preferencia,patrib):
    v_referencias = preferencia[:-1]
    v_lista = v_referencias.split(";")
    v_atrib = patrib
    v_atributo = None
    v_retorno = None
    v_json_atr = None
    v_achou = 'N'
    v_json = {}
    for c_rs in v_lista:
        v_achou = 'N'
        for l_atr in v_atrib:
            if v_achou == 'N':
                if (l_atr['RAT_CH_TIPO'] == 'P') and (l_atr['RAT_BO_GRUPO'] == 'N'):
                    if c_rs == l_atr['RAT_VALUE']:
                        if v_retorno is None:
                            v_retorno = l_atr['RAT_ST_DESCRICAO']
                            v_json_atr = '{"'+l_atr['PAI_ST_DESCRICAO']+'": "'+l_atr['RAT_ST_DESCRICAO']+'"}'
                            objeto = json.loads(v_json_atr)
                            v_achou = 'S'
                        else:
                            v_retorno += ' / '
                            v_retorno += l_atr['RAT_ST_DESCRICAO']
                            v_json_atr = '{"'+l_atr['PAI_ST_DESCRICAO']+'": "'+l_atr['RAT_ST_DESCRICAO']+'"}'
                            objeto = json.loads(v_json_atr)
                            v_achou = 'S'
                #break
                #Busca valores do campo livre;
                else:
                    #Formata o atributo
                    if l_atr['RAT_VALUE'] in c_rs:
                        v_atributo = c_rs.replace(l_atr['RAT_VALUE'],'')
                        if v_retorno is None:
                            v_retorno = v_atributo
                            v_json_atr = '{"'+l_atr['RAT_ST_DESCRICAO']+'": "'+v_atributo+'"}'
                            objeto = json.loads(v_json_atr)
                            v_achou = 'S'
                        else:
                            v_retorno += ' / '
                            v_retorno += v_atributo
                            v_json_atr = '{"'+l_atr['RAT_ST_DESCRICAO']+'": "'+v_atributo+'"}'
                            objeto = json.loads(v_json_atr)
                            v_achou = 'S'
        if v_achou == 'S':
            v_json.update(objeto)
    objeto = {"Caracteristicas":v_retorno}
    v_json.update(objeto)
    #raise Exception(v_json)
    return v_json

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def formatar_ordem(pOrdem):
        v_ordem = pOrdem
        v_ordem_oper = None
        v_ordem_ordem = None
        v_ord_filial = None
        #print('ordem',v_ordem)
        if len(v_ordem) == 15:
            v_ordem_oper = v_ordem[-4:-1]
            v_ordem_ordem = v_ordem[6:-4]
            v_ord_filial = v_ordem[0:3]
        if len(v_ordem) == 14:
            v_ordem_oper = v_ordem[-4:-1]
            v_ordem_ordem = v_ordem[5:-4]
            v_ord_filial = v_ordem[0:3]
        elif len(v_ordem) == 13:
            v_ordem_oper =v_ordem[-4:-1]
            v_ordem_ordem =v_ordem[4:-4]
            v_ord_filial =v_ordem[0:2]
        elif len(v_ordem) == 12:
            v_ordem_oper =v_ordem[-4:-1]
            v_ordem_ordem =v_ordem[3:-4]
            v_ord_filial =v_ordem[0:1]
        else:
            v_ordem_ordem =v_ordem[3:-4]

        l_retorno = []
        l_retorno.append(dict(ordem = int(v_ordem_ordem),
                              filial = int(v_ord_filial),
                            operacao = int(v_ordem_oper)))
        v_retorno ={}
        v_retorno = json.dumps(l_retorno)
        return  v_retorno    

class IntAPI:
    def __init__(self,pparam):
        self.equip_logado = 'N'
        self.dbname = 'Producao.db'
        self.tpo_st_id = None
        self.car_st_id = None
        self.cfg_st_id = None
        self.maquina   = None
        self.org_in    = None
        self.uri       = None
        self.fil_in = pparam.get('fil_in_codigo')
        self.ordem_in = pparam.get('ord_in_codigo')
        self.usuario = pparam.get('usuario')
        self.seq_controle = pparam.get('ctl_in_codigo')
        self.cliente = pparam.get('cliente')
        self.pk = pparam.get('pk')
        self.lote_demanda = pparam.get('lote')
        #Busca dados do equipamento cadastrado;
        funcao = 'equipamento/'
        app_url = geturlprod(funcao)
        payload = {'cliente': self.cliente,'filial':self.fil_in}
        v_printer = requests.get(app_url, params=payload).json()
        for rs_printer in v_printer:
            self.maquina = rs_printer['MAQ_IN_CODIGO']
        if self.fil_in and self.ordem_in:
            c_operacoes = self.operacoes_ordem()
            for v_operacoes in c_operacoes:
                self.org_in = v_operacoes['ORG_IN_CODIGO']            
    def operacoes_ordem(self):
        self.funcao = 'oper_ordem'
        self.uri= geturlapi(self.funcao)        
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload).json()
        return vresponse
    
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
        self.uri = geturlapp(self.funcao)        
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

    def listar_producao(self):
        if self.pk:
            payload = {'pk': self.pk}        
        else:
            payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        self.funcao = 'apontamentos'
        self.uri = geturlapp(self.funcao)
        json_producao = requests.get(self.uri, params=payload).json()
        return json_producao

    def delete_producao(self):
        payload = {'pk': self.pk}
        self.funcao = 'apontamentos/'
        self.uri = geturlapp(self.funcao)
        jason_delete = requests.delete(self.uri, params=payload)
        return jason_delete

    def listar_demanda(self,pparams):
        if pparams:
            self.pk = pparams.get('pk')
            self.ordem_in = pparams.get('ordem')
            self.fil_in = pparams.get('filial')
            self.lote_demanda = pparams.get('lote')
        if self.pk:
            payload = {'pk': self.pk}
        elif self.fil_in and self.ordem_in and self.lote_demanda:
            #listar no form
            payload = {'ordem': self.ordem_in,'filial': self.fil_in, 'lote':self.lote_demanda}
        else:
            payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        print('payload demanda 287',payload)
        self.funcao = 'demandas/'
        self.uri = geturlapp(self.funcao)
        json_producao = requests.get(self.uri, params=payload).json()
        return json_producao

    def delete_demanda(self):
        payload = {'pk': self.pk}
        self.funcao = 'demandas/'
        self.uri = geturlapp(self.funcao)
        jason_delete = requests.delete(self.uri, params=payload)
        return jason_delete

    def empenho_demanda(self):
        if settings.GRAVAR_LOCAL:
            self.funcao = 'demandas/'
            self.uri = geturlapp(self.funcao)
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

    def get_tipo_ordens(self,pparams):
        self.fil_in = pparams
        self.funcao = 'get_tipoordens/'
        self.uri = geturlapi(self.funcao)
        payload = {'filial': self.fil_in}
        #busca no Mega os tipo de Ordens
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        if vRes_json:
            for rs in vRes_json:
                self.funcao = 'tipoordens/'
                self.uri = geturlapp(self.funcao)
                self.tpo_st_id = rs.get('TPO_ST_ID')
                payload = {'tpo_st_id': self.tpo_st_id}
                vget = requests.get(self.uri, params=payload).json()
                if vget:
                    pass
                else:
                    requests.post(self.uri, data=rs)
        return vRes_json

    def get_config_aponta(self,pparams):
        self.fil_in = pparams
        self.funcao = 'get_configaponta/'
        self.uri = geturlapi(self.funcao)
        payload = {'filial': self.fil_in}
        #busca no Mega os tipo de Ordens
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        if vRes_json:
            for rs in vRes_json:
                self.funcao = 'configurar_aponta/'
                self.uri = geturlapp(self.funcao)
                self.cfg_st_id = rs.get('CFG_ST_ID')
                payload = {'cfg_st_id': self.cfg_st_id}
                vget = requests.get(self.uri, params=payload).json()
                if vget:
                    pass
                else:
                    requests.post(self.uri, data=rs)
        return vRes_json

    def get_referencia_atributos(self,pparams):
        self.fil_in = pparams
        self.funcao = 'get_referencia/'
        self.uri = geturlapi(self.funcao)
        payload = {'filial': self.fil_in}
        #busca no Mega os tipo de Ordens
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        if vRes_json:
            for rs in vRes_json:
                self.funcao = 'referencia/'
                self.uri = geturlapp(self.funcao)
                self.car_st_id = rs.get('CAR_ST_ID')
                payload = {'car_st_id': self.car_st_id}
                vget = requests.get(self.uri, params=payload).json()
                if vget:
                    pass
                else:
                    requests.post(self.uri, data=rs)
        return vRes_json
    
    def gravar_ocorrencia(self,v_params):
        funcao = 'ocorrencias'
        #print('Passou aqui linha 160')

        api_ocorrencia = geturlapp(funcao)
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
        
class IntOrdens:
    def __init__(self):
        self.org_in = None
        self.fil_in = None
        self.pro_in = None
    def buscaOrdens(self,pparams):
        #Busca as ordens pendentes no Mega;
        lista_conv = []
        funcao = 'GetOrdensPendentes/'
        try:
            api_ordenspendentes = geturlapi(funcao)
            if pparams[1] is None:
                payload = {'org_in_codigo': pparams[0],'param': pparams[3]}
            else:
                payload = {'org_in_codigo': pparams[0],'fil_in_codigo': pparams[1],'ord_in_codigo': pparams[2],'param': pparams[3]}
            #Reabre a ordem para atualização
            if (pparams[3] == 'S'):
                pay = {'ORG_IN_CODIGO': pparams[0], 'ORD_SEQ_IN_CODIGO': pparams[1],'ORD_IN_CODIGO': pparams[2],'param': pparams[3]}
                vput = requests.put(api_ordenspendentes, data=pay)                
            #baixa novamente todos os dados
            vresponse = requests.get(api_ordenspendentes, params=payload).json()
            #Se encontrar ordem pendente segue continua;
            if vresponse:
                for ord in vresponse:                    
                    #busca dados das Ordens
                    funcao = 'GetManProOrdens/'
                    #try:
                    if 1==1:
                        api_getordens = geturlapi(funcao)
                        payload = {'org_in_codigo': ord['org_in_codigo'],
                                   'ord_seq_in_codigo': ord['ord_seq_in_codigo'],
                                   'ord_in_codigo': ord['ord_in_codigo']}
                        c_getordens = requests.get(api_getordens, params=payload).json()
                        #Se encontrar a ordem segue adiante;
                        if c_getordens:
                            for d_ord in c_getordens:
                                self.fil_in = d_ord['FIL_IN_CODIGO']
                                c_get_inf = {'umidade': d_ord['ORD_RE_UMIDADE'],'lote_ordem': d_ord['LOTE_ORDEM'],'destino': d_ord['ORD_ST_DESTINO'],'origem': d_ord['ORD_ST_ORIGEM']}
                                #Busca Demandas da Ordem;
                                funcao = 'get_demandaordens/'
                                uri = geturlapi(funcao)
                                c_get_demandas = requests.get(uri, params=payload).json()
                                #Busca Item da Ordem + SubProdutos;
                                funcao = 'itensordem/'
                                uri = geturlapi(funcao)
                                payload = {'ordem': d_ord['ORD_IN_CODIGO'],'filial': d_ord['FIL_IN_CODIGO']}
                                c_get_itens = requests.get(uri, params=payload).json()
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
                                funcao = 'ordens/'
                                #print(v_dados)
                                dadosOrdens = geturlapp(funcao)
                                payload = {'org_in_codigo': ord['org_in_codigo'],
                                           'ord_seq_in_codigo': ord['ord_seq_in_codigo'],
                                           'ord_in_codigo': ord['ord_in_codigo']}
                                c_apagaordem = requests.put(dadosOrdens, params=payload)
                                c_response = requests.post(dadosOrdens, data=v_dados)
                                # faz update nas ordens atualizadas;
                                v_update_ordem = {'ORG_IN_CODIGO': d_ord['ORG_IN_CODIGO'],
                                                  'ORD_SEQ_IN_CODIGO': d_ord['ORD_SEQ_IN_CODIGO'],
                                                  'ORD_IN_CODIGO': d_ord['ORD_IN_CODIGO'],
                                                  'param':'N'}
                                print(v_update_ordem)
                                funcao = 'GetOrdensPendentes/'
                                api_ordenspendentes = geturlapi(funcao)
                                do_response = requests.put(api_ordenspendentes, data=v_update_ordem)
                                #Busca Itens da ordem
                                if c_get_itens:
                                    for d_itens in c_get_itens:
                                        self.pro_in = d_itens['pro_in_codigo']
                                        pro_medidas = []
                                        pro_medidas.append(dict(PRO_RE_COMPRIMENTO = d_itens['pro_re_comprimento'],
                                                                PRO_RE_LARGURA = d_itens['pro_re_largura'],
                                                                PRO_RE_ESPESSURA = d_itens['pro_re_espessura']
                                                               ))
                                        funcao = 'get_proconversor/'
                                        payload = {'fil_in_codigo': self.fil_in,'pro_in_codigo':self.pro_in}
                                        conv_url = geturlapi(funcao)
                                        pro_conversor =requests.get(conv_url, params=payload).json()
                                        if not(pro_conversor):
                                            lista_conv = []
                                            lista_conv.append(dict(CONVERSORES = None))
                                            pro_conversor =  json.dumps(lista_conv)                                            
                                        if d_itens['rfc_in_codigo']!=0:
                                            #Busca atributos dos Itens
                                            funcao = 'listaatributos/'
                                            uri = geturlapi(funcao)
                                            payload = {'item': d_itens['pro_in_codigo'],'filial': d_ord['FIL_IN_CODIGO']}
                                            c_get_atrib = requests.get(uri, params=payload).json()
                                            #Busca Características dos Itens
                                            funcao = 'listareferencias/'
                                            uri = geturlapi(funcao)
                                            c_get_ref = requests.get(uri, params=payload).json()
                                            #grava itens na tabela
                                            v_dados_produtos = {'PRO_TAB_IN_CODIGO': d_ord['PRO_TAB_IN_CODIGO'],
                                                                'PRO_PAD_IN_CODIGO': d_ord['PRO_PAD_IN_CODIGO'],
                                                                'PRO_IN_CODIGO': d_itens['pro_in_codigo'],
                                                                'PRO_ST_DESCRICAO': d_itens['pro_st_descricao'],
                                                                'UNI_ST_UNIDADE': d_itens['uni_st_unidade'],
                                                                'RFC_IN_CODIGO': d_itens['rfc_in_codigo'],
                                                                'PRO_ST_ATRIBUTOS': json.dumps(c_get_atrib),
                                                                'PRO_ST_REFERENCIA': json.dumps(c_get_ref),
                                                                'PRO_ST_MEDIDAS': json.dumps(pro_medidas),
                                                                'MVS_ST_REFERENCIA':d_itens['mvs_st_referencia'],
                                                                'PRO_ST_ID':d_itens['pro_st_id'],
                                                                'PRO_ST_CONVERSOR':json.dumps(pro_conversor)}
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
                                                                       'PRO_ST_ID':d_itens['pro_st_id'],
                                                                       'PRO_ST_CONVERSOR':json.dumps(pro_conversor)}                                            
                                        #verifica se existe o item cadastrado
                                        #print(v_dados_produtos)
                                        funcaoapp = 'itensOrdens/'
                                        uriapp = geturlapp(funcaoapp)
                                        payload = {'pro_pad_in_codigo': d_itens['pro_pad_in_codigo'],
                                                   'pro_in_codigo': d_itens['pro_in_codigo'],
                                                   'rfc_in_codigo':d_itens['rfc_in_codigo']}
                                        c_appitens = requests.get(uriapp, params=payload).json()
                                        if c_appitens:
                                            v_delete = requests.delete(uriapp, data=v_dados_produtos)
                                        respio = requests.post(uriapp, data=v_dados_produtos)                                                                                
                    #except:
                    #    pass
        except:
            pass
        #integra maquinas
        funcao = 'GetCadMaquinas/'
        uri = geturlapi(funcao)
        payload = {'org': self.org_in,'filial': self.fil_in}
        cur_maq = requests.get(uri, params=payload).json()        
        for v_maq in cur_maq:
            if v_maq['CTR_ST_ID']!= '0':
                #Busca dados da máquina;
                funcao = 'maquina/'
                app_url = geturlprod(funcao)
                payload = {'cmaq_id': v_maq['CMAQ_ST_ID'], 'ctr_id':v_maq['CTR_ST_ID']}
                v_maquina = requests.get(app_url, params=payload).json()
                if not(v_maquina):
                    v_dados_maq = {'CTR_ST_ID': v_maq['CTR_ST_ID'],
                                   'CMAQ_ST_ID': v_maq['CMAQ_ST_ID'],
                                   'CTR_ST_NOME': v_maq['CTR_ST_NOME'],
                                   'CMAQ_ST_NOME': v_maq['CMAQ_ST_NOME'],
                                   'CMAQ_ST_CODIGO': v_maq['CMAQ_ST_CODIGO'],
                                   'MAQ_CH_APONTAMENTO':1,                                
                                  'MAQ_CH_DEMANDA':0}                    
                    try:
                        ret_maq = requests.post(app_url, data=v_dados_maq)
                        #atualiza
                        funcao = 'GetCadMaquinas/'
                        uri_put = geturlapi(funcao)
                        payload = {'CTR_ST_ID': v_maq['CTR_ST_ID'],'CMAQ_ST_ID': v_maq['CMAQ_ST_ID']}
                        ret_PutMaq = requests.put(uri_put, data=payload)                    
                    except:
                        pass   
class prep_producao:
    def __init__(self):
        self.equip_logado = 'N'
        self.dbname = 'Producao.db'
        self.fil_in_codigo = None
        self.ord_in_codigo = None
        self.pro_in_codigo = None
        self.ctl_in_codigo = None
        self.retorno = None
        self.ord_pro_in_codigo = None
        self.cliente = None
        self.origem = None
        self.tpo_st_codigo = None
        self.seqmov = None
        self.lote = None
        self.ord_st_id = None
        self.pro_st_id = None
        self.cmaq_st_id = None
        self.cmaq_st_codigo = None
        self.str_now = None
        self.str_eti = None
        self.pro_st_descricao = None
        self.referencia = None
        self.referenciaDesc = None
        self.pro_re_qtdrefugo = 0
        self.apt_re_quantidade = 0
        self.apt_re_quantConv = 0
        self.fator = 0
        self.maquina = None
        self.host = '192.168.1.211'
        self.maquina = None
        self.pro_pad_in_codigo = None
        self.uni_st_unidade = None
        self.rfc_in_codigo = 0
        self.pro_re_comprimento = 0
        self.pro_re_largura= 0
        self.pro_re_espessura = 0
        self.pro_st_madeira = None
        self.mvs_st_referencia = None
        self.umidade = None
        self.lote_ordem = None
        self.destino = None
        self.classificacao = None
        self.volume = None
        self.pilha = None
        #dados para etiqueta
        self.string1 = ''
        self.string2 = ''
        self.seqlote = 0
        self.fornecedor = ''
        self.row_now = timezone.now()
        self.str_now = self.row_now.strftime('%Y-%m-%d')
        self.str_eti = self.row_now.strftime('%d/%m/%Y')

    def valida_situacao_ordem(self,pparams):
        self.fil_in_codigo = pparams.get('filial')
        self.ord_in_codigo = pparams.get('ordem')
        payload = {'ordem': self.ord_in_codigo,'filial': self.fil_in_codigo}
        funcao = 'get_situacaoordem/'
        app_itens = geturlapi(funcao)
        c_sit = requests.get(app_itens, params=payload).json()
        return c_sit
    
    def prepara_demandas(self,pparams):
        self.fil_in_codigo = pparams.get('filial')
        self.ord_in_codigo = pparams.get('ordem')
        payload = {'ord_in_codigo': self.ord_in_codigo,'fil_in_codigo': self.fil_in_codigo}
        funcao = 'ordens/'
        d2 = {}
        app_itens = geturlapp(funcao)
        payload = {'org_in_codigo': None,
                   'ord_in_codigo': self.ord_in_codigo,
                   'fil_in_codigo': self.fil_in_codigo}
        c_appitens = requests.get(app_itens, params=payload).json()
        for r_appitens in c_appitens:
            #print('passou aqui linha 705',r_appitens)
            d2 = r_appitens['PRO_ST_DEMANDAS']
        return d2    
    def total_apontamento(self,pparams):
        funcao = 'apontamentos/'
        app_url = geturlapp(funcao)
        c_apontamentos = requests.get(app_url, params=pparams).json()
        total_demanda = 0
        total_qtd = 0
        saldo_demanda = 0
        funcao = 'demandas/'
        app_url = geturlapp(funcao)
        c_demandas = requests.get(app_url, params=pparams).json()
        total_qtd = c_apontamentos['total_ordem']
        if total_qtd is None:
            total_qtd = 0
        total_demanda = c_demandas['total_lote']
        if total_demanda is None:
            total_demanda = 0
        if (total_qtd is not None) and (total_demanda is not None):
            if total_qtd < total_demanda:
                saldo_demanda = total_demanda - total_qtd 
        elif (total_demanda is not None):
            saldo_demanda = total_demanda
        resumo = {'total_ordem': total_qtd, 'ordem': self.ord_in_codigo, 'total_demanda': total_demanda, 'saldo_demanda': saldo_demanda}
        return resumo
    def listar_saldo(self,pparams):
        self.fil_in_codigo = pparams.get('filial')
        self.lote = pparams.get('lote')
        payload = {'lote': self.lote,'filial': self.fil_in_codigo}
        funcao = 'get_saldolote/' 
        app_url = geturlapi(funcao)      
        c_saldo = requests.get(app_url, params=payload).json()                
        return c_saldo
    def get_dadosOrdem(self,pparams):
        self.fil_in_codigo = pparams.get('filial')
        self.ord_in_codigo = pparams.get('ordem')
        self.retorno = pparams.get('retorno')
        payload = {'ord_in_codigo': self.ord_in_codigo,'fil_in_codigo': self.fil_in_codigo}
        funcao = 'ordens/'
        d2 = {}
        app_itens = geturlapp(funcao)
        payload = {'org_in_codigo': None,
                   'ord_in_codigo': self.ord_in_codigo,
                   'fil_in_codigo': self.fil_in_codigo}
        c_rs = requests.get(app_itens, params=payload).json()            
        for r_cr in c_rs:
            if self.retorno == 'descricao':
                d2 = r_cr['PRO_ST_ITENS']
                Produto = [item for item in d2 if item.get('tipo_item') == 'Produto']
                for rs_item in Produto:
                    self.pro_st_descricao = rs_item.get('pro_st_descricao').upper() if rs_item else None
                return self.pro_st_descricao
            elif self.retorno == 'tpo':
                self.tpo_st_codigo = r_cr['TPO_ST_CODIGO']
            return self.tpo_st_codigo
    def prepara_apontamento(self,plista):
        v_lista = []
        v_lista.append(plista[0])
        v_lista.append(plista[1])
        v_lista.append(plista[2])
        v_lista.append(plista[3])
        v_criar = 'N'        
        funcao = 'ordens/'
        d2 = {}
        v_ord_st_id = None
        app_itens = geturlapp(funcao)
        payload = {'org_in_codigo': None,
                   'ord_in_codigo': v_lista[0],
                   'fil_in_codigo': v_lista[1]}
        c_appitens = requests.get(app_itens, params=payload).json()
        for r_appitens in c_appitens:
            d2 = r_appitens['PRO_ST_ITENS']
            v_lista.append(r_appitens['PRO_PAD_IN_CODIGO'])
            v_lista.append(r_appitens['TPO_ST_CODIGO'])
            v_lista.append(r_appitens['PRO_IN_CODIGO'])            
            v_ord_st_id = r_appitens['ORD_ST_ID']
            v_infoadic = r_appitens['PRO_ST_INFOADIC']
        pay_tot = {'ordem': v_lista[0],'filial': v_lista[1],'total': 'S'}
        v_totais = self.total_apontamento(pay_tot)            
        v_ordem = {'ord_in_codigo': v_lista[0],'fil_in_codigo': v_lista[1],'ctl_in_codigo': v_lista[2],'cliente': v_lista[3],'pro_pad_in_codigo': v_lista[4],'tpo_st_codigo':v_lista[5],'pro_in_codigo': v_lista[6],'ord_st_id':v_ord_st_id,
                   'total_apontamento': v_totais}        
        #Busca dados do equipamento cadastrado;
        funcao = 'equipamento/'
        app_url = geturlprod(funcao)
        payload = {'cliente': v_lista[3],'filial':v_lista[1]}
        v_printer = requests.get(app_url, params=payload).json()
        for rs_printer in v_printer:
                self.maquina = rs_printer['MAQ_IN_CODIGO']
                self.host = rs_printer['PRINTER_ST_IP']
        #Busca dados da máquina;
        funcao = 'maquina/'
        app_url = geturlprod(funcao)
        if v_lista[1] ==312:
            payload = {'cmaq_id': self.maquina}
        else:
            payload = {'cmaq_id': self.maquina}
        v_maquina = requests.get(app_url, params=payload).json()
        try:
            lista = d2
            if (v_lista[1] == 3) and (v_lista[5]== 'OP002'):
                v_criar = 'S'
            else:
                v_criar = 'N'
        except:
            pass
        v_retorno = {'lista': lista,'ord_in_codigo': v_lista[0],'tipo_op': v_criar,'fil_in_codigo': v_lista[1],'ordem': json.dumps(v_ordem),
                     'ord_infoadic':v_infoadic,'equipamento' : v_printer, 'maquina' : v_maquina, 'origem': plista[4], 'fornecedor':  plista[5]}        
        return v_retorno
    def monta_lote(self):
        #monta o lote;
        str_seq = str(self.seqmov)
        str_ano = self.row_now.strftime('%Y')
        str_sem = self.row_now.strftime('%U')
        str_dia = self.row_now.strftime('%d')
        str_doc = str(self.ord_in_codigo)
        str_sem = str(str_sem.zfill(2))
        str_dia = str(str_dia.zfill(2))
        str_seq = str(str_seq.zfill(6))
        str_doc = str(str_doc.zfill(8))
        str_lote = str_ano+str_sem+str_dia+str_doc+str_seq
        return str_lote
    
    def incluir_apontamento(self,pApontamento):
        v_lista = []
        # 1) inicializa as variáveis
        self.row_now = timezone.now()
        self.str_now = self.row_now.strftime('%Y-%m-%d')
        self.str_eti = self.row_now.strftime('%d/%m/%Y')
        self.fil_in_codigo = pApontamento['fil_in_codigo']
        self.ord_in_codigo = pApontamento['ord_in_codigo']
        self.pro_in_codigo = pApontamento['v_item']
        self.fator = 0
        if self.fil_in_codigo == 3:
            self.origem = pApontamento['v_origem']
            self.fornecedor = pApontamento['v_fornecedor']
        self.referencia = pApontamento['v_referencia']
        self.pro_re_qtdrefugo = pApontamento['v_refugo']
        self.apt_re_quantidade = pApontamento['v_quantidade']
        
        list_ordem    = (pApontamento['list_ordem'])
        lista         = pApontamento['lista']
        cr_ord_adic   = pApontamento['ord_infoadic']
        cr_equipamento = pApontamento['equipamento']
        cr_maquina    = pApontamento['maquina']        
        # 2) Dados da Ordem
        self.ctl_in_codigo = list_ordem['ctl_in_codigo']
        self.cliente = list_ordem['cliente']
        self.tpo_st_codigo = list_ordem['tpo_st_codigo']
        self.ord_st_id = list_ordem['ord_st_id']
        self.ord_pro_in_codigo = list_ordem['pro_in_codigo']
        # 3) Itens da Ordem
        for rs_itn in lista:
            if (rs_itn['pro_in_codigo']== self.pro_in_codigo):
                self.pro_st_descricao = rs_itn['pro_st_descricao']
                self.pro_st_id  = rs_itn['pro_st_id']
                self.pro_pad_in_codigo = rs_itn['pro_pad_in_codigo']
                self.uni_st_unidade = rs_itn['uni_st_unidade']
                self.rfc_in_codigo = rs_itn['rfc_in_codigo']
                self.pro_re_comprimento = rs_itn['pro_re_comprimento']
                self.pro_re_largura= rs_itn['pro_re_largura']
                self.pro_re_espessura = rs_itn['pro_re_espessura']
                self.pro_st_madeira = rs_itn['pro_st_madeira']
                self.mvs_st_referencia = rs_itn['mvs_st_referencia']
        # Busca Caracterísiticas do produto
        if self.rfc_in_codigo !=0:
            funcao = 'referencia/'
            url = geturlapp(funcao)
            payload = {'rfc_in_codigo': self.rfc_in_codigo}
            dict_atrib = requests.get(url, params=payload).json()
            if dict_atrib:
                json_caracteristas = formatar_caracteristicas(self.referencia,dict_atrib)
                #print(json_caracteristas)
                self.referenciaDesc = json_caracteristas['Caracteristicas']
                #regra para Filial Zk Laminadora
                if self.fil_in_codigo == 312:
                    try:
                        self.pro_re_comprimento = int(json_caracteristas.get('Comprimento'))
                    except:
                        pass
                    try:
                        self.pro_re_largura= int(json_caracteristas.get('Largura'))
                    except:
                        pass
                    try:
                        self.classificacao= json_caracteristas.get('Classificacao')
                    except:
                        pass
        else:
            self.referencia = '*'
            self.referenciaDesc = self.referencia
        for rs_itn in lista:
            # Se a filial for 3 e o item for P100 (7376) busca as medidas do item pai;
            if (self.fil_in_codigo == 3) and (self.pro_in_codigo == 7376):
                if (rs_itn['pro_in_codigo']== self.ord_pro_in_codigo):
                    self.pro_re_comprimento = rs_itn['pro_re_comprimento']
                    self.pro_re_largura= rs_itn['pro_re_largura']
                    self.pro_re_espessura = rs_itn['pro_re_espessura']
        # 4) Dados da Impressora e máquina vinculada;
        for rs_printer in cr_equipamento:
            self.host = rs_printer['PRINTER_ST_IP']
            self.maquina = rs_printer['MAQ_IN_CODIGO']
        # 5) Dados da máquina vinculada;
        for rs_maquina in cr_maquina:
            self.cmaq_st_codigo = rs_maquina['CMAQ_ST_CODIGO']
            self.cmaq_st_id = rs_maquina['CMAQ_ST_ID']
        # 6) Dados dos campos especificos da ordem;
        self.umidade = cr_ord_adic['umidade']
        self.lote_ordem = cr_ord_adic['lote_ordem']
        self.destino = cr_ord_adic['destino']
        if (self.fil_in_codigo == 312):
            self.origem = cr_ord_adic['origem']        
        v_lista.append(self.ord_in_codigo)
        v_lista.append(self.fil_in_codigo)
        v_lista.append(self.ctl_in_codigo)
        v_lista.append(self.cliente)
        v_iniseq = IntAPI_sqlite(v_lista)
        self.seqmov = v_iniseq.seq_movprod_sqlite()
        str_seq = str(self.seqmov)
        self.seqlote = str(str_seq.zfill(6))
        # 7) converte a unidade pelos campos específicos do produto
        v_med= []
        v_med.append(self.tpo_st_codigo)
        v_med.append(self.pro_re_comprimento)
        v_med.append(self.pro_re_largura)
        v_med.append(self.pro_re_espessura)
        v_med.append(self.apt_re_quantidade)
        v_med.append(self.fil_in_codigo)
        if self.fil_in_codigo == 312:
            if self.pro_in_codigo in [110,276,283,285,286,284]:
                #Busca o conversor do Item
                funcao = 'itensOrdens/'
                url_itn = geturlapp(funcao)
                payload_itn = {'pro_st_id': self.pro_st_id}
                cr_prod = requests.get(url_itn, params=payload_itn).json()
                for res_prod in cr_prod:
                    v_conversor = json.loads(res_prod['PRO_ST_CONVERSOR'])
                    if v_conversor:
                        for rs_cn in v_conversor:
                            self.fator = float(rs_cn.get('UNI_ST_FORMULA').replace(',','.'))
            if self.fator > 0:
                self.apt_re_quantConv = round(self.apt_re_quantidade*self.fator,3)
            elif self.pro_in_codigo == 281:
                self.apt_re_quantConv = self.apt_re_quantidade
            elif self.pro_in_codigo == 282:
                self.apt_re_quantConv = self.apt_re_quantidade
            elif self.classificacao == 'Retalho':
                self.apt_re_quantConv = self.apt_re_quantidade
            elif self.rfc_in_codigo == 0:
                self.apt_re_quantConv = self.apt_re_quantidade
            else:
                self.apt_re_quantConv = converter_unidade(v_med)        
        else:
            self.apt_re_quantConv = converter_unidade(v_med)
        #raise Exception(self.apt_re_quantConv)
        # 8) monta o lote da ordem;
        self.lote = self.monta_lote()
        # 9) imprimir etiqueta
        v_listEti = []
        # quebra a descrição do item para a etiqueta;
        if len(self.pro_st_descricao) < 28:
            self.string1 = self.pro_st_descricao
            self.string2 = ''
        else:
            v_sep = ' '
            #busca o primeiro indice da string;
            v_idx = self.pro_st_descricao[1:28].rfind(v_sep)
            self.string1 = self.pro_st_descricao[0:v_idx+1]
            self.string2 = self.pro_st_descricao[v_idx+2:]
        #Carrega a lista para gerar a Etiqueta;
        if self.fil_in_codigo == 312:
            if not(self.host=='192.168.60.100') or not(self.host=='192.168.60.101'):
                self.host=='192.168.60.100'
        v_listEti.append(dict(ordem = self.ord_in_codigo,
                              descr1 = self.string1,
                              descr2 = self.string2,
                              un = self.uni_st_unidade,
                              grupo = '',
                              codbar = self.lote,
                              qtde = self.apt_re_quantidade,
                              lote = self.lote,
                              data = self.str_eti,
                              seqlote = self.seqlote,
                              #código da máquina
                              maquina = self.cmaq_st_codigo,
                              #dados da impressora do equipamento
                              impressora =self.host,
                              #Campos específicos do produto;
                              comprimento = self.pro_re_comprimento,
                              largura = self.pro_re_largura,
                              espessura =self.pro_re_espessura,
                              madeira = self.pro_st_madeira,
                              #dados dos campos específicos da ordem;
                              destino = self.destino,
                              umidade = self.umidade,
                              loteordem = self.lote_ordem,
                              tipoordem = self.tpo_st_codigo,
                              item = self.pro_in_codigo,
                              origem = self.origem,
                              pallet = self.referenciaDesc,
                              classificacao = self.classificacao,
                              qtde_conv = self.apt_re_quantConv,
                              filial = self.fil_in_codigo,
                              volume = self.volume,
                              pilha= self.pilha,
                              fornecedor = self.fornecedor))
        json_eti= {}
        json_eti = json.dumps(v_listEti)
        #print(json_eti)
        #Carrega os dados para o apontamento;
        dados = {'FIL_IN_CODIGO': self.fil_in_codigo,
                 'APT_IN_SEQUENCIA': self.seqmov,
                 'APT_DT_APONTAMENTO': self.str_now,
                 'APT_CH_STATUS': 'A',
                 'ORD_IN_CODIGO': self.ord_in_codigo,
                 'PRO_IN_CODIGO': self.pro_in_codigo,
                 'ORL_RE_QTDLOTE' : self.apt_re_quantidade,
                 'ORL_ST_REFERENCIA' :self.referencia,
                 'CTL_IN_CODIGO' : self.ctl_in_codigo,
                 'PRO_ST_DESCRICAO' : self.pro_st_descricao,
                 'PRO_ST_LOTE': self.lote,
                 'PRO_ST_SEQUENCIAL': self.seqlote,
                 'PRO_ST_ETIQUETA': json_eti,
                 'RFC_ST_DESCRICAO':self.referenciaDesc,
                 'PRO_RE_QTDREFUGO':self.pro_re_qtdrefugo,
                 'PRO_RE_QTDCONV':self.apt_re_quantConv,
                 'PRO_ST_LOTEORI':self.origem,
                 'PRO_ST_ID':self.pro_st_id,
                 'ORD_ST_ID': self.ord_st_id,
                 'CMAQ_ST_ID':self.cmaq_st_id,
                 'ORL_RE_QTDAJUSTADA':self.apt_re_quantConv,
                 'PRO_ST_FORNECEDOR':self.fornecedor}
        funcao = 'apontamentos/'
        api_producao = geturlapp(funcao)
        #print('DADOS',dados)
        try:
            response = requests.post(api_producao, data=dados)
        except:
            response = {'msg': 'erro'}
        #obj_itens.apt_inserirlote(v_dlotes)
        try:
            c_etiqueta = gera_etiqueta(json_eti)
        except:
            c_etiqueta = {'msg': 'erro'}
        #guarda o ultimo apontamento na sessão'''
        return self.seqmov
    
    def imprimirEtiquetaReceb(self, pParams):
        v_listEti = []
        json_eti = {}
        funcao = 'lotesreceb/'
        get_url = geturlapi(funcao)
        payload = {'nota': pParams[0], 'filial':pParams[1], 'lote':pParams[2]}
        c_rs = requests.get(get_url, params=payload).json()
        for itn in c_rs:
            #print(itn)
            self.fil_in_codigo = itn['FIL_IN_CODIGO']
            self.pro_st_descricao =  itn['PRO_ST_DESCRICAO']
            self.pro_in_codigo =  itn['PRO_IN_CODIGO']
            self.pro_in_codigo = itn['PRO_IN_CODIGO']
            self.seqlote = itn['SEQUENCIAL']
            self.apt_re_quantidade = 1
            self.pro_re_comprimento = itn['COMPRIMENTO']
            self.pro_re_largura = itn['LARGURA']
            self.origem = itn['ORIGEM']
            self.ord_in_codigo = itn['AVR_ST_NOTA']
            self.lote_ordem = itn['MVL_ST_LOTEFORNE']
            self.lote = itn['MVL_ST_LOTEFORNE']
            self.volume = itn['VOLUME']
            self.apt_re_quantConv = float(itn['MVL_RE_QUANTIDADE'])
            self.row_now = trata_data_sqlite(itn['AVR_DT_ENTRADANF'])
            self.str_eti = self.row_now.strftime('%d/%m/%Y')
            self.classificacao = itn['CLASSIFICACAO']
            self.host = pParams[3]
            self.pilha = itn['PILHA']

            if len(self.pro_st_descricao) < 28:
                self.string1 = self.pro_st_descricao
                self.string2 = ''
            else:
                v_sep = ' '
                #busca o primeiro indice da string;
                v_idx = self.pro_st_descricao[1:28].rfind(v_sep)
                self.string1 = self.pro_st_descricao[0:v_idx+1]
                self.string2 = self.pro_st_descricao[v_idx+2:]
            v_listEti.append(dict(ordem = self.ord_in_codigo,
                              descr1 = self.string1,
                              descr2 = self.string2,
                              un = self.uni_st_unidade,
                              grupo = '',
                              codbar = self.lote,
                              qtde = self.apt_re_quantidade,
                              lote = self.lote,
                              data = self.str_eti,
                              seqlote = self.seqlote,
                              #código da máquina
                              maquina = self.cmaq_st_codigo,
                              #dados da impressora do equipamento
                              impressora =self.host,
                              #Campos específicos do produto;
                              comprimento = self.pro_re_comprimento,
                              largura = self.pro_re_largura,
                              espessura =self.pro_re_espessura,
                              madeira = self.pro_st_madeira,
                              #dados dos campos específicos da ordem;
                              destino = self.destino,
                              umidade = self.umidade,
                              loteordem = self.lote_ordem,
                              tipoordem = self.tpo_st_codigo,
                              item = self.pro_in_codigo,
                              origem = self.origem,
                              pallet = self.referenciaDesc,
                              classificacao = self.classificacao,
                              qtde_conv = self.apt_re_quantConv,
                              filial = self.fil_in_codigo,
                              volume = self.volume,
                              pilha= self.pilha))

            json_eti = json.dumps(v_listEti)
            #try:
            c_etiqueta = gera_etiqueta(json_eti)
            #except:
            #    c_etiqueta = {'msg': 'erro'}
        return {'resultado':'OK'}
    def imprimirEtiquetaInventario(self, pParams):
        v_listEti = []
        json_eti = {}
        funcao = 'lotesinvent/'
        get_url = geturlapi(funcao)
        payload = {'doc': pParams[0], 'filial':pParams[1], 'lote':pParams[2]}
        c_rs = requests.get(get_url, params=payload).json()
        for itn in c_rs:
            #print(itn)
            self.fil_in_codigo = itn['FIL_IN_CODIGO']
            self.pro_st_descricao =  itn['PRO_ST_DESCRICAO']
            self.pro_in_codigo =  itn['PRO_IN_CODIGO']
            self.pro_in_codigo = itn['PRO_IN_CODIGO']
            self.seqlote = itn['SEQUENCIAL']
            self.apt_re_quantidade = 1
            self.pro_re_comprimento = itn['COMPRIMENTO']
            self.pro_re_largura = itn['LARGURA']
            self.origem = itn['ORIGEM']
            self.ord_in_codigo = itn['AVR_ST_NOTA']
            self.lote_ordem = itn['MVL_ST_LOTEFORNE']
            self.lote = itn['MVL_ST_LOTEFORNE']
            self.volume = itn['VOLUME']
            self.apt_re_quantConv = float(itn['MVL_RE_QUANTIDADE'])
            self.row_now = trata_data_sqlite(itn['AVR_DT_ENTRADANF'])
            self.str_eti = self.row_now.strftime('%d/%m/%Y')
            self.classificacao = itn['CLASSIFICACAO']
            self.host = pParams[3]
            self.pilha = itn['PILHA']
            self.tpo_st_codigo = 'INVT'

            if len(self.pro_st_descricao) < 28:
                self.string1 = self.pro_st_descricao
                self.string2 = ''
            else:
                v_sep = ' '
                #busca o primeiro indice da string;
                v_idx = self.pro_st_descricao[1:28].rfind(v_sep)
                self.string1 = self.pro_st_descricao[0:v_idx+1]
                self.string2 = self.pro_st_descricao[v_idx+2:]
            v_listEti.append(dict(ordem = self.ord_in_codigo,
                              descr1 = self.string1,
                              descr2 = self.string2,
                              un = self.uni_st_unidade,
                              grupo = '',
                              codbar = self.lote,
                              qtde = self.apt_re_quantidade,
                              lote = self.lote,
                              data = self.str_eti,
                              seqlote = self.seqlote,
                              #código da máquina
                              maquina = self.cmaq_st_codigo,
                              #dados da impressora do equipamento
                              impressora =self.host,
                              #Campos específicos do produto;
                              comprimento = self.pro_re_comprimento,
                              largura = self.pro_re_largura,
                              espessura =self.pro_re_espessura,
                              madeira = self.pro_st_madeira,
                              #dados dos campos específicos da ordem;
                              destino = self.destino,
                              umidade = self.umidade,
                              loteordem = self.lote_ordem,
                              tipoordem = self.tpo_st_codigo,
                              item = self.pro_in_codigo,
                              origem = self.origem,
                              pallet = self.referenciaDesc,
                              classificacao = self.classificacao,
                              qtde_conv = self.apt_re_quantConv,
                              filial = self.fil_in_codigo,
                              volume = self.volume,
                              pilha= self.pilha))

            json_eti = json.dumps(v_listEti)
            #try:
            c_etiqueta = gera_etiqueta(json_eti)
            #except:
            #    c_etiqueta = {'msg': 'erro'}
        return {'resultado':'OK'}
    
class IntAPI_sqlite:
    def __init__(self, pParams):
        self.funcao = None
        self.uri = None
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        self.ord_st_id = None
        self.seq_apt = None
        self.dbname = self.dbname = settings.DATABASE        
    def listar_producao_sqlite(self, pParams):
        self.funcao = 'apontamentos/'
        self.uri = geturlapp(self.funcao)
        #print(self.uri)
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_producao= {}
        json_producao = json.dumps(vRes_json)
        return json_producao
    def itens_ordem_sqlite(self, pParams):
        json_Itens= {}
        self.funcao = 'ordens/'
        self.uri = geturlapp(self.funcao)
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        c_appitens = requests.get(self.uri, params=payload).json()
        if c_appitens:
            for r_appitens in c_appitens:
                d_tens = r_appitens['PRO_ST_ITENS']
                json_Itens = json.dumps(d_tens)
        #print(json_Itens)
        return json_Itens
    def listar_ocorrencias_sqlite(self):
        self.funcao = 'atividade/'
        self.uri = geturlapp(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_ocorrencias= {}
        json_ocorrencias = json.dumps(vRes_json)
        return json_ocorrencias
    def seq_movdem_sqlite(self):
        v_seqdem = 0
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apd.mov_in_sequencia IS NULL THEN 1 ELSE
                                      max(apd.mov_in_sequencia)+1 END as mov_in_sequencia
                            from Apt_Pro_Demandas apd''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_seqdem = 1
                else:
                    v_seqdem = int(rs[0])
        return v_seqdem

    def seq_movprod_sqlite(self):
        v_sequencia = 0
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apd.apt_in_sequencia IS NULL THEN 1 ELSE
                                      max(apd.apt_in_sequencia)+1 END as apt_in_sequencia
                            from apt_apontaordem apd''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_sequencia = 1
                else:
                    v_sequencia = int(rs[0])
        return v_sequencia

    def seq_ocor_sqlite(self):
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apo.ati_in_sequencia IS NULL THEN 1 ELSE
                                      max(apo.ati_in_sequencia)+1 END as ati_in_sequencia
                            from Apt_Ocorrencia apo''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        v_seqOcorrencia = 0
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_seqOcorrencia = 1
                else:
                    v_seqOcorrencia = int(rs[0])
        return v_seqOcorrencia    
    def total_prod(self, pParams):
        self.funcao = 'apontamentos/'
        self.uri = geturlapp(self.funcao)        
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        self.seq_apt = pParams[2]
        #payload = {'ordem': self.ordem_in,'filial': self.fil_in, 'ctl_in_codigo': self.seq_apt, 'status': 'A', 'gera_resumo':'N'}
        #Busca as ordens para geração do resumo de produção;
        '''c_rs = requests.get(self.uri, params=payload).json()
        for v_rs in c_rs:
            #trava as ordens para geração do resumo de produção;
            payload = {'ordem': self.ordem_in,'filial': self.fil_in, 'status': 'A', 'gera_resumo':'S','sequencia':v_rs['APT_IN_SEQUENCIA']}
            c_tr = requests.put(self.uri, params=payload)'''
        payload = {'ordem': self.ordem_in,'filial': self.fil_in, 'status': 'A', 'group_by':'S'}
        vRes_json = requests.get(self.uri, params=payload).json()
        #grava o teste na tabela
        '''self.funcao = 'resordens/'
        self.uri = geturlapp(self.funcao)
        dados = data = {"RES_IN_SEQUENCIA": 3, "ORD_ST_ID": 62537, "PRO_ST_ID": 2775, "PRO_RE_QTDINFORMADA": 40.905, "RES_ST_STATUS": "A"}
        #print('DADOS',dados)
        response = requests.post(self.uri, data=dados)'''
        return vRes_json

    def apt_resumoProd(self):
        self.funcao = 'ordens/'
        self.uri = geturlapp(self.funcao)
        payload = {'ord_in_codigo': self.ordem_in,'fil_in_codigo': self.fil_in}
        c_rs = requests.get(self.uri, params=payload).json()
        if c_rs:
             for r_rs in c_rs:
                 self.ord_st_id  = r_rs['ORD_ST_ID']
        self.funcao = 'resordens/'
        self.uri = geturlapp(self.funcao)
        payload = {'ord_st_id': self.ord_st_id}
        c_rs = requests.get(self.uri, params=payload).json()
        return c_rs

class Login_inicial_sqlite:
    def __init__(self,p_ordem,p_usuario,ip):
        self.ord_filial = None
        self.ordem_in = None
        self.ord_operacao = None
        self.equipamento_cad = 'N'
        self.ender_ip = ip
        #getEnderIP()
        self.dbname = settings.DATABASE
        self.usuario_in = p_usuario
        self.ordem_st_extenso = p_ordem
        r_ordem = json.loads(formatar_ordem(self.ordem_st_extenso))
        for v_ord in r_ordem:
            self.ordem_in = v_ord['ordem']
            self.ord_filial = v_ord['filial']
            self.ord_operacao = v_ord['operacao']

    def apt_usuario_sqlite(self):
        v_params = []
        usuarios = {}
        lista = []
        if self.equipamento_cad == 'N':
            con = sqlite3.connect(self.dbname)
            v_params.append(self.usuario_in)
            selectSQL = ('''select opd.opd_in_codigo,
                              opd.opd_st_cracha,
                              opd.opd_st_nome
                         from Apt_Pro_CadOperador opd
                         where opd.opd_st_cracha = ?
                       order by opd_in_codigo''')
            cur = con.execute(selectSQL,v_params)
            #cur.setString(1, self.usuario_in)
            c_rs = cur.fetchall()
            cur.close
            con.close
            if c_rs is None:
                print ('Vazio')
            for rs in c_rs:
                lista.append(dict(opd_in_codigo = rs[0],
                              opd_st_alternativo = rs[1],
                              opd_st_descricao = rs[2]))
        else:
            lista.append(dict(opd_in_codigo = None,
                              opd_st_alternativo = None,
                              opd_st_descricao = None))
        usuarios = json.dumps(lista)
        return usuarios

    def equipamento_cadastrado(self):
        v_params = []
        con = sqlite3.connect(self.dbname)
        v_params.append(self.ender_ip)
        selectSQL = ('''select *
                         from apt_equipamentos eqp
                        where eqp.eqp_st_ipaddress = ?''')
        cur = con.execute(selectSQL,v_params)
        #cur.setString(1, self.ender_ip)
        c_rs = cur.fetchall()
        cur.close
        con.close
        v_equipamento_cad = 'N'
        for rs in c_rs:
            v_equipamento_cad = 'S'
        return v_equipamento_cad

    def seq_initapt_sqlite(self):
        sequencia = 1
        con = sqlite3.connect(self.dbname)
        selectSQL =('''select CASE WHEN apc.ctl_in_codigo IS NULL THEN 1 ELSE
                                      max(apc.ctl_in_codigo)+1 END as ctl_in_codigo
                            from apt_controle apc''')
        cur = con.execute(selectSQL)
        c_rs = cur.fetchall()
        cur.close
        con.close
        for rs in c_rs:
            if not rs[0] is None:
                sequencia = rs[0]
            else:
                sequencia = 1
        return sequencia
    
    def userLogado_sqlite(self):
        logado = False
        pro_st_descricao = None
        if self.usuario_in:
            con = sqlite3.connect(self.dbname)
            v_lista = []
            v_lista.append(self.usuario_in)
            v_lista.append(self.ordem_st_extenso)
            selectSQL = ('''select apc.*
                              from apt_controle apc
                             where apc.ctl_st_usuario = ?
                               and apc.ord_st_extenso = ?
                               and apc.ctl_dt_logout is null''')
            cur = con.execute(selectSQL,v_lista)
            c_rs = cur.fetchall()
            #print(c_rs)
            cur.close
            con.close
            lista = []
            #busca o item principal da ordem para trazer a descrição do produto;
            dados = {"ordem": self.ordem_in,'filial': self.ord_filial, 'retorno':'descricao'}
            v_dados = prep_producao()
            pro_st_descricao = v_dados.get_dadosOrdem(dados)
            if c_rs:
                for rs in c_rs:
                    lista.append(dict(ctl_in_codigo = int(rs[0]),
                                      logado = True,
                                      pro_st_descricao = pro_st_descricao))
            else:
                lista.append(dict(ctl_in_codigo = None,
                                  logado = False,
                                  pro_st_descricao = pro_st_descricao))
            usuarios = json.dumps(lista)
        return usuarios
    def descontar_sqlite(self):
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        #row_now = timezone.now()
        #str_now = row_now.strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        str_now = now.strftime('%Y-%m-%d %H:%M:%S')
        v_lista = []
        v_lista.append(str_now)
        v_lista.append(self.usuario_in)
        v_lista.append(self.ordem_st_extenso)
        #print(v_lista)
        #v_lista.append(self.seq_controle)
        #print (self.usuario_in, self.seq_controle,str_now)
        ExecSQL =('''update apt_controle
                          set ctl_dt_logout = ?
                        where ctl_st_usuario = ?
                          and ord_st_extenso = ?''')
        cur.execute(ExecSQL,v_lista)
        con.commit()
        #cur.setString(1, str_now)
        #cur.setString(2, self.usuario_in)
        #cur.setInt(3, self.seq_controle)
        #cur.executeUpdate()
        cur.close
        con.close
        return True
    def conectar_sqlite(self):
        v_params = []
        v_iniciar = []
        v_conect = {}
        maquina = None
        impressora = None
        maquina_id = ''
        ordem_id = ''
        pro_st_descricao = ''
        now = datetime.now()
        v_count = 0
        str_now = now.strftime('%Y-%m-%d %H:%M:%S')
        sequencia = self.seq_initapt_sqlite()
        v_params.append(sequencia)
        v_params.append(self.usuario_in)
        v_params.append(self.ordem_in)
        v_params.append(str_now)
        v_params.append(self.ender_ip)
        v_params.append(self.ordem_st_extenso)
        funcao = 'ordens/'
        app_url = geturlapp(funcao)
        payload = {'ord_in_codigo': self.ordem_in,'fil_in_codigo': self.ord_filial}
        try:
            cur_ord = requests.get(app_url, params=payload).json()
            if not (cur_ord):
                v_listOrd = []
                v_listOrd.append(None)
                v_listOrd.append(self.ord_filial)
                v_listOrd.append(self.ordem_in)
                ini = IntOrdens()
                while cur_ord is None:
                    ini.buscaOrdens(v_listOrd)
                    cur_ord = requests.get(app_url, params=payload).json()
                    v_count += 1
                    if v_count > 5:  # Evitar loop infinito
                        break
                for rs_ord in cur_ord:
                    ordem_id = rs_ord['ORD_ST_ID']
            else:
                for rs_ord in cur_ord:
                    ordem_id = rs_ord['ORD_ST_ID']            
        except:
            pass
        #busca o item principal da ordem para trazer a descrição do produto;
        dados = {"ordem": self.ordem_in,'filial': self.ord_filial, 'retorno':'descricao'}
        v_dados = prep_producao()
        pro_st_descricao = v_dados.get_dadosOrdem(dados)
        funcao = 'equipamento/'
        app_url = geturlprod(funcao)
        payload = {'cliente': v_params[4],'filial':self.ord_filial}
        try:
            cr_printer = requests.get(app_url, params=payload).json()
            for rs_printer in cr_printer:
                maquina = rs_printer['MAQ_IN_CODIGO']
                impressora = rs_printer['PRINTER_ST_IP']
        except:
            pass
        if maquina is not None:
            funcao = 'maquina/'
            app_url = geturlprod(funcao)
            payload = {'cmaq_id': maquina}
            try:
                cr_maquina = requests.get(app_url, params=payload).json()
                if cr_maquina:
                    for rs_maquina in cr_maquina:
                        maquina_id = rs_maquina['CMAQ_ST_ID']
            except:
                pass        
        funcao = 'controleApt/'
        uri = geturlprod(funcao)
        dados = data = {"CTL_IN_CODIGO": sequencia,
                        "CTL_ST_USUARIO": self.usuario_in,
                        "ORD_IN_CODIGO": self.ordem_in,
                        "CTL_DT_LOGIN": str_now,
                        "CTL_ST_IPADDRESS": self.ender_ip,
                        "ORD_ST_EXTENSO": self.ordem_st_extenso,
                        "CTL_ST_STATUS": 'A',
                        "FIL_IN_CODIGO": self.ord_filial,
                        "ORD_ST_ID":ordem_id,
                        "CMAQ_ST_ID":maquina_id,
                        "PRINTER_ST_IP":impressora}
        try:
            response = requests.post(uri, data=dados)
            v_iniciar.append(dict(ctl_in_codigo = sequencia,
                                   logado = True,
                                   pro_st_descricao = pro_st_descricao))
        except:
            v_iniciar.append(dict(ctl_in_codigo = None,
                                   logado = False,
                                   pro_st_descricao = pro_st_descricao))
        v_conect = json.dumps(v_iniciar)
        return v_conect

class Controle:
    def __init__(self,pParams):
        v_params = pParams
        self.ord_filial = None
        self.ord_odem = None
        self.controle = v_params.get('ctl')
        self.impressora = None
    def getControle(self):
        cr_ctl = {}
        funcao = 'controleApt/'
        app_url = geturlprod(funcao)
        payload = {'ctl_in_codigo': self.controle}
        try:
            cr_ctl = requests.get(app_url, params=payload).json()
        except:
            pass
        return cr_ctl
    def putControle(self, pParams):
        self.impressora = pParams.get('impressora')
        funcao = 'controleApt/'
        app_url = geturlprod(funcao)
        cr_ctl = {}
        payload = {'ctl_in_codigo': self.controle, 'impressora': self.impressora}
        try:
            cr_ctl = requests.put(app_url, params=payload).json()
        except:
            pass
        return cr_ctl
