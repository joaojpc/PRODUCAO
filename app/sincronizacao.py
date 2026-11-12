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
Diferencas do NMV: itens com chaves minusculas (apt_intprod2) e rfc_in_codigo = 0 nao busca
atributos/caracteristicas (a rotina antiga daqui le a chave certa).
AJUSTE 2026-11-11 (JPC): decisao do usuario -- do NMV/ZK: troca de PK (ordens = ORD_ST_ID, itens =
PRO_ST_ID; busca direto pela PK), tipo das caracteristicas vindo do Mega (RAT_CH_TIPOCONTEUDO, de todas as
caracteristicas do app), normalizacao dos itens com JSON no padrao antigo e atualizacao da caracteristica
que ja existe (atualizar_caracteristica_existente, usada pelo "Baixar Ordens").
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
                'RAT_CH_TIPO': 1, 'RAT_BO_GRUPO': 1, 'CAR_BO_OBRIGATORIO': 1, 'PAI_ST_DESCRICAO': 70,
                'RAT_CH_TIPOCONTEUDO': 1}
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


def montar_plano(con, org_in_codigo, fil_in_codigo=None, ord_in_codigo=None, param=None, tipos=True):
    """Le no Oracle e monta exatamente o que a rotina antiga gravaria. So leitura.
    tipos=False: nao le o tipo de todas as caracteristicas (o script de atualizacao em massa le uma vez so)."""
    from api import services as oracle
    plano = {'ordens': [], 'itens': {}, 'caracteristicas': {}, 'maquinas': [], 'operadores': [], 'erros': [],
             'tipos': {}}
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
                            linha_car = linha_caracteristica(car)  # AJUSTE 2026-11-11: mesma montagem
                            if linha_car is not None:
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
    # AJUSTE 2026-11-11 (JPC): do ZK -- tipo do conteudo (RAT_CH_TIPOCONTEUDO: 'N' numerico; 'S'/nulo texto) de
    # TODAS as caracteristicas do app, nao so as da OP -- lido no Mega por referencia (cache da rodada)
    if fil_in_codigo is not None and tipos:
        for rfc in local.referencias_locais():
            try:
                for car in _cache(memo_car, (fil_in_codigo, rfc), lambda: _jsonavel(
                        oracle.sync_caracteristicas_referencia(con, fil_in_codigo, rfc))):
                    plano['tipos'][car.get('CAR_ST_ID')] = car.get('RAT_CH_TIPOCONTEUDO')
            except Exception as e:
                plano['erros'].append(f'Tipo das características (referência {rfc}): {e}')
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
        # AJUSTE 2026-11-11 (JPC): do ZK -- JSON gravado no padrao antigo (texto dentro de texto) tambem conta
        # como diferente: a 1a rodada regrava normalizado; depois so o que mudar de conteudo
        if not _igual(nova.get(c), valor) or (c in colunas_json and local.json_aninhado(atual.get(c), nova.get(c))):
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


def _decisoes_itens(plano, ids):
    """AJUSTE 2026-11-11 (JPC): PK = PRO_ST_ID (antes tambem agrupava item antigo sem ID)."""
    locais = _agrupar(local.itens_locais(ids), lambda l: l['PRO_ST_ID'])
    return {i: locais.get(i, []) for i in ids}


def _ordem_local(o):
    """AJUSTE 2026-11-11 (JPC): pela PK ORD_ST_ID (antes tambem org + seq + ordem para linha sem ID)."""
    return local.ordem_local(o['linha']['ORD_ST_ID'])


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


def _tipos_diferentes(plano):
    """AJUSTE 2026-11-11 (JPC): do ZK -- {CAR_ST_ID: tipo do Mega} das caracteristicas ja gravadas no app cujo
    tipo esta diferente (texto maior que a coluna fica de fora, como o serializer da rotina antiga)."""
    atuais = local.tipos_locais()
    return {c: t for c, t in plano.get('tipos', {}).items()
            if c in atuais and atuais[c] != t and (t is None or len(str(t)) <= TAMANHOS_CAR['RAT_CH_TIPOCONTEUDO'])}


def linha_caracteristica(car):
    """Linha da caracteristica como o montar_plano monta (default de CAR_BO_OBRIGATORIO); None se invalida."""
    linha = {c: car.get(c) for c in local.COLUNAS_CARACTERISTICA}
    if linha['CAR_BO_OBRIGATORIO'] is None:
        linha['CAR_BO_OBRIGATORIO'] = 'S'  # default do modelo (antiga)
    return None if _invalido(linha, OBRIGATORIOS_CAR, TAMANHOS_CAR) else linha


def atualizar_caracteristica_existente(car):
    """AJUSTE 2026-11-11 (JPC): do ZK (cb27d34) -- o "Baixar Ordens" aplica a regra da sincronizacao nova na
    caracteristica que ja existe no app (antes era ignorada): UPDATE so das colunas diferentes do Mega (car =
    linha do get_referencia), com a mesma comparacao do _decidir. Linha invalida fica como esta.
    Devolve as colunas atualizadas."""
    from django.db import connection, transaction
    linha = linha_caracteristica(car)
    if linha is None:
        return []
    # PRODUCAO: a API get_referencia daqui nao devolve RAT_CH_TIPOCONTEUDO -- sem ele na linha, o tipo fica fora
    # da comparacao (senao apagaria o tipo gravado pela sincronizacao nova)
    colunas = [c for c in local.COLUNAS_CARACTERISTICA
               if c != 'RAT_CH_TIPOCONTEUDO' or 'RAT_CH_TIPOCONTEUDO' in car]
    d = _decidir(linha, local.caracteristicas_locais([linha['CAR_ST_ID']]), colunas, set(), local.PK_CARACTERISTICA)
    if d['situacao'] != 'diferente':
        return []
    with transaction.atomic(), connection.cursor() as cur:
        local.atualizar(cur, 'Car_AtributosReferencia', d['campos'], set(), linha, local.PK_CARACTERISTICA, d['pk'])
    return d['campos']


def gravar_tipos_caracteristicas(plano):
    """AJUSTE 2026-11-11 (JPC): do ZK -- UPDATE so do RAT_CH_TIPOCONTEUDO das caracteristicas existentes com
    tipo diferente do Mega (na pratica 1 vez). Uma transacao: erro = nada gravado. Devolve (atualizadas, erros)."""
    from django.db import connection, transaction
    try:
        difs = _tipos_diferentes(plano)
        with transaction.atomic(), connection.cursor() as cur:
            for car_st_id, tipo in difs.items():
                local.atualizar(cur, 'Car_AtributosReferencia', ['RAT_CH_TIPOCONTEUDO'], set(),
                                {'RAT_CH_TIPOCONTEUDO': tipo}, local.PK_CARACTERISTICA, car_st_id)
        return len(difs), []
    except Exception as e:
        return 0, [f'Tipo das características: {e}']


def atualizar_tipos_caracteristicas(con, fil_in_codigo, gravar=True):
    """AJUSTE 2026-11-11 (JPC): tipo (RAT_CH_TIPOCONTEUDO) de TODAS as caracteristicas do app igual ao do Mega, numa
    leitura so (usado pelo script atualizar_ordens_mega). Erro de uma referencia nao derruba as outras.
    Devolve (atualizadas ou diferentes, erros)."""
    from api import services as oracle
    plano, erros = {'tipos': {}}, []
    for rfc in local.referencias_locais():
        try:
            for car in _jsonavel(oracle.sync_caracteristicas_referencia(con, fil_in_codigo, rfc)):
                plano['tipos'][car.get('CAR_ST_ID')] = car.get('RAT_CH_TIPOCONTEUDO')
        except Exception as e:
            erros.append(f'Tipo das características (referência {rfc}): {e}')
    if not gravar:
        return len(_tipos_diferentes(plano)), erros
    atualizadas, erros_grav = gravar_tipos_caracteristicas(plano)
    return atualizadas, erros + erros_grav


def normalizar_itens_existentes():
    """AJUSTE 2026-11-11 (JPC): do ZK -- regrava no padrao novo (JSON normalizado) os campos dos itens que ainda
    estao no formato antigo -- so o formato muda. Uma transacao: erro = nada gravado.
    Devolve (itens normalizados, erros)."""
    from django.db import connection, transaction
    try:
        pendentes = local.itens_json_antigo()
        with transaction.atomic(), connection.cursor() as cur:
            for pro_st_id, novos in pendentes:
                local.atualizar(cur, 'apt_itens_ordens', list(novos), local.JSON_ITEM, novos, local.PK_ITEM,
                                pro_st_id)
        return len(pendentes), []
    except Exception as e:
        return 0, [f'Normalização dos itens: {e}']


gravar_plano = gravar  # AJUSTE 2026-11-11: usado dentro de sincronizar_ordens


def sincronizar_ordens(org_in_codigo, fil_in_codigo=None, ord_in_codigo=None, param='N', conexao=None,
                       gravar=None, normalizar=True, tipos=True):
    """Chamada pela view. Nunca levanta excecao. Devolve o resumo da rodada.
    AJUSTE 2026-11-11 (JPC): conexao propria com with (decisao do usuario: toda conexao com with).
    gravar=None segue SYNC_ORDENS_GRAVA (False = so compara); normalizar/tipos=False pulam os passos que valem
    para o app inteiro (o script atualizar_ordens_mega faz cada um uma vez so)."""
    gravar = SYNC_ORDENS_GRAVA if gravar is None else gravar
    from contextlib import nullcontext
    inicio = time.perf_counter()
    resumo = {'gravado': False, 'erros': [], 'ordens': [], 'itens': {}, 'caracteristicas_novas': 0,
              'maquinas_novas': 0, 'tempo_ms': 0, 'erro_conexao': None}
    try:
        if conexao is None:
            from oracle_connection import getOracleConnection
            conexao = getOracleConnection()
            if not conexao:
                resumo['erro_conexao'] = 'Sem conexão com o Oracle (Mega). Nada foi lido.'
                return resumo
            contexto = conexao
        else:
            contexto = nullcontext(conexao)
        with contexto as con:
            plano = montar_plano(con, org_in_codigo, fil_in_codigo, ord_in_codigo, param, tipos=tipos)
        # AJUSTE 2026-11-11 (JPC): do ZK -- antes de comparar, itens ainda no padrao antigo de JSON sao regravados
        # normalizados (na pratica 1 vez; depois so se o "Baixar Ordens" antigo gravar no formato velho)
        erros_norm = []
        if gravar and normalizar:
            resumo['itens_normalizados'], erros_norm = normalizar_itens_existentes()
        resumo.update(comparar(plano))
        resumo['erros'] = list(plano['erros']) + erros_norm
        if gravar:
            gravadas, erros = gravar_plano(plano)
            resumo.update({'gravado': True, 'ops_gravadas': gravadas})
            resumo['erros'] += erros
            # AJUSTE 2026-11-11 (JPC): do ZK -- tipo de todas as caracteristicas existentes igual ao do Mega
            resumo['caracteristicas_tipo'], erros = gravar_tipos_caracteristicas(plano)
            resumo['erros'] += erros
        else:
            resumo['caracteristicas_tipo'] = len(_tipos_diferentes(plano))  # so compara
        if SYNC_OPERADORES_GRAVA and gravar:
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


# AJUSTE 2026-10-20 (copiado do NMV, validado la): login/Reglote testam o Oracle antes de baixar a OP
ORACLE_TIMEOUT_LOGIN = 3  # segundos para desistir da conexao (sem isso: ~21 s com o Oracle fora)


def conexao_oracle_testada(timeout=ORACLE_TIMEOUT_LOGIN):
    """Abre a conexao com timeout curto e TESTA (select 1 from dual) antes de baixar qualquer coisa.
    Devolve a conexao aberta ou None. Nunca levanta excecao."""
    con = None
    try:
        from oracle_connection import getOracleConnection
        con = getOracleConnection(timeout=timeout)
        if con:
            with con.cursor() as cur:
                cur.execute('select 1 from dual')
                cur.fetchone()
            return con
    except Exception as e:
        print('ORACLE SEM RESPOSTA:', e)
    if con:
        try:
            con.close()
        except Exception:
            pass
    return None


def sincronizar_ordem_login(fil_in_codigo, ord_in_codigo):
    """Login na ordem / Reglote com a OP fora do app: testa a conexao (3 s) e baixa a OP pela rotina
    nova, gravando so o que mudou. Sem Oracle: nada e baixado e o login segue. (No NMV ha uma 2a
    tentativa com 'S'; aqui o get_integracao por filial nao filtra status -- seria a mesma busca.)
    Nunca levanta excecao; erro_conexao preenchido = nada foi baixado."""
    con = conexao_oracle_testada()
    if not con:
        return {'gravado': False, 'erros': [], 'ordens': [], 'itens': {}, 'caracteristicas_novas': 0,
                'maquinas_novas': 0, 'tempo_ms': 0,
                'erro_conexao': 'Sem conexão com o Oracle (Mega). Não foi possível baixar a OP.'}
    with con:  # AJUSTE 2026-11-11 (JPC): toda conexao com with (decisao do usuario)
        # AJUSTE 2026-11-11 (JPC): login leve -- so a OP do operador; o tipo de todas as caracteristicas e a
        # normalizacao do app inteiro ficam com o botao "Baixar Ordens" e o script atualizar_ordens_mega
        resumo = sincronizar_ordens(org_da_filial(fil_in_codigo), fil_in_codigo, ord_in_codigo, 'N', conexao=con,
                                    normalizar=False, tipos=False)
    print('SINCRONIZAR OP LOGIN', fil_in_codigo, ord_in_codigo, '->', resumo.get('ordens'),
          resumo.get('erros'), resumo.get('erro_conexao'), f"{resumo.get('tempo_ms')} ms")
    return resumo
