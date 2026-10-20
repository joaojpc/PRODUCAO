# -*- coding: utf-8 -*-
"""
AJUSTE 2026-10-06: gravacao direta no Oracle para o fechamento diario de OP.
Copiado do projeto MP (apontamento/integracao_apontamento.py, fluxo "Efetivar Apontamento"):
grava lote(s) e demanda(s) pendentes do controle numa UNICA transacao Oracle (tudo ou
nada), marca 'I' no local e chama p_efetivaapontamento. Diferenca do MP: NAO encerra o
controle -- quem fecha e' o Fechamento (api_view.py), so' depois de tudo dar certo.
Usado SO pelo fechamento diario; integrarProducao, Encerrar e cron nao mudam.
- JPC - João Castro

AJUSTE 2026-10-20: rotina UNICA efetivar_apontamento(v_session, atividade, etapa, data) --
decisao do usuario: cada forma de efetivar e uma ATIVIDADE numerada (tabela ATIVIDADES abaixo):
  1 = efetivar apontamento em duas etapas (botao da Manutencao): etapa 1 grava, etapa 2 efetiva;
  2 = efetivar apontamento em etapa unica (Fechamento diario): grava e efetiva com a data da tela;
  3 = integrar apontamento pelo cron (api_producao): grava os pendentes, sem efetivar.
Mesmas pecas por dentro (_gravar_pendentes, _efetivar); nova forma = nova atividade. Convive com
o cron: lote/demanda ja gravados pela procedure sao reconhecidos (f_valida_*) e so marcados 'I'.
"""
from __future__ import unicode_literals

from datetime import datetime as _dt

from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas

# Chave geral (mesmo modelo do EFETIVAR_GRAVA_ORACLE do MP): False = o fechamento grava so' o
# local (como antes). Ligar/desligar por commit + deploy, depois de validar com uma OP real.
# AJUSTE 2026-10-20: decisao do usuario -- ligada (atividade 2: o fechamento diario grava e efetiva
# no Mega antes de fechar; erro do Oracle volta para o operador e o controle continua aberto).
FECHAMENTO_GRAVA_ORACLE = True


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
    aberto pra tentar de novo). Devolve o dict de resultado.
    AJUSTE 2026-10-20: atalho da rotina unica -- atividade 2 (etapa unica)."""
    return efetivar_apontamento(v_session, ATIVIDADE_ETAPA_UNICA, 1, data_apontamento)


# AJUSTE 2026-10-20 (JPC): protecoes da gravacao no Oracle copiadas do NMV (validado) / MP:
# conexao testada antes, limite de tempo na gravacao (lock de outra sessao do Mega vira mensagem),
# 'I' no app so depois de reler no Oracle pela chave exata (numa transacao) e CTL inteiro conferido
# (app x Mega) antes de efetivar. Valem para todas as atividades e para o cron.
ORACLE_TESTE_TIMEOUT_S = 15       # teste da conexao (SELECT 1 FROM dual)
GRAVACAO_TIMEOUT_MS = 120000      # gravacao dos lotes/demandas (nao vale para commit nem efetivar)
_ERRO_TEMPO = r'DPY-4024|DPI-1067|DPI-1080|ORA-03156|ORA-00054'
MSG_SEM_CONEXAO = 'Sem conexão com o Oracle (Mega). Nada foi gravado. Tente novamente em instantes.'
MSG_ORACLE_BLOQUEADO = ('O Oracle (Mega) não respondeu a tempo -- provavelmente bloqueado por outra '
                        'sessão do Mega. Nada foi gravado. Tente novamente em instantes.')
MSG_NAO_CONFIRMADO = ('Gravado no Oracle, mas não foi possível confirmar tudo pela chave exata '
                      '({faltando}). Nada foi marcado no app -- conferir no Mega.')
MSG_FALHA_CARIMBO = ('Gravado e confirmado no Oracle, mas falhou ao marcar no app. Tente de novo: '
                     'o que já está no Oracle não é gravado de novo.')


def abrir_conexao_oracle_testada():
    """Abre a conexao e testa com SELECT 1 FROM dual (limite de tempo). Devolve (con, None) ou
    (None, mensagem). Quem chama fecha a conexao (with con)."""
    from apontamento.apontamento import _abrir_conexao
    con = None
    try:
        con = _abrir_conexao()
        con.call_timeout = ORACLE_TESTE_TIMEOUT_S * 1000
        with con.cursor() as cur:
            cur.execute('SELECT 1 FROM dual')
            cur.fetchone()
        con.call_timeout = 0
        return con, None
    except Exception:
        import traceback
        print('ERRO TESTE CONEXAO ORACLE:', traceback.format_exc())
        if con:
            try:
                con.close()
            except Exception:
                pass
        return None, MSG_SEM_CONEXAO


def _pendentes(ctl_in_codigo):
    lotes = Apt_ApontaOrdem.objects.filter(CTL_IN_CODIGO=ctl_in_codigo, APT_CH_STATUS='A')
    demandas = Apt_Pro_Demandas.objects.filter(CTL_IN_CODIGO=ctl_in_codigo, MOV_ST_STATUS='A')
    return lotes, demandas


def _chave(row, seq):
    return (int(row.FIL_IN_CODIGO), int(row.ORD_IN_CODIGO), int(seq), int(row.CTL_IN_CODIGO))


def _confirmar_e_carimbar(con, lotes, demandas_ok):
    """Depois do commit no Oracle: rele pela chave exata (fil, ord, mvp/mvd, ctl); so se TUDO
    estiver la, marca 'I' no app numa unica transacao (so o que ainda esta 'A'). Devolve None (ok)
    ou a mensagem de erro. Nunca levanta excecao."""
    from apontamento.apontamento import confirmar_no_oracle
    ch_lotes = {_chave(r, r.APT_IN_SEQUENCIA) for r in lotes}
    ch_dem = {_chave(r, r.MOV_IN_SEQUENCIA) for r in demandas_ok}
    try:
        achou_l = confirmar_no_oracle(con, 'lote', ch_lotes) if ch_lotes else {}
        achou_d = confirmar_no_oracle(con, 'demanda', ch_dem) if ch_dem else {}
    except Exception:
        import traceback
        print('ERRO CONFIRMAR NO ORACLE:', traceback.format_exc())
        return MSG_NAO_CONFIRMADO.format(faltando='falha ao reler o Oracle')
    falta_l = sorted(k[2] for k in ch_lotes if k not in achou_l)
    falta_d = sorted(k[2] for k in ch_dem if k not in achou_d)
    if falta_l or falta_d:
        faltando = ', '.join(filter(None, [f'lotes {falta_l}' if falta_l else '',
                                           f'demandas {falta_d}' if falta_d else '']))
        print(f'ERRO CONFIRMAR: nao achados no Oracle -- {faltando}')
        return MSG_NAO_CONFIRMADO.format(faltando=faltando)
    try:
        from django.db import transaction
        with transaction.atomic():
            if lotes:
                Apt_ApontaOrdem.objects.filter(APT_IN_SEQUENCIA__in=[r.APT_IN_SEQUENCIA for r in lotes],
                                               APT_CH_STATUS='A').update(APT_CH_STATUS='I')
            if demandas_ok:
                Apt_Pro_Demandas.objects.filter(MOV_IN_SEQUENCIA__in=[r.MOV_IN_SEQUENCIA for r in demandas_ok],
                                                MOV_ST_STATUS='A').update(MOV_ST_STATUS='I')
    except Exception:
        import traceback
        print('ERRO CARIMBAR APP:', traceback.format_exc())
        return MSG_FALHA_CARIMBO
    return None


def _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado):
    """Itens 1 e 2 do fluxo do MP: grava tudo ou nada e marca 'I'. Devolve (gravou, apt_in_sequencia).
    AJUSTE 2026-10-20: separado do _gravar_e_efetivar_controle para o botao Efetivar Apontamento.
    AJUSTE 2026-10-20 (protecoes do NMV): gravacao com limite de tempo; 'I' so depois de reler no
    Oracle pela chave exata. Faltou algo: nada e marcado (o retry nao regrava o que ja esta la)."""
    import re
    lotes, demandas = list(lotes), list(demandas)
    try:
        con.call_timeout = GRAVACAO_TIMEOUT_MS
        lotes_gravados, resultados_demanda = _gravar_tudo_ou_nada(con, v_session, lotes, demandas)
        con.call_timeout = 0
    except Exception as e:
        try:
            con.rollback()
        except Exception:
            pass
        resultado['erro'] = 1
        resultado['erros'] = [str(e)]
        if re.search(_ERRO_TEMPO, str(e)):
            resultado['erro_oracle'] = MSG_ORACLE_BLOQUEADO
        return False, None  # nada foi gravado; controle continua aberto
    con.commit()  # tudo deu certo -- lote(s) e demanda(s) juntos
    linhas_por_mvd = {row.MOV_IN_SEQUENCIA: row for row in demandas}
    dem_ok, ok_dem, erros_dem = [], 0, []
    for r in resultados_demanda:
        mensagem = r.get('mensagem')
        if mensagem in ('Ok', 'Cancelada', 'Ja cancelada no local'):
            if mensagem == 'Ok' and r.get('mvd') in linhas_por_mvd:
                dem_ok.append(linhas_por_mvd[r.get('mvd')])
            ok_dem += 1
        else:
            erros_dem.append(f"Demanda mvd={r.get('mvd')}: {r.get('detalhe', mensagem)}")
    erro_conf = _confirmar_e_carimbar(con, [row for row, _resp in lotes_gravados], dem_ok)
    if erro_conf:
        resultado['erro'] = 1
        resultado['erro_oracle'] = erro_conf
        return False, None
    apt_gravado = lotes_gravados[0][1][0]['sequencia'] if lotes_gravados else None
    if apt_gravado and controle and controle.APT_IN_SEQUENCIA != apt_gravado:
        controle.APT_IN_SEQUENCIA = apt_gravado
        controle.save(update_fields=['APT_IN_SEQUENCIA'])
    resultado.update({'ok': len(lotes_gravados) + ok_dem, 'erro': len(erros_dem), 'erros': erros_dem})
    return True, apt_gravado


def verificar_ctl_integrado(con, controle):
    """Copia do NMV/MP. So leitura. Antes de efetivar: nada 'A' no app; todo 'I' esta no Oracle pela
    chave exata; o Oracle nao tem item deste CTL cancelado/inexistente no app; um unico apontamento
    ABERTO. Devolve (apt_in_sequencia aberto ou None, None) ou (None, mensagem).
    AJUSTE 2026-10-20 (particularidade PRODUCAO): apontamento ja efetivado ('E') no Mega nao entra na
    regra de "um apontamento so" -- o botao pode efetivar no meio do dia e o operador seguir
    apontando no mesmo CTL (novo apontamento aberto no Mega); o fechamento efetiva o que estiver aberto."""
    from apontamento.apontamento import itens_do_ctl_no_oracle, _apt_ch_status
    ctl = controle.CTL_IN_CODIGO
    lotes = list(Apt_ApontaOrdem.objects.filter(CTL_IN_CODIGO=ctl).values_list(
        'FIL_IN_CODIGO', 'ORD_IN_CODIGO', 'APT_IN_SEQUENCIA', 'APT_CH_STATUS'))
    dems = list(Apt_Pro_Demandas.objects.filter(CTL_IN_CODIGO=ctl).values_list(
        'FIL_IN_CODIGO', 'ORD_IN_CODIGO', 'MOV_IN_SEQUENCIA', 'MOV_ST_STATUS'))
    problemas = []
    pend_l = sorted(s for _f, _o, s, st in lotes if st == 'A')
    pend_d = sorted(s for _f, _o, s, st in dems if st == 'A')
    if pend_l:
        problemas.append(f'lote(s) pendente(s) no app (não gravado(s) no Mega): {pend_l}')
    if pend_d:
        problemas.append(f'demanda(s) pendente(s) no app (não gravada(s) no Mega): {pend_d}')
    pares = {(int(f), int(o)) for f, o, _s, _st in lotes + dems}
    if controle.FIL_IN_CODIGO and controle.ORD_IN_CODIGO:
        pares.add((int(controle.FIL_IN_CODIGO), int(controle.ORD_IN_CODIGO)))
    ora_l, ora_d = {}, {}
    for fil, ord_ in pares:
        itens = itens_do_ctl_no_oracle(con, fil, ord_, ctl)
        ora_l.update(itens['lotes'])
        ora_d.update(itens['demandas'])
    i_l = {int(s) for _f, _o, s, st in lotes if st == 'I'}
    i_d = {int(s) for _f, _o, s, st in dems if st == 'I'}
    ativos_l = {int(s) for _f, _o, s, st in lotes if st != 'C'}
    ativos_d = {int(s) for _f, _o, s, st in dems if st != 'C'}
    if i_l - set(ora_l):
        problemas.append(f'lote(s) integrado(s) no app sem registro no Mega: {sorted(i_l - set(ora_l))}')
    if i_d - set(ora_d):
        problemas.append(f'demanda(s) integrada(s) no app sem registro no Mega: {sorted(i_d - set(ora_d))}')
    if set(ora_l) - ativos_l:
        problemas.append(f'lote(s) no Mega cancelado(s) ou inexistente(s) no app: {sorted(set(ora_l) - ativos_l)}')
    if set(ora_d) - ativos_d:
        problemas.append(f'demanda(s) no Mega cancelada(s) ou inexistente(s) no app: '
                         f'{sorted(set(ora_d) - ativos_d)}')
    apts = sorted(set(ora_l.values()) | set(ora_d.values()))
    with con.cursor() as cur:
        abertos = [a for a in apts if _apt_ch_status(cur, a) == 'A']
    if len(abertos) > 1:
        problemas.append(f'itens do CTL em mais de um apontamento aberto no Mega: {abertos}')
    if problemas:
        return None, (f'Apontamento não efetivado: o CTL {ctl} não está totalmente integrado -- '
                      + '; '.join(problemas) + '. Conferir antes de efetivar.')
    return (abertos[0] if abertos else None), None


def _efetivar(con, v_session, controle, ctl_in_codigo, apt_in_sequencia, data_apontamento, resultado):
    """Item 3 do fluxo do MP: p_efetivaapontamento no apontamento ABERTO do CTL (conferido antes por
    verificar_ctl_integrado). Sem apontamento aberto: nada a efetivar."""
    from apontamento.apontamento import efetivar_apontamento_oracle
    if apt_in_sequencia and controle:
        usuario_efetivou = v_session.get('usuario') or controle.CTL_ST_USUARIO
        msg_efetivar, efetivado = efetivar_apontamento_oracle(
            apt_in_sequencia, usuario_efetivou, controle.FIL_IN_CODIGO, conexao=con,
            data_apontamento=data_apontamento)
        resultado['msg_efetivar'] = msg_efetivar
        resultado['efetivado_oracle'] = efetivado
        resultado['apt_in_sequencia'] = apt_in_sequencia
    else:
        # nada aberto no Oracle para esse controle (sem producao ou ja efetivado): nada a efetivar
        resultado['efetivado_oracle'] = True


def _gravar_e_efetivar_controle(v_session, data_apontamento, resultado):
    """Itens 1, 2 e 3 do fluxo do MP (gravar tudo ou nada, marcar 'I', efetivar), sem o
    encerramento do controle. AJUSTE 2026-10-20: conexao testada e CTL inteiro conferido."""
    ctl_in_codigo = v_session.get('ctl_in_codigo')
    if not ctl_in_codigo:
        resultado['erro_oracle'] = 'Controle (CTL_IN_CODIGO) não informado.'
        return resultado

    from apontamento.models import Apt_Controle
    controle = Apt_Controle.objects.filter(CTL_IN_CODIGO=ctl_in_codigo).first()
    if not controle:
        resultado['erro_oracle'] = f'Controle {ctl_in_codigo} não encontrado no app.'
        return resultado

    lotes, demandas = _pendentes(ctl_in_codigo)
    con, erro = abrir_conexao_oracle_testada()
    if erro:
        resultado['erro_oracle'] = erro
        return resultado
    with con:
        if lotes or demandas:
            gravou, _apt = _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado)
            if not gravou:
                return resultado
        # Sempre confere e tenta efetivar (cobre o retry depois de um efetivar que falhou)
        apt_in_sequencia, erro_ctl = verificar_ctl_integrado(con, controle)
        if erro_ctl:
            resultado['erro_oracle'] = erro_ctl
            return resultado
        _efetivar(con, v_session, controle, ctl_in_codigo, apt_in_sequencia, data_apontamento, resultado)
    return resultado


# ---------------------------------------------------------------------------
# AJUSTE 2026-10-20: rotina UNICA do "Efetivar Apontamento" -- decisao do usuario: uma rotina so,
# cada forma de efetivar e uma ATIVIDADE numerada. Nova forma = nova linha em ATIVIDADES.
ATIVIDADE_DUAS_ETAPAS = 1
ATIVIDADE_ETAPA_UNICA = 2
ATIVIDADE_CRON = 3  # AJUSTE 2026-10-20: integracao pelo cron (api_producao), como o NMV/MP

# Chaves por atividade (liga/desliga por commit + deploy)
BOTAO_EFETIVAR_TODAS_OPS = True  # atividade 1: botao da manutencao liberado para todas as OPs
# atividade 3: cron grava direto nas tabelas do Oracle (False = api_producao volta para as procedures)
CRON_GRAVA_ORACLE_DIRETO = True

ATIVIDADES = {
    ATIVIDADE_DUAS_ETAPAS: {
        'nome': 'Efetivar apontamento em duas etapas', 'quem': 'botão Efetivar Apontamento (Manutenção)',
        # etapa 1: grava os pendentes ('A') no Oracle (tudo ou nada) e marca 'I' -- nao efetiva;
        # etapa 2: sem pendencia no app e com apontamento aberto no Mega, efetiva com a data da tela
        #          de confirmacao (editavel). Nao encerra o controle.
        'etapas': (1, 2), 'chave': 'BOTAO_EFETIVAR_TODAS_OPS'},
    ATIVIDADE_ETAPA_UNICA: {
        'nome': 'Efetivar apontamento em etapa única', 'quem': 'Fechamento diário',
        # etapa unica: grava os pendentes e efetiva na mesma chamada, com a data da tela do fechamento
        # (FEC_DT_DATA + hora fim). Quem fecha o controle e o Fechamento, so se tudo deu certo.
        'etapas': (1,), 'chave': 'FECHAMENTO_GRAVA_ORACLE'},
    ATIVIDADE_CRON: {
        'nome': 'Integrar apontamento pelo cron', 'quem': 'api_producao (cron)',
        # etapa unica: grava os pendentes ('A') de cada CTL aberto direto nas tabelas do Oracle (tudo
        # ou nada por CTL, mesmas protecoes); NAO efetiva e NAO encerra o CTL (como o NMV/MP).
        'etapas': (1,), 'chave': 'CRON_GRAVA_ORACLE_DIRETO'},
}

MSG_PENDENTE = ('Ainda há lote(s)/demanda(s) pendente(s) no app. Clique em Efetivar Apontamento para '
                'gravar no Oracle antes de efetivar.')
MSG_NADA_ABERTO = 'Nenhum apontamento aberto no Mega para este controle. Nada a efetivar.'
MSG_SEM_CONTROLE = 'Controle não encontrado na sessão. Favor logar na ordem.'


def atividade_ligada(atividade):
    info = ATIVIDADES.get(atividade)
    return bool(info and globals().get(info['chave']))


def _novo_resultado(ctl_in_codigo, atividade=None, etapa=None):
    return {'ctl_in_codigo': ctl_in_codigo, 'ok': 0, 'erro': 0, 'erros': [], 'pendentes': 0,
            'msg_efetivar': None, 'efetivado_oracle': False, 'erro_oracle': None, 'apt_in_sequencia': None,
            'atividade': atividade, 'etapa': etapa}


def efetivar_apontamento(v_session, atividade, etapa=1, data_apontamento=None):
    """Rotina unica do Efetivar Apontamento. atividade/etapa conforme ATIVIDADES. Nunca levanta
    excecao: erro do Oracle vira resultado['erro_oracle'] (o controle continua aberto pra tentar de
    novo). Devolve o dict de resultado (com 'atividade' e 'etapa')."""
    ctl_in_codigo = v_session.get('ctl_in_codigo')
    resultado = _novo_resultado(ctl_in_codigo, atividade, etapa)
    rotulo = f'[Atividade {atividade} - etapa {etapa}]'
    info = ATIVIDADES.get(atividade)
    if info is None or etapa not in info['etapas']:
        resultado['erro_oracle'] = f'{rotulo} atividade/etapa inexistente. Nada foi gravado.'
        return resultado
    if not atividade_ligada(atividade):
        resultado['erro_oracle'] = f"{info['nome']} desligada ({info['chave']}). Nada foi gravado."
        return resultado
    try:
        if atividade == ATIVIDADE_ETAPA_UNICA:
            _gravar_e_efetivar_controle(v_session, data_apontamento, resultado)
        elif not ctl_in_codigo:
            resultado['erro_oracle'] = MSG_SEM_CONTROLE
        elif atividade == ATIVIDADE_CRON or etapa == 1:
            _etapa_gravar(v_session, ctl_in_codigo, resultado)
        else:
            _etapa_efetivar(v_session, ctl_in_codigo, data_apontamento, resultado)
    except Exception as e:
        import traceback
        print(f'ERRO EFETIVAR APONTAMENTO {rotulo}:', traceback.format_exc())
        resultado['erro_oracle'] = str(e)
    return resultado


def _etapa_gravar(v_session, ctl_in_codigo, resultado):
    """Atividade 1, etapa 1: grava no Oracle o que estiver pendente ('A') no controle. Nao efetiva.
    resultado['pendentes'] = 0 quando nao havia nada a gravar (proximo passo: etapa 2)."""
    from apontamento.models import Apt_Controle
    controle = Apt_Controle.objects.filter(CTL_IN_CODIGO=ctl_in_codigo).first()
    lotes, demandas = _pendentes(ctl_in_codigo)
    resultado['pendentes'] = len(lotes) + len(demandas)
    if not resultado['pendentes']:
        return
    # AJUSTE 2026-10-20: conexao testada antes de gravar (protecoes do NMV)
    con, erro = abrir_conexao_oracle_testada()
    if erro:
        resultado['erro_oracle'] = erro
        return
    with con:
        _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado)


def _etapa_efetivar(v_session, ctl_in_codigo, data_apontamento, resultado):
    """Atividade 1, etapa 2: confere o CTL inteiro (app x Mega) e efetiva o apontamento aberto,
    na mesma conexao testada."""
    from apontamento.models import Apt_Controle
    controle = Apt_Controle.objects.filter(CTL_IN_CODIGO=ctl_in_codigo).first()
    if not controle:
        resultado['erro_oracle'] = 'Controle não encontrado no app.'
        return
    if any(_pendentes(ctl_in_codigo)):
        resultado['erro_oracle'] = MSG_PENDENTE
        return
    con, erro = abrir_conexao_oracle_testada()
    if erro:
        resultado['erro_oracle'] = erro.replace('gravado', 'efetivado')
        return
    with con:
        apt_in_sequencia, erro_ctl = verificar_ctl_integrado(con, controle)
        if erro_ctl or not apt_in_sequencia:
            resultado['erro_oracle'] = erro_ctl or MSG_NADA_ABERTO
            return
        _efetivar(con, v_session, controle, ctl_in_codigo, apt_in_sequencia, data_apontamento, resultado)


def conferir_controle(v_session):
    """Antes da tela da data (atividade 1, etapa 2): nada pendente no app, CTL inteiro conferido
    (app x Mega, como o NMV) e apontamento aberto no Mega. Devolve {'erro': texto ou None,
    'apt_in_sequencia': ...}. So leitura."""
    ctl_in_codigo = v_session.get('ctl_in_codigo')
    try:
        if not ctl_in_codigo:
            return {'erro': MSG_SEM_CONTROLE, 'apt_in_sequencia': None}
        if any(_pendentes(ctl_in_codigo)):
            return {'erro': MSG_PENDENTE, 'apt_in_sequencia': None}
        from apontamento.models import Apt_Controle
        controle = Apt_Controle.objects.filter(CTL_IN_CODIGO=ctl_in_codigo).first()
        if not controle:
            return {'erro': 'Controle não encontrado no app.', 'apt_in_sequencia': None}
        con, erro = abrir_conexao_oracle_testada()
        if erro:
            return {'erro': erro.replace('gravado', 'efetivado'), 'apt_in_sequencia': None}
        with con:
            apt_in_sequencia, erro_ctl = verificar_ctl_integrado(con, controle)
        if erro_ctl:
            return {'erro': erro_ctl, 'apt_in_sequencia': None}
        if not apt_in_sequencia:
            return {'erro': MSG_NADA_ABERTO, 'apt_in_sequencia': None}
        return {'erro': None, 'apt_in_sequencia': apt_in_sequencia}
    except Exception as e:
        return {'erro': f'Oracle: {e}', 'apt_in_sequencia': None}


# Atalhos (mesmo comportamento de antes, agora pela rotina unica)
def gravar_controle(v_session):
    return efetivar_apontamento(v_session, ATIVIDADE_DUAS_ETAPAS, 1)


def efetivar_controle(v_session, data_apontamento):
    return efetivar_apontamento(v_session, ATIVIDADE_DUAS_ETAPAS, 2, data_apontamento)
