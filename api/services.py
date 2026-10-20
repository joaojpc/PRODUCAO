# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-20 (JPC): sincronizacao de ordens Oracle -> SQLite (rotina NOVA, isolada),
copiada do NMV e ajustada ao PRODUCAO. Leitura no Oracle por SQL nativo / procedures, com a
conexao recebida (uma so para a rodada inteira, sem HTTP). MESMO SQL e mesmas procedures que os
endpoints usados hoje pelo "Baixar Ordens" daqui (api/api_view.py: GetDadosProducao.get_integracao,
get_pro_ordens, demandas_ordem, itens_ordem, get_pro_conversor, itn_atributos, itn_referencias,
get_ref_atributos; GetDadosRecebimento.get_cadOperadores; GetDadosMaquina.apt_GetDadosMaquina). Nada aqui grava no
Oracle. Quem chama: app/sincronizacao.py.
Diferencas do NMV (o PRODUCAO le diferente): get_integracao com filial sem filtro de status,
itens pela apt_intprod2 (chaves minusculas) e caracteristicas sem rat_ch_tipoconteudo.
"""


def _linhas_dict(cur):
    colunas = [c[0] for c in cur.description]
    return [dict(zip(colunas, r)) for r in cur.fetchall()]


def _proc_ref_cursor(con, procedure, params_antes, params_depois=()):
    """Chama procedure que devolve REF CURSOR; devolve (colunas, linhas)."""
    with con.cursor() as cur:
        ref_cursor = con.cursor()
        cur.callproc(procedure, list(params_antes) + [ref_cursor] + list(params_depois))
        colunas = [c[0] for c in ref_cursor.description] if ref_cursor.description else []
        linhas = ref_cursor.fetchall()
        ref_cursor.close()
    return colunas, linhas


def sync_ordens_pendentes(con, org_in_codigo, fil_in_codigo=None, ord_in_codigo=None, param=None):
    """= GetDadosProducao.get_integracao. Com filial: a OP informada, sem filtro de status (no
    PRODUCAO o filtro ord_ch_integrada/ord_ch_modificada esta comentado no SQL de hoje)."""
    if fil_in_codigo is None:
        sql = """select ord.org_in_codigo, ord.ord_seq_in_codigo, ord.ord_in_codigo
                   from idp.int_pro_ordens ord
                  where ord.ord_ch_integrada = :ord_ch_integrada
                    and ord.org_in_codigo = :org_in_codigo
                  order by ord.ord_in_codigo"""
        binds = {'ord_ch_integrada': 'N', 'org_in_codigo': org_in_codigo}
    else:
        sql = """select ord.org_in_codigo, ord.ord_seq_in_codigo, ord.ord_in_codigo
                   from idp.int_pro_ordens ord
                  where ord.fil_in_codigo = :fil_in_codigo
                    and ord.ord_in_codigo = :ord_in_codigo
                  order by ord.ord_in_codigo"""
        binds = {'fil_in_codigo': fil_in_codigo, 'ord_in_codigo': ord_in_codigo}
    with con.cursor() as cur:
        cur.execute(sql, binds)
        return [dict(org_in_codigo=int(r[0]), ord_seq_in_codigo=int(r[1]), ord_in_codigo=int(r[2]))
                for r in cur.fetchall()]


def sync_dados_ordem(con, org_in_codigo, ord_seq_in_codigo, ord_in_codigo):
    """= GetDadosProducao.get_pro_ordens (mesmas chaves e conversoes)."""
    sql = """select ord.org_tab_in_codigo, ord.org_pad_in_codigo, ord.org_in_codigo, ord.org_tau_st_codigo,
                    ord.ord_tab_in_codigo, ord.ord_seq_in_codigo, ord.ord_in_codigo, ord.pro_tab_in_codigo,
                    ord.pro_pad_in_codigo, ord.pro_in_codigo, ord.ord_re_qtde_ordem, ord.fil_in_codigo,
                    ord.tpo_st_codigo_tipo, nvl(oce.ord_re_umidade,0) ord_re_umidade,
                    decode(oce.ord_re_estufa, null, null,
                           lpad(oce.ord_re_estufa,2,0)||'/'||lpad(oce.ord_re_carga,2,0)||'/'||
                           decode(oce.ord_re_ano, null, to_char(sysdate,'yy'), lpad(oce.ord_re_ano,2,0))
                    ) as lote_ordem,
                    oce.ord_st_destino,
                    lpad(ord.org_tab_in_codigo,3,0)||lpad(ord.org_pad_in_codigo,3,0)||lpad(ord.org_in_codigo,7,0)||
                    lpad(ord.org_tau_st_codigo,3,0)||lpad(ord.ord_tab_in_codigo,3,0)||lpad(ord.ord_seq_in_codigo,3,0)||
                    lpad(ord.ord_in_codigo,20,0) as ord_st_id,
                    lpad(ord.pro_tab_in_codigo,3,0)||lpad(ord.pro_pad_in_codigo,3,0)||lpad(ord.pro_in_codigo,7,0) as pro_st_id,
                    lpad(ord.tpo_tab_in_codigo,3,0)||lpad(ord.tpo_pad_in_codigo,3,0)||lpad(ord.tpo_st_codigo_tipo,6,0) as tpo_st_id,
                    oce.ord_st_origem
               from pro_ordens ord, pro_ordenscmpesp oce
              where ord.org_tab_in_codigo = oce.org_tab_in_codigo (+)
                and ord.org_pad_in_codigo = oce.org_pad_in_codigo (+)
                and ord.org_in_codigo     = oce.org_in_codigo     (+)
                and ord.org_tau_st_codigo = oce.org_tau_st_codigo (+)
                and ord.ord_tab_in_codigo = oce.ord_tab_in_codigo (+)
                and ord.ord_seq_in_codigo = oce.ord_seq_in_codigo (+)
                and ord.ord_in_codigo     = oce.ord_in_codigo     (+)
                and ord.org_in_codigo = :org_in_codigo
                and ord.ord_seq_in_codigo = :ord_seq_in_codigo
                and ord.ord_in_codigo = :ord_in_codigo
              order by ord.ord_in_codigo"""
    with con.cursor() as cur:
        cur.execute(sql, {'org_in_codigo': org_in_codigo, 'ord_seq_in_codigo': ord_seq_in_codigo,
                          'ord_in_codigo': ord_in_codigo})
        linhas = cur.fetchall()
    return [dict(ORG_TAB_IN_CODIGO=int(rs[0]), ORG_PAD_IN_CODIGO=int(rs[1]), ORG_IN_CODIGO=int(rs[2]),
                 ORG_TAU_ST_CODIGO=rs[3], ORD_TAB_IN_CODIGO=int(rs[4]), ORD_SEQ_IN_CODIGO=int(rs[5]),
                 ORD_IN_CODIGO=int(rs[6]), PRO_TAB_IN_CODIGO=int(rs[7]), PRO_PAD_IN_CODIGO=int(rs[8]),
                 PRO_IN_CODIGO=int(rs[9]), ORD_RE_QTDE_ORDEM=float(rs[10]), FIL_IN_CODIGO=int(rs[11]),
                 TPO_ST_CODIGO_TIPO=rs[12], ORD_RE_UMIDADE=0 if rs[13] is None else int(rs[13]),
                 LOTE_ORDEM=rs[14], ORD_ST_DESTINO=rs[15], PRO_ST_ID=rs[17], ORD_ST_ID=rs[16],
                 TPO_ST_ID=rs[18], ORD_ST_ORIGEM=rs[19])
            for rs in linhas]


def sync_demandas_ordem(con, org_in_codigo, ord_seq_in_codigo, ord_in_codigo):
    """= GetDadosProducao.demandas_ordem (procedure apt_intprod.apt_retornaDemanda)."""
    _cols, linhas = _proc_ref_cursor(con, 'idp.apt_intprod.apt_retornaDemanda',
                                     (org_in_codigo, ord_seq_in_codigo, ord_in_codigo))
    return [dict(com_in_codigo=int(rs[9]), com_st_descricao=rs[12], uni_st_unidade=rs[13]) for rs in linhas]


def sync_itens_ordem(con, fil_in_codigo, ord_in_codigo):
    """= GetDadosProducao.itens_ordem (procedure apt_intprod2.apt_retornaitens), mesmas chaves
    minusculas -- formato que as telas do PRODUCAO leem em PRO_ST_ITENS."""
    _cols, linhas = _proc_ref_cursor(con, 'idp.apt_intprod2.apt_retornaitens', (fil_in_codigo, ord_in_codigo))
    return [dict(pro_pad_in_codigo=int(rs[1]), pro_in_codigo=int(rs[2]), pro_st_descricao=rs[3],
                 uni_st_unidade=rs[4], rfc_in_codigo=int(rs[5]), pro_re_comprimento=rs[6],
                 pro_re_largura=rs[7], pro_re_espessura=rs[8], pro_st_madeira=rs[9],
                 mvs_st_referencia=rs[10], pro_st_id=rs[11], pro_re_perda=rs[13], tipo_item=rs[14])
            for rs in linhas]


def sync_conversor(con, fil_in_codigo, pro_in_codigo):
    """= GetDadosProducao.get_pro_conversor."""
    sql = """select fmt.fmt_st_nome, fu.uni_st_formula, fu.uni_st_fator
               from est_fatorunidade fu, est_formatos fmt,
                    (select pro.uni_st_unidade, pun.uni_st_unidade fmt_st_unidade, pun.fmt_tab_in_codigo,
                            pun.fmt_pad_in_codigo, pun.fmt_st_codigo
                       from est_prouni pun, est_produtos pro
                      where pun.pro_tab_in_codigo = pro.pro_tab_in_codigo
                        and pun.pro_pad_in_codigo = pro.pro_pad_in_codigo
                        and pun.pro_in_codigo     = pro.pro_in_codigo
                        and pun.pro_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 100, sysdate)
                        and pun.pro_in_codigo     = :pro_in_codigo) ci
              where fu.fmt_tab_in_codigo = fmt.fmt_tab_in_codigo
                and fu.fmt_pad_in_codigo = fmt.fmt_pad_in_codigo
                and fu.fmt_st_codigo     = fmt.fmt_st_codigo
                and ci.fmt_tab_in_codigo = fu.fmt_tab_in_codigo
                and ci.fmt_pad_in_codigo = fu.fmt_pad_in_codigo
                and ci.fmt_st_codigo     = fu.fmt_st_codigo
                and ci.uni_st_unidade    = fu.un2_st_unidade
                and ci.fmt_st_unidade    = fu.un1_st_unidade"""
    with con.cursor() as cur:
        cur.execute(sql, {'fil_in_codigo': fil_in_codigo, 'pro_in_codigo': pro_in_codigo})
        return _linhas_dict(cur)


def sync_atributos_item(con, fil_in_codigo, pro_in_codigo):
    """= GetDadosProducao.itn_atributos (procedure apt_intprod.apt_retornaatributo)."""
    _cols, linhas = _proc_ref_cursor(con, 'idp.apt_intprod.apt_retornaatributo', (fil_in_codigo, pro_in_codigo))
    return [dict(pai_rat_in_codigo=int(rs[0]), rat_in_codigo=int(rs[1]), rat_st_descricao=rs[2],
                 rat_value=rs[3], rat_ch_tipo=rs[4]) for rs in linhas]


def sync_referencias_item(con, fil_in_codigo, pro_in_codigo):
    """= GetDadosProducao.itn_referencias (procedure apt_intprod.apt_retornacaracteristica)."""
    _cols, linhas = _proc_ref_cursor(con, 'idp.apt_intprod.apt_retornacaracteristica',
                                     (fil_in_codigo, pro_in_codigo))
    return [dict(rat_in_codigo=int(rs[0]), rat_st_opcoes=rs[1], itn_desc=rs[2], rat_desc=rs[3],
                 rat_ch_tipo=rs[4], ref_rat_value=rs[5], rfc_in_codigo=int(rs[6])) for rs in linhas]


def sync_caracteristicas_referencia(con, fil_in_codigo, rfc_in_codigo):
    """= GetDadosProducao.get_ref_atributos (sem rat_ch_tipoconteudo, como no PRODUCAO)."""
    sql = """select lpad(cr.rat_tab_in_codigo,3,'0')||lpad(cr.rat_pad_in_codigo,3,'0')||lpad(cr.rat_in_codigo,7,'0')||
                    lpad(cr.rfc_tab_in_codigo,3,'0')||lpad(cr.rfc_pad_in_codigo,3,'0')||lpad(cr.rfc_in_codigo,7,'0') as car_st_id,
                    lpad(cr.rat_tab_in_codigo,3,'0')||lpad(cr.rat_pad_in_codigo,3,'0')||lpad(cr.rat_in_codigo,7,'0') as rat_st_id,
                    lpad(cr.rfc_tab_in_codigo,3,'0')||lpad(cr.rfc_pad_in_codigo,3,'0')||lpad(cr.rfc_in_codigo,7,'0') as rfc_st_id,
                    ar.pai_rat_in_codigo, ar.rat_in_codigo, ar.rat_st_descricao,
                    case when ar.rat_ch_tipo = 'P' then lpad(ar.pai_rat_in_codigo,7,'0')||'='||ar.rat_in_codigo
                         else lpad(ar.rat_in_codigo,7,'0')||'=' end as rat_value,
                    ar.rat_ch_tipo, cr.car_in_prioridade, cr.rfc_in_codigo,
                    case when ar.pai_rat_in_codigo = ar.rat_in_codigo then 'S' else 'N' end as rat_bo_grupo_new,
                    ar.rat_bo_grupo, cr.car_bo_obrigatorio, pai.rat_st_descricao as pai_st_descricao
               from est_atributoreferencia ar, est_caracatributoreferencia cr, est_atributoreferencia pai
              where ar.rat_tab_in_codigo = cr.rat_tab_in_codigo
                and ar.rat_pad_in_codigo = cr.rat_pad_in_codigo
                and ar.rat_in_codigo = cr.rat_in_codigo
                and pai.rat_tab_in_codigo = ar.rat_tab_in_codigo
                and pai.rat_pad_in_codigo = ar.rat_pad_in_codigo
                and pai.rat_in_codigo = ar.pai_rat_in_codigo
                and cr.rfc_in_codigo = :rfc_in_codigo
                and cr.rfc_pad_in_codigo = pck_mega.achapadraodatabela(:fil_in_codigo, 141, sysdate)
              order by cr.rfc_in_codigo, cr.car_in_prioridade"""
    with con.cursor() as cur:
        cur.execute(sql, {'fil_in_codigo': fil_in_codigo, 'rfc_in_codigo': rfc_in_codigo})
        return _linhas_dict(cur)


def sync_operadores(con, fil_in_codigo):
    """= GetDadosRecebimento.get_cadOperadores (operador 'all'), mesmo SQL.
    Devolve no formato do app: OPD_ST_CRACHA (= opd_st_alternativo), OPD_ST_NOME, FIL_IN_CODIGO."""
    with con.cursor() as cur:
        cur.execute("""select opd.opd_st_alternativo, opd.opd_st_descricao
                         from pro_cadoperador opd, pro_cadoperadorcmpesp oce
                        where opd.opd_tab_in_codigo = oce.opd_tab_in_codigo (+)
                          and opd.opd_pad_in_codigo = oce.opd_pad_in_codigo (+)
                          and opd.opd_in_codigo     = oce.opd_in_codigo (+)
                          and opd.opd_pad_in_codigo = pck_mega.achapadraodatabela(:fil, 228, sysdate)""",
                    {'fil': int(fil_in_codigo)})
        return [dict(OPD_ST_CRACHA=r[0], OPD_ST_NOME=r[1], FIL_IN_CODIGO=int(fil_in_codigo))
                for r in cur.fetchall()]


def sync_maquinas(con):
    """= GetDadosMaquina.apt_GetDadosMaquina (filial 3 fixa no original -- mantido)."""
    _cols, linhas = _proc_ref_cursor(con, 'idp.apt_intprod.apt_GetDadosMaquina', (), (3,))
    if not linhas:
        return [dict(CTR_ST_ID='0', CMAQ_ST_ID='0', CTR_ST_NOME='0', CMAQ_ST_NOME='0', CMAQ_ST_CODIGO='0')]
    return [dict(CTR_ST_ID=v[0], CMAQ_ST_ID=v[1], CTR_ST_NOME=v[2], CMAQ_ST_NOME=v[3], CMAQ_ST_CODIGO=v[4])
            for v in linhas]
