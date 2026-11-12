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

import os
from contextlib import ExitStack, contextmanager, nullcontext
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


def validar_antes_de_gravar(con, controle, demandas):
    """AJUSTE 2026-11-11 (JPC): copiado do ZK (decisao do usuario) -- PRIMEIRO as validacoes, so depois a
    gravacao. SOMENTE LEITURA: confere no Mega TODOS os lotes das demandas pendentes do CTL (mesmas fontes da
    gravacao) e devolve os avisos agrupados pelo apontamento de origem do lote (caso ZK OP 3462: 11 lotes da
    OP 3463 com o apontamento 441606 aberto no Mega). Lista vazia = pode seguir. Nunca levanta excecao:
    falha aqui devolve [] e a gravacao (tudo ou nada) continua validando cada demanda."""
    try:
        from apontamento.apontamento import lotes_demanda_nao_encontrados, origem_lote_oracle
        demandas = [d for d in demandas if d.PRO_ST_LOTE not in (None, '', '*')]
        if not controle or not demandas:
            return []
        faltando = set(lotes_demanda_nao_encontrados(controle.FIL_IN_CODIGO, controle.ORD_IN_CODIGO,
                                                     [str(d.PRO_ST_LOTE) for d in demandas], con))
        grupos = {}  # origem (ord, apt, status) ou None -> [lotes]
        with con.cursor() as cur:
            for lote in sorted(faltando):
                grupos.setdefault(origem_lote_oracle(cur, lote), []).append(lote)
        avisos = []
        for origem, lotes in sorted(grupos.items(), key=lambda g: str(g[0])):
            qtd = f"{len(lotes)} lote(s): {', '.join(lotes)}"
            if origem and origem[2] == 'A':
                avisos.append(f"Para conseguir apontar a OP {controle.ORD_IN_CODIGO}, alguém precisa efetivar no "
                              f"Mega o apontamento {origem[1]} da OP {origem[0]} ({qtd}).")
            elif origem:
                avisos.append(f"Lotes fora do estoque do Mega, produzidos na OP {origem[0]} (apontamento "
                              f"{origem[1]}, situação {origem[2]} no Mega) -- verifique no Mega ({qtd}).")
            else:
                avisos.append(f"Lotes que não estão no estoque do Mega nem em nenhum apontamento -- confira se a "
                              f"etiqueta lida está correta e se o lote já foi apontado ({qtd}).")
        return avisos
    except Exception:
        import traceback
        print(f'ERRO VALIDAR ANTES DE GRAVAR CTL {getattr(controle, "CTL_IN_CODIGO", None)}:',
              traceback.format_exc())
        return []


import tempfile
TRAVA_CTL = os.path.join(tempfile.gettempdir(), 'producao_ctl_{ctl}.lock')  # /tmp no servidor
MSG_EM_INTEGRACAO = ('O controle {ctl} já está sendo gravado no Mega por outro processo (outro clique ou a '
                     'integração automática). Nada foi feito agora -- aguarde alguns segundos e tente novamente.')


@contextmanager
def _trava_ctl(ctl_in_codigo):
    """AJUSTE 2026-11-11 (JPC): copiado do ZK/NMV (7c035b0, OP 562: duplo clique criou apontamento duplicado) --
    trava por CTL entre processos (gunicorn = botao, cron = api_producao). Sem esperar: se outro processo esta
    gravando o mesmo CTL, devolve False e quem chamou desiste com aviso. O arquivo e aberto so para leitura (flock
    funciona assim), entao a permissao de quem o criou nao atrapalha o outro usuario; O_CREAT so quando nao
    existe (fs.protected_regular no /tmp). Sem fcntl (Windows, desenvolvimento) nao trava."""
    try:
        import fcntl
    except ImportError:
        yield True
        return
    caminho = TRAVA_CTL.format(ctl=int(ctl_in_codigo))
    try:
        try:
            fd = os.open(caminho, os.O_RDONLY)
        except FileNotFoundError:
            fd = os.open(caminho, os.O_RDONLY | os.O_CREAT, 0o644)
    except OSError:
        # a trava nunca pode travar o fluxo por falha dela mesma (decisao do usuario): segue sem trava, com log
        import traceback
        print('AVISO TRAVA CTL indisponivel (segue sem trava):', caminho, traceback.format_exc())
        yield True
        return
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def operador_sem_permissao(con, v_session, controle):
    """AJUSTE 2026-11-11 (JPC): igual ao MP (8c07346, ordem 69205) -- falta de permissao do operador aparece ANTES
    de gravar (antes: gravava e so no efetivar acusava 'usuario nao encontrado'). Mesmo operador/filial que o
    efetivar usa (quem esta na sessao; senao quem abriu o CTL). So leitura. Devolve a mensagem ou None."""
    if not controle:
        return None
    from apontamento.apontamento import operador_tem_permissao
    usuario = v_session.get('usuario') or controle.CTL_ST_USUARIO
    if operador_tem_permissao(con, usuario, controle.FIL_IN_CODIGO):
        return None
    return (f'Operador {usuario} sem permissão no Mega para efetivar apontamento (filial '
            f'{controle.FIL_IN_CODIGO}): não tem grupo de usuário cadastrado. Nada foi gravado -- '
            f'solicite a liberação e tente novamente.')


def _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado, conferir_operador=False):
    """Itens 1 e 2 do fluxo do MP: grava tudo ou nada e marca 'I'. Devolve (gravou, apt_in_sequencia).
    AJUSTE 2026-10-20: separado do _gravar_e_efetivar_controle para o botao Efetivar Apontamento.
    AJUSTE 2026-10-20 (protecoes do NMV): gravacao com limite de tempo; 'I' so depois de reler no
    Oracle pela chave exata. Faltou algo: nada e marcado (o retry nao regrava o que ja esta la).
    AJUSTE 2026-11-11 (JPC): protecoes do MP/NMV/ZK -- trava por CTL (outro processo gravando o mesmo CTL: nada e
    feito), permissao do operador antes de gravar (conferir_operador: botao e fechamento, que efetivam; o cron
    nao efetiva) e reserva sem espera das linhas da ordem no Mega (bloqueada: aviso na hora, nada gravado)."""
    ctl = getattr(controle, 'CTL_IN_CODIGO', None) or v_session.get('ctl_in_codigo')
    if not ctl:
        return _gravar_pendentes_sem_trava(con, v_session, controle, lotes, demandas, resultado, conferir_operador)
    with _trava_ctl(ctl) as livre:
        if not livre:
            resultado['erro'] = 1
            resultado['erro_oracle'] = MSG_EM_INTEGRACAO.format(ctl=ctl)
            return False, None
        return _gravar_pendentes_sem_trava(con, v_session, controle, lotes, demandas, resultado, conferir_operador)


def _gravar_pendentes_sem_trava(con, v_session, controle, lotes, demandas, resultado, conferir_operador):
    import re
    from apontamento.apontamento import TabelaBloqueada, reservar_para_gravacao
    lotes, demandas = list(lotes), list(demandas)
    if conferir_operador:
        erro_operador = operador_sem_permissao(con, v_session, controle)
        if erro_operador:
            resultado['erro'] = 1
            resultado['erro_oracle'] = erro_operador
            return False, None
    # AJUSTE 2026-11-11 (JPC): modelo ZK -- valida os lotes das demandas no Mega antes de gravar; com aviso,
    # para e nada e gravado (o aviso diz o que fazer, ex.: efetivar o apontamento de origem do lote)
    avisos = validar_antes_de_gravar(con, controle, demandas)
    if avisos:
        resultado['erro'] = len(avisos)
        resultado['erro_oracle'] = 'Nada foi gravado. ' + ' '.join(avisos)
        return False, None
    try:
        con.call_timeout = GRAVACAO_TIMEOUT_MS
        if controle and (lotes or demandas):
            reservar_para_gravacao(con, controle.FIL_IN_CODIGO, controle.ORD_IN_CODIGO)
        lotes_gravados, resultados_demanda = _gravar_tudo_ou_nada(con, v_session, lotes, demandas)
        con.call_timeout = 0
    except TabelaBloqueada as e:
        try:
            con.rollback()
        except Exception:
            pass
        con.call_timeout = 0
        resultado['erro'] = 1
        resultado['erro_oracle'] = str(e)
        return False, None
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


def alinhar_centro_do_apontamento(con, apt_in_sequencia):
    """AJUSTE 2026-11-11 (JPC): copiado do NMV -- antes da procedure, centro/maquina do apontamento
    conferidos pela programacao da OP no Mega (apontamento.alinhar_centro_programacao). Commita o ajuste
    (a procedure e transacao autonoma e so ve o que ja foi commitado). Nunca levanta excecao.
    Devolve (aviso ou None, erro ou None)."""
    from apontamento.apontamento import alinhar_centro_programacao
    try:
        r = alinhar_centro_programacao(con, apt_in_sequencia)
        if r['erro']:
            con.rollback()
            return None, r['erro']
        if r['aviso']:
            con.commit()
            print(f'CENTRO APT {apt_in_sequencia}: {r["aviso"]}')
        return r['aviso'], None
    except Exception as e:
        import traceback
        print('ERRO ALINHAR CENTRO (excecao):', traceback.format_exc())
        try:
            con.rollback()
        except Exception:
            pass
        return None, f'Erro ao conferir o centro do apontamento pela programação ({e}). Nada foi efetivado.'


def _efetivar(con, v_session, controle, ctl_in_codigo, apt_in_sequencia, data_apontamento, resultado):
    """Item 3 do fluxo do MP: p_efetivaapontamento no apontamento ABERTO do CTL (conferido antes por
    verificar_ctl_integrado). Sem apontamento aberto: nada a efetivar."""
    from apontamento.apontamento import efetivar_apontamento_oracle
    if apt_in_sequencia and controle:
        # AJUSTE 2026-11-11 (JPC): modelo NMV -- centro/maquina pela programacao da OP antes da procedure
        aviso_centro, erro_centro = alinhar_centro_do_apontamento(con, apt_in_sequencia)
        if erro_centro:
            resultado['erro_oracle'] = erro_centro
            return
        resultado['aviso_centro'] = aviso_centro
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
            gravou, _apt = _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado,
                                             conferir_operador=True)  # AJUSTE 2026-11-11: fechamento efetiva
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
            'aviso_centro': None,  # AJUSTE 2026-11-11: centro/maquina corrigidos pela programacao da OP
            'atividade': atividade, 'etapa': etapa}


# ---------------------------------------------------------------------------
# AJUSTE 2026-11-11 (JPC): decisao do usuario -- LOG PROPRIO DA INTEGRACAO para monitorar erros: logs/integracao.log
# (rotacionado: 5 MB x 10), uma linha por evento (gravar/efetivar pela rotina unica -- botao, fechamento e cron --,
# cancelar, centro corrigido, CTL novo aberto), com data, CTL, OP, operador, resultado e erro. Nunca levanta excecao:
# falha no log nao interrompe nada.
# ---------------------------------------------------------------------------
LOG_INTEGRACAO_MAX_BYTES = 5 * 1024 * 1024
LOG_INTEGRACAO_ARQUIVOS = 10


def _rodando_testes():
    """manage.py test: o log real nao recebe eventos de teste (validacao de 11/11 no servidor: a bateria escreveu
    52 linhas de teste no logs/integracao.log de producao)."""
    import sys
    return len(sys.argv) > 1 and sys.argv[1] == 'test'


def _logger_integracao():
    import logging
    logger = logging.getLogger('producao.integracao')
    if not logger.handlers:
        logger.propagate = False
        logger.setLevel(logging.INFO)
        if _rodando_testes():
            logger.addHandler(logging.NullHandler())
            return logger
        from logging.handlers import RotatingFileHandler
        from django.conf import settings

        class _HandlerCompartilhado(RotatingFileHandler):
            """O cron (api_producao) roda como root e o gunicorn como suporte: todo arquivo do log (inclusive o
            novo, depois do rodizio) fica 666 para os dois gravarem. chmod de arquivo de outro dono falha calado."""
            def _open(self):
                stream = super()._open()
                try:
                    os.chmod(self.baseFilename, 0o666)
                except OSError:
                    pass
                return stream

        pasta = os.path.join(str(settings.BASE_DIR), 'logs')
        os.makedirs(pasta, exist_ok=True)
        try:
            os.chmod(pasta, 0o777)
        except OSError:
            pass
        handler = _HandlerCompartilhado(os.path.join(pasta, 'integracao.log'), maxBytes=LOG_INTEGRACAO_MAX_BYTES,
                                        backupCount=LOG_INTEGRACAO_ARQUIVOS, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s pid=%(process)d %(message)s'))
        logger.addHandler(handler)
    return logger


def registrar_evento(evento, erro=None, **campos):
    """Uma linha no log da integracao: evento=... campo=valor ... [erro=...]. Com erro, nivel ERROR."""
    try:
        partes = [f'evento={evento}'] + [f'{k}={v}' for k, v in campos.items() if v not in (None, '', [])]
        if erro:
            partes.append(f'erro={" | ".join(erro) if isinstance(erro, (list, tuple)) else erro}')
        texto = ' '.join(str(p).replace('\n', ' ') for p in partes)
        logger = _logger_integracao()
        (logger.error if erro else logger.info)(texto)
    except Exception:
        pass


def _registrar_resultado(v_session, atividade, etapa, resultado):
    erro = resultado.get('erro_oracle') or (resultado.get('erros') if resultado.get('erro') else None)
    if not erro and resultado.get('msg_efetivar') and not resultado.get('efetivado_oracle') and etapa == 2:
        erro = resultado.get('msg_efetivar')
    if not erro and not resultado.get('pendentes') and not resultado.get('ok') and atividade == ATIVIDADE_CRON:
        return  # cron sem nada a gravar: nao polui o log
    registrar_evento('integracao', erro=erro, atividade=atividade, etapa=etapa,
                     ctl=resultado.get('ctl_in_codigo'), op=v_session.get('ordem'),
                     operador=v_session.get('usuario'), pendentes=resultado.get('pendentes'),
                     gravados=resultado.get('ok'), apt=resultado.get('apt_in_sequencia'),
                     efetivado=resultado.get('efetivado_oracle') or None,
                     centro=resultado.get('aviso_centro'),
                     avisos=None if resultado.get('erro') else resultado.get('erros'))


def efetivar_apontamento(v_session, atividade, etapa=1, data_apontamento=None):
    """AJUSTE 2026-11-11 (JPC): casca da rotina unica -- todo resultado vai para o log da integracao."""
    resultado = _efetivar_apontamento_rotina(v_session, atividade, etapa, data_apontamento)
    _registrar_resultado(v_session, atividade, etapa, resultado)
    return resultado


def _efetivar_apontamento_rotina(v_session, atividade, etapa=1, data_apontamento=None):
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
            _etapa_gravar(v_session, ctl_in_codigo, resultado,
                          conferir_operador=atividade != ATIVIDADE_CRON)  # AJUSTE 2026-11-11: cron nao efetiva
        else:
            _etapa_efetivar(v_session, ctl_in_codigo, data_apontamento, resultado)
    except Exception as e:
        import traceback
        print(f'ERRO EFETIVAR APONTAMENTO {rotulo}:', traceback.format_exc())
        resultado['erro_oracle'] = str(e)
    return resultado


def _etapa_gravar(v_session, ctl_in_codigo, resultado, conferir_operador=False):
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
        _gravar_pendentes(con, v_session, controle, lotes, demandas, resultado, conferir_operador)


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


# ---------------------------------------------------------------------------
# AJUSTE 2026-11-11 (JPC): Fase 3 -- cancelamento no modelo ZK (decisoes do usuario): NADA SE APAGA, cancela; os
# registros do app e do Mega ficam ESPELHADOS (mesma informacao): cancelar marca 'C' no app e, se o item ja foi
# integrado ('I'), 'C' no Mega na mesma operacao -- TUDO OU NADA (Mega sem conexao, item ja efetivado ou nao
# localizado: nada muda nos dois lados e a mensagem diz o que fazer). So registros do app (chave exata: filial,
# OP, seq. do app e CTL); o que foi incluido direto no Mega fica so no Mega. Lote cancelado apaga a sub do lote
# (PRO_ORDEMLOTESUB) e demanda cancelada recalcula o empenho (APT_APONTADEMANDA), como no ZK.
# ---------------------------------------------------------------------------
_TAB_LOCAL_CANC = {'lote': (Apt_ApontaOrdem, 'APT_IN_SEQUENCIA', 'APT_CH_STATUS'),
                   'demanda': (Apt_Pro_Demandas, 'MOV_IN_SEQUENCIA', 'MOV_ST_STATUS')}
_NOME_TIPO = {'lote': 'Lote', 'demanda': 'Demanda'}
MSG_CANC_SEM_CONEXAO = 'Sem conexão com o Mega. Nada foi cancelado. Tente novamente em instantes.'
MSG_CANC_NAO_LOCALIZADO = ('{tipo} {seq} não localizado(a) no Mega (CTL {ctl}). Nada foi cancelado '
                           '-- conferir no Mega.')
MSG_CANC_NAO_ABERTO = ('{tipo} {seq} não está aberto(a) no Mega (status {situacao}). Nada foi '
                       'cancelado: cancele o apontamento no Mega e depois refaça o cancelamento aqui.')
MSG_CANC_VARIOS_FORA = '{tipo} {seq} não pertence a esta ordem/filial.'
MSG_CANC_VARIOS_STATUS = '{tipo} {seq} está com status {status} (só A ou I podem ser cancelados).'
MSG_CANC_VARIOS_NADA = 'Nada foi cancelado (nem no Mega, nem no app).'
MSG_CANC_VARIOS_APP_FALHOU = ('Cancelado no Mega, mas falhou ao marcar no app ({erro}). Refaça o cancelamento '
                              '(no Mega já constam cancelados) para acertar o app.')


def itens_selecionados(tipo, pks, fil_in_codigo, ord_in_codigo):
    """Registros do app pelos sequenciais escolhidos, so da OP/filial informada, ordenados pelo sequencial."""
    modelo, col_seq, _col_status = _TAB_LOCAL_CANC[tipo]
    pks = sorted({int(p) for p in pks})
    if not pks:
        return []
    return list(modelo.objects.filter(FIL_IN_CODIGO=fil_in_codigo, ORD_IN_CODIGO=ord_in_codigo,
                                      **{f'{col_seq}__in': pks}).order_by(col_seq))


def _cancelar_selecionados(tipo, pks, fil_in_codigo, ord_in_codigo, conexao=None):
    """Cancela um ou varios lotes/demandas, TUDO OU NADA. Nunca levanta excecao. Ordem: confere no app -> Mega
    (FOR UPDATE + cancela, sem commit) -> app (um UPDATE para 'C', numa transacao) com o commit do Mega dentro
    dela: falha no app desfaz o Mega; falha no Mega desfaz o app.
    Devolve {'ok': bool, 'cancelados': [seq], 'no_mega': [seq], 'erros': [texto]}."""
    import re
    from django.db import transaction
    from apontamento.apontamento import cancelar_varios_cur
    modelo, col_seq, col_status = _TAB_LOCAL_CANC[tipo]
    nome = _NOME_TIPO[tipo]
    resultado = {'ok': False, 'cancelados': [], 'no_mega': [], 'erros': []}
    try:
        pks = sorted({int(p) for p in pks})
    except (TypeError, ValueError):
        resultado['erros'] = ['Seleção inválida.', MSG_CANC_VARIOS_NADA]
        return resultado
    if not pks:
        resultado['erros'] = ['Nenhum item selecionado.']
        return resultado
    try:
        regs = {int(getattr(r, col_seq)): r for r in itens_selecionados(tipo, pks, fil_in_codigo, ord_in_codigo)}
    except Exception as e:
        import traceback
        print('ERRO CANCELAR SELECIONADOS:', tipo, pks, traceback.format_exc())
        resultado['erros'] = [f'Erro ao cancelar ({e}).', MSG_CANC_VARIOS_NADA]
        return resultado
    erros = [MSG_CANC_VARIOS_FORA.format(tipo=nome, seq=p) for p in pks if p not in regs]
    erros += [MSG_CANC_VARIOS_STATUS.format(tipo=nome, seq=p, status=getattr(r, col_status))
              for p, r in regs.items() if getattr(r, col_status) not in ('A', 'I')]
    integrados = [r for p, r in sorted(regs.items()) if getattr(r, col_status) == 'I']
    erros += [MSG_CANC_NAO_LOCALIZADO.format(tipo=nome, seq=getattr(r, col_seq), ctl=None)
              for r in integrados if r.CTL_IN_CODIGO is None]
    if erros:
        resultado['erros'] = erros + [MSG_CANC_VARIOS_NADA]
        return resultado
    # AJUSTE 2026-11-11 (JPC): trava por CTL (como o ZK) -- nao cancela enquanto o mesmo CTL esta sendo gravado
    ctls = sorted({int(r.CTL_IN_CODIGO) for r in regs.values() if r.CTL_IN_CODIGO is not None})
    with ExitStack() as travas:
        ocupados = [c for c in ctls if not travas.enter_context(_trava_ctl(c))]
        if ocupados:
            resultado['erros'] = [MSG_EM_INTEGRACAO.format(ctl=c) for c in ocupados] + [MSG_CANC_VARIOS_NADA]
            return resultado
        if not integrados:
            return _marcar_cancelados_app(modelo, col_seq, col_status, pks, fil_in_codigo, ord_in_codigo,
                                          None, resultado)
        # AJUSTE 2026-11-11 (JPC): toda conexao com with (decisao do usuario); conexao de fora nao e fechada aqui
        if conexao is None:
            conexao_aberta, erro = abrir_conexao_oracle_testada()
            if erro:
                resultado['erros'] = [MSG_CANC_SEM_CONEXAO]
                return resultado
            contexto = conexao_aberta
        else:
            contexto = nullcontext(conexao)
        with contexto as con:
            try:
                con.call_timeout = ORACLE_TESTE_TIMEOUT_S * 1000
                with con.cursor() as cur:
                    res = cancelar_varios_cur(cur, tipo, fil_in_codigo, ord_in_codigo,
                                              [(getattr(r, col_seq), r.CTL_IN_CODIGO) for r in integrados])
            except Exception as e:
                import traceback
                print('ERRO CANCELAR SELECIONADOS (MEGA):', tipo, pks, traceback.format_exc())
                try:
                    con.rollback()
                except Exception:
                    pass
                resultado['erros'] = ([MSG_ORACLE_BLOQUEADO.replace('gravado', 'cancelado')]
                                      if re.search(_ERRO_TEMPO, str(e)) else
                                      [f'Erro ao cancelar ({e}).', MSG_CANC_VARIOS_NADA])
                return resultado
            for (seq, ctl), (acao, sits) in sorted(res['problemas'].items()):
                textos = {'tipo': nome, 'seq': seq, 'ctl': ctl}
                erros.append(MSG_CANC_NAO_LOCALIZADO.format(**textos) if acao == 'nao_localizado'
                             else MSG_CANC_NAO_ABERTO.format(situacao=', '.join(sits), **textos))
            if erros:
                con.rollback()
                resultado['erros'] = erros + [MSG_CANC_VARIOS_NADA]
                return resultado
            resultado['no_mega'] = res['cancelados']
            return _marcar_cancelados_app(modelo, col_seq, col_status, pks, fil_in_codigo, ord_in_codigo,
                                          con, resultado)


def cancelar_selecionados(tipo, pks, fil_in_codigo, ord_in_codigo, conexao=None):
    """AJUSTE 2026-11-11 (JPC): casca -- todo cancelamento vai para o log da integracao."""
    resultado = _cancelar_selecionados(tipo, pks, fil_in_codigo, ord_in_codigo, conexao)
    registrar_evento('cancelar', erro=None if resultado['ok'] else resultado['erros'], tipo=tipo,
                     filial=fil_in_codigo, op=ord_in_codigo, seqs=pks, cancelados=resultado['cancelados'],
                     no_mega=resultado['no_mega'])
    return resultado


def _marcar_cancelados_app(modelo, col_seq, col_status, pks, fil_in_codigo, ord_in_codigo, con, resultado):
    """Marca 'C' no app num UPDATE so (transacao); com con (itens integrados), o commit do Mega vai DENTRO da
    transacao do app: falha no app desfaz o Mega; falha no commit do Mega desfaz o app."""
    import re
    from django.db import transaction
    mega_commitado = False
    try:
        with transaction.atomic():
            alterados = modelo.objects.filter(FIL_IN_CODIGO=fil_in_codigo, ORD_IN_CODIGO=ord_in_codigo,
                                              **{f'{col_seq}__in': pks, f'{col_status}__in': ('A', 'I')}
                                              ).update(**{col_status: 'C'})
            if alterados != len(pks):
                raise RuntimeError('status mudou durante o cancelamento (outro usuário/processo)')
            if con is not None:
                con.commit()
                mega_commitado = True
        resultado.update({'ok': True, 'cancelados': pks})
    except Exception as e:
        import traceback
        print('ERRO CANCELAR SELECIONADOS (APP):', pks, traceback.format_exc())
        if con is not None and not mega_commitado:
            try:
                con.rollback()
            except Exception:
                pass
        if mega_commitado:
            resultado['erros'] = [MSG_CANC_VARIOS_APP_FALHOU.format(erro=e)]
        else:
            resultado['no_mega'] = []
            resultado['erros'] = ([MSG_ORACLE_BLOQUEADO.replace('gravado', 'cancelado')]
                                  if re.search(_ERRO_TEMPO, str(e)) else
                                  [f'Erro ao cancelar ({e}).', MSG_CANC_VARIOS_NADA])
    return resultado


# ---------------------------------------------------------------------------
# AJUSTE 2026-11-11 (JPC): Fase 3 -- demandas com lote ja consumido no Mega (modelo ZK, caso OP 3500 / CTL 3196):
# antes de gravar, a tela lista essas demandas; OK confere de novo e cancela (cancelar_selecionados, tudo ou nada).
# ---------------------------------------------------------------------------
MSG_CONSUMIDAS_MUDOU = 'A lista de demandas mudou desde a tela anterior: nada foi cancelado. Confira de novo.'
MSG_CONSUMIDAS_SEM_MEGA = 'Não foi possível conferir as demandas no Mega ({erro}). Nada foi cancelado nem gravado.'


def demandas_lote_consumido(ctl_in_codigo, conexao):
    """SOMENTE LEITURA: demandas pendentes ('A') do CTL cujo lote ja foi todo consumido no Mega. Conexao aberta por
    quem chama. Devolve [{'ctl', 'seq', 'lote', 'item', 'saldo', 'consumo': [{'ord', 'ctl', 'mvd', 'qtd'}]}].
    Levanta excecao em falha (quem chama decide)."""
    from apontamento.apontamento import lotes_consumidos_cur
    demandas = [d for d in Apt_Pro_Demandas.objects.filter(CTL_IN_CODIGO=ctl_in_codigo, MOV_ST_STATUS='A')
                .order_by('MOV_IN_SEQUENCIA') if d.PRO_ST_LOTE not in (None, '', '*')]
    if not demandas:
        return []
    with conexao.cursor() as cur:
        consumidos = lotes_consumidos_cur(cur, [d.PRO_ST_LOTE for d in demandas])
    return [{'ctl': d.CTL_IN_CODIGO, 'seq': d.MOV_IN_SEQUENCIA, 'lote': d.PRO_ST_LOTE,
             'item': d.PRO_IN_CODIGO or consumidos[str(d.PRO_ST_LOTE)]['pro'],
             'saldo': consumidos[str(d.PRO_ST_LOTE)]['saldo'],
             'consumo': [{'ord': o, 'ctl': c, 'mvd': m, 'qtd': q}
                         for o, c, m, q in consumidos[str(d.PRO_ST_LOTE)]['consumo']]}
            for d in demandas if str(d.PRO_ST_LOTE) in consumidos]


def conferir_lotes_consumidos(ctl_in_codigo):
    """SOMENTE LEITURA. Devolve (lista, erro). Falha (ex.: Oracle fora): ([], texto) -- a gravacao segue como antes
    (continua tudo ou nada), nada trava."""
    try:
        con, erro = abrir_conexao_oracle_testada()
        if erro:
            return [], erro
        with con:
            return demandas_lote_consumido(ctl_in_codigo, con), None
    except Exception as e:
        import traceback
        print('ERRO CONFERIR LOTES CONSUMIDOS CTL', ctl_in_codigo, traceback.format_exc())
        return [], str(e)


def cancelar_demandas_consumidas(ctl_in_codigo, fil_in_codigo, ord_in_codigo, seqs):
    """OK da tela de aviso: confere de novo no Mega; se a lista mudou (ou nao deu para conferir), nada e cancelado.
    Senao cancela essas demandas (cancelar_selecionados, tudo ou nada).
    Devolve {'ok': bool, 'cancelados': [seq], 'consumidas': lista atual, 'erros': [texto]}."""
    try:
        confirmadas = {int(s) for s in seqs}
    except (TypeError, ValueError):
        confirmadas = None
    atual, erro = conferir_lotes_consumidos(ctl_in_codigo)
    if erro:
        return {'ok': False, 'cancelados': [], 'consumidas': atual,
                'erros': [MSG_CONSUMIDAS_SEM_MEGA.format(erro=erro)]}
    if confirmadas != {int(d['seq']) for d in atual}:
        return {'ok': False, 'cancelados': [], 'consumidas': atual, 'erros': [MSG_CONSUMIDAS_MUDOU]}
    if not atual:
        return {'ok': True, 'cancelados': [], 'consumidas': [], 'erros': []}
    res = cancelar_selecionados('demanda', sorted(confirmadas), fil_in_codigo, ord_in_codigo)
    return {'ok': res['ok'], 'cancelados': res['cancelados'], 'consumidas': atual, 'erros': res['erros']}


# ---------------------------------------------------------------------------
# AJUSTE 2026-11-11 (JPC): Fase 3 -- dados da tela "Efetivar no Mega" com as consistencias do ZK.
# ---------------------------------------------------------------------------
def totais_efetivar(lotes, demandas):
    """Totalizador para conferencia (modelo ZK): apontamentos por item + total (PRO_RE_QTDCONV, senao
    ORL_RE_QTDLOTE) e demandas. Cancelados ('C') ficam fora; demanda em 9999 tambem (contada a parte)."""
    from decimal import Decimal

    def _dec(valor):
        return Decimal(str(valor)) if valor not in (None, '') else Decimal('0')
    itens = {}
    for l in lotes:
        if l.APT_CH_STATUS == 'C':
            continue
        qtd = _dec(l.PRO_RE_QTDCONV) if l.PRO_RE_QTDCONV else _dec(l.ORL_RE_QTDLOTE)
        item = itens.setdefault(l.PRO_IN_CODIGO, {'item': l.PRO_IN_CODIGO, 'descricao': l.PRO_ST_DESCRICAO or '',
                                                  'qtd_lotes': 0, 'quantidade': Decimal('0')})
        item['qtd_lotes'] += 1
        item['quantidade'] += qtd
    validas = [_dec(d.PRO_RE_QTDLOTE) for d in demandas if d.MOV_ST_STATUS != 'C']
    somadas = [q for q in validas if q != 9999]
    return {'itens': list(itens.values()),
            'lotes': sum(i['qtd_lotes'] for i in itens.values()),
            'lotes_qtd': sum((i['quantidade'] for i in itens.values()), Decimal('0')),
            'demandas': len(somadas), 'demandas_qtd': sum(somadas, Decimal('0')),
            'demandas_9999': len(validas) - len(somadas)}


def situacao_op_no_mega(fil_in_codigo, ord_in_codigo):
    """Situacao da OP no Mega para o controle vazio. Nunca levanta excecao. Devolve (lista, erro ou None)."""
    try:
        from apontamento.apontamento import situacao_op_no_mega as _situacao
        con, erro = abrir_conexao_oracle_testada()
        if erro:
            return [], erro
        with con:
            with con.cursor() as cur:
                return _situacao(cur, fil_in_codigo, ord_in_codigo), None
    except Exception as e:
        import traceback
        print('ERRO SITUACAO OP NO MEGA:', traceback.format_exc())
        return [], str(e)
