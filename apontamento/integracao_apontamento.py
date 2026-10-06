# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-06: gravacao direta no Oracle para o fechamento diario de OP.
Copiado do projeto MP (apontamento/integracao_apontamento.py, fluxo "Efetivar Apontamento"):
grava lote(s) e demanda(s) pendentes do controle numa UNICA transacao Oracle (tudo ou
nada), marca 'I' no local e chama p_efetivaapontamento. Diferenca do MP: NAO encerra o
controle -- quem fecha e' o Fechamento (api_view.py), so' depois de tudo dar certo.
Usado SO pelo fechamento diario; integrarProducao, Encerrar e cron nao mudam.
- JPC - João Castro
"""
from __future__ import unicode_literals

import os
from datetime import datetime as _dt

from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas

# Chave geral: desligada, o fechamento grava so' o local (como antes). Liga pela variavel de
# ambiente FECHAMENTO_GRAVA_ORACLE=1 do processo (gunicorn), lida na subida; padrao desligado.
FECHAMENTO_GRAVA_ORACLE = os.environ.get('FECHAMENTO_GRAVA_ORACLE', '0').strip().lower() in ('1', 'true', 'sim', 's')


def _dados_lote(row, v_session):
    return {
        'fil_in_codigo': row.FIL_IN_CODIGO,
        'ord_in_codigo': row.ORD_IN_CODIGO,
        'ctl_in_codigo': row.CTL_IN_CODIGO,
        'plf_in_sqoperacao': v_session.get('seq_in_operacao'),
        'apt_dt_inclusao': _dt.now().strftime('%Y-%m-%d'),
        'mvp_in_sequencia': row.APT_IN_SEQUENCIA,
        'apt_re_quantidade': row.ORL_RE_QTDLOTE,
        'apt_re_qtdeconvertida': row.PRO_RE_QTDCONV,
        'apt_re_qtderefugo': row.PRO_RE_QTDREFUGO,
        'pro_in_codigo': row.PRO_IN_CODIGO,
        # PRODUCAO: mesma observacao fixa que o integrarProducao usa quando nao ha' outra
        'pro_st_obs': row.APT_ST_OBSERV or 'Lote integrado pelo ACB',
        'pro_st_docorigem': row.PRO_ST_LOTEORI,
        'pro_st_referencia': row.ORL_ST_REFERENCIA,
        'pro_st_destino': 'I',
        'pro_st_lote': str(row.PRO_ST_LOTE),
        'apt_dt_lote': row.APT_DT_APONTAMENTO,
        'cmaq_st_id': row.CMAQ_ST_ID,
        'pro_st_id': row.PRO_ST_ID,
        'ord_st_id': row.ORD_ST_ID,
        'ord_st_extenso': v_session.get('ordem'),
        # PRODUCAO: o integrarProducao ja' envia o fornecedor (no MP vai None)
        'pro_st_fornecedor': row.PRO_ST_FORNECEDOR,
    }


def _dados_demanda(row, v_session):
    return {
        'fil_in_codigo': row.FIL_IN_CODIGO,
        'ord_in_codigo': row.ORD_IN_CODIGO,
        'ctl_in_codigo': row.CTL_IN_CODIGO,
        'plf_in_sqoperacao': v_session.get('seq_in_operacao'),
        'apt_dt_inclusao': _dt.now().strftime('%Y-%m-%d'),
        'mvd_in_sequencia': row.MOV_IN_SEQUENCIA,
        'pro_st_lote': str(row.PRO_ST_LOTE),
        'pro_re_qtdlote': row.PRO_RE_QTDLOTE,
        'cmaq_st_id': row.CMAQ_ST_ID,
        'ord_st_id': row.ORD_ST_ID,
        'ord_st_extenso': v_session.get('ordem'),
        'pro_in_codigo': row.PRO_IN_CODIGO or 0,
    }


def _gravar_tudo_ou_nada(con, v_session, lotes, demandas):
    """Igual ao MP: grava lote(s) e demanda(s) na MESMA transacao Oracle, sem commit;
    levanta excecao na primeira falha (o chamador faz rollback/commit)."""
    from apontamento.apontamento import gravar_lote, gravar_demanda
    lotes_gravados = []
    for row in lotes:
        dados = _dados_lote(row, v_session)
        resp = gravar_lote(dados, conexao=con, auto_commit=False)
        if not (resp and all(r.get('mensagem') == 'Ok' and r.get('mensagem_sub') == 'Ok' for r in resp)):
            detalhe = resp[0].get('detalhe') if resp else 'sem retorno'
            raise RuntimeError(f'Lote {row.PRO_ST_LOTE} (seq {row.APT_IN_SEQUENCIA}): {detalhe}')
        lotes_gravados.append((row, resp))

    resultados_demanda = []
    if demandas:
        lista_dados = [_dados_demanda(row, v_session) for row in demandas]
        resultados_demanda = gravar_demanda(lista_dados, conexao=con, auto_commit=False)
        if resultados_demanda and len(resultados_demanda) == 1 and resultados_demanda[0].get('mensagem') == 'Erro':
            raise RuntimeError(f"Demandas: {resultados_demanda[0].get('detalhe')}")

    return lotes_gravados, resultados_demanda


def gravar_e_efetivar_controle(v_session, data_apontamento=None):
    """Casca: qualquer excecao do Oracle vira resultado['erro_oracle'] (o controle continua
    aberto pra tentar de novo). Devolve o dict de resultado."""
    resultado = {'ctl_in_codigo': v_session.get('ctl_in_codigo'), 'ok': 0, 'erro': 0, 'erros': [],
                 'msg_efetivar': None, 'efetivado_oracle': False, 'erro_oracle': None}
    try:
        return _gravar_e_efetivar_controle(v_session, data_apontamento, resultado)
    except Exception as e:
        import traceback
        print('ERRO FECHAMENTO ORACLE (excecao):', traceback.format_exc())
        resultado['erro_oracle'] = str(e)
        return resultado


def _gravar_e_efetivar_controle(v_session, data_apontamento, resultado):
    """Itens 1, 2 e 3 do fluxo do MP (gravar tudo ou nada, marcar 'I', efetivar), sem o
    encerramento do controle."""
    ctl_in_codigo = v_session.get('ctl_in_codigo')
    if not ctl_in_codigo:
        resultado['erro_oracle'] = 'Controle (CTL_IN_CODIGO) não informado.'
        return resultado

    from apontamento.models import Apt_Controle
    controle = Apt_Controle.objects.filter(CTL_IN_CODIGO=ctl_in_codigo).first()

    lotes = Apt_ApontaOrdem.objects.filter(CTL_IN_CODIGO=ctl_in_codigo, APT_CH_STATUS='A')
    demandas = Apt_Pro_Demandas.objects.filter(CTL_IN_CODIGO=ctl_in_codigo, MOV_ST_STATUS='A')

    from apontamento.apontamento import _abrir_conexao, efetivar_apontamento_oracle, _apt_in_sequencia_do_ctl
    with _abrir_conexao() as con:
        apt_in_sequencia = None
        if lotes or demandas:
            try:
                lotes_gravados, resultados_demanda = _gravar_tudo_ou_nada(con, v_session, lotes, demandas)
            except Exception as e:
                con.rollback()
                resultado['erro'] = 1
                resultado['erros'] = [str(e)]
                return resultado  # nada foi gravado; controle continua aberto
            con.commit()  # tudo deu certo -- lote(s) e demanda(s) juntos
            for row, _resp in lotes_gravados:
                row.APT_CH_STATUS = 'I'
                row.save(update_fields=['APT_CH_STATUS'])
            if lotes_gravados and controle:
                apt_gravado = lotes_gravados[0][1][0]['sequencia']
                if controle.APT_IN_SEQUENCIA != apt_gravado:
                    controle.APT_IN_SEQUENCIA = apt_gravado
                    controle.save(update_fields=['APT_IN_SEQUENCIA'])
            linhas_por_mvd = {row.MOV_IN_SEQUENCIA: row for row in demandas}
            ok_dem = erro_dem = 0
            erros_dem = []
            for r in resultados_demanda:
                mensagem = r.get('mensagem')
                if mensagem in ('Ok', 'Cancelada', 'Ja cancelada no local'):
                    if mensagem == 'Ok':
                        row = linhas_por_mvd.get(r.get('mvd'))
                        if row is not None:
                            row.MOV_ST_STATUS = 'I'
                            row.save(update_fields=['MOV_ST_STATUS'])
                    ok_dem += 1
                else:
                    erro_dem += 1
                    erros_dem.append(f"Demanda mvd={r.get('mvd')}: {r.get('detalhe', mensagem)}")
            resultado.update({'ok': len(lotes_gravados) + ok_dem, 'erro': erro_dem, 'erros': erros_dem})
            apt_in_sequencia = lotes_gravados[0][1][0]['sequencia'] if lotes_gravados else None

        # Sempre tenta efetivar (cobre o retry depois de um efetivar que falhou)
        if apt_in_sequencia is None:
            with con.cursor() as cur:
                apt_in_sequencia = _apt_in_sequencia_do_ctl(cur, ctl_in_codigo)
        if apt_in_sequencia and controle:
            usuario_efetivou = v_session.get('usuario') or controle.CTL_ST_USUARIO
            msg_efetivar, efetivado = efetivar_apontamento_oracle(
                apt_in_sequencia, usuario_efetivou, controle.FIL_IN_CODIGO, conexao=con,
                data_apontamento=data_apontamento)
            resultado['msg_efetivar'] = msg_efetivar
            resultado['efetivado_oracle'] = efetivado
        else:
            # nada apontado no Oracle para esse controle: nao ha' o que efetivar
            resultado['efetivado_oracle'] = True
    return resultado
