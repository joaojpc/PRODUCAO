# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-20 (JPC): sincronizacao de ordens Oracle -> SQLite (rotina NOVA, isolada), copiada
do NMV. Lado SQLite: leitura e gravacao por SQL nativo (django.db.connection, parametros %s), sem
ORM. Campos JSON gravados NORMALIZADOS: json.dumps uma vez, ensure_ascii=False (sem '\\' de escape
nem texto JSON dentro de texto). Grava so o que mudou (INSERT do novo, UPDATE das colunas
diferentes, DELETE das linhas duplicadas). Quem chama: app/sincronizacao.py; ler_json e
referencia_padrao tambem sao usados pelos leitores (antigo e novo formato).
AJUSTE 2026-11-11 (JPC): decisao do usuario -- troca de PK igual ao NMV/ZK: apt_pro_ordens com PK
ORD_ST_ID e apt_itens_ordens com PK PRO_ST_ID (migracoes 0047/0048, depois da 0044 que preenche os IDs
vazios e deixa a linha mais nova). Sem TAB_IN_SEQUENCIA, a busca e direto pela PK (nao ha mais linha sem
ID nem duplicada). Do ZK tambem: RAT_CH_TIPOCONTEUDO das caracteristicas, MVS_ST_REFERENCIA em JSON e
normalizacao dos itens gravados no padrao antigo (itens_json_antigo).
"""
import json

from django.db import connection

COLUNAS_ORDEM = ['ORG_TAB_IN_CODIGO', 'ORG_PAD_IN_CODIGO', 'ORG_IN_CODIGO', 'ORG_TAU_ST_CODIGO',
                 'ORD_TAB_IN_CODIGO', 'ORD_SEQ_IN_CODIGO', 'ORD_IN_CODIGO', 'PRO_TAB_IN_CODIGO',
                 'PRO_PAD_IN_CODIGO', 'PRO_IN_CODIGO', 'ORD_RE_QTDE_ORDEM', 'FIL_IN_CODIGO', 'TPO_ST_CODIGO',
                 'PRO_ST_ITENS', 'PRO_ST_DEMANDAS', 'PRO_ST_INFOADIC', 'PRO_ST_ID', 'ORD_ST_ID', 'TPO_ST_ID']
JSON_ORDEM = {'PRO_ST_ITENS', 'PRO_ST_DEMANDAS', 'PRO_ST_INFOADIC'}

COLUNAS_ITEM = ['PRO_TAB_IN_CODIGO', 'PRO_PAD_IN_CODIGO', 'PRO_IN_CODIGO', 'PRO_ST_DESCRICAO', 'UNI_ST_UNIDADE',
                'RFC_IN_CODIGO', 'PRO_ST_ATRIBUTOS', 'PRO_ST_REFERENCIA', 'PRO_ST_MEDIDAS', 'MVS_ST_REFERENCIA',
                'PRO_ST_ID', 'PRO_ST_CONVERSOR']
# MVS_ST_REFERENCIA: JSON padrao igual ao NMV/ZK (AJUSTE 2026-11-11: coluna JSONField, migracao 0046).
JSON_ITEM = {'PRO_ST_ATRIBUTOS', 'PRO_ST_REFERENCIA', 'PRO_ST_MEDIDAS', 'MVS_ST_REFERENCIA', 'PRO_ST_CONVERSOR'}

# AJUSTE 2026-11-11 (JPC): RAT_CH_TIPOCONTEUDO do Mega ('N' = numerico), como no ZK (migracao 0045)
COLUNAS_CARACTERISTICA = ['CAR_ST_ID', 'RAT_ST_ID', 'RFC_ST_ID', 'PAI_RAT_IN_CODIGO', 'RAT_IN_CODIGO',
                          'RAT_ST_DESCRICAO', 'RAT_VALUE', 'RAT_CH_TIPO', 'CAR_IN_PRIORIDADE', 'RFC_IN_CODIGO',
                          'RAT_BO_GRUPO', 'CAR_BO_OBRIGATORIO', 'PAI_ST_DESCRICAO', 'RAT_CH_TIPOCONTEUDO']

COLUNAS_MAQUINA = ['CTR_ST_ID', 'CMAQ_ST_ID', 'CTR_ST_NOME', 'CMAQ_ST_NOME', 'CMAQ_ST_CODIGO',
                   'MAQ_CH_APONTAMENTO', 'MAQ_CH_DEMANDA']


def json_texto(valor):
    """JSON normalizado para gravar: uma camada so, sem escape de acento."""
    return json.dumps(valor, ensure_ascii=False)


def ler_json(valor):
    """Decodifica JSON gravado em qualquer formato (normalizado ou texto JSON dentro de texto,
    como a rotina antiga grava em apt_itens_ordens). Texto que nao e JSON volta como esta."""
    while isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except ValueError:
            return valor
    return valor


def json_aninhado(texto, novo):
    """AJUSTE 2026-11-11 (JPC): copiado do ZK -- True quando o gravado e texto JSON dentro de texto (padrao
    antigo, ex.: '"[{...}]"') e o valor novo e lista/objeto: a sincronizacao regrava a coluna normalizada
    mesmo com o conteudo igual."""
    if not isinstance(texto, str) or not isinstance(novo, (list, dict)):
        return False
    try:
        return isinstance(json.loads(texto), str)
    except ValueError:
        return False


def referencia_padrao(valor):
    """Caracteristica padrao do item (MVS_ST_REFERENCIA) em texto, entendendo o padrao antigo
    (texto cru: 'Indefinido' ou '0000730=732;...') e o novo (JSON padrao {"MVS_ST_REFERENCIA": ...,
    "PRO_RE_CE": ..., "PRO_RE_APROV": ...}, inclusive texto JSON dentro de texto).
    Vazio/nulo = 'Indefinido'."""
    valor = ler_json(valor)
    if isinstance(valor, dict):
        valor = ler_json(valor.get('MVS_ST_REFERENCIA'))
    return valor if isinstance(valor, str) and valor.strip() else 'Indefinido'


def referencia_json(item):
    """MVS_ST_REFERENCIA no padrao novo (JSON padrao) a partir de um item. Aceita as chaves
    maiusculas (apt_itens_ordens) e as minusculas (itens da ordem, apt_intprod2 do PRODUCAO)."""
    atual = ler_json(item.get('MVS_ST_REFERENCIA', item.get('mvs_st_referencia')))
    base = atual if isinstance(atual, dict) else {}
    return {'MVS_ST_REFERENCIA': referencia_padrao(atual),
            'PRO_RE_CE': base.get('PRO_RE_CE', item.get('PRO_RE_CE', item.get('pro_re_ce'))),
            'PRO_RE_APROV': base.get('PRO_RE_APROV', item.get('PRO_RE_APROV', item.get('pro_re_aprov')))}


def _consultar(sql, params=()):
    with connection.cursor() as cur:
        cur.execute(sql, list(params))
        colunas = [c[0].upper() for c in cur.description]
        return [dict(zip(colunas, linha)) for linha in cur.fetchall()]


def _marcas(qtd):
    return ', '.join(['%s'] * qtd)


def _valores(linha, colunas, colunas_json):
    return [json_texto(linha.get(c)) if c in colunas_json else linha.get(c) for c in colunas]


# Gravar so o que estiver diferente (le, compara campo a campo e faz UPDATE so das colunas
# diferentes), em vez de apagar e inserir. Nao pode haver linha duplicada: com mais de uma linha na
# mesma chave, fica a 1a que a leitura devolve e as extras saem (maquina e operador: a de menor PK,
# como no NMV). AJUSTE 2026-11-11 (JPC): PK de ordens/itens = ORD_ST_ID/PRO_ST_ID (migracoes 0047/0048).
PK_ORDEM, PK_ITEM, PK_CARACTERISTICA, PK_MAQUINA = 'ORD_ST_ID', 'PRO_ST_ID', 'CAR_ST_ID', 'MAQ_IN_SEQUENCIA'
CHAVE_MAQUINA = ('CMAQ_ST_ID', 'CTR_ST_ID')
# Maquina: so os campos que vem do Mega sao comparados; MAQ_CH_APONTAMENTO/MAQ_CH_DEMANDA sao
# configuracao local (so preenchidos na inclusao).
COMPARA_MAQUINA = ['CTR_ST_NOME', 'CMAQ_ST_NOME', 'CMAQ_ST_CODIGO']
# Operadores -- chave cracha + filial; so o nome e comparado/atualizado
COLUNAS_OPERADOR = ['OPD_ST_CRACHA', 'OPD_ST_NOME', 'FIL_IN_CODIGO']
CHAVE_OPERADOR = ('OPD_ST_CRACHA', 'FIL_IN_CODIGO')
COMPARA_OPERADOR = ['OPD_ST_NOME']
PK_OPERADOR = 'OPD_IN_CODIGO'


# --------------------------------------------------------------------- leitura (comparar)
def ordem_local(ord_st_id):
    """AJUSTE 2026-11-11 (JPC): pela PK ORD_ST_ID (antes tambem procurava linha antiga sem ID)."""
    return _consultar('SELECT * FROM apt_pro_ordens WHERE ORD_ST_ID = %s', [ord_st_id])


def itens_locais(pro_st_ids):
    """AJUSTE 2026-11-11 (JPC): pela PK PRO_ST_ID (antes tambem procurava item antigo sem ID)."""
    pro_st_ids = list(pro_st_ids)
    if not pro_st_ids:
        return []
    return _consultar(f'SELECT * FROM apt_itens_ordens WHERE PRO_ST_ID IN ({_marcas(len(pro_st_ids))})',
                      pro_st_ids)


def caracteristicas_locais(car_st_ids):
    """Linhas completas (para comparar campo a campo)."""
    car_st_ids = list(car_st_ids)
    if not car_st_ids:
        return []
    return _consultar(f'SELECT * FROM Car_AtributosReferencia WHERE CAR_ST_ID IN ({_marcas(len(car_st_ids))})',
                      car_st_ids)


def maquinas_locais():
    return _consultar('SELECT * FROM Apt_Pro_CadMaquinas ORDER BY MAQ_IN_SEQUENCIA')


def operadores_locais(fil_in_codigo):
    """ORDER BY -- o 1o fica quando ha duplicidade."""
    return _consultar('SELECT * FROM Apt_Pro_CadOperador WHERE FIL_IN_CODIGO = %s ORDER BY OPD_IN_CODIGO',
                      [fil_in_codigo])


# --------------------------------------------------------------------- gravacao
# Quem chama abre a transacao (uma por OP): insere o novo, atualiza so as colunas diferentes (pela
# PK da linha que fica) e apaga duplicadas -- nada de apagar e inserir.
def inserir(cur, tabela, colunas, colunas_json, linha):
    cur.execute(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({_marcas(len(colunas))})",
                _valores(linha, colunas, colunas_json))


def atualizar(cur, tabela, colunas, colunas_json, linha, pk_coluna, pk_valor):
    if colunas:
        cur.execute(f"UPDATE {tabela} SET {', '.join(f'{c} = %s' for c in colunas)} WHERE {pk_coluna} = %s",
                    _valores(linha, colunas, colunas_json) + [pk_valor])


def apagar(cur, tabela, pk_coluna, pk_valores):
    pk_valores = list(pk_valores)
    if pk_valores:
        cur.execute(f'DELETE FROM {tabela} WHERE {pk_coluna} IN ({_marcas(len(pk_valores))})', pk_valores)


def inserir_maquinas(cur, linhas):
    if linhas:
        cur.executemany(f"INSERT INTO Apt_Pro_CadMaquinas ({', '.join(COLUNAS_MAQUINA)}) "
                        f"VALUES ({_marcas(len(COLUNAS_MAQUINA))})",
                        [_valores(l, COLUNAS_MAQUINA, set()) for l in linhas])


# --------------------------------------------------------------------- AJUSTE 2026-11-11 (JPC): do ZK
def itens_json_antigo():
    """Itens com campo JSON fora do padrao novo (texto JSON dentro de texto, ou MVS_ST_REFERENCIA em texto cru).
    Devolve [(PRO_ST_ID, {coluna: valor normalizado})] -- so o formato muda, o conteudo e o mesmo. Usado pela
    sincronizacao nova para normalizar os itens existentes."""
    saida = []
    for linha in _consultar(f"SELECT PRO_ST_ID, {', '.join(sorted(JSON_ITEM))} FROM apt_itens_ordens"):
        novos = {}
        for c in JSON_ITEM:
            bruto = linha.get(c)
            if bruto is None:
                continue
            valor = ler_json(bruto)
            if c == 'MVS_ST_REFERENCIA':
                if not isinstance(valor, dict):
                    novos[c] = referencia_json({'MVS_ST_REFERENCIA': valor})
            elif json_aninhado(bruto, valor):
                novos[c] = valor
        if novos:
            saida.append((linha['PRO_ST_ID'], novos))
    return saida


def referencias_locais():
    """Referencias com caracteristica cadastrada no app (para ler o tipo no Mega)."""
    return [r['RFC_IN_CODIGO'] for r in
            _consultar('SELECT DISTINCT RFC_IN_CODIGO FROM Car_AtributosReferencia ORDER BY RFC_IN_CODIGO')]


def tipos_locais():
    """{CAR_ST_ID: RAT_CH_TIPOCONTEUDO} de todas as caracteristicas do app."""
    return {r['CAR_ST_ID']: r['RAT_CH_TIPOCONTEUDO'] for r in
            _consultar('SELECT CAR_ST_ID, RAT_CH_TIPOCONTEUDO FROM Car_AtributosReferencia')}
