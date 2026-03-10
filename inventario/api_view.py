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
def geturlinv(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/inv/'+funcao
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
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return v_retorno
def sequencial(pParam):
    v_seq = 1
    con = sqlite3.connect(settings.DATABASE)
    if pParam[0] == 'V':
        selectSQL = ('''select CASE WHEN b.ITI_IN_SEQUENCIA IS NULL THEN 1 
                               ELSE max(b.ITI_IN_SEQUENCIA)+1 END as ITI_IN_SEQUENCIA
                          from alm_InventarioItens b''')
        cur = con.execute(selectSQL)
    elif pParam[0] == 'A':
        selectSQL = ('''select CASE WHEN b.INV_IN_SEQUENCIA IS NULL THEN 1 
                               ELSE max(b.INV_IN_SEQUENCIA)+1 END as INV_IN_SEQUENCIA
                          from alm_Inventario b''')
        cur = con.execute(selectSQL)
    else:
        selectSQL = ('''select CASE WHEN b.INV_IN_SEQUENCIA IS NULL THEN 1 
                               ELSE max(b.INV_IN_SEQUENCIA)+1 END as INV_IN_SEQUENCIA
                          from alm_Inventario b''')
        cur = con.execute(selectSQL)
    c_rs = cur.fetchall()
    cur.close
    con.close
    for rs in c_rs:
        if not rs[0] is None:
            v_seq = rs[0]
        else:
            v_seq = 1
    return v_seq
def InventItem(pParams):
    seq_baixa=1
    v_saldo_estoque = float(0);
    v_saldo_baixas = float(0);
    v_qtde_baixas = float(0);
    v_params =[]
    #Busca Sequencial da Requisição
    v_params.append('V')
    seq_baixa = sequencial(v_params)
    #busca Saldo em estoque do item;
    funcao = 'consultasaldo/'
    get_url = geturlapi(funcao)
    payload = {'id': pParams[0]}
    c_rs = requests.get(get_url, params=payload).json()
    for v_rs in c_rs:
        v_saldo_estoque = v_rs['mvs_re_quantidade']
    #busca saldo de baixas do item;
    funcao = 'reqItem/'
    get_url = geturlest(funcao)
    payload = {'item': pParams[0],'status':'A'}
    c_rs = requests.get(get_url, params=payload).json()
    for v_rs in c_rs:
        v_qtde_baixas = float(v_rs['BXI_RE_QUANTIDADE'])
        v_saldo_baixas = v_saldo_baixas+v_qtde_baixas;
    #saldo informado na conferência;
    v_saldo_informado = pParams[1];
    v_saldo_Ajuste = (v_saldo_informado-v_saldo_estoque+v_saldo_baixas)
    if v_saldo_Ajuste > 0:
        v_tipo_mov = 'EDI';
    else:
        v_tipo_mov = 'SDI';
    if (abs(v_saldo_Ajuste) > 0):
        dados = data = {"ITI_IN_SEQUENCIA": seq_baixa,
                        "INV_IN_SEQUENCIA": pParams[2],
                        "ITI_ID_PRODUTO": pParams[0],
                        "ITI_RE_QUANTIDADE":abs(v_saldo_Ajuste),
                        "ITI_CH_STATUS": 'A',
                        "ITI_ST_TIPOMOV":v_tipo_mov                        
                        }
        #se não existir inventário para o Item criar, senão fazer update;
        funcao = 'invItem/'
        get_urlinv = geturlinv(funcao)
        payload = {'item': pParams[0],'status':'A'}
        i_rs = requests.get(get_urlinv, params=payload).json()
        if i_rs:
            for v_rs in i_rs:    
                #atualiza movimento de inventário.            
                v_atualiza = {'item': pParams[0],'status':'A','sequencia':v_rs['ITI_IN_SEQUENCIA'],'movimento':0, 'quantidade':abs(v_saldo_Ajuste)}
                response = requests.put(get_urlinv, data=v_atualiza)                
        else:
            #cria movimento de ajuste;
            response = requests.post(get_urlinv, data=dados)
def Listar_itensInvent(pParams):
    funcao = 'invItem/'
    get_url = geturlinv(funcao)
    payload = {'inventario': pParams[0],'status':'A'}    
    c_rs = requests.get(get_url, params=payload).json()
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return c_rs

def IntegraInventario(pParam):
    # Busca inventários em Aberto
    funcao = 'gravarinventario/'
    get_urlest = geturlinv(funcao)
    payload = {'status':'A','sequencia':pParam[0],'filial':pParam[1]}
    c_inv = requests.get(get_urlest, params=payload).json()
    if c_inv:
        for r_inv in c_inv:
            dados = r_inv
            # Busca Itens em aberto;
            funcao = 'invItem/'
            get_urlest = geturlinv(funcao)
            payload = {'status':'A','inventario':r_inv['INV_IN_SEQUENCIA']}
            c_itn = requests.get(get_urlest, params=payload).json()
            if c_itn:
                funcao = 'geraInventario/'
                get_urlapi = geturlapi(funcao)
                #grava a integração do inventário
                c_respReq = requests.post(get_urlapi, data=dados).json()
                if c_respReq['movimento'] is not None:
                    funcao = 'gravarinventario/'
                    get_urlest = geturlinv(funcao)
                    payload = {'sequencia':r_inv['INV_IN_SEQUENCIA'],'movimento':c_respReq['movimento'],'status': 'B'}
                    c_encerra = requests.put(get_urlest, data=payload)
def buscaInventario(pParam):
    funcao = 'gravarinventario/'
    get_url = geturlinv(funcao)
    payload = {'usuario': pParam[0],'status':'A','filial':pParam[1]}
    c_rs = requests.get(get_url, params=payload).json()
    v_retorno ={}
    v_retorno = json.dumps(c_rs)
    return v_retorno

def criarInventario(pParam):
    funcao = 'gravarinventario/'
    get_urlest = geturlinv(funcao)
    row_now = timezone.now()
    str_now = row_now.strftime('%Y-%m-%d')
    v_params =[]
    #Busca Sequencial da Requisição
    v_params.append('A')
    v_params.append(0)
    v_seq = sequencial(v_params)
    dados = data = {"INV_IN_SEQUENCIA": v_seq,
                    "INV_DT_MOVIMENTO": str_now,
                    "INV_ST_USUARIO": pParam[0],
                    "INV_CH_STATUS": 'A',
                    "FIL_IN_CODIGO": pParam[1],
                    "INV_ID_CCUSTO": ''}
    response = requests.post(get_urlest, data=dados)
    return v_seq
