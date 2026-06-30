# services.py
"""CRUD Puro. DB=producao.db. oracledb Thin. 3 Django -> 4 Oracle. Atômico."""
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Tuple
import oracledb
from collections import defaultdict

from oracle_connection import getOracleConnection # tem que usar oracledb.connect()
SQLITE_DB = "producao.db"

@contextmanager
def sqlite_con():
    con = sqlite3.connect(SQLITE_DB, timeout=30.0)
    con.execute("PRAGMA foreign_keys=ON"); con.execute("PRAGMA journal_mode=WAL")
    try: yield con
    except: con.rollback(); raise
    else: con.commit()
    finally: con.close()

@contextmanager
def oracle_tx():
    con = getOracleConnection() # oracledb.connect(user=..., password=..., dsn=..., thin=True)
    if con is None: raise ConnectionError("Oracle Down")
    con.autocommit = False
    try: yield con
    except: con.rollback(); print("ORACLE ROLLBACK TOTAL"); raise
    else: con.commit(); print("ORACLE COMMIT TOTAL")
    finally: con.close()

def select_controles_pendentes() -> List:
    sql = "SELECT * FROM Apt_Controle WHERE CTL_ST_STATUS = 'A'"
    with sqlite_con() as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute(sql).fetchall()]

def select_filhos_por_ctl(ctl_ids: List[int]) -> Tuple[List, List]:
    if not ctl_ids: return [], []
    placeholders = ','.join('?' * len(ctl_ids))
    sql_ordem = f"SELECT * FROM Apt_ApontaOrdem WHERE CTL_IN_CODIGO IN ({placeholders}) AND APT_CH_STATUS='A'"
    sql_demanda = f"SELECT * FROM Apt_Pro_Demandas WHERE CTL_IN_CODIGO IN ({placeholders}) AND MOV_ST_STATUS='A'"
    with sqlite_con() as con:
        con.row_factory = sqlite3.Row
        ordens = [dict(row) for row in con.execute(sql_ordem, ctl_ids).fetchall()]
        demandas = [dict(row) for row in con.execute(sql_demanda, ctl_ids).fetchall()]
    return ordens, demandas

def f_rfc_in_codigo(cur, pro: int, pad: int) -> int:
    cur.execute("SELECT NVL(PRO.RFC_IN_CODIGO,0) FROM EST_PRODUTOS PRO WHERE PRO.PRO_TAB_IN_CODIGO=100 AND PRO.PRO_PAD_IN_CODIGO=:1 AND PRO.PRO_IN_CODIGO=:2", (pad, pro))
    row = cur.fetchone()
    return row[0] if row else 0

def next_orl_st_slote(cur, org: int, ord: int) -> int:
    cur.execute("""SELECT COUNT(1)+1 FROM IDP.APT_APONTAORDEM_LOTE x
     WHERE x.ORG_TAU_ST_CODIGO='G' AND x.ORG_TAB_IN_CODIGO=53 AND x.ORD_SEQ_IN_CODIGO=1 AND x.ORG_IN_CODIGO=:1
       AND x.ORD_IN_CODIGO=:2 AND x.ORD_TAB_IN_CODIGO=218 AND x.ORG_PAD_IN_CODIGO=1""", (org, ord))
    return cur.fetchone()[0]

def get_or_create_apt_pai(cur, d_ctl: Dict) -> Dict:
    """REGRA: Apt_Controle -> APT_APONTAORDEM. oracledb não usa OBJECT RETURNING"""
    sql = "SELECT * FROM IDP.APT_APONTAORDEM APT WHERE APT.CTL_IN_CODIGO=:1 AND APT.APT_CH_STATUS='A' FETCH FIRST 1 ROWS ONLY"
    cur.execute(sql, (d_ctl['CTL_IN_CODIGO'],))
    row = cur.fetchone()
    if row: return dict(zip([d[0] for d in cur.description], row))

    # INSERT PAI usando CTL_IN_CODIGO como SEQ
    sql = """INSERT INTO APT_APONTAORDEM (APT_IN_SEQUENCIA, FIL_IN_CODIGO, APT_DT_APONTAMENTO, APT_CH_STATUS,
                      CTL_IN_CODIGO, ORG_TAB_IN_CODIGO, ORG_PAD_IN_CODIGO, ORG_IN_CODIGO, ORG_TAU_ST_CODIGO,
                      ORD_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO)
    VALUES (:1,:2,TO_DATE(:3,'YYYY-MM-DD'),:4,:1,53,1,:5,'G',218,1)"""
    cur.execute(sql, (d_ctl['CTL_IN_CODIGO'], d_ctl['FIL_IN_CODIGO'], d_ctl['CTL_DT_EMISSAO'], 'A', d_ctl['FIL_IN_CODIGO']))

    cur.execute(sql, (d_ctl['CTL_IN_CODIGO'],)) # SELECT DEPOIS
    return dict(zip([d[0] for d in cur.description], cur.fetchone()))

def processa_controle(cur, d_ctl: Dict, ordens: List, demandas: List):
    """REGRA CLONE: 1 Controle = 1 PAI + N LOTE + N LOTE_APONTAMENTO + N DEMANDA"""
    vTAB_APT = get_or_create_apt_pai(cur, d_ctl)
    vpro_pad = cur.execute("SELECT IDP.PCK_MEGA.ACHAPADRAODATABELA(:1,100,SYSDATE) FROM DUAL", (d_ctl['FIL_IN_CODIGO'],)).fetchone()[0]

    for d_ord in ordens:
        # 1. RFC / REFERENCIA
        vcodreferencia = f_rfc_in_codigo(cur, d_ord['PRO_IN_CODIGO'], vpro_pad)
        vmvl_st_referencia = d_ord['ORL_ST_REFERENCIA'] or '*'
        if vcodreferencia!= 0 and vmvl_st_referencia == '*': raise ValueError('e obrigatorio informar as caracteristicas!')

        # 2. SLOTE
        vorl_st_slote = next_orl_st_slote(cur, d_ord['ORG_IN_CODIGO'], d_ord['ORD_IN_CODIGO'])
        vmvl_st_loteforne = d_ord['PRO_ST_LOTE']

        # 3. INSERT PRO_ORDEMLOTESUB
        cur.execute("""INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX(PRO_ORDEMLOTESUB PRO_PK_ORDEMLOTESUB) */
        INTO PRO_ORDEMLOTESUB (ORG_TAU_ST_CODIGO, ORG_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO, ORG_IN_CODIGO, ORD_IN_CODIGO, ORD_TAB_IN_CODIGO,
                               ORG_PAD_IN_CODIGO, ORL_ST_LOTEFABRICACAO, ORL_ST_SLOTEFABRICACAO, ORL_ST_REFERENCIA, ORL_RE_QTDLOTE,
                               ORL_RE_QTDRECEBIDA, ORL_RE_QTDREFUGADA, ORL_RE_QTDINTERDITADA, ORL_CH_ORIGEM)
        VALUES ('G',53,1,:1,:2,218,1,:3,:4,:5,:6,0,:7,0,'O')""",
                    (d_ord['ORG_IN_CODIGO'], d_ord['ORD_IN_CODIGO'], vmvl_st_loteforne, vorl_st_slote, vmvl_st_referencia, d_ord['ORL_RE_QTDLOTE'], d_ord['PRO_RE_QTDREFUGO'] or 0))

        # 4. INSERT APT_APONTAORDEM_LOTE
        cur.execute("""INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX(APT_APONTAORDEM_LOTE PK_APT_APONTAORDEM_LOTE) */
        INTO IDP.APT_APONTAORDEM_LOTE (APT_IN_SEQUENCIA, ORG_TAB_IN_CODIGO, ORG_PAD_IN_CODIGO, ORG_IN_CODIGO, ORG_TAU_ST_CODIGO,
                                       ORD_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO, ORD_IN_CODIGO, FIL_IN_CODIGO, CTL_IN_CODIGO, MVP_IN_SEQUENCIA,
                                       ORL_ST_LOTEFABRICACAO, ORL_ST_SLOTEFABRICACAO, ORL_ST_REFERENCIA, PRO_TAB_IN_CODIGO, PRO_PAD_IN_CODIGO,
                                       PRO_IN_CODIGO, ORL_RE_QTDLOTE, ORL_RE_UNIDADE, ORL_ST_TIPOLOTE, APT_CH_STATUS, ORL_ST_LOTEOBS,
                                       ORI_DOC_ORIGEM, APT_DT_INCLUSAO, ORL_RE_QTDREF, APT_REF_IN_CODIGO)
        VALUES (:1,53,1,:2,'G',218,1,:3,:4,:5,:6,:7,:8,:9,100,:10,:11,:12,:12,'P','A',:13,:14,TO_DATE(:15,'YYYY-MM-DD'),:16,:17)""",
                    (vTAB_APT['APT_IN_SEQUENCIA'], d_ord['ORG_IN_CODIGO'], d_ord['ORD_IN_CODIGO'], d_ctl['FIL_IN_CODIGO'], d_ctl['CTL_IN_CODIGO'], d_ord['APT_IN_SEQUENCIA'],
                     vmvl_st_loteforne, vorl_st_slote, vmvl_st_referencia, vpro_pad, d_ord['PRO_IN_CODIGO'], d_ord['ORL_RE_QTDLOTE'],
                     d_ord['PRO_ST_DESCRICAO'], d_ord['PRO_ST_ID'], d_ord['APT_DT_APONTAMENTO'], d_ord['PRO_RE_QTDREFUGO'] or 0, 2 if d_ord['PRO_RE_QTDREFUGO'] else None))

    # 5. BULK INSERT APT_APONTADEMANDA_ESTOQUE
    rows = []
    for d_ord in ordens:
        for d_dem in demandas:
            if d_dem['ORD_IN_CODIGO'] == d_ord['ORD_IN_CODIGO']:
                rows.append((
                    vTAB_APT['APT_IN_SEQUENCIA'], 53,1,d_ord['ORG_IN_CODIGO'],'G',218,1,d_ord['ORD_IN_CODIGO'],
                    100,1,d_dem['PRO_IN_CODIGO'],1,d_ctl['CTL_DT_EMISSAO'],vTAB_APT['PLF_IN_SQOPERACAO'],d_dem['MOV_IN_SEQUENCIA'],
                    d_ctl['FIL_IN_CODIGO'],None,None,None,None,None,None,None,None,d_dem.get('PRO_ST_LOTE'),None,None,None,'N',
                    d_dem['PRO_RE_QTDLOTE'],None,None,d_ctl['CTL_IN_CODIGO'],None,d_ord['ORD_ST_ID'],d_ord['CMAQ_ST_ID'],
                    None,None,0,'S',0,'A'
                ))
    if rows:
        sql = """INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX(APT_APONTADEMANDA_ESTOQUE PK_APT_APONTADEMANDA_ESTOQUE) */
        INTO APT_APONTADEMANDA_ESTOQUE (APT_IN_SEQUENCIA, ORG_TAB_IN_CODIGO, ORG_PAD_IN_CODIGO, ORG_IN_CODIGO, ORG_TAU_ST_CODIGO,
            ORD_TAB_IN_CODIGO, ORD_SEQ_IN_CODIGO, ORD_IN_CODIGO, COM_TAB_IN_CODIGO, COM_PAD_IN_CODIGO, COM_IN_CODIGO, DDE_IN_OPERACAO,
            DDE_DT_NECESSIDADE, PLF_IN_SQOPERACAO, MVS_IN_SEQUENCIA, FIL_IN_CODIGO, ALM_TAB_IN_CODIGO, ALM_PAD_IN_CODIGO, ALM_IN_CODIGO,
            LOC_IN_CODIGO, MVS_IN_RESERVA, NAT_TAB_IN_CODIGO, NAT_PAD_IN_CODIGO, NAT_ST_CODIGO, MVS_ST_REFERENCIA, MVS_ST_LOTEFORNE,
            MVS_DT_ENTRADA, MVS_DT_VALIDADE, IRE_CH_TIPORESERVA, APT_RE_QTDESELECIONADA, EMM_IN_SEQUENCIA, MVT_IN_LANCAM, CTL_IN_CODIGO,
            MVD_IN_SEQUENCIA, ORD_ST_ID, CMAQ_ST_ID, MVL_ST_LOG, VIN_MVT_IN_LANCAM, APT_RE_QTDEAVISO, APT_BO_LOTEESTOQUE, SALDO_ESTOQUE, DDE_ST_SITUACAO)
        VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,TO_DATE(:13,'YYYY-MM-DD'),:14,:15,:16,:17,:18,:19,:20,:21,:22,:23,:24,:25,:26,:27,:28,:29,:30,:31,:32,:33,:34,:35,:36,:37,:38,:39,:40,:41,:42)"""
        cur.executemany(sql, rows)

def bulk_update_status_tudo(ctl_ids: List[int]):
    if not ctl_ids: return
    sql_sqlite_ctl = "UPDATE Apt_Controle SET CTL_ST_STATUS =? WHERE CTL_IN_CODIGO =?"
    sql_sqlite_ordem = "UPDATE Apt_ApontaOrdem SET APT_CH_STATUS =? WHERE CTL_IN_CODIGO =?"
    sql_sqlite_demanda = "UPDATE Apt_Pro_Demandas SET MOV_ST_STATUS =? WHERE CTL_IN_CODIGO =?"
    with sqlite_con() as scon:
        scon.executemany(sql_sqlite_ctl, [('I', i) for i in ctl_ids])
        scon.executemany(sql_sqlite_ordem, [('I', i) for i in ctl_ids])
        scon.executemany(sql_sqlite_demanda, [('I', i) for i in ctl_ids])