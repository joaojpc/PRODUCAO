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
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest
from .services import CAMPOS_CADITENS, select_caditens, inserir_caditens, atualizar_caditens
from .services import CAMPOS_ITEMALMOXA, select_itemalmoxa, inserir_itemalmoxa, atualizar_itemalmoxa
from .services import CAMPOS_CENTROCUSTOS, select_centrocustos, inserir_centrocustos, atualizar_centrocustos

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
    # AJUSTE 2026-10-06: carga full do Oracle comparada com a tabela local (JSON x JSON);
    # grava o que for diferente: novo é inserido, alterado é atualizado, só local é mantido.
    # A leitura do Oracle exige a filial (antes não era enviada e a API falhava).
    c_oracle = requests.get(geturlapi('GetCentroCustos/'), params={'filial': pParam['filial']}).json() or []
    c_local = {d['CUS_ID_CCUSTO']: d for d in select_centrocustos()}
    obrigatorios = ['CUS_ID_CCUSTO','CUS_IDE_ST_CODIGO','CUS_ST_EXTENSO','CUS_ST_DESCRICAO']
    v_retorno = {'lidos': len(c_oracle), 'novos': 0, 'alterados': 0, 'erros': 0}
    novos, alterados, vistos = [], [], set()
    for d in c_oracle:
        if any(d.get(c) is None for c in obrigatorios):
            v_retorno['erros'] += 1
            continue
        chave = d['CUS_ID_CCUSTO']
        if chave in vistos:
            continue
        vistos.add(chave)
        if chave not in c_local:
            novos.append(d)
        elif any(d.get(c) != c_local[chave].get(c) for c in CAMPOS_CENTROCUSTOS):
            alterados.append(d)
    try:
        v_retorno['novos'] = inserir_centrocustos(novos)
        v_retorno['alterados'] = atualizar_centrocustos(alterados)
    except Exception as erro:
        v_retorno['erros'] += 1
        print('Erro ao gravar centro de custos', erro)
    return v_retorno

def _separar_novos_alterados(lista, campos, obrigatorios, fn_select):
    # Regra: compara o JSON do Oracle com o local (campos[0] é a chave).
    # Sem campo obrigatório -> erro; não existe local -> novo; existe e diferente -> alterado; igual -> nada.
    validos = [d for d in (lista or []) if all(d.get(c) is not None for c in obrigatorios)]
    erros = len(lista or []) - len(validos)
    c_local = fn_select([d[campos[0]] for d in validos])
    novos, alterados, vistos = [], [], set()
    for d in validos:
        chave = d[campos[0]]
        if chave in vistos:
            continue
        vistos.add(chave)
        if chave not in c_local:
            novos.append(d)
        elif any(d.get(c) != c_local[chave].get(c) for c in campos):
            alterados.append(d)
    return novos, alterados, erros

def Buscar_CadastroProdutos(pParam):
    # AJUSTE 2026-10-06: monta o JSON da API (Oracle), aplica a regra aqui e entrega ao services
    # para gravar (SQL puro), no lugar do GET/POST na API /est/. Contadores vão para a tela man_almoxa.
    # O Oracle só devolve o item que pode ser atualizado (marcado lá); não devolveu -> nada é alterado.
    # As localizações acompanham o item devolvido: nova é gravada, diferente é atualizada.
    payload = {'id': pParam['id'],'filial': pParam['filial']}
    c_itens = requests.get(geturlapi('GetCadastroItens/'), params=payload).json() or []
    c_locais = []
    for c_a in c_itens:
        if not c_a.get('BXI_ID_PRODUTO'):
            continue
        #busca local de estoque configurado no item
        payload = {'id': c_a['BXI_ID_PRODUTO'], 'filial': pParam['filial']}
        c_locais += requests.get(geturlapi('GetItenslocalizacao/'), params=payload).json() or []
    v_retorno = {'itens_lidos': len(c_itens), 'itens_novos': 0, 'itens_atualizados': 0,
                 'locais_novos': 0, 'locais_atualizados': 0, 'erros': 0}
    itens_novos, itens_alterados, erros = _separar_novos_alterados(c_itens, CAMPOS_CADITENS,
        ['BXI_ID_PRODUTO','PRO_TAB_IN_CODIGO','PRO_PAD_IN_CODIGO','PRO_IN_CODIGO'], select_caditens)
    v_retorno['erros'] += erros
    locais_novos, locais_alterados, erros = _separar_novos_alterados(c_locais, CAMPOS_ITEMALMOXA,
        ['LOC_ID_PROALMFIL','LOC_ID_ALMOXA','LOC_ID_ORG','LOC_ID_PRODUTO','LOC_IN_FILIAL','ALM_IN_CODIGO','LOC_IN_CODIGO'],
        select_itemalmoxa)
    v_retorno['erros'] += erros
    try:
        v_retorno['itens_novos'] = inserir_caditens(itens_novos)
        v_retorno['itens_atualizados'] = atualizar_caditens(itens_alterados)
        v_retorno['locais_novos'] = inserir_itemalmoxa(locais_novos)
        v_retorno['locais_atualizados'] = atualizar_itemalmoxa(locais_alterados)
    except Exception as erro:
        v_retorno['erros'] += 1
        print('Erro ao gravar cadastro de produtos', erro)
    return v_retorno

def Sincronizar_CadastroProdutos(pParam):
    # AJUSTE 2026-10-06: sincroniza substituindo (update_or_create) est_CadItens e est_CadItemAlmoxa
    # pelos dados do Oracle. Registros locais que não vêm do Oracle são mantidos.
    from django.db import transaction
    from almoxarifado.models import est_CadItens, est_CadItemAlmoxa
    campos_item = ['PRO_TAB_IN_CODIGO','PRO_PAD_IN_CODIGO','PRO_IN_CODIGO','PRO_ST_DESCRICAO','UNI_ST_UNIDADE']
    campos_loc = ['LOC_ID_ALMOXA','LOC_ID_ORG','LOC_ID_PRODUTO','LOC_IN_FILIAL','ALM_IN_CODIGO',
                  'LOC_IN_CODIGO','ALM_ST_DESCRICAO','LOC_ST_DESCRICAO']
    v_retorno = {'itens_lidos': 0, 'itens_novos': 0, 'itens_atualizados': 0,
                 'locais_novos': 0, 'locais_atualizados': 0, 'erros': 0}
    payload = {'id': pParam['id'],'filial': pParam['filial']}
    c_rs = requests.get(geturlapi('GetCadastroItens/'), params=payload).json()
    for c_a in (c_rs or []):
        v_retorno['itens_lidos'] += 1
        try:
            #busca local de estoque configurado no item (filial do operador)
            payload = {'id': c_a['BXI_ID_PRODUTO'], 'filial': pParam['filial']}
            c_prl = requests.get(geturlapi('GetItenslocalizacao/'), params=payload).json()
            with transaction.atomic():
                obj, criado = est_CadItens.objects.update_or_create(
                    BXI_ID_PRODUTO=c_a['BXI_ID_PRODUTO'],
                    defaults={k: c_a.get(k) for k in campos_item})
                v_retorno['itens_novos' if criado else 'itens_atualizados'] += 1
                for r_prl in (c_prl or []):
                    # Em erro no Oracle a API devolve só LOC_ID_PROALMFIL -> ignora o registro incompleto
                    if not r_prl.get('LOC_ID_PRODUTO'):
                        v_retorno['erros'] += 1
                        continue
                    obj, criado = est_CadItemAlmoxa.objects.update_or_create(
                        LOC_ID_PROALMFIL=r_prl['LOC_ID_PROALMFIL'],
                        defaults={k: r_prl.get(k) for k in campos_loc})
                    v_retorno['locais_novos' if criado else 'locais_atualizados'] += 1
        except Exception as erro:
            v_retorno['erros'] += 1
            print('Erro ', c_a.get('BXI_ID_PRODUTO'), erro)
    return v_retorno
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
