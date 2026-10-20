# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-20 (JPC): sincronizacao de ordens Oracle -> SQLite (rotina NOVA, isolada), copiada
do NMV. Recebe as chamadas das views. Mesmo comportamento do "Baixar Ordens" de hoje
(apontamento/api_view.py IntOrdens.buscaOrdens), mais enxuto:
  - leitura no Oracle por api/services.py (SQL nativo, UMA conexao, sem HTTP);
  - gravacao no SQLite por app/services.py (SQL nativo, sem ORM, JSON normalizado, uma transacao
    por OP), so do que estiver diferente (INSERT/UPDATE de colunas/DELETE de duplicadas);
  - cache por produto/referencia dentro da rodada; erro de uma OP nao derruba as outras.
Regras da rotina antiga do PRODUCAO mantidas de proposito (documentadas onde aparecem). O "Baixar
Ordens" continua intacto. Nada aqui grava no Oracle.
Diferencas do NMV: itens com chaves minusculas (apt_intprod2), rfc_in_codigo = 0 nao busca
atributos/caracteristicas (a rotina antiga daqui le a chave certa) e sem troca de PK.
"""
import time
from datetime import date, datetime
from decimal import Decimal

from app import services as local

# Decisao do usuario (igual ao NMV): botao "Sincronizar Ordens (nova)" grava a OP logada so no que
# estiver diferente. False = so compara.
SYNC_ORDENS_GRAVA = True
# Operadores com chave propria (operador cadastrado no Mega sem cadastro no app).
SYNC_OPERADORES_GRAVA = True

TAMANHOS_ORDEM = {'ORG_TAU_ST_CODIGO': 3, 'TPO_ST_CODIGO': 5, 'PRO_ST_ID': 13, 'ORD_ST_ID': 44, 'TPO_ST_ID': 12}
OBRIGATORIOS_ORDEM = ['ORG_TAB_IN_CODIGO', 'ORG_PAD_IN_CODIGO', 'ORG_IN_CODIGO', 'ORG_TAU_ST_CODIGO',
                      'ORD_TAB_IN_CODIGO', 'ORD_SEQ_IN_CODIGO', 'ORD_IN_CODIGO', 'PRO_TAB_IN_CODIGO',
                      'PRO_PAD_IN_CODIGO', 'PRO_IN_CODIGO', 'ORD_RE_QTDE_ORDEM']
TAMANHOS_ITEM = {'PRO_ST_DESCRICAO': 70, 'UNI_ST_UNIDADE': 8, 'PRO_ST_ID': 13}
OBRIGATORIOS_ITEM = ['PRO_TAB_IN_CODIGO', 'PRO_PAD_IN_CODIGO', 'PRO_IN_CODIGO', 'PRO_ST_DESCRICAO',
                     'UNI_ST_UNIDADE', 'RFC_IN_CODIGO']
TAMANHOS_CAR = {'CAR_ST_ID': 26, 'RAT_ST_ID': 13, 'RFC_ST_ID': 13, 'RAT_ST_DESCRICAO': 70, 'RAT_VALUE': 100,
                'RAT_CH_TIPO': 1, 'RAT_BO_GRUPO': 1, 'CAR_BO_OBRIGATORIO': 1, 'PAI_ST_DESCRICAO': 70}
OBRIGATORIOS_CAR = ['CAR_ST_ID', 'PAI_RAT_IN_CODIGO', 'RAT_IN_CODIGO', 'RFC_IN_CODIGO']


def org_da_filial(fil_in_codigo):
    """Mesmo de-para do botao "Baixar Ordens" (apontamento/views.py manutencao, get_ordens)."""
    return {3: 2, 312: 311, 302: 301}.get(fil_in_codigo, 2)


def _jsonavel(valor):
    """Mesmos tipos que chegam hoje pela API (DRF): Decimal -> float, data -> ISO."""
    if isinstance(valor, dict):
        return {k: _jsonavel(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_jsonavel(v) for v in valor]
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def _invalido(linha, obrigatorios, tamanhos):
    """O serializer da rotina antiga recusava (409) linha sem campo obrigatorio ou texto
    maior que a coluna. Devolve o motivo ou None."""
    faltando = [c for c in obrigatorios if linha.get(c) in (None, '')]
    if faltando:
        return f'campo(s) obrigatório(s) vazio(s): {faltando}'
    longos = [c for c, t in tamanhos.items() if linha.get(c) is not None and len(str(linha[c])) > t]
    if longos:
        return f'texto maior que a coluna: {longos}'
    return None


def _cache(memo, chave, buscar):
    if chave not in memo:
        memo[chave] = buscar()
    return memo[chave]


def _monta_ord_st_id(d_ord):
    """ORD_ST_ID vazio montado com as 7 colunas da chave (apontamento.api_view.monta_ordem)."""
    from apontamento.api_view import monta_ordem
    return monta_ordem([d_ord.get(c) for c in local.COLUNAS_ORDEM[:3]] + [str(d_ord.get('ORG_TAU_ST_CODIGO'))]
                       + [d_ord.get(c) for c in local.COLUNAS_ORDEM[4:7]])


def _monta_pro_st_id(pro_tab, pro_pad, pro_in):
    """PRO_ST_ID vazio montado com PRO_TAB/PAD/IN (apontamento.api_view.monta_produto, 3+3+7)."""
    from apontamento.api_view import monta_produto
    return monta_produto([pro_tab, pro_pad, pro_in])


def montar_plano(con, org_in_codigo, fil_in_codigo=None, ord_in_codigo=None, param=None):
    """Le no Oracle e monta exatamente o que a rotina antiga gravaria. So leitura."""
    from api import services as oracle
    plano = {'ordens': [], 'itens': {}, 'caracteristicas': {}, 'maquinas': [], 'operadores': [], 'erros': []}
    memo_conv, memo_atr, memo_ref, memo_car = {}, {}, {}, {}
    for pend in oracle.sync_ordens_pendentes(con, org_in_codigo, fil_in_codigo, ord_in_codigo, param):
        try:
            for d_ord in oracle.sync_dados_ordem(con, pend['org_in_codigo'], pend['ord_seq_in_codigo'],
                                                 pend['ord_in_codigo']):
                fil = d_ord['FIL_IN_CODIGO']
                demandas = _jsonavel(oracle.sync_demandas_ordem(
                    con, pend['org_in_codigo'], pend['ord_seq_in_codigo'], pend['ord_in_codigo']))
                itens = _jsonavel(oracle.sync_itens_ordem(con, fil, d_ord['ORD_IN_CODIGO']))
                ordem = {c: d_ord.get(c) for c in local.COLUNAS_ORDEM if c in d_ord}
                if not ordem.get('ORD_ST_ID'):  # chave da comparacao nunca nula
                    ordem['ORD_ST_ID'] = _monta_ord_st_id(d_ord)
                if not ordem.get('PRO_ST_ID'):
                    ordem['PRO_ST_ID'] = _monta_pro_st_id(d_ord.get('PRO_TAB_IN_CODIGO'),
                                                          d_ord.get('PRO_PAD_IN_CODIGO'), d_ord.get('PRO_IN_CODIGO'))
                # mvs_st_referencia dos itens da ordem no padrao novo (JSON padrao), como no NMV;
                # a lista da tela (prepara_apontamento) converte de volta para texto
                itens_ordem = [dict(i, mvs_st_referencia=local.referencia_json(i)) for i in itens]
                ordem.update({'TPO_ST_CODIGO': d_ord.get('TPO_ST_CODIGO_TIPO'), 'PRO_ST_ITENS': itens_ordem,
                              'PRO_ST_DEMANDAS': demandas,
                              'PRO_ST_INFOADIC': {'umidade': d_ord.get('ORD_RE_UMIDADE'),
                                                  'lote_ordem': d_ord.get('LOTE_ORDEM'),
                                                  'destino': d_ord.get('ORD_ST_DESTINO'),
                                                  'origem': d_ord.get('ORD_ST_ORIGEM')}})
                entrada = {'ord': d_ord['ORD_IN_CODIGO'], 'org': d_ord['ORG_IN_CODIGO'],
                           'seq': d_ord['ORD_SEQ_IN_CODIGO'], 'linha': ordem, 'itens': [], 'cars': [],
                           'erro': _invalido(ordem, OBRIGATORIOS_ORDEM, TAMANHOS_ORDEM)}
                for d in itens:
                    pro = d.get('pro_in_codigo')
                    rfc = d.get('rfc_in_codigo')
                    conv = _cache(memo_conv, (fil, pro), lambda: _jsonavel(oracle.sync_conversor(con, fil, pro)))
                    # Rotina antiga daqui: rfc_in_codigo != 0 busca atributos/referencias/caracteristicas;
                    # rfc 0 grava os marcadores [{"PRO_ST_ATRIBUTOS": null}] / [{"PRO_ST_REFERENCIA": null}].
                    if rfc != 0:
                        atr = _cache(memo_atr, (fil, pro), lambda: oracle.sync_atributos_item(con, fil, pro))
                        ref = _cache(memo_ref, (fil, pro), lambda: oracle.sync_referencias_item(con, fil, pro))
                        for car in _cache(memo_car, (fil, rfc), lambda: _jsonavel(
                                oracle.sync_caracteristicas_referencia(con, fil, rfc))):
                            linha_car = {c: car.get(c) for c in local.COLUNAS_CARACTERISTICA}
                            if linha_car['CAR_BO_OBRIGATORIO'] is None:
                                linha_car['CAR_BO_OBRIGATORIO'] = 'S'  # default do modelo (antiga)
                            if not _invalido(linha_car, OBRIGATORIOS_CAR, TAMANHOS_CAR):
                                plano['caracteristicas'].setdefault(linha_car['CAR_ST_ID'], linha_car)
                                entrada['cars'].append(linha_car['CAR_ST_ID'])
                    else:
                        atr, ref = [{'PRO_ST_ATRIBUTOS': None}], [{'PRO_ST_REFERENCIA': None}]
                    item = {'PRO_TAB_IN_CODIGO': d_ord.get('PRO_TAB_IN_CODIGO'),  # da ordem, como na antiga
                            'PRO_PAD_IN_CODIGO': d_ord.get('PRO_PAD_IN_CODIGO'),
                            'PRO_IN_CODIGO': pro, 'PRO_ST_DESCRICAO': d.get('pro_st_descricao'),
                            'UNI_ST_UNIDADE': d.get('uni_st_unidade'), 'RFC_IN_CODIGO': rfc,
                            'PRO_ST_ATRIBUTOS': atr, 'PRO_ST_REFERENCIA': ref,
                            'PRO_ST_MEDIDAS': [{'PRO_RE_COMPRIMENTO': d.get('pro_re_comprimento'),
                                                'PRO_RE_LARGURA': d.get('pro_re_largura'),
                                                'PRO_RE_ESPESSURA': d.get('pro_re_espessura')}],
                            'MVS_ST_REFERENCIA': local.referencia_json(d),
                            'PRO_ST_ID': d.get('pro_st_id'),
                            'PRO_ST_CONVERSOR': conv or [{'CONVERSORES': None}]}
                    if not item['PRO_ST_ID']:  # chave da comparacao nunca nula
                        item['PRO_ST_ID'] = _monta_pro_st_id(item['PRO_TAB_IN_CODIGO'], item['PRO_PAD_IN_CODIGO'], pro)
                    erro_item = _invalido(item, OBRIGATORIOS_ITEM, TAMANHOS_ITEM)
                    if erro_item:
                        plano['erros'].append(f"OP {entrada['ord']} item {pro}: {erro_item}")
                        continue
                    plano['itens'][item['PRO_ST_ID']] = item
                    entrada['itens'].append(item['PRO_ST_ID'])
                if entrada['erro']:
                    plano['erros'].append(f"OP {entrada['ord']}: {entrada['erro']}")
                plano['ordens'].append(entrada)
        except Exception as e:
            plano['erros'].append(f"OP {pend.get('ord_in_codigo')}: {e}")
    # Maquinas sempre lidas e comparadas (a rotina antiga so cadastrava a que faltava). Flags so
    # valem na inclusao.
    vistas = set()
    for m in oracle.sync_maquinas(con):
        chave = _chave_maquina(m)
        if m['CTR_ST_ID'] != '0' and chave not in vistas:
            vistas.add(chave)
            plano['maquinas'].append(dict(m, MAQ_CH_APONTAMENTO=1, MAQ_CH_DEMANDA=0))
    # Operadores da filial (cracha e nome nunca vazios; repetido sai)
    if fil_in_codigo is not None:
        try:
            vistos = set()
            for op in oracle.sync_operadores(con, fil_in_codigo):
                chave = _chave_operador(op)
                if op.get('OPD_ST_CRACHA') and op.get('OPD_ST_NOME') and chave not in vistos:
                    vistos.add(chave)
                    plano['operadores'].append(op)
        except Exception as e:
            plano['erros'].append(f'Operadores: {e}')
    return plano


def _chave_maquina(linha):
    return tuple(str(linha.get(c)) for c in local.CHAVE_MAQUINA)


def _chave_operador(linha):
    return (str(linha.get('OPD_ST_CRACHA')).strip(), int(linha.get('FIL_IN_CODIGO')))


def _igual(a, b):
    numeros = (int, float, Decimal)
    if isinstance(a, numeros) and isinstance(b, numeros) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(float(a) - float(b)) < 1e-9
    return a == b


def _diferencas(nova, atual, colunas, colunas_json):
    difs = []
    for c in colunas:
        valor = local.ler_json(atual.get(c)) if c in colunas_json else atual.get(c)
        if not _igual(nova.get(c), valor):
            difs.append(c)
    return difs


def _decidir(nova, atuais, colunas, colunas_json, pk):
    """O que fazer com UMA linha. atuais = linhas locais da mesma chave, na ordem da leitura: a 1a
    fica (comparada campo a campo), as demais sao duplicadas e saem."""
    if not atuais:
        return {'situacao': 'nova', 'campos': [], 'pk': None, 'extras': []}
    difs = _diferencas(nova, atuais[0], colunas, colunas_json)
    return {'situacao': 'diferente' if difs else 'igual', 'campos': difs, 'pk': atuais[0][pk],
            'extras': [a[pk] for a in atuais[1:]]}


def _agrupar(linhas, chave):
    grupos = {}
    for l in linhas:
        grupos.setdefault(chave(l), []).append(l)
    return grupos


def _chave_item(linha):
    """PRO_ST_ID da linha local; vazio (item antigo) = montado com PRO_TAB/PAD/IN (AJUSTE 2026-10-20)."""
    if (linha.get('PRO_ST_ID') or '').strip():
        return linha['PRO_ST_ID']
    return _monta_pro_st_id(linha.get('PRO_TAB_IN_CODIGO'), linha.get('PRO_PAD_IN_CODIGO'), linha.get('PRO_IN_CODIGO'))


def _decisoes_itens(plano, ids):
    pros = sorted({plano['itens'][i]['PRO_IN_CODIGO'] for i in ids})
    locais = _agrupar(local.itens_locais(ids, pros), _chave_item)
    return {i: locais.get(i, []) for i in ids}


def _ordem_local(o):
    """Linhas locais da OP do plano (ORD_ST_ID ou, sem ID, org + seq + ordem)."""
    return local.ordem_local(o['linha']['ORD_ST_ID'], o['org'], o['seq'], o['ord'])


def _decisoes_caracteristicas(plano, ids):
    locais = _agrupar(local.caracteristicas_locais(ids), lambda l: l['CAR_ST_ID'])
    return {c: _decidir(plano['caracteristicas'][c], locais.get(c, []), local.COLUNAS_CARACTERISTICA,
                        set(), local.PK_CARACTERISTICA) for c in ids}


def _decisoes_maquinas(plano):
    locais = _agrupar(local.maquinas_locais(), _chave_maquina)
    return [(m, _decidir(m, locais.get(_chave_maquina(m), []), local.COMPARA_MAQUINA, set(), local.PK_MAQUINA))
            for m in plano['maquinas']]


def _decisoes_operadores(plano):
    if not plano.get('operadores'):
        return []
    locais = _agrupar(local.operadores_locais(plano['operadores'][0]['FIL_IN_CODIGO']), _chave_operador)
    return [(op, _decidir(op, locais.get(_chave_operador(op), []), local.COMPARA_OPERADOR, set(),
                          local.PK_OPERADOR)) for op in plano['operadores']]


def gravar_operadores(plano):
    """INSERT do operador novo, UPDATE do nome diferente, duplicado sai (fica o de menor
    OPD_IN_CODIGO). Nunca apaga operador que nao veio do Mega. Devolve (gravados, erros)."""
    from django.db import connection, transaction
    try:
        with transaction.atomic(), connection.cursor() as cur:
            decisoes = _decisoes_operadores(plano)
            for op, d in decisoes:
                _aplicar(cur, 'Apt_Pro_CadOperador', local.COLUNAS_OPERADOR, set(), local.PK_OPERADOR, op, d)
        return sum(d['situacao'] != 'igual' or bool(d['extras']) for _op, d in decisoes), []
    except Exception as e:
        return 0, [f'Operadores: {e}']


def comparar(plano):
    """Compara o plano com o SQLite (JSON comparado pelo conteudo). So leitura. Conta tambem
    duplicadas e caracteristicas/maquinas/operadores diferentes."""
    ordens = []
    for o in plano['ordens']:
        d = _decidir(o['linha'], _ordem_local(o), local.COLUNAS_ORDEM, local.JSON_ORDEM, local.PK_ORDEM)
        ordens.append({'ord': o['ord'], 'situacao': d['situacao'], 'campos': d['campos'],
                       'itens': len(o['itens']), 'duplicadas': len(d['extras']), 'erro': o['erro']})
    itens = {'novos': 0, 'iguais': 0, 'diferentes': [], 'duplicados': 0}
    for pro_st_id, atuais in _decisoes_itens(plano, list(plano['itens'])).items():
        item = plano['itens'][pro_st_id]
        d = _decidir(item, atuais, local.COLUNAS_ITEM, local.JSON_ITEM, local.PK_ITEM)
        itens['duplicados'] += len(d['extras'])
        if d['situacao'] == 'nova':
            itens['novos'] += 1
        elif d['situacao'] == 'diferente':
            itens['diferentes'].append({'pro_st_id': pro_st_id, 'pro_in_codigo': item['PRO_IN_CODIGO'],
                                        'campos': d['campos']})
        else:
            itens['iguais'] += 1
    cars = list(_decisoes_caracteristicas(plano, list(plano['caracteristicas'])).values())
    maqs = [d for _m, d in _decisoes_maquinas(plano)]
    ops = [d for _o, d in _decisoes_operadores(plano)]
    return {'operadores_novos': sum(d['situacao'] == 'nova' for d in ops),
            'operadores_diferentes': sum(d['situacao'] == 'diferente' for d in ops), 'ordens': ordens, 'itens': itens,
            'caracteristicas_novas': sum(d['situacao'] == 'nova' for d in cars),
            'caracteristicas_diferentes': sum(d['situacao'] == 'diferente' for d in cars),
            'maquinas_novas': sum(d['situacao'] == 'nova' for d in maqs),
            'maquinas_diferentes': sum(d['situacao'] == 'diferente' for d in maqs),
            'maquinas_duplicadas': sum(len(d['extras']) for d in maqs)}


def _aplicar(cur, tabela, colunas_insert, colunas_json, pk, linha, d):
    """INSERT do novo, UPDATE so das colunas diferentes, DELETE das duplicadas."""
    if d['situacao'] == 'nova':
        local.inserir(cur, tabela, colunas_insert, colunas_json, linha)
    elif d['situacao'] == 'diferente':
        local.atualizar(cur, tabela, d['campos'], colunas_json, linha, pk, d['pk'])
    local.apagar(cur, tabela, pk, d['extras'])


def gravar(plano):
    """Grava no SQLite, uma transacao por OP, so o que estiver diferente -- ordem, itens e
    caracteristicas: INSERT do novo, UPDATE so das colunas diferentes, linhas duplicadas apagadas
    (OP/item: fica a mais nova). Maquinas: mesma regra, comparando so os campos do Mega.
    Devolve (ops gravadas, erros)."""
    from django.db import connection, transaction
    gravadas, erros = 0, []
    for o in plano['ordens']:
        if o['erro']:
            continue
        try:
            with transaction.atomic(), connection.cursor() as cur:
                d = _decidir(o['linha'], _ordem_local(o), local.COLUNAS_ORDEM, local.JSON_ORDEM, local.PK_ORDEM)
                _aplicar(cur, 'apt_pro_ordens', local.COLUNAS_ORDEM, local.JSON_ORDEM, local.PK_ORDEM,
                         o['linha'], d)
                for pro_st_id, atuais in _decisoes_itens(plano, list(dict.fromkeys(o['itens']))).items():
                    item = plano['itens'][pro_st_id]
                    _aplicar(cur, 'apt_itens_ordens', local.COLUNAS_ITEM, local.JSON_ITEM, local.PK_ITEM, item,
                             _decidir(item, atuais, local.COLUNAS_ITEM, local.JSON_ITEM, local.PK_ITEM))
                for car_st_id, d in _decisoes_caracteristicas(plano, list(dict.fromkeys(o['cars']))).items():
                    _aplicar(cur, 'Car_AtributosReferencia', local.COLUNAS_CARACTERISTICA, set(),
                             local.PK_CARACTERISTICA, plano['caracteristicas'][car_st_id], d)
            gravadas += 1
        except Exception as e:
            erros.append(f"OP {o['ord']}: {e}")
    if plano['maquinas']:
        try:
            with transaction.atomic(), connection.cursor() as cur:
                for m, d in _decisoes_maquinas(plano):
                    _aplicar(cur, 'Apt_Pro_CadMaquinas', local.COLUNAS_MAQUINA, set(), local.PK_MAQUINA, m, d)
        except Exception as e:
            erros.append(f'Máquinas: {e}')
    return gravadas, erros


def sincronizar_ordens(org_in_codigo, fil_in_codigo=None, ord_in_codigo=None, param='N', conexao=None):
    """Chamada pela view. Nunca levanta excecao. Devolve o resumo da rodada."""
    inicio = time.perf_counter()
    resumo = {'gravado': False, 'erros': [], 'ordens': [], 'itens': {}, 'caracteristicas_novas': 0,
              'maquinas_novas': 0, 'tempo_ms': 0, 'erro_conexao': None}
    fechar = conexao is None
    try:
        if fechar:
            from oracle_connection import getOracleConnection
            conexao = getOracleConnection()
            if not conexao:
                resumo['erro_conexao'] = 'Sem conexão com o Oracle (Mega). Nada foi lido.'
                return resumo
        try:
            plano = montar_plano(conexao, org_in_codigo, fil_in_codigo, ord_in_codigo, param)
        finally:
            if fechar:
                conexao.close()
        resumo.update(comparar(plano))
        resumo['erros'] = list(plano['erros'])
        if SYNC_ORDENS_GRAVA:
            gravadas, erros = gravar(plano)
            resumo.update({'gravado': True, 'ops_gravadas': gravadas})
            resumo['erros'] += erros
        if SYNC_OPERADORES_GRAVA:
            gravados, erros = gravar_operadores(plano)
            resumo['operadores_gravados'] = gravados
            resumo['erros'] += erros
    except Exception as e:
        import traceback
        print('ERRO SINCRONIZAR ORDENS:', traceback.format_exc())
        resumo['erro_conexao'] = str(e)
    finally:
        resumo['tempo_ms'] = int((time.perf_counter() - inicio) * 1000)
    return resumo
