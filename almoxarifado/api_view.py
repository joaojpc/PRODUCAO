# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import socket
import json
import sqlite3
import datetime
from django.utils import timezone
from producao import settings
import requests

def geturlapp(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/app/'+funcao
    return url_principal
def geturlapi(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/api/'+funcao
    return url_principal
def geturlprod(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/prod/'+funcao
    return url_principal
def geturlest(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/est/'+funcao
    return url_principal
def formatar_ccusto(pParam):
        v_param = pParam
        v_tabela = None
        v_padrao = None
        v_extenso = None
        v_reduzido = None        
        if len(v_param) == 18:
            v_reduzido = v_param[11:19]
            v_extenso = v_param[6:11]
            v_padrao = v_param[3:6]
            v_tabela = v_param[0:3]
        elif len(v_param) == 17:
            v_reduzido = v_param[13:19]
            v_extenso = v_param[6:13]
            v_padrao = v_param[3:6]
            v_tabela = v_param[0:3]
        elif len(v_param) == 15:
            v_reduzido = v_param[13:19]
            v_extenso = v_param[6:13]
            v_padrao = v_param[3:6]
            v_tabela = v_param[0:3]
        else:
            pass
        l_retorno = []
        l_retorno.append(dict(reduzido = (v_reduzido),
                              extenso = (v_extenso),
                              padrao = (v_padrao),
                              tabela = (v_tabela)
                              ))
        v_retorno ={}
        v_retorno = json.dumps(l_retorno)
        return v_retorno

def numConcat(num1, num2):
      num1 = str(num1)
      num2 = str(num2)

      num1 += num2
      return int(num1)

def lista_usuarios(pParam):
    funcao = 'operador/'
    get_url = geturlprod(funcao)
    payload = {'operador': pParam}
    c_rs = requests.get(get_url, params=payload).json()
    if not c_rs:
        v_opd = buscar_Operadores(pParam)
        c_rs = requests.get(get_url, params=payload).json()
    return c_rs    

def buscar_Operadores(pParams):
    v_fil_in = 302
    v_opd_in = pParams
    funcao = 'get_operadores/'
    get_urlapi = geturlapi(funcao)
    payload = {'filial': v_fil_in, 'operador': v_opd_in}
    c_rs = requests.get(get_urlapi, params=payload).json()
    if c_rs:
        for rs in c_rs:
            funcao = 'operador/'
            get_urlest = geturlprod(funcao)
            dados = {"OPD_ST_CRACHA": rs.get('OPD_ST_ALTERNATIVO'),
                     "OPD_ST_NOME": rs.get('OPD_ST_DESCRICAO'),
                     "FIL_IN_CODIGO": v_fil_in}
            response = requests.post(get_urlest, data=dados)
    return response

def lista_ccusto(pParam):
    funcao = 'centrocustos/'
    get_urlest = geturlest(funcao)
    payload = {'id_centrocusto': pParam}
    c_rs = requests.get(get_urlest, params=payload).json()    
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return v_retorno

def cria_login(pParam):
    v_params = []
    v_params.append(str(pParam.get('usuario')))
    v_params.append(str(pParam.get('centrocusto')))
    v_params.append(str(pParam.get('ordemservico')))
    #Busca Usuário
    v_usu = lista_usuarios(v_params[0])
    for c_usu in v_usu:
        nomeusuario = c_usu['OPD_ST_NOME']
        filial = c_usu['FIL_IN_CODIGO']
    v_params.append(filial)        
    v_ret = json.loads(lista_ccusto(v_params[1]))    
    for v_rs in v_ret:
        ccustoDesc = v_rs['CUS_ST_DESCRICAO']
        v_reduzido = v_rs['CUS_IN_REDUZIDO']        
        v_params.append(v_reduzido)
    #verifica se tem requisição em aberto para o usuário e centro de custos e ordem de serviço;
    cr_req = json.loads(buscarequisicao(v_params))
    if cr_req:
        for v_cur in cr_req:
            v_req = v_cur['BXA_IN_SEQUENCIA']
    else:
        v_req = criarRequisicao(v_params)
    v_retorno ={'nomeusuario':nomeusuario,'filial':filial, 'requisicao':v_req,'ccustoDesc':ccustoDesc,'reduzido': v_reduzido,'ordemservico':v_params[2]}
    return v_retorno

def buscarequisicao(pParam):
    funcao = 'requisicao/'
    get_url = geturlest(funcao)
    payload = {'usuario': pParam[0],'id_ccusto':pParam[1],'status':'A','ordemservico':pParam[2],'filial':pParam[3]}
    c_rs = requests.get(get_url, params=payload).json()
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return v_retorno

def criarRequisicao(pParam):
    funcao = 'requisicao/'
    get_urlest = geturlest(funcao)
    row_now = timezone.now()
    str_now = row_now.strftime('%Y-%m-%d')
    v_params =[]
    #Busca Sequencial da Requisição
    v_params.append('R')
    v_params.append(0)
    seq_baixa = sequencial(v_params)
    dados = data = {"BXA_IN_SEQUENCIA": seq_baixa,
                    "BXA_DT_APONTAMENTO": str_now,
                    "BXA_ST_USUARIO": pParam[0],
                    "BXA_IN_CCUSTO": int(pParam[4]),
                    "BXA_CH_STATUS": 'A',
                    "FIL_IN_CODIGO": pParam[3],
                    "CUS_ID_CCUSTO": pParam[1],
                    "OS_ST_ID": pParam[2]}
    response = requests.post(get_urlest, data=dados)
    return seq_baixa
def sequencial(pParam):
    v_seq = 1
    con = sqlite3.connect(settings.DATABASE)
    if pParam[0] == 'R':
        selectSQL = ('''select CASE WHEN b.bxa_in_sequencia IS NULL THEN 1 
                               ELSE max(b.bxa_in_sequencia)+1 END as bxa_in_sequencia
                          from bxa_AlmoxaBaixa b''')
        cur = con.execute(selectSQL)
    else:
        v_lista = []
        v_lista.append(pParam[1])
        selectSQL = ('''select CASE WHEN i.bxi_in_sequencia IS NULL THEN 1 
                               ELSE max(i.bxi_in_sequencia)+1 END as bxi_in_sequencia                              
                          from bxi_AlmoxaBaixaItens i
                         where i.bxa_in_sequencia = ?''')
        cur = con.execute(selectSQL,v_lista)
    c_rs = cur.fetchall()
    cur.close
    con.close
    for rs in c_rs:
        if not rs[0] is None:
            v_seq = rs[0]
        else:
            v_seq = 1
    return v_seq

def incluirItem(pParams):
    funcao = 'reqItem/'
    seq_item=None
    get_urlest = geturlest(funcao)
    row_now = timezone.now()
    str_now = row_now.strftime('%Y-%m-%d')
    v_params =[]
    #Busca Sequencial da Requisição    
    v_params.append('I')
    v_params.append(pParams[0])
    seq_baixa = sequencial(v_params)
    seq_item = numConcat(pParams[0],seq_baixa)
    dados = data = {"BXI_ID_REQUISICAO": seq_item,
                    "BXI_IN_SEQUENCIA": seq_baixa,
                    "BXA_IN_SEQUENCIA": pParams[0],
                    "BXI_ID_PRODUTO": pParams[1],
                    "BXI_RE_QUANTIDADE":pParams[2],
                    "BXI_CH_STATUS": 'A',
                    "BXI_ID_ALMOXA":pParams[3],
                    "FIL_IN_CODIGO":pParams[4]}
    response = requests.post(get_urlest, data=dados)

def Listar_itensBaixa(pParams):
    funcao = 'reqItem/'
    get_url = geturlest(funcao)
    payload = {'sequencia': pParams[0], 'filial': pParams[1]}
    c_rs = requests.get(get_url, params=payload).json()
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return c_rs

def Item_requisicao(pParams):
    funcao = 'produtos/'
    get_urlest = geturlest(funcao)
    payload = {'item': pParams}
    c_prod = requests.get(get_urlest, params=payload).json()
    v_retorno ={}
    v_retorno = json.dumps(c_prod)
    return c_prod

def Buscar_CentroCusto(pParam):
    funcao = 'GetCentroCustos/'
    get_urlapi = geturlapi(funcao)
    payload = {'reduzido': None}
    c_rs = requests.get(get_urlapi, params=payload).json()
    if c_rs:
        for c_a in c_rs:
            funcao = 'centrocustos/'
            get_urlest = geturlest(funcao)
            get_urlest = geturlest(funcao)
            payload = {'id_centrocusto': c_a['CUS_ID_CCUSTO']}
            #Verificar se o Item ainda não foi cadastrado
            c_custo= requests.get(get_urlest, params=payload).json()
            if not c_custo:
                dados = c_a
                response = requests.post(get_urlest, data=dados)

def Buscar_CadastroProdutos(pParam):
    funcao = 'GetCadastroItens/'
    get_urlapi = geturlapi(funcao)
    #payload = {'padrao': pParam}
    payload = {'id': pParam['id'],'filial': pParam['filial']}
    c_rs = requests.get(get_urlapi, params=payload).json()
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
            #busca local de estoque configurado no item
            funcao = 'GetItenslocalizacao/'                
            get_urlapi = geturlapi(funcao)                
            payload = {'id': c_a['BXI_ID_PRODUTO'], 'filial':pParam['filial']}
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
def Integrarequisicao(pParam):
    # Busca requisições em aberto
    v_requisicao = pParam[0]
    v_filial = pParam[1]
    funcao = 'requisicao/'
    get_urlest = geturlest(funcao)
    payload = {'requisicao':None,'sequencia':v_requisicao,'status': 'L', 'filial': v_filial}
    c_encerra = requests.put(get_urlest, data=payload)
    '''if v_requisicao == 0:
        payload = {'sequencia':None,'status': 'A'}
    else:
        payload = {'sequencia':v_requisicao,'status': 'A'}
    c_req = requests.get(get_urlest, params=payload).json()
    if c_req:        
        for v_req in c_req:
            # Alterado em 22/01/2024 para melhorar desempenho.
            # A integração será feita por serviço e não pela aplicação.
            payload = {'requisicao':None,'sequencia':v_req['BXA_IN_SEQUENCIA'],'status': 'L'}
            c_encerra = requests.put(get_urlest, data=payload)            
            #prepara a integração da requisição
            dados = v_req
            funcao = 'geraBaixas/'
            get_urlapi = geturlapi(funcao)
            #grava a integração da requisição
            c_respReq = requests.post(get_urlapi, data=dados).json()
            #faz update no status da requisição
            for v_res in c_respReq:
                payload = {'requisicao':v_res['req_in_sequencia'],'sequencia':v_res['bxa_in_sequencia'],'status': 'B'}
                c_encerra = requests.put(get_urlest, data=payload)'''
