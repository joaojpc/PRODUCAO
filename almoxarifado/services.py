# services.py
# AJUSTE 2026-10-06: acesso direto (SQL puro) às tabelas locais, no lugar das APIs /est/.
# Função burra: só select/insert/update. Regra de negócio fica na api_view.
from django.db import connection, transaction

def _select(tabela, campos, lista_chaves):
    # campos[0] é a chave; devolve {chave: dict} dos registros locais
    locais = {}
    with connection.cursor() as cursor:
        for i in range(0, len(lista_chaves), 500):
            bloco = lista_chaves[i:i + 500]
            cursor.execute(f"SELECT {', '.join(campos)} FROM {tabela} WHERE {campos[0]} IN ({', '.join(['%s'] * len(bloco))})", bloco)
            for r in cursor.fetchall():
                locais[r[0]] = dict(zip(campos, r))
    return locais

def _inserir(tabela, campos, lista_dicts):
    if not lista_dicts:
        return 0
    sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({', '.join(['%s'] * len(campos))})"
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.executemany(sql, [[d.get(c) for c in campos] for d in lista_dicts])
    return len(lista_dicts)

def _atualizar(tabela, campos, lista_dicts):
    # campos[0] é a chave do WHERE
    if not lista_dicts:
        return 0
    sql = f"UPDATE {tabela} SET {', '.join(c + ' = %s' for c in campos[1:])} WHERE {campos[0]} = %s"
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.executemany(sql, [[d.get(c) for c in campos[1:]] + [d[campos[0]]] for d in lista_dicts])
    return len(lista_dicts)

CAMPOS_CADITENS = ['BXI_ID_PRODUTO','PRO_TAB_IN_CODIGO','PRO_PAD_IN_CODIGO','PRO_IN_CODIGO',
                   'PRO_ST_DESCRICAO','UNI_ST_UNIDADE']
CAMPOS_ITEMALMOXA = ['LOC_ID_PROALMFIL','LOC_ID_ALMOXA','LOC_ID_ORG','LOC_ID_PRODUTO','LOC_IN_FILIAL',
                     'ALM_IN_CODIGO','LOC_IN_CODIGO','ALM_ST_DESCRICAO','LOC_ST_DESCRICAO']
CAMPOS_CENTROCUSTOS = ['CUS_ID_CCUSTO','CUS_TAB_IN_CODIGO','CUS_PAD_IN_CODIGO','CUS_IDE_ST_CODIGO',
                       'CUS_IN_REDUZIDO','CUS_ST_EXTENSO','CUS_ST_DESCRICAO']

def select_caditens(ids):
    return _select('est_CadItens', CAMPOS_CADITENS, ids)
def inserir_caditens(lista_dicts):
    return _inserir('est_CadItens', CAMPOS_CADITENS, lista_dicts)
def atualizar_caditens(lista_dicts):
    return _atualizar('est_CadItens', CAMPOS_CADITENS, lista_dicts)

def select_itemalmoxa(ids):
    return _select('est_CadItemAlmoxa', CAMPOS_ITEMALMOXA, ids)
def inserir_itemalmoxa(lista_dicts):
    return _inserir('est_CadItemAlmoxa', CAMPOS_ITEMALMOXA, lista_dicts)
def atualizar_itemalmoxa(lista_dicts):
    return _atualizar('est_CadItemAlmoxa', CAMPOS_ITEMALMOXA, lista_dicts)

def select_centrocustos():
    # devolve a tabela local inteira como lista de dicts (mesmo formato do JSON da API)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(CAMPOS_CENTROCUSTOS)} FROM bxa_CentroCustos")
        return [dict(zip(CAMPOS_CENTROCUSTOS, r)) for r in cursor.fetchall()]
def inserir_centrocustos(lista_dicts):
    return _inserir('bxa_CentroCustos', CAMPOS_CENTROCUSTOS, lista_dicts)
def atualizar_centrocustos(lista_dicts):
    return _atualizar('bxa_CentroCustos', CAMPOS_CENTROCUSTOS, lista_dicts)
