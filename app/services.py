# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-20 (JPC): sincronizacao de ordens Oracle -> SQLite (rotina NOVA, isolada), copiada
do NMV. Lado SQLite: leitura e gravacao por SQL nativo (django.db.connection, parametros %s), sem
ORM. Campos JSON gravados NORMALIZADOS: json.dumps uma vez, ensure_ascii=False (sem '\\' de escape
nem texto JSON dentro de texto). Grava so o que mudou (INSERT do novo, UPDATE das colunas
diferentes, DELETE das linhas duplicadas). Quem chama: app/sincronizacao.py; ler_json e
referencia_padrao tambem sao usados pelos leitores (antigo e novo formato).
Diferenca do NMV: aqui nao houve troca de PK (decisao do usuario) -- apt_pro_ordens e
apt_itens_ordens seguem com PK TAB_IN_SEQUENCIA; a chave natural da comparacao e ORD_ST_ID /
PRO_ST_ID e, havendo duplicadas, fica a MAIS NOVA (maior TAB_IN_SEQUENCIA, como a migracao 0044).
AJUSTE 2026-10-20: linha antiga gravada SEM o ID entra pela chave da rotina antiga (OP: org + seq
+ ordem; item: produto) e e atualizada (recebe o ID) -- antes virava uma linha nova duplicada.
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
# MVS_ST_REFERENCIA: decisao do usuario -- JSON padrao igual ao NMV; aqui a coluna segue CharField
# (sem migracao), guardando o JSON como texto.
JSON_ITEM = {'PRO_ST_ATRIBUTOS', 'PRO_ST_REFERENCIA', 'PRO_ST_MEDIDAS', 'MVS_ST_REFERENCIA', 'PRO_ST_CONVERSOR'}

# Sem RAT_CH_TIPOCONTEUDO (nao existe no PRODUCAO)
COLUNAS_CARACTERISTICA = ['CAR_ST_ID', 'RAT_ST_ID', 'RFC_ST_ID', 'PAI_RAT_IN_CODIGO', 'RAT_IN_CODIGO',
                          'RAT_ST_DESCRICAO', 'RAT_VALUE', 'RAT_CH_TIPO', 'CAR_IN_PRIORIDADE', 'RFC_IN_CODIGO',
                          'RAT_BO_GRUPO', 'CAR_BO_OBRIGATORIO', 'PAI_ST_DESCRICAO']

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
# mesma chave, fica a 1a que a leitura devolve e as extras saem (OP/item: a mais nova; maquina e
# operador: a de menor PK, como no NMV). PK local de cada tabela:
PK_ORDEM, PK_ITEM, PK_CARACTERISTICA, PK_MAQUINA = ('TAB_IN_SEQUENCIA', 'TAB_IN_SEQUENCIA', 'CAR_ST_ID',
                                                    'MAQ_IN_SEQUENCIA')
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
def ordem_local(ord_st_id, org_in_codigo=None, ord_seq_in_codigo=None, ord_in_codigo=None):
    """Linhas da ordem pela chave ORD_ST_ID, a mais nova primeiro (a 1a fica; as demais sao
    duplicadas). AJUSTE 2026-10-20: linha antiga com ORD_ST_ID vazio entra pela chave da rotina
    antiga (org + seq + ordem)."""
    return _consultar("SELECT * FROM apt_pro_ordens WHERE ORD_ST_ID = %s "
                      "OR ((ORD_ST_ID IS NULL OR TRIM(ORD_ST_ID) = '') AND ORG_IN_CODIGO = %s "
                      "AND ORD_SEQ_IN_CODIGO = %s AND ORD_IN_CODIGO = %s) ORDER BY TAB_IN_SEQUENCIA DESC",
                      [ord_st_id, org_in_codigo, ord_seq_in_codigo, ord_in_codigo])


def itens_locais(pro_st_ids, pro_in_codigos=()):
    """Itens pelo PRO_ST_ID, os mais novos primeiro. AJUSTE 2026-10-20: com pro_in_codigos, entram
    tambem os itens antigos com PRO_ST_ID vazio desses produtos (quem chama agrupa pelo ID montado)."""
    pro_st_ids, pro_in_codigos = list(pro_st_ids), list(pro_in_codigos)
    if not pro_st_ids:
        return []
    sql = f'SELECT * FROM apt_itens_ordens WHERE PRO_ST_ID IN ({_marcas(len(pro_st_ids))})'
    if pro_in_codigos:
        sql += (f" OR ((PRO_ST_ID IS NULL OR TRIM(PRO_ST_ID) = '') "
                f"AND PRO_IN_CODIGO IN ({_marcas(len(pro_in_codigos))}))")
    return _consultar(sql + ' ORDER BY TAB_IN_SEQUENCIA DESC', pro_st_ids + pro_in_codigos)


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
