# -*- encoding: utf-8 -*-
# AJUSTE 2026-10-06: copiado do projeto MP (apontamento/apontamento.py) sem mudar regra de
# gravacao. No PRODUCAO e' usado SO pelo fechamento diario (Fechamento em api_view.py), com a
# chave FECHAMENTO_GRAVA_ORACLE; a conexao vem de oracle_connection. - JPC - João Castro
"""
Gravacao direta (SQL puro) do lote de producao nas tabelas Oracle, no lugar da
procedure apt_intprod2.cli_p_lotes_ordem (ETAPA 1: lote).

AJUSTE 2026-09-21: arquivo ISOLADO (apontamento/apontamento.py; importacao:
`from apontamento.apontamento import gravar_lote`) -- nada no projeto importa este
modulo e nenhum fluxo de producao o chama. Nao altera tabelas (sem DDL, sem DELETE): a gravacao
e so INSERT de linhas; o unico UPDATE e o cancelamento de demanda ('A'->'C', ver abaixo).
Tabelas gravadas, na mesma transacao (um unico commit no fim):
  1. APT_APONTAORDEM        (so se nao houver apontamento aberto)
  2. PRO_ORDEMLOTESUB       (so quando o lote e do tipo 'P')
  3. APT_APONTAORDEM_LOTE

FORA DO ESCOPO desta etapa (ficam para depois, hoje feitos so pela procedure):
  - man_pck_ordem.p_abreordem + update de PRO_DEMANDA_DEP (ordem ainda nao 'AB')
  - p_SumarizaLotes
  - p_programacaoordem (origem de APT_MAQ_IN_CODIGO -> parametro opcional)

Retorno de gravar_lote() tem o mesmo formato que o Python de hoje consome
(apt_integrarlote): lista de dict(sequencia, mensagem, mensagem_sub).

ETAPA 2 (2026-09-22): gravar_demanda(), no lugar da procedure
apt_intprod2.p_inseredemanda_lotespro. Recebe uma LISTA de demandas (nao uma
por vez) e grava tudo numa transacao so:
  1. Valida TODAS as linhas primeiro (sem gravar nada) -- qualquer erro aborta
     a lista inteira, nada fica parcialmente gravado.
  2. So depois grava, em bloco (executemany, poucos round-trips):
     a. PRO_ORDEMLOTESUB ... nao, PRO_DEMANDA_DEP (linhas novas de componente
        que ainda nao existe la; so SELECT/INSERT, sem UPDATE -- autorizado
        pelo usuario em 2026-09-21)
     b. APT_APONTADEMANDA_ESTOQUE (uma linha por demanda validada)
     c. APT_APONTADEMANDA (agregado por org/ord/componente/operacao; tenta
        UPDATE pela chave natural e faz INSERT so' onde o UPDATE nao achou
        linha -- mesmo criterio da procedure p_cria_demanda, em 2 passadas
        em lote em vez de round-trip por linha)
  3. Um unico commit no final. Mede o tempo da fase de gravacao
     (time.perf_counter()) e devolve em 'tempo_ms'.

MVS_ST_REFERENCIA (apt_apontademanda_estoque) resolvido com dado real
(est_movsumarizado/est_lotesmovimento); pAPT_RE_QUANTIDADE=9999 tratado como
"saldo total do lote" (confirmado contra a ordem 68783). Demanda ja cancelada
NO LOCAL (mov_st_status='C', campo opcional no payload) nunca e' gravada no
Oracle.

AJUSTE 2026-09-22: FMT_ST_CODIGO/FMT_TAB_IN_CODIGO/FMT_PAD_IN_CODIGO
(apt_apontademanda) ficam SEMPRE em branco no apontamento da demanda --
decisao do usuario: a quantidade ja' vem certa de est_movsumarizado, o
conversor e' do produto apontado (lote), nao da demanda. As funcoes
_buscar_conversor_local/_buscar_fmt_tab_pad (resolvem o conversor via
Apt_ApontaOrdem/apt_itens_ordens local + EST_PROUNI no Oracle, com
desambiguacao por formula quando ha' mais de um conversor no catalogo)
continuam no modulo pra uso futuro, mas NAO sao chamadas aqui.

FORA DO ESCOPO desta etapa (gaps sem fonte confirmada; ficam NULL/None e
marcados no codigo -- nao adivinhar regra de negocio):
  - UN2_ST_UNIDADE (apt_apontademanda): sem origem confirmada.
  - Aviso de recebimento (filial 3, cli_aviso_receb_item*) -- nao implementado;
    se a demanda nao resolver produto/almoxarifado/local (nem em
    est_movsumarizado nem em est_lotesmovimento), da' erro em vez de inserir
    uma linha "sem lote" como a procedure faz (v_temlote='N').
"""
from datetime import datetime, date
import json
import time

# AJUSTE 2026-09-21: `insert ... values <record>` da procedure grava TODAS as
# colunas (as nao preenchidas ficam NULL e o DEFAULT da coluna nao vale). Aqui
# essas colunas com DEFAULT entram como NULL explicito para o resultado ser o mesmo.
_NULOS_APT_APONTAORDEM = ('APT_BO_ENCERRA', 'APT_BO_PARCIAL', 'APT_BO_TERMINOMATERIAL',
                          'APT_ST_REFERENCIA')
_NULOS_APT_APONTAORDEM_LOTE = ('APT_CH_IMPRESSO', 'APT_RE_QTDEETIQUETA')


def _abrir_conexao():
    # Import so aqui: importar este modulo nao inicializa o Oracle Client.
    from oracle_connection import getOracleConnection
    con = getOracleConnection()
    if not con:
        raise ConnectionError('Nao foi possivel conectar ao Oracle.')
    return con


def _eh_duplicado(erro):
    """True para ORA-00001 (chave duplicada) -- a procedure trata como 'Ok'."""
    try:
        return erro.args[0].code == 1
    except (AttributeError, IndexError):
        return 'ORA-00001' in str(erro)


def _para_data(valor):
    """'2026-09-21' / '2026/09/21' / '2026-09-21T10:00:00...' -> datetime."""
    if isinstance(valor, (datetime, date)):
        return valor
    texto = str(valor)[:10].replace('/', '-')
    return datetime.strptime(texto, '%Y-%m-%d')


def _insert(cur, tabela, valores, nulos=()):
    colunas = list(valores) + list(nulos)
    marcas = [f':{c}' for c in valores] + ['NULL'] * len(nulos)
    cur.execute(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join(marcas)})",
                valores)


def _dict_linha(cur):
    colunas = [c[0].lower() for c in cur.description]
    linha = cur.fetchone()
    return dict(zip(colunas, linha)) if linha else None


def _normalizar(dados):
    """Mesma conversao de tipos que apt_integrarlote faz antes de chamar a procedure."""
    plf = dados.get('plf_in_sqoperacao')
    return {
        'fil': int(dados['fil_in_codigo']),
        'ord': int(dados['ord_in_codigo']),
        'ctl': int(dados['ctl_in_codigo']),
        'plf': int(plf) if plf is not None else None,
        'dt_apt': _para_data(dados['apt_dt_inclusao']),
        'mvp': int(dados['mvp_in_sequencia']),
        'qtd_unidade': float(dados['apt_re_quantidade']),      # pmvl_re_quantidade
        'qtd_mov': float(dados['apt_re_qtdeconvertida']),      # pmvl_re_quantmov
        'qtd_ref': float(dados['apt_re_qtderefugo']),          # pmvl_re_quantref
        'pro': int(dados['pro_in_codigo']),
        'obs': dados.get('pro_st_obs'),
        'doc_origem': dados.get('pro_st_docorigem'),
        'referencia': dados.get('pro_st_referencia'),
        'destino': dados.get('pro_st_destino'),
        'lote': dados.get('pro_st_lote'),
        'dt_lote': _para_data(dados['apt_dt_lote']),
        'cmaq_st_id': dados.get('cmaq_st_id'),
        'ord_st_id': dados.get('ord_st_id'),
        'pro_st_id': dados.get('pro_st_id'),
        'extenso': dados.get('ord_st_extenso'),
        'fornecedor': dados.get('pro_st_fornecedor'),
        'maq': dados.get('apt_maq_in_codigo'),  # opcional: p_programacaoordem fica p/ depois
    }


def _buscar_ordem(cur, d):
    cur.execute("""SELECT org_tab_in_codigo, org_pad_in_codigo, org_in_codigo, org_tau_st_codigo,
                          ord_tab_in_codigo, ord_seq_in_codigo, ord_in_codigo, fil_in_codigo,
                          tpo_tab_in_codigo, tpo_pad_in_codigo, tpo_st_codigo_tipo
                     FROM pro_ordens
                    WHERE ord_in_codigo = :ord AND fil_in_codigo = :fil
                      AND ord_seq_in_codigo = pck_mega.achapadraodatabela(:fil, 218, SYSDATE)""",
                {'ord': d['ord'], 'fil': d['fil']})
    return _dict_linha(cur)


def _buscar_padroes(cur, fil):
    cur.execute("""SELECT pck_mega.achapadraodatabela(:fil, 204, SYSDATE),
                          pck_mega.achapadraodatabela(:fil, 100, SYSDATE)
                     FROM dual""", {'fil': fil})
    ati_pad, pro_pad = cur.fetchone()
    return {'ati_pad': ati_pad, 'pro_pad': pro_pad}


def _chave_ordem(o):
    return {'org_tab_in_codigo': o['org_tab_in_codigo'], 'org_pad_in_codigo': o['org_pad_in_codigo'],
            'org_in_codigo': o['org_in_codigo'], 'org_tau_st_codigo': o['org_tau_st_codigo'],
            'ord_tab_in_codigo': o['ord_tab_in_codigo'], 'ord_seq_in_codigo': o['ord_seq_in_codigo'],
            'ord_in_codigo': o['ord_in_codigo']}


def _tem_apontamento_aberto(cur, ordem):
    """Equivale a f_valida_apontamento."""
    cur.execute("""SELECT COUNT(*) FROM apt_apontaordem
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND apt_ch_status = 'A'""",
                _chave_ordem(ordem))
    return cur.fetchone()[0] > 0


def _buscar_apontamento_aberto(cur, ordem, plf):
    # AJUSTE 2026-09-21: a procedure fica com a ultima linha de um loop sem ORDER BY;
    # aqui o criterio e explicito: o de maior APT_IN_SEQUENCIA.
    cur.execute("""SELECT apt_in_sequencia, org_tab_in_codigo, org_pad_in_codigo, org_in_codigo,
                          org_tau_st_codigo, ord_tab_in_codigo, ord_seq_in_codigo, ord_in_codigo,
                          fil_in_codigo, plf_in_sqoperacao
                     FROM apt_apontaordem
                    WHERE fil_in_codigo = :fil AND ord_in_codigo = :ord
                      AND (plf_in_sqoperacao = :plf OR :plf IS NULL)
                      AND apt_ch_status = 'A'
                    ORDER BY apt_in_sequencia DESC""",
                {'fil': ordem['fil_in_codigo'], 'ord': ordem['ord_in_codigo'], 'plf': plf})
    return _dict_linha(cur)


def _criar_apontamento(cur, ordem, d, pads):
    """Equivale a apt_inserir_apt (ramo INSERT; o ramo UPDATE da procedure e codigo morto)."""
    plf = d['plf']
    if plf is None and d['extenso']:
        # AJUSTE 2026-09-22 (2): conferido com dado real da ordem 68783
        # (ord_st_extenso = "30200687830500", 14 chars) contra separa_idordem()
        # (api_producao.py, list_ordem=[0,3,10,13]) - o campo plf_in_sqoperacao
        # real e' extenso[10:13] (3 chars: fil[0:3] + ord[3:10] + plf[10:13]),
        # NAO 13 caracteres como o comentario da procedure documentada sugeria
        # (essa "substr(...,11,13)" deve ser de um extenso mais longo, de outro
        # contexto). Usa a MESMA fatia da funcao real ja em uso, nao a formula
        # da procedure.
        plf = int(d['extenso'][10:13])
    cur.execute("""SELECT ati_in_codigoint FROM pro_tipoordens
                    WHERE tpo_tab_in_codigo = :tab AND tpo_pad_in_codigo = :pad
                      AND tpo_st_codigo_tipo = :tipo""",
                {'tab': ordem['tpo_tab_in_codigo'], 'pad': ordem['tpo_pad_in_codigo'],
                 'tipo': ordem['tpo_st_codigo_tipo']})
    linha = cur.fetchone()
    ati_in = linha[0] if linha else None

    valores = dict(_chave_ordem(ordem))
    valores.update({
        'fil_in_codigo': ordem['fil_in_codigo'],
        'ctl_in_codigo': d['ctl'],
        'apt_maq_in_codigo': d['maq'],
        'plf_in_sqoperacao': plf,
        'apt_dt_apontamento': d['dt_apt'],
        'apt_ati_tab_in_codigo': 204,
        'apt_ati_pad_in_codigo': pads['ati_pad'],
        'apt_ati_in_codigo': ati_in,
        'apt_ch_status': 'A',
        'apt_ord_st_extenso': d['extenso'],
    })
    # AJUSTE 2026-09-21: sequencia = max+1 da tabela (igual a procedure, sem sequence).
    # Se outro processo pegar o mesmo numero (ORA-00001), tenta de novo em vez de ignorar.
    for _ in range(3):
        cur.execute("SELECT NVL(MAX(apt_in_sequencia), 0) + 1 FROM apt_apontaordem")
        valores['apt_in_sequencia'] = cur.fetchone()[0]
        try:
            _insert(cur, 'APT_APONTAORDEM', valores, _NULOS_APT_APONTAORDEM)
            break
        except Exception as e:
            if not _eh_duplicado(e):
                raise
    else:
        raise RuntimeError('Nao foi possivel gerar APT_IN_SEQUENCIA para APT_APONTAORDEM.')
    apt = dict(_chave_ordem(ordem))
    apt.update({'apt_in_sequencia': valores['apt_in_sequencia'], 'fil_in_codigo': ordem['fil_in_codigo'],
                'plf_in_sqoperacao': plf})
    return apt


def _lote_ja_integrado(cur, apt, mvp):
    """Equivale a f_valida_intproducao: chave = ordem + mvp_in_sequencia (ctl nao entra)."""
    cur.execute("""SELECT COUNT(*) FROM apt_apontaordem_lote
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND mvp_in_sequencia = :mvp""",
                dict(_chave_ordem(apt), mvp=mvp))
    return cur.fetchone()[0] > 0


def _gravar_dados_lote(cur, cur_local, apt, d, pads):
    # tipo do lote: 'P' = produto da ordem, 'S' = subproduto
    cur.execute("""SELECT 'P' FROM pro_ordens
                    WHERE org_in_codigo = :org AND fil_in_codigo = :fil
                      AND ord_in_codigo = :ord AND pro_in_codigo = :pro""",
                {'org': apt['org_in_codigo'], 'fil': apt['fil_in_codigo'],
                 'ord': apt['ord_in_codigo'], 'pro': d['pro']})
    tipo = 'P' if cur.fetchone() else 'S'

    # referencia: item sem referencia usa '*'; com referencia ela e obrigatoria
    cur.execute("""SELECT NVL(rfc_in_codigo, 0) FROM est_produtos
                    WHERE pro_tab_in_codigo = 100 AND pro_pad_in_codigo = :pad
                      AND pro_in_codigo = :pro""",
                {'pad': pads['pro_pad'], 'pro': d['pro']})
    linha = cur.fetchone()
    rfc = linha[0] if linha else 0
    if rfc == 0:
        referencia = '*'
    else:
        if d['referencia'] is None or d['referencia'] == 'null':
            raise ValueError('e obrigatorio informar as caracteristicas!')
        referencia = d['referencia']

    slote = d['mvp']  # mvp_in_sequencia e obrigatorio (validado em gravar_lote)

    if d['lote'] is None:
        cur.execute("""SELECT IDP.CLI_PCK_ESPECIFICOSMANUF.CUS_F_TABFILSEQLOTE(:org, :fil, 218, :ord)
                         FROM dual""",
                    {'org': apt['org_in_codigo'], 'fil': apt['fil_in_codigo'], 'ord': apt['ord_in_codigo']})
        lote = cur.fetchone()[0]
    else:
        lote = d['lote']

    chave = _chave_ordem(apt)
    if tipo == 'P':
        valores = dict(chave)
        valores.update({'orl_st_lotefabricacao': lote, 'orl_st_slotefabricacao': slote,
                        'orl_st_referencia': referencia, 'orl_re_qtdlote': d['qtd_mov'],
                        'orl_re_qtdrecebida': 0, 'orl_re_qtdrefugada': 0,
                        'orl_re_qtdinterditada': 0, 'orl_ch_origem': 'O'})
        try:
            _insert(cur, 'PRO_ORDEMLOTESUB', valores,
                    ('ORL_ST_REFERENCIAPAI', 'ORL_CH_ORIGEMPAI'))
        except Exception as e:
            if not _eh_duplicado(e):
                raise

    doc = d['doc_origem']
    if doc is not None and len(doc) == 22:
        doc = str(int(doc[8:16]))
    valores = dict(chave)
    valores.update({
        'apt_in_sequencia': apt['apt_in_sequencia'],
        'fil_in_codigo': apt['fil_in_codigo'],
        'ctl_in_codigo': d['ctl'],
        'mvp_in_sequencia': d['mvp'],
        'ord_st_id': d['ord_st_id'],
        'pro_st_id': d['pro_st_id'],
        'cmaq_st_id': d['cmaq_st_id'],
        'orl_st_comprador': d['fornecedor'],
        'orl_doc_origem': doc,
        'orl_re_qtdref': d['qtd_ref'] if d['qtd_ref'] > 0 else 0,
        'apt_ref_in_codigo': 2 if d['qtd_ref'] > 0 else None,
        'orl_st_lotefabricacao': lote,
        'orl_st_slotefabricacao': slote,
        'orl_st_referencia': referencia,
        'pro_tab_in_codigo': 100,
        'pro_pad_in_codigo': pads['pro_pad'],
        'pro_in_codigo': d['pro'],
        'orl_re_qtdlote': d['qtd_mov'],
        'orl_re_unidade': d['qtd_unidade'],
        'orl_st_tipolote': tipo,
        'apt_ch_status': 'A',
        'orl_st_loteobs': d['obs'],
        'ord_st_destino': d['destino'],
        'apt_dt_inclusao': d['dt_lote'],
    })
    # AJUSTE 2026-09-22: FMT_ST_CODIGO NAO pode ficar em branco no apontamento de producao
    # (decisao do usuario) -- resolve pelo proprio lote local (APT_IN_SEQUENCIA = mvp) ou,
    # na falta, pelo catalogo apt_itens_ordens.PRO_ST_CONVERSOR + formula (_conversor_do_lote).
    fmt_st_codigo = _conversor_do_lote(cur_local, d['mvp'])
    nulos_lote = _NULOS_APT_APONTAORDEM_LOTE
    if fmt_st_codigo is not None:
        valores['fmt_st_codigo'] = fmt_st_codigo
    else:
        nulos_lote = _NULOS_APT_APONTAORDEM_LOTE + ('FMT_ST_CODIGO',)
    try:
        _insert(cur, 'APT_APONTAORDEM_LOTE', valores, nulos_lote)
    except Exception as e:
        if not _eh_duplicado(e):
            raise


def _apontamento_do_lote_integrado(cur, ordem, d):
    """Apontamento em que o lote (ordem + mvp) ja foi gravado, com o mesmo ctl; None se o
    lote ja existe sob outro ctl (divergencia -- aparece na conciliacao)."""
    cur.execute("""SELECT apt_in_sequencia, fil_in_codigo FROM apt_apontaordem_lote
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND mvp_in_sequencia = :mvp
                      AND ctl_in_codigo = :ctl
                    ORDER BY apt_in_sequencia FETCH FIRST 1 ROW ONLY""",
                dict(_chave_ordem(ordem), mvp=d['mvp'], ctl=d['ctl']))
    linha = cur.fetchone()
    if linha is None:
        return None
    return dict(_chave_ordem(ordem), apt_in_sequencia=linha[0], fil_in_codigo=linha[1])


def _validar_lote(cur, d):
    """
    AJUSTE 2026-09-23: validacao SOMENTE LEITURA do lote -- mesmas checagens de
    _fluxo_lote que podem abortar (ordem nao encontrada, apontamento aberto mas
    pra operacao diferente), sem criar nem gravar nada. Usada pra validar TODOS os
    lotes/demandas do "Efetivar Apontamento" ANTES de gravar qualquer um (ver
    integracao_apontamento.gravar_e_encerrar_controle) -- decisao do usuario:
    "grava tudo somente se der certo, senao nao grava nada".
    Levanta ValueError com a mesma mensagem que _fluxo_lote levantaria. Devolve
    dict(ja_integrado=bool, precisa_criar_apontamento=bool) so' informativo.
    """
    ordem = _buscar_ordem(cur, d)
    if ordem is None:
        raise ValueError(f"Ordem {d['ord']} (filial {d['fil']}) nao encontrada em PRO_ORDENS.")
    if _lote_ja_integrado(cur, ordem, d['mvp']):
        return {'ja_integrado': True, 'precisa_criar_apontamento': False}
    if _tem_apontamento_aberto(cur, ordem):
        apt = _buscar_apontamento_aberto(cur, ordem, d['plf'])
        if apt is None:
            raise ValueError('Ha apontamento aberto na ordem, mas nao para a operacao informada.')
        return {'ja_integrado': False, 'precisa_criar_apontamento': False}
    return {'ja_integrado': False, 'precisa_criar_apontamento': True}


def _fluxo_lote(cur, cur_local, d):
    ordem = _buscar_ordem(cur, d)
    if ordem is None:
        raise ValueError(f"Ordem {d['ord']} (filial {d['fil']}) nao encontrada em PRO_ORDENS.")
    # AJUSTE 2026-09-21: a procedure cria o apontamento ANTES de checar se o lote ja foi
    # integrado (podia deixar um apontamento vazio duplicado). Aqui a checagem vem primeiro:
    # lote ja integrado => nao grava nem cria nada.
    if _lote_ja_integrado(cur, ordem, d['mvp']):
        return _apontamento_do_lote_integrado(cur, ordem, d)
    pads = _buscar_padroes(cur, d['fil'])
    if _tem_apontamento_aberto(cur, ordem):
        apt = _buscar_apontamento_aberto(cur, ordem, d['plf'])
        if apt is None:
            raise ValueError('Ha apontamento aberto na ordem, mas nao para a operacao informada.')
    else:
        apt = _criar_apontamento(cur, ordem, d, pads)
    _gravar_dados_lote(cur, cur_local, apt, d, pads)
    return apt


def _retorno(cur, apt, d):
    cur.execute("""SELECT apt_in_sequencia FROM apt_apontaordem_lote
                    WHERE org_in_codigo = :org AND fil_in_codigo = :fil
                      AND apt_in_sequencia = :apt AND ctl_in_codigo = :ctl
                      AND mvp_in_sequencia = :mvp""",
                {'org': apt['org_in_codigo'], 'fil': apt['fil_in_codigo'],
                 'apt': apt['apt_in_sequencia'], 'ctl': d['ctl'], 'mvp': d['mvp']})
    return [dict(sequencia=r[0], mensagem='Ok', mensagem_sub='Ok') for r in cur.fetchall()]


def _gravar_lote(con, dados, dry_run=False, auto_commit=True):
    # Import so aqui (igual ao Oracle): nao inicializa o Django DB na importacao do modulo.
    from django.db import connections
    # AJUSTE 2026-09-21: sem ctl o lote nao fecha a sincronia com o local; sem mvp a checagem
    # de duplicidade (ordem + mvp) nao funciona (comparar com NULL nunca casa) -- nao grava.
    for obrigatorio in ('ctl_in_codigo', 'mvp_in_sequencia'):
        if dados.get(obrigatorio) is None:
            return [dict(sequencia=0, mensagem='Erro', mensagem_sub='Erro',
                         detalhe=f'{obrigatorio} e obrigatorio.')]
    d = _normalizar(dados)
    if dry_run:
        # AJUSTE 2026-09-23: so' valida (SELECT), sempre com rollback no final -- usado
        # pra checar TODOS os lotes/demandas do "Efetivar Apontamento" antes de gravar
        # qualquer um (ver integracao_apontamento.gravar_e_encerrar_controle).
        try:
            with con.cursor() as cur:
                plano = _validar_lote(cur, d)
            con.rollback()
            return [dict(mensagem='Ok', mensagem_sub='Ok', **plano)]
        except Exception as e:
            con.rollback()
            return [dict(sequencia=0, mensagem='Erro', mensagem_sub='Erro', detalhe=str(e))]
    try:
        with con.cursor() as cur, connections['default'].cursor() as cur_local:
            apt = _fluxo_lote(cur, cur_local, d)
            # AJUSTE 2026-09-23: auto_commit=False -- usado quando o chamador quer
            # gravar lote(s) + demanda(s) na MESMA transacao (ver
            # gravar_e_encerrar_controle em integracao_apontamento.py), commitando so'
            # se TUDO der certo. O apontamento criado aqui (se nao existia) fica
            # visivel pra demanda DENTRO da mesma transacao mesmo sem commit ainda.
            if auto_commit:
                con.commit()  # unico commit: as 3 tabelas ficam sincronizadas
            return _retorno(cur, apt, d) if apt else []
    except Exception as e:
        con.rollback()
        print(f'Erro ao gravar lote (ordem {dados.get("ord_in_codigo")}): {e}')
        return [dict(sequencia=0, mensagem='Erro', mensagem_sub='Erro', detalhe=str(e))]


def gravar_lote(dados, conexao=None, dry_run=False, auto_commit=True):
    """
    dados: mesmo dict que api_producao.integrador monta (v_dadosProd) e envia hoje
    a apt_intprod2.cli_p_lotes_ordem; chave opcional 'apt_maq_in_codigo'.
    conexao: conexao Oracle aberta (reaproveitada e NAO fechada aqui); se None,
    abre uma propria e fecha ao final.
    dry_run=True: so' valida (SELECT), sem gravar nada, sempre com rollback (ver
    _gravar_lote). Devolve [dict(mensagem='Ok', ja_integrado=bool,
    precisa_criar_apontamento=bool)] se valido, ou [dict(mensagem='Erro', detalhe=...)].
    auto_commit=False: grava de verdade mas NAO commita (caller decide). So' faz
    sentido com conexao explicita.
    """
    if conexao is None:
        with _abrir_conexao() as con:
            return _gravar_lote(con, dados, dry_run=dry_run, auto_commit=auto_commit)
    return _gravar_lote(conexao, dados, dry_run=dry_run, auto_commit=auto_commit)


# ---------------------------------------------------------------------------
# ETAPA 2: demanda (gravar_demanda), no lugar da procedure
# apt_intprod2.p_inseredemanda_lotespro. Ver docstring do modulo.
# ---------------------------------------------------------------------------

def _normalizar_demanda(dados):
    """Mesma conversao de tipos que apt_integrarDemanda faz antes de chamar a procedure."""
    pro = dados.get('pro_in_codigo')
    lote = dados.get('pro_st_lote')
    return {
        'fil': int(dados['fil_in_codigo']),
        'ord': int(dados['ord_in_codigo']),
        'ctl': int(dados['ctl_in_codigo']),
        'plf': int(dados['plf_in_sqoperacao']) if dados.get('plf_in_sqoperacao') is not None else None,
        'dt_apt': _para_data(dados['apt_dt_inclusao']),
        'mvd': int(dados['mvd_in_sequencia']),
        'lote': str(lote) if lote not in (None, '') else '*',
        'qtd': float(dados['pro_re_qtdlote']),
        'cmaq_st_id': dados.get('cmaq_st_id'),
        'ord_st_id': dados.get('ord_st_id'),
        'extenso': dados.get('ord_st_extenso'),
        'pro': int(pro) if pro else 0,   # AJUSTE: 0 = "nao informado", igual ao Python de hoje
    }


def _pads_demanda(cur, fil):
    cur.execute("""SELECT pck_mega.achapadraodatabela(:fil, 100, SYSDATE),
                          pck_mega.achapadraodatabela(:fil, 105, SYSDATE)
                     FROM dual""", {'fil': fil})
    com_pad, alm_pad = cur.fetchone()
    return {'com_pad': com_pad, 'alm_pad': alm_pad}


def _demanda_ja_integrada(cur, apt, d, com_in_codigo):
    """Equivale a f_valida_intdemanda: (apt+lote='*') OU (lote=lote,lote<>'*'), com
    mvd_in_sequencia e com_in_codigo batendo ou nulos no Oracle. So' leitura."""
    cur.execute("""SELECT * FROM apt_apontademanda_estoque
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo
                      AND ((apt_in_sequencia = :apt AND :lote = '*') OR (mvs_st_loteforne = :lote AND :lote <> '*'))
                      AND (mvd_in_sequencia = :mvd OR mvd_in_sequencia IS NULL)
                      AND (com_in_codigo = :com OR com_in_codigo IS NULL)
                    ORDER BY mvd_in_sequencia NULLS LAST FETCH FIRST 1 ROW ONLY""",
                dict(_chave_ordem(apt), apt=apt['apt_in_sequencia'], lote=d['lote'],
                     mvd=d['mvd'], com=com_in_codigo))
    return _dict_linha(cur)


def _buscar_dados_baixa_demanda(cur, apt, d):
    """Soma est_movsumarizado (pelo lote) + apt_apontaordem_lote (lote de fabricacao do
    apontamento aberto), igual ao loop principal de p_inseredemanda_lotespro. Devolve o
    produto/almoxarifado/local/qtd disponivel; None se nao achar nenhuma linha.

    AJUSTE 2026-09-22: quando o lote e' especifico (<> '*'), filtra SO' pelo lote --
    pro_in_codigo NAO entra no filtro (so' e' usado como alternativa quando lote = '*').
    Testado contra dado real da ordem 68783: com as duas condicoes em OR (como o texto
    da procedure sugeria), toda demanda de um mesmo item vinha com a MESMA quantidade
    (soma de todos os lotes do item, nao so' do lote pedido) -- confirmado errado
    comparando com est_movsumarizado por lote, um a um."""
    if d['lote'] != '*':
        cur.execute("""
            SELECT pro_in_codigo, alm_in_codigo, loc_in_codigo, SUM(qtd) AS qtd
              FROM (
                    SELECT pro_in_codigo, alm_in_codigo, loc_in_codigo, mvs_re_quantidade AS qtd
                      FROM est_movsumarizado WHERE mvs_st_loteforne = :lote
                    UNION ALL
                    SELECT pro_in_codigo, NULL, NULL, orl_re_qtdlote AS qtd
                      FROM apt_apontaordem_lote
                     WHERE org_in_codigo = :org AND fil_in_codigo = :fil AND ord_in_codigo = :ord
                       AND apt_in_sequencia = :apt AND apt_ch_status = 'A'
                       AND orl_st_lotefabricacao = :lote
                   )
             GROUP BY pro_in_codigo, alm_in_codigo, loc_in_codigo
             ORDER BY qtd DESC FETCH FIRST 1 ROW ONLY""",
                    {'lote': d['lote'], 'org': apt['org_in_codigo'], 'fil': apt['fil_in_codigo'],
                     'ord': apt['ord_in_codigo'], 'apt': apt['apt_in_sequencia']})
    else:
        # AJUSTE 2026-09-24 (3): lote '*' tem regra propria (almoxarifados permitidos da
        # maquina) -- ver _buscar_dados_baixa_demanda_sem_lote.
        return _buscar_dados_baixa_demanda_sem_lote(cur, apt, d)
    linha = cur.fetchone()
    if linha is None and d['lote'] != '*':
        # AJUSTE 2026-09-22: lote sem linha em est_movsumarizado (ja consumido/sumarizado) --
        # busca o ultimo lancamento do lote em est_lotesmovimento (por MVT_IN_LANCAM) e usa
        # o saldo de la.
        cur.execute("""SELECT pro_in_codigo, alm_in_codigo, loc_in_codigo, mvl_re_saldo
                         FROM est_lotesmovimento
                        WHERE mvl_st_loteforne = :lote
                        ORDER BY mvt_in_lancam DESC FETCH FIRST 1 ROW ONLY""",
                    {'lote': d['lote']})
        linha = cur.fetchone()
    if linha is None:
        return None
    pro, alm, loc, qtd = linha
    if not loc:
        cur.execute("""SELECT alm_in_codigo, loc_in_codigo FROM est_produtolocaliza
                        WHERE pro_in_codigo = :pro AND fil_in_codigo = :fil
                          AND epl_in_prioridade = 1 FETCH FIRST 1 ROW ONLY""",
                    {'pro': pro, 'fil': apt['fil_in_codigo']})
        prioridade = cur.fetchone()
        if prioridade:
            alm, loc = prioridade
    referencia = _buscar_referencia_lote(cur, d['lote'])
    # AJUSTE 2026-09-24: decisao do usuario -- MVS_ST_REFERENCIA NUNCA pode ficar nulo
    # (o efetivar depende dele pra achar o saldo). Sem referencia no estoque, recusa na
    # validacao -- nada e' gravado (tudo-ou-nada) e o erro volta pro operador.
    if referencia is None:
        raise ValueError(f"Item {pro} sem referência no estoque (est_movsumarizado) para o "
                         f"lote {d['lote']} (almox {alm}, local {loc}).")
    return {'pro': pro, 'alm': alm, 'loc': loc, 'qtd_disponivel': qtd, 'referencia': referencia}


def _maquina_da_ordem(cur, apt):
    """AJUSTE 2026-09-24: chave completa da maquina (maq_tab/maq_pad/maq_in_codigo) da
    PROGRAMACAO DA ORDEM (pro_prog_ordem) -- mesmo filtro de p_programacaoordem
    (apt_intprod2.sql): chaves da ordem + operacao do apontamento + tmp_ch_aponta='S'.
    Devolve (tab, pad, cod) ou None."""
    cur.execute("""SELECT maq_tab_in_codigo, maq_pad_in_codigo, maq_in_codigo
                     FROM pro_prog_ordem
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND fil_in_codigo = :fil_in_codigo
                      AND tmp_ch_aponta = 'S'
                      AND (plf_in_sqoperacao = :plf OR :plf IS NULL)
                      AND maq_in_codigo IS NOT NULL
                    ORDER BY plf_in_sqoperacao DESC FETCH FIRST 1 ROW ONLY""",
                {k: apt[k] for k in ('org_tab_in_codigo', 'org_pad_in_codigo', 'org_in_codigo',
                                     'org_tau_st_codigo', 'ord_tab_in_codigo', 'ord_seq_in_codigo',
                                     'ord_in_codigo', 'fil_in_codigo')}
                | {'plf': apt.get('plf_in_sqoperacao')})
    return cur.fetchone()


def _buscar_dados_baixa_demanda_sem_lote(cur, apt, d):
    """AJUSTE 2026-09-24 (3): demanda sem lote ('*') -- decisoes do usuario:
    - so' almoxarifado/local PERMITIDOS pra maquina da ordem (apt_pro_maquina_alm, chave
      completa maq_tab/maq_pad/maq_in_codigo vinda de pro_prog_ordem, ver
      _maquina_da_ordem), na filial do apontamento e padrao do produto dela (igual a
      Consulta.lista_saldo); pro_in_codigo do estoque = com_in_codigo da demanda;
    - escolhe o permitido com saldo >= quantidade pedida (9999 = saldo total, basta ter
      saldo) de MENOR maq_in_prioridade; se nenhum tiver o suficiente, o de menor
      prioridade que tenha ALGUM saldo (o efetivar acusa a falta);
    - almox/local/referencia saem da MESMA linha do est_movsumarizado (referencia nunca
      nula);
    - sem programacao/maquina ou sem almox permitido cadastrado: recusa (nada gravado).
    Bugs reais que isso corrige (ordem 68783): referencia NULL e almox/local de outra
    filial/nao permitido gravados em apt_apontademanda_estoque."""
    if not d['pro']:
        raise ValueError('Demanda com lote "*" precisa de pro_in_codigo (nao veio nenhum).')
    maquina = _maquina_da_ordem(cur, apt)
    if maquina is None:
        raise ValueError(f"Ordem {apt['ord_in_codigo']} (operação {apt.get('plf_in_sqoperacao')}) "
                         f"sem máquina na programação (pro_prog_ordem).")
    maq_tab, maq_pad, maq = maquina
    cur.execute("""SELECT COUNT(*) FROM apt_pro_maquina_alm
                    WHERE maq_tab_in_codigo = :mtab AND maq_pad_in_codigo = :mpad AND maq_in_codigo = :maq""",
                {'mtab': maq_tab, 'mpad': maq_pad, 'maq': maq})
    if not cur.fetchone()[0]:
        raise ValueError(f"Máquina {maq} sem almoxarifados permitidos cadastrados (apt_pro_maquina_alm).")
    qtd_pedida = 0 if d['qtd'] == 9999 else (d['qtd'] or 0)
    cur.execute("""
        SELECT e.pro_in_codigo, e.alm_in_codigo, e.loc_in_codigo, SUM(e.mvs_re_quantidade) AS saldo,
               e.mvs_st_referencia, m.maq_in_prioridade
          FROM est_movsumarizado e
          JOIN apt_pro_maquina_alm m
            ON m.alm_tab_in_codigo = e.alm_tab_in_codigo AND m.alm_pad_in_codigo = e.alm_pad_in_codigo
           AND m.alm_in_codigo = e.alm_in_codigo AND m.loc_in_codigo = e.loc_in_codigo
         WHERE m.maq_tab_in_codigo = :mtab AND m.maq_pad_in_codigo = :mpad AND m.maq_in_codigo = :maq
           AND e.pro_in_codigo = :pro AND e.mvs_st_loteforne = '*'
           AND e.fil_in_codigo = :fil
           AND e.pro_pad_in_codigo = idp.pck_mega.achapadraodatabela(:fil, 100, sysdate)
           AND e.mvs_st_referencia IS NOT NULL
         GROUP BY e.pro_in_codigo, e.alm_in_codigo, e.loc_in_codigo, e.mvs_st_referencia, m.maq_in_prioridade
        HAVING SUM(e.mvs_re_quantidade) > 0
         ORDER BY CASE WHEN SUM(e.mvs_re_quantidade) >= :qtd_pedida THEN 0 ELSE 1 END,
                  m.maq_in_prioridade
         FETCH FIRST 1 ROW ONLY""",
                {'mtab': maq_tab, 'mpad': maq_pad, 'maq': maq, 'pro': d['pro'],
                 'fil': apt['fil_in_codigo'], 'qtd_pedida': qtd_pedida})
    linha = cur.fetchone()
    if linha is None:
        raise ValueError(f"Item {d['pro']} sem saldo nos almoxarifados permitidos para a máquina {maq} "
                         f"(filial {apt['fil_in_codigo']}).")
    pro, alm, loc, saldo, referencia, _prioridade = linha
    return {'pro': pro, 'alm': alm, 'loc': loc, 'qtd_disponivel': saldo, 'referencia': referencia}


def _buscar_referencia_lote(cur, lote):
    """MVS_ST_REFERENCIA pro lote: MESMO texto vindo de est_movsumarizado (se ainda existe
    la) ou, na falta, o ultimo lancamento de est_lotesmovimento (MVL_ST_REFERENCIA)."""
    cur.execute("""SELECT MAX(mvs_st_referencia) FROM est_movsumarizado
                    WHERE mvs_st_loteforne = :lote AND mvs_st_referencia IS NOT NULL""",
                {'lote': lote})
    linha = cur.fetchone()
    if linha and linha[0] is not None:
        return linha[0]
    cur.execute("""SELECT mvl_st_referencia FROM est_lotesmovimento
                    WHERE mvl_st_loteforne = :lote AND mvl_st_referencia IS NOT NULL
                    ORDER BY mvt_in_lancam DESC FETCH FIRST 1 ROW ONLY""", {'lote': lote})
    linha = cur.fetchone()
    return linha[0] if linha else None


def _resolver_demanda_dep(cur, apt, com_in_codigo, contador_lis):
    """Acha a linha de PRO_DEMANDA_DEP do componente (ultima operacao, dde_in_operacao=0
    como no backup); se nao existir, prepara (sem inserir ainda) uma copia da ultima
    operacao com com_in_codigo=componente, dde_re_qtde_requisitada=0, dde_st_situacao='AB',
    lis_in_sequencia=max+10 -- igual ao p_cria_demanda. So' SELECT aqui (sem INSERT/UPDATE)."""
    cur.execute("""SELECT * FROM pro_demanda_dep
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND com_in_codigo = :com AND dde_in_operacao = 0""",
                dict(_chave_ordem(apt), com=com_in_codigo))
    achada = _dict_linha(cur)
    if achada:
        return achada, None
    # AJUSTE 2026-09-30: varias demandas do MESMO componente novo no mesmo lote de gravacao
    # geravam uma linha nova cada, com a mesma PK (PK_DEMANDA_DEP nao tem lis_in_sequencia)
    # -> ORA-00001 no executemany (ordens 68821/68913). A linha nova e' criada uma vez so'
    # por componente; as demais demandas reaproveitam ela sem inserir de novo. Guardada no
    # proprio contador_lis (chave de 4 posicoes, nao colide com a (org, ord) do contador).
    chave_nova = ('nova_dep', apt['org_in_codigo'], apt['ord_in_codigo'], com_in_codigo)
    if chave_nova in contador_lis:
        return contador_lis[chave_nova], None
    cur.execute("""SELECT * FROM pro_demanda_dep
                    WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                      AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                      AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                      AND ord_in_codigo = :ord_in_codigo AND dde_in_operacao = 0
                    ORDER BY dde_in_operacao DESC FETCH FIRST 1 ROW ONLY""",
                _chave_ordem(apt))
    base = _dict_linha(cur)
    if base is None:
        raise ValueError(f"Componente {com_in_codigo} nao existe em PRO_DEMANDA_DEP e nao "
                          f"ha nenhuma operacao da ordem {apt['ord_in_codigo']} pra copiar.")
    # AJUSTE 2026-09-22: contado em memoria (mesmo motivo do _proximo_mvs) -- se mais de um
    # componente novo aparecer no mesmo lote de gravacao, um SELECT MAX+10 por linha
    # devolveria o mesmo numero pra todos (nada commitado ainda ate o executemany final).
    chave = (apt['org_in_codigo'], apt['ord_in_codigo'])
    if chave not in contador_lis:
        cur.execute("""SELECT NVL(MAX(lis_in_sequencia), 0) FROM pro_demanda_dep
                        WHERE org_in_codigo = :org AND ord_in_codigo = :ord""",
                    {'org': apt['org_in_codigo'], 'ord': apt['ord_in_codigo']})
        contador_lis[chave] = cur.fetchone()[0]
    contador_lis[chave] += 10
    lis = contador_lis[chave]
    nova = dict(base)
    nova.update({'com_in_codigo': com_in_codigo, 'dde_re_qtde_requisitada': 0,
                 'dde_st_situacao': 'AB', 'lis_in_sequencia': lis})
    contador_lis[chave_nova] = nova
    return nova, nova


def _validar_demanda(cur, apt, pads, d, contador_lis):
    """Fase de validacao de UMA demanda (nenhum INSERT aqui). Devolve o 'plano' de
    gravacao, ou um dict {'ja_integrada': ...} se nao ha nada a gravar."""
    item = _buscar_dados_baixa_demanda(cur, apt, d)
    if item is None:
        raise ValueError(f"Nao foi possivel localizar produto/lote para a demanda "
                          f"(mvd_in_sequencia={d['mvd']}, lote={d['lote']}).")
    com_in_codigo = d['pro'] or item['pro']
    ja_integrada = _demanda_ja_integrada(cur, apt, d, com_in_codigo)
    if ja_integrada:
        return {'ja_integrada': ja_integrada, 'd': d}
    demanda_dep, nova_demanda_dep = _resolver_demanda_dep(cur, apt, com_in_codigo, contador_lis)
    # AJUSTE 2026-09-22: regra real da procedure (p_inseredemanda_lotespro) -- 9999 e' o
    # sentinela "saldo total do lote" (usa o que achou em est_movsumarizado/lote); qualquer
    # outro valor de pro_re_qtdlote e' a quantidade EXATA pedida, nao o saldo do lote.
    if d['qtd'] == 9999:
        qtd_selecionada = item['qtd_disponivel']
    else:
        qtd_selecionada = d['qtd']
    return {'ja_integrada': None, 'd': d, 'item': item, 'com_in_codigo': com_in_codigo,
            'demanda_dep': demanda_dep, 'nova_demanda_dep': nova_demanda_dep,
            'qtd_selecionada': qtd_selecionada}


def _proximo_mvs(cur, apt, contador):
    """Proximo mvs_in_sequencia (org+ord), contado em memoria dentro da FASE 2 -- as varias
    linhas de uma mesma ordem so' vao pro Oracle juntas no executemany do final, entao um
    SELECT MAX+1 por linha devolveria o MESMO numero pra todas (nada commitado ainda),
    violando a PK. AJUSTE 2026-09-22: bug real, encontrado gravando a ordem 68783 de
    verdade (ORA-00001 em PK_APT_APONTADEMANDA_ESTOQUE)."""
    chave = (apt['org_in_codigo'], apt['ord_in_codigo'])
    if chave not in contador:
        cur.execute("""SELECT NVL(MAX(mvs_in_sequencia), 0) FROM apt_apontademanda_estoque
                        WHERE org_in_codigo = :org AND ord_in_codigo = :ord""",
                    {'org': apt['org_in_codigo'], 'ord': apt['ord_in_codigo']})
        contador[chave] = cur.fetchone()[0]
    contador[chave] += 1
    return contador[chave]


def _linha_estoque(cur, apt, pads, plano, mvs):
    d, item = plano['d'], plano['item']
    valores = dict(_chave_ordem(apt))
    epoca = datetime(2000, 1, 1)
    valores.update({
        'apt_in_sequencia': apt['apt_in_sequencia'], 'fil_in_codigo': apt['fil_in_codigo'],
        'com_tab_in_codigo': 100, 'com_pad_in_codigo': pads['com_pad'], 'com_in_codigo': plano['com_in_codigo'],
        'dde_in_operacao': 0, 'dde_dt_necessidade': plano['demanda_dep']['dde_dt_necessidade'],
        'plf_in_sqoperacao': d['plf'] if d['plf'] is not None else apt.get('plf_in_sqoperacao'),
        'mvs_in_sequencia': mvs,
        'alm_tab_in_codigo': 105, 'alm_pad_in_codigo': pads['alm_pad'], 'alm_in_codigo': item['alm'],
        'loc_in_codigo': item['loc'], 'mvs_in_reserva': 0,
        'nat_tab_in_codigo': 143, 'nat_pad_in_codigo': 1, 'nat_st_codigo': 'DP',
        'mvs_st_loteforne': d['lote'], 'mvs_dt_entrada': epoca, 'mvs_dt_validade': epoca,
        'apt_re_qtdeselecionada': plano['qtd_selecionada'],
        'ctl_in_codigo': d['ctl'], 'mvd_in_sequencia': d['mvd'],
        'ord_st_id': d['ord_st_id'], 'cmaq_st_id': d['cmaq_st_id'],
        'apt_re_qtdeaviso': 0, 'apt_bo_loteestoque': 'S', 'saldo_estoque': plano['qtd_selecionada'],
        # AJUSTE 2026-09-22: resolvido via est_movsumarizado/est_lotesmovimento (ver
        # _buscar_referencia_lote); None vira NULL no bind normalmente -- fica SEMPRE
        # presente no dict (nao condicional), senao o executemany quebra (ORA-01036) quando
        # uma linha do lote tem referencia e outra nao (dicts com chaves diferentes).
        'mvs_st_referencia': item.get('referencia'),
    })
    # DDE_ST_SITUACAO e os demais continuam sem fonte confirmada -- NULL, igual ao
    # 'insert values <record>' original.
    nulos = ['DDE_ST_SITUACAO', 'IRE_CH_TIPORESERVA', 'EMM_IN_SEQUENCIA',
             'MVT_IN_LANCAM', 'MVL_ST_LOG', 'VIN_MVT_IN_LANCAM']
    return valores, nulos


def _conversor_via_catalogo(cur_local, pro_ordem, qtd_lote, qtd_conv):
    """Catalogo apt_itens_ordens.PRO_ST_CONVERSOR do item (produto final apontado). Com 2+
    conversores no catalogo (ex.: varios formatos de caixa), desambigua pela FORMULA:
    PRO_RE_QTDCONV / ORL_RE_QTDLOTE tem que bater com o UNI_ST_FORMULA de exatamente um
    -- confirmado com dado real da ordem 68783 (167,400/60,000 = 2,79 = "Cx 2,79 M²",
    FMT_ST_CODIGO='310', entre 2 opcoes do item 269). None se nao achar/desambiguar."""
    cur_local.execute(
        "SELECT PRO_ST_CONVERSOR FROM apt_itens_ordens WHERE PRO_IN_CODIGO = %s", [pro_ordem])
    linha = cur_local.fetchone()
    if not linha or not linha[0]:
        return None
    conversores = linha[0]
    try:
        # AJUSTE 2026-09-22: o valor vem com JSON serializado 2x (uma string JSON dentro
        # de outra) -- decodifica ate' virar lista (no maximo 2 voltas, senao desiste).
        for _ in range(2):
            if isinstance(conversores, str):
                conversores = json.loads(conversores)
            else:
                break
    except (TypeError, ValueError):
        return None
    if not isinstance(conversores, list):
        return None
    codigos = [c for c in conversores if isinstance(c, dict) and c.get('FMT_ST_CODIGO')]
    if len(codigos) == 1:
        return codigos[0]['FMT_ST_CODIGO']
    if not codigos or not qtd_lote:
        return None
    razao = float(qtd_conv) / float(qtd_lote)
    candidatos = []
    for c in codigos:
        try:
            formula = float(str(c['UNI_ST_FORMULA']).replace(',', '.'))
        except (TypeError, ValueError):
            continue
        if abs(formula - razao) < 0.005:
            candidatos.append(c['FMT_ST_CODIGO'])
    return candidatos[0] if len(candidatos) == 1 else None


def _conversor_do_lote(cur_local, apt_in_sequencia):
    """FMT_ST_CODIGO do lote local (Apt_ApontaOrdem, achado pelo APT_IN_SEQUENCIA = mvp_in_
    sequencia -- a PROPRIA linha do lote sendo gravado). Se a linha ja' tem FMT_ST_CODIGO
    gravado, usa direto; senao cai pro catalogo (_conversor_via_catalogo). None se nao
    achar a linha ou nao conseguir desambiguar."""
    cur_local.execute(
        "SELECT PRO_IN_CODIGO, FMT_ST_CODIGO, ORL_RE_QTDLOTE, PRO_RE_QTDCONV "
        "FROM Apt_ApontaOrdem WHERE APT_IN_SEQUENCIA = %s", [apt_in_sequencia])
    linha = cur_local.fetchone()
    if not linha:
        return None
    pro_ordem, fmt_st_codigo, qtd_lote, qtd_conv = linha
    if fmt_st_codigo is not None:
        return fmt_st_codigo
    return _conversor_via_catalogo(cur_local, pro_ordem, qtd_lote, qtd_conv)


def _buscar_conversor_local(cur_local, mvd, ord_in_codigo):
    """FMT_ST_CODIGO ('conversor') do lote local (Apt_ApontaOrdem) que gerou essa demanda,
    e o PRO_IN_CODIGO do ITEM DA ORDEM (produto final) a quem esse conversor pertence --
    o conversor e' do produto que foi apontado, NAO do componente da demanda; e' por isso
    que EST_PROUNI (chamada de _buscar_fmt_tab_pad) tem que ser consultada com esse
    PRO_IN_CODIGO, nao com o com_in_codigo da demanda. Devolve (fmt_st_codigo, pro_ordem)
    -- (None, None) se nao achar nada. SQL puro, so leitura.

    Tenta primeiro MOV_IN_SEQUENCIA = mvd_in_sequencia (o que o operador realmente
    escolheu naquele lote -- mais especifico, mas nem sempre gravado); senao cai pro
    catalogo (_conversor_via_catalogo), pegando PRO_IN_CODIGO/quantidades de QUALQUER
    linha da ordem (nao ha' um mvp especifico aqui como no lote)."""
    # AJUSTE 2026-09-22: sao casos distintos -- cada busca usa o PRO_IN_CODIGO da SUA
    # PROPRIA linha de Apt_ApontaOrdem (nao uma linha generica "qualquer uma da ordem").
    cur_local.execute(
        "SELECT PRO_IN_CODIGO, FMT_ST_CODIGO FROM Apt_ApontaOrdem WHERE MOV_IN_SEQUENCIA = %s "
        "AND FMT_ST_CODIGO IS NOT NULL", [mvd])
    linha = cur_local.fetchone()
    if linha:
        return linha[1], linha[0]

    # AJUSTE: SQLite (cur_local) usa LIMIT, nao FETCH FIRST (isso e' so' Oracle).
    cur_local.execute(
        "SELECT PRO_IN_CODIGO, ORL_RE_QTDLOTE, PRO_RE_QTDCONV FROM Apt_ApontaOrdem "
        "WHERE ORD_IN_CODIGO = %s AND PRO_IN_CODIGO IS NOT NULL LIMIT 1", [ord_in_codigo])
    linha = cur_local.fetchone()
    if not linha:
        return None, None
    pro_ordem, qtd_lote, qtd_conv = linha
    return _conversor_via_catalogo(cur_local, pro_ordem, qtd_lote, qtd_conv), pro_ordem


def _buscar_fmt_tab_pad(cur, pro_in_codigo, pro_pad_in_codigo, fmt_st_codigo):
    """FMT_TAB_IN_CODIGO/FMT_PAD_IN_CODIGO (chave completa do conversor) em EST_PROUNI,
    casando por PRO_IN_CODIGO + PRO_PAD_IN_CODIGO (chave do produto) + FMT_ST_CODIGO ja'
    resolvido (_buscar_conversor_local). None/None se fmt_st_codigo nao veio ou nao existe
    essa combinacao no Oracle."""
    if fmt_st_codigo is None:
        return None, None
    cur.execute("""SELECT fmt_tab_in_codigo, fmt_pad_in_codigo FROM est_prouni
                    WHERE pro_in_codigo = :pro AND pro_pad_in_codigo = :pad
                      AND fmt_st_codigo = :fmt
                    FETCH FIRST 1 ROW ONLY""",
                {'pro': pro_in_codigo, 'pad': pro_pad_in_codigo, 'fmt': fmt_st_codigo})
    linha = cur.fetchone()
    return linha if linha else (None, None)


def _linha_apontademanda(apt, plano, soma, fmt_st_codigo, fmt_tab, fmt_pad):
    d, dep = plano['d'], plano['demanda_dep']
    valores = dict(_chave_ordem(apt))
    valores.update({
        'apt_in_sequencia': apt['apt_in_sequencia'],
        'com_tab_in_codigo': 100, 'com_pad_in_codigo': dep['com_pad_in_codigo'] if 'com_pad_in_codigo' in dep else dep.get('com_pad_in_codigo'),
        'com_in_codigo': plano['com_in_codigo'], 'dde_in_operacao': 0,
        'dde_dt_necessidade': dep['dde_dt_necessidade'], 'dde_re_qtde_padrao': soma,
        'plf_in_sqoperacao': d['plf'] if d['plf'] is not None else apt.get('plf_in_sqoperacao'),
        'pro_st_tipobaixa': 'M', 'dde_bo_atende': 'S', 'dde_re_qtde_disponivel': soma,
        'dde_bo_reservado': 'N', 'dde_re_qtde_padrao_mov': soma,
    })
    nulos = ['UN2_ST_UNIDADE']  # sem fonte confirmada
    # AJUSTE 2026-09-22: FMT_ST_CODIGO vem do 'conversor' gravado localmente em
    # Apt_ApontaOrdem (casando por MOV_IN_SEQUENCIA); FMT_TAB_IN_CODIGO/FMT_PAD_IN_CODIGO
    # (a chave completa do conversor) resolvidos em EST_PROUNI (Oracle), casando por
    # PRO_IN_CODIGO + FMT_ST_CODIGO (_buscar_fmt_tab_pad). Ficam NULL so' se o local nao
    # tiver conversor gravado ou o Oracle nao tiver essa combinacao produto+conversor.
    if fmt_st_codigo is not None and fmt_tab is not None:
        valores['fmt_st_codigo'] = fmt_st_codigo
        valores['fmt_tab_in_codigo'] = fmt_tab
        valores['fmt_pad_in_codigo'] = fmt_pad
    else:
        nulos += ['FMT_ST_CODIGO', 'FMT_TAB_IN_CODIGO', 'FMT_PAD_IN_CODIGO']
    return valores, nulos


_SQL_CANCELAR_LOCAL = (
    # AJUSTE 2026-09-22: so' 'I' (ja integrada ao Oracle) vira 'C'. 'A' ainda nao foi pro
    # Oracle (cancelar no Oracle nao tem por que refletir nela) e 'C' ja e' no-op.
    "UPDATE Apt_Pro_Demandas SET MOV_ST_STATUS = 'C' "
    "WHERE FIL_IN_CODIGO = %s AND ORD_IN_CODIGO = %s AND MOV_IN_SEQUENCIA = %s "
    "AND CTL_IN_CODIGO = %s AND MOV_ST_STATUS = 'I'")


def _gravar_demandas(con, lista_dados, dry_run=False, auto_commit=True):
    # Import so aqui (igual ao Oracle): nao inicializa o Django DB na importacao do modulo.
    from django.db import connections
    resultados = []
    with con.cursor() as cur, connections['default'].cursor() as cur_local:
        # ---- FASE 1: validar tudo, sem gravar nada (aborta a lista inteira no 1o erro) ----
        planos, canceladas, puladas_c_local = [], [], []
        contador_lis = {}
        for dados in lista_dados:
            for obrigatorio in ('ctl_in_codigo', 'mvd_in_sequencia'):
                if dados.get(obrigatorio) is None:
                    raise ValueError(f'{obrigatorio} e obrigatorio.')
            # AJUSTE 2026-09-22: demanda ja cancelada NO LOCAL (mov_st_status='C', quando o
            # chamador passa esse campo -- opcional, so' pra essa checagem) nunca e' gravada
            # no Oracle. Confirmado com dado real da ordem 68783: 5 das 22 linhas locais
            # estavam 'C' e nao deveriam ser recriadas.
            if dados.get('mov_st_status') == 'C':
                puladas_c_local.append(dados.get('mvd_in_sequencia'))
                continue
            d = _normalizar_demanda(dados)
            # AJUSTE 2026-09-22: se o Oracle ja mostra essa demanda 'C' (cancelada por outro
            # meio -- ex.: tela local ainda nao espelhou), so' espelha o cancelamento no app
            # local (SQL puro, mesma rotina) e NAO grava nada nessa linha.
            if 'C' in _situacoes_demanda_oracle(cur, d['fil'], d['ord'], d['mvd'], d['ctl']):
                canceladas.append(d)
                continue
            ordem = _buscar_ordem(cur, d)
            if ordem is None:
                raise ValueError(f"Ordem {d['ord']} (filial {d['fil']}) nao encontrada em PRO_ORDENS.")
            pads = _pads_demanda(cur, d['fil'])
            if not _tem_apontamento_aberto(cur, ordem):
                raise ValueError(f"Ordem {d['ord']} nao tem apontamento aberto -- grave o lote primeiro.")
            apt = _buscar_apontamento_aberto(cur, ordem, d['plf'])
            if apt is None:
                raise ValueError('Ha apontamento aberto na ordem, mas nao para a operacao informada.')
            planos.append({**_validar_demanda(cur, apt, pads, d, contador_lis), 'apt': apt, 'pads': pads})

        if dry_run:
            # So' leitura: nao grava, nao cancela, devolve o plano pra conferencia. Rollback
            # por seguranca (a fase 1 nao devia ter escrito nada, mas nao custa garantir).
            con.rollback()
            plano_visivel = []
            for p in planos:
                plano_visivel.append({
                    'mvd_in_sequencia': p['d']['mvd'], 'ctl_in_codigo': p['d']['ctl'],
                    'com_in_codigo': p.get('com_in_codigo'),
                    'ja_integrada': bool(p['ja_integrada']),
                    'nova_demanda_dep': p.get('nova_demanda_dep') is not None,
                    'qtd_selecionada': p.get('qtd_selecionada'),
                    'apt_in_sequencia': p['apt']['apt_in_sequencia'],
                })
            for d in canceladas:
                plano_visivel.append({'mvd_in_sequencia': d['mvd'], 'ctl_in_codigo': d['ctl'],
                                      'seria_cancelada_no_local': True})
            for mvd in puladas_c_local:
                plano_visivel.append({'mvd_in_sequencia': mvd, 'pulada_ja_C_no_local': True})
            return plano_visivel

        # ---- FASE 2: gravar em bloco (executemany), um commit so no final ----
        inicio = time.perf_counter()
        novas_dep, linhas_estoque, agregados = [], [], {}
        nulos_dep = nulos_estoque = ()
        contador_mvs = {}
        for plano in planos:
            d = plano['d']
            if plano['ja_integrada']:
                resultados.append(dict(mensagem='Ok', item=plano['ja_integrada'].get('com_in_codigo'),
                                       Sequencia=plano['ja_integrada'].get('mvd_in_sequencia'), mvd=d['mvd']))
                continue
            if plano['nova_demanda_dep'] is not None:
                novas_dep.append(plano['nova_demanda_dep'])
            mvs = _proximo_mvs(cur, plano['apt'], contador_mvs)
            valores, nulos_estoque = _linha_estoque(cur, plano['apt'], plano['pads'], plano, mvs)
            linhas_estoque.append(valores)
            chave_agr = (plano['apt']['org_in_codigo'], plano['apt']['ord_in_codigo'],
                         plano['com_in_codigo'], 0)
            agregados.setdefault(chave_agr, {'apt': plano['apt'], 'plano': plano, 'soma': 0.0})
            agregados[chave_agr]['soma'] += plano['qtd_selecionada']
            # AJUSTE 2026-09-23: 'mvd' sempre presente e sempre = MOV_IN_SEQUENCIA local
            # (Apt_Pro_Demandas), pra quem for marcar 'I' local ter certeza do campo
            # certo -- 'Sequencia' aqui e' o MVS_IN_SEQUENCIA (Oracle, PK da linha em
            # APT_APONTADEMANDA_ESTOQUE), NAO o mvd; sao numeros diferentes.
            resultados.append(dict(mensagem='Ok', item=plano['com_in_codigo'],
                                   Sequencia=valores['mvs_in_sequencia'], mvd=d['mvd']))

        if novas_dep:
            colunas = list(novas_dep[0])
            marcas = [f':{c}' for c in colunas]
            cur.executemany(f"INSERT INTO PRO_DEMANDA_DEP ({', '.join(colunas)}) VALUES ({', '.join(marcas)})",
                            novas_dep)
        if linhas_estoque:
            colunas = list(linhas_estoque[0]) + list(nulos_estoque)
            marcas = [f':{c}' for c in colunas[:len(linhas_estoque[0])]] + ['NULL'] * len(nulos_estoque)
            cur.executemany(
                f"INSERT INTO APT_APONTADEMANDA_ESTOQUE ({', '.join(colunas)}) VALUES ({', '.join(marcas)})",
                linhas_estoque)
        for chave_agr, info in agregados.items():
            # AJUSTE 2026-09-22: decisao do usuario -- deixar FMT_ST_CODIGO/FMT_TAB_IN_CODIGO/
            # FMT_PAD_IN_CODIGO em branco no apontamento da demanda; a quantidade ja' vem
            # certa de est_movsumarizado, o conversor nao se aplica aqui (era do produto
            # apontado, nao da demanda). _buscar_conversor_local/_buscar_fmt_tab_pad ficam
            # no modulo (podem servir noutro contexto) mas nao sao mais chamadas aqui.
            valores, nulos_apontademanda = _linha_apontademanda(
                info['apt'], info['plano'], info['soma'], None, None, None)
            # AJUSTE 2026-09-22: oracledb (execute com dict) da' ORA-01036 se o dict tiver
            # chave que NAO aparece no SQL como bind -- so' passa as chaves usadas aqui,
            # nao o 'valores' inteiro (que tem colunas so' do INSERT/_insert).
            _chaves_update = ('dde_re_qtde_padrao', 'dde_re_qtde_disponivel', 'dde_re_qtde_padrao_mov',
                              'org_tab_in_codigo', 'org_pad_in_codigo', 'org_in_codigo', 'org_tau_st_codigo',
                              'ord_tab_in_codigo', 'ord_seq_in_codigo', 'ord_in_codigo', 'com_in_codigo',
                              'dde_in_operacao', 'dde_dt_necessidade', 'apt_in_sequencia')
            cur.execute("""UPDATE apt_apontademanda SET dde_re_qtde_padrao = :dde_re_qtde_padrao,
                              dde_re_qtde_disponivel = :dde_re_qtde_disponivel,
                              dde_re_qtde_padrao_mov = :dde_re_qtde_padrao_mov
                            WHERE org_tab_in_codigo = :org_tab_in_codigo AND org_pad_in_codigo = :org_pad_in_codigo
                              AND org_in_codigo = :org_in_codigo AND org_tau_st_codigo = :org_tau_st_codigo
                              AND ord_tab_in_codigo = :ord_tab_in_codigo AND ord_seq_in_codigo = :ord_seq_in_codigo
                              AND ord_in_codigo = :ord_in_codigo AND com_in_codigo = :com_in_codigo
                              AND dde_in_operacao = :dde_in_operacao AND dde_dt_necessidade = :dde_dt_necessidade
                              AND apt_in_sequencia = :apt_in_sequencia""",
                        {k: valores[k] for k in _chaves_update})
            if cur.rowcount == 0:
                _insert(cur, 'APT_APONTADEMANDA', valores, nulos_apontademanda)
        # AJUSTE 2026-09-23: auto_commit=False -- usado quando o chamador quer gravar
        # lote(s) + demanda(s) na MESMA transacao (ver gravar_e_encerrar_controle em
        # integracao_apontamento.py), commitando so' no final se TUDO der certo. Sem
        # isso, validar a demanda ANTES do lote virar real (commitado) sempre falhava
        # com "nao tem apontamento aberto" quando o lote e' quem cria esse apontamento.
        if auto_commit:
            con.commit()

        # Espelha as canceladas no app local (SQL puro, mesma rotina/mesmo commit logico).
        if canceladas:
            cur_local.executemany(
                _SQL_CANCELAR_LOCAL,
                [[d['fil'], d['ord'], d['mvd'], d['ctl']] for d in canceladas])
            if not connections['default'].get_autocommit():
                connections['default'].commit()
        for d in canceladas:
            resultados.append(dict(mensagem='Cancelada', item=None, Sequencia=d['mvd'], mvd=d['mvd']))
        for mvd in puladas_c_local:
            resultados.append(dict(mensagem='Ja cancelada no local', item=None, Sequencia=mvd, mvd=mvd))
        tempo_ms = int((time.perf_counter() - inicio) * 1000)
    for r in resultados:
        r['tempo_ms'] = tempo_ms
    return resultados


def gravar_demanda(lista_dados, conexao=None, dry_run=False, auto_commit=True):
    """
    lista_dados: LISTA de dicts, mesmo formato que api_producao.apt_integrarDemanda recebe
    hoje (por linha, um pra apt_intprod2.p_inseredemanda_lotespro): fil_in_codigo,
    ord_in_codigo, ctl_in_codigo, plf_in_sqoperacao, apt_dt_inclusao, mvd_in_sequencia,
    pro_st_lote, pro_re_qtdlote, cmaq_st_id, ord_st_id, ord_st_extenso, pro_in_codigo.
    Grava tudo numa unica transacao (tudo ou nada) -- ver docstring do modulo.
    conexao: conexao Oracle aberta (reaproveitada e NAO fechada aqui); se None, abre uma
    propria e fecha ao final.
    dry_run=True: roda so a FASE 1 (validacao, leitura) e devolve o plano de gravacao
    (o que SERIA inserido/atualizado), sem tocar Oracle nem o app local. Sempre da'
    rollback no final (por seguranca, mesmo sendo so leitura).
    auto_commit=False: grava de verdade mas NAO commita (caller decide, ex.: pra gravar
    junto com um lote na mesma transacao -- ver gravar_e_encerrar_controle). So' faz
    sentido com conexao explicita (senao a conexao fecha antes do caller commitar).
    Retorno: lista de dict(mensagem, item, Sequencia, tempo_ms) -- mesmo formato de
    apt_integrarDemanda + tempo_ms (tempo da fase de gravacao, em milissegundos); com
    dry_run=True, lista de dict(mvd_in_sequencia, com_in_codigo, qtd_selecionada, ...).
    """
    try:
        if conexao is None:
            with _abrir_conexao() as con:
                return _gravar_demandas(con, lista_dados, dry_run=dry_run, auto_commit=auto_commit)
        return _gravar_demandas(conexao, lista_dados, dry_run=dry_run, auto_commit=auto_commit)
    except Exception as e:
        if conexao is not None:
            conexao.rollback()
        print(f'Erro ao gravar demanda: {e}')
        return [dict(mensagem='Erro', item=None, Sequencia=None, detalhe=str(e))]


# ---------------------------------------------------------------------------
# SINCRONIA local x Oracle -- confirmacao e conciliacao sao SOMENTE LEITURA.
# AJUSTE 2026-09-21: quem marca o registro local como 'I'/'C' continua sendo o
# integraOrdens; aqui so se confirma no Oracle que a linha existe e se listam
# divergencias. Nada e corrigido automaticamente. A unica escrita desta secao e
# cancelar_demanda_oracle (UPDATE de dde_st_situacao 'A'->'C', chamado explicitamente).
# ---------------------------------------------------------------------------
# tipo -> (tabela Oracle, coluna com a sequencia local)
_TAB_SEQ = {'lote': ('APT_APONTAORDEM_LOTE', 'MVP_IN_SEQUENCIA'),
            'demanda': ('APT_APONTADEMANDA_ESTOQUE', 'MVD_IN_SEQUENCIA')}


def _com_cursor(conexao, funcao):
    if conexao is None:
        with _abrir_conexao() as con:
            with con.cursor() as cur:
                return funcao(cur)
    with conexao.cursor() as cur:
        return funcao(cur)


def _existe(cur, tipo, fil, ord_, seq, ctl):
    # AJUSTE 2026-09-21: ctl_in_codigo e obrigatorio -- o registro tem que existir
    # nos dois lados com o mesmo controle.
    if ctl is None:
        raise ValueError('ctl_in_codigo e obrigatorio para confirmar a sincronia.')
    tabela, coluna = _TAB_SEQ[tipo]
    cur.execute(f"SELECT 1 FROM {tabela} WHERE fil_in_codigo = :fil AND ord_in_codigo = :ord "
                f"AND {coluna} = :seq AND ctl_in_codigo = :ctl FETCH FIRST 1 ROW ONLY",
                {'fil': int(fil), 'ord': int(ord_), 'seq': int(seq), 'ctl': int(ctl)})
    return cur.fetchone() is not None


def lote_existe_no_oracle(fil_in_codigo, ord_in_codigo, mvp_in_sequencia, ctl_in_codigo,
                          conexao=None):
    """True se o lote (APT_IN_SEQUENCIA local = mvp_in_sequencia) esta em APT_APONTAORDEM_LOTE
    com o mesmo ctl_in_codigo (obrigatorio)."""
    return _com_cursor(conexao, lambda cur: _existe(
        cur, 'lote', fil_in_codigo, ord_in_codigo, mvp_in_sequencia, ctl_in_codigo))


def demanda_existe_no_oracle(fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo,
                             conexao=None):
    """True se a demanda (MOV_IN_SEQUENCIA local = mvd_in_sequencia) esta em
    APT_APONTADEMANDA_ESTOQUE com o mesmo ctl_in_codigo (obrigatorio)."""
    return _com_cursor(conexao, lambda cur: _existe(
        cur, 'demanda', fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo))


def _chaves_oracle(cur, tipo, dias, so_canceladas=False):
    """Chaves (fil, ord, seq, ctl) gravadas no Oracle nos ultimos `dias` dias; ctl pode ser None.
    so_canceladas (so demanda): apenas linhas com dde_st_situacao = 'C'."""
    if tipo == 'lote':
        sql = """SELECT fil_in_codigo, ord_in_codigo, mvp_in_sequencia, ctl_in_codigo
                   FROM apt_apontaordem_lote
                  WHERE mvp_in_sequencia IS NOT NULL AND apt_dt_inclusao >= TRUNC(SYSDATE) - :dias"""
    else:
        sql = """SELECT d.fil_in_codigo, d.ord_in_codigo, d.mvd_in_sequencia, d.ctl_in_codigo
                   FROM apt_apontademanda_estoque d
                   JOIN apt_apontaordem a ON a.apt_in_sequencia = d.apt_in_sequencia
                  WHERE d.mvd_in_sequencia IS NOT NULL
                    AND a.apt_dt_apontamento >= TRUNC(SYSDATE) - :dias"""
        if so_canceladas:
            sql += " AND d.dde_st_situacao = 'C'"
    cur.execute(sql, {'dias': dias})
    return {(int(f), int(o), int(s), None if c is None else int(c))
            for f, o, s, c in cur.fetchall()}


def _conciliar_tipo(cur, tipo, locais, dias):
    campo = 'mvp_in_sequencia' if tipo == 'lote' else 'mvd_in_sequencia'
    do_oracle = _chaves_oracle(cur, tipo, dias)
    oracle_sem_ctl = sorted(k[:3] for k in do_oracle if k[3] is None)
    do_oracle = {k for k in do_oracle if k[3] is not None}
    canceladas_oracle = _chaves_oracle(cur, tipo, dias, so_canceladas=True) if tipo == 'demanda' else set()
    chaves_locais = set()
    local_sem_ctl, local_i_sem_oracle, local_a_no_oracle = [], [], []
    canc_local_ativa_oracle, canc_local_nao_cancelavel, canc_oracle_ativa_local = [], [], []
    for r in locais:
        if r.get('ctl_in_codigo') is None:
            local_sem_ctl.append(r)
            continue
        chave = (int(r['fil_in_codigo']), int(r['ord_in_codigo']), int(r[campo]),
                 int(r['ctl_in_codigo']))
        chaves_locais.add(chave)
        if tipo == 'demanda' and r['status'] == 'C':
            # cancelada localmente: so pode ser cancelada no Oracle o que ainda esta 'A'.
            # Nunca enviada ao Oracle (sem linhas) => nada a fazer.
            situacoes = _situacoes_demanda_oracle(cur, *chave)
            if 'A' in situacoes:
                canc_local_ativa_oracle.append(r)
            elif situacoes and 'C' not in situacoes:
                canc_local_nao_cancelavel.append(r)   # ex.: ja baixada ('B')
            continue
        if tipo == 'demanda' and chave in canceladas_oracle and r['status'] in ('A', 'I'):
            canc_oracle_ativa_local.append(r)
            continue
        no_oracle = chave in do_oracle or _existe(cur, tipo, *chave)
        if r['status'] == 'I' and not no_oracle:
            local_i_sem_oracle.append(r)
        elif r['status'] == 'A' and no_oracle:
            local_a_no_oracle.append(r)
    resultado = {'local_sem_ctl': local_sem_ctl,
                 'oracle_sem_ctl': oracle_sem_ctl,
                 'local_i_sem_oracle': local_i_sem_oracle,
                 'local_a_no_oracle': local_a_no_oracle,
                 'oracle_sem_local': sorted(do_oracle - chaves_locais)}
    if tipo == 'demanda':
        resultado.update({'cancelada_local_ativa_oracle': canc_local_ativa_oracle,
                          'cancelada_local_nao_cancelavel': canc_local_nao_cancelavel,
                          'cancelada_oracle_ativa_local': canc_oracle_ativa_local})
    return resultado


def _situacoes_demanda_oracle(cur, fil, ord_, seq, ctl):
    """Situacoes (dde_st_situacao; '?' = nulo) das linhas da demanda no Oracle."""
    cur.execute("""SELECT DISTINCT NVL(dde_st_situacao, '?') FROM apt_apontademanda_estoque
                    WHERE fil_in_codigo = :fil AND ord_in_codigo = :ord
                      AND mvd_in_sequencia = :seq AND ctl_in_codigo = :ctl""",
                {'fil': int(fil), 'ord': int(ord_), 'seq': int(seq), 'ctl': int(ctl)})
    return {r[0] for r in cur.fetchall()}


def _cancelar_demanda(con, fil, ord_, seq, ctl):
    if ctl is None:
        raise ValueError('ctl_in_codigo e obrigatorio para cancelar a demanda.')
    try:
        with con.cursor() as cur:
            # UNICO UPDATE do modulo: so dde_st_situacao, so 'A' -> 'C', chave completa com ctl.
            cur.execute("""UPDATE apt_apontademanda_estoque SET dde_st_situacao = 'C'
                            WHERE fil_in_codigo = :fil AND ord_in_codigo = :ord
                              AND mvd_in_sequencia = :seq AND ctl_in_codigo = :ctl
                              AND dde_st_situacao = 'A'""",
                        {'fil': int(fil), 'ord': int(ord_), 'seq': int(seq), 'ctl': int(ctl)})
            alteradas = cur.rowcount
        con.commit()
        return alteradas
    except Exception:
        con.rollback()
        raise


def cancelar_demanda_oracle(fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo,
                            conexao=None):
    """
    Espelha no Oracle o cancelamento feito no local: dde_st_situacao 'A' -> 'C' nas linhas de
    APT_APONTADEMANDA_ESTOQUE da demanda (filial, ordem, mvd_in_sequencia, ctl obrigatorio).
    Nao mexe em linhas 'B' (baixadas), nulas ou ja 'C'. Sem DELETE. Devolve quantas linhas
    mudou (0 = nada a cancelar). Quantidade em APT_APONTADEMANDA NAO e alterada.
    """
    if conexao is None:
        with _abrir_conexao() as con:
            return _cancelar_demanda(con, fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo)
    return _cancelar_demanda(conexao, fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo)


def _demandas_canceladas_no_oracle(cur, fil_in_codigo, ord_in_codigo, mvds):
    """
    AJUSTE 2026-09-23: consulta ENXUTA (1 unica ida ao Oracle, so' pelos mvd_in_sequencia
    pendentes dessa ordem -- nao escaneia dias/ordens de outros apontamentos como
    _chaves_oracle faz) pra saber quais dessas demandas ja foram canceladas no Oracle
    (dde_st_situacao='C'). So' leitura. Devolve set de mvd_in_sequencia cancelados.
    """
    if not mvds:
        return set()
    marcas = ','.join(f':m{i}' for i in range(len(mvds)))
    binds = {'fil': int(fil_in_codigo), 'ord': int(ord_in_codigo)}
    binds.update({f'm{i}': int(m) for i, m in enumerate(mvds)})
    cur.execute(f"""SELECT DISTINCT mvd_in_sequencia FROM apt_apontademanda_estoque
                     WHERE fil_in_codigo = :fil AND ord_in_codigo = :ord
                       AND mvd_in_sequencia IN ({marcas}) AND dde_st_situacao = 'C'""", binds)
    return {int(r[0]) for r in cur.fetchall()}


def sincronizar_cancelamentos_demanda(fil_in_codigo, ord_in_codigo, mvds_pendentes, conexao=None):
    """
    AJUSTE 2026-09-23: espelha no LOCAL o cancelamento que so' pode acontecer no Oracle
    -- decisao do usuario: "uma vez integrado pro Oracle, so' pode ser cancelado la".
    Recebe os mvd_in_sequencia locais ainda 'A'/'I' pra essa ordem (ver
    integracao_apontamento.sincronizar_cancelamentos, que busca isso no Django e faz
    o UPDATE local em lote) e devolve so' os que estao 'C' no Oracle -- essa funcao NAO
    grava nada, so' leitura (o UPDATE local fica no chamador, que tem acesso ao ORM).
    """
    return _com_cursor(conexao, lambda cur: _demandas_canceladas_no_oracle(
        cur, fil_in_codigo, ord_in_codigo, mvds_pendentes))


def _apt_in_sequencia_do_ctl(cur, ctl_in_codigo):
    """
    AJUSTE 2026-09-23: fallback pra achar o apt_in_sequencia (Oracle) de um controle
    quando NENHUM lote foi gravado NESTE request (ja' estava 'I' de antes) -- so'
    leitura. Bug real corrigido: um mesmo ctl_in_codigo pode ter VARIAS linhas em
    apt_apontaordem_lote (residuo de ciclos de teste antigos com apt_in_sequencia
    diferentes) -- pegar "qualquer uma" (sem filtro) podia devolver um apontamento
    JA ENCERRADO/errado em vez do que esta realmente ABERTO agora. Filtra por
    apt_ch_status='A' (join com apt_apontaordem) e pega o mais recente
    (apt_in_sequencia DESC) se ainda assim houver mais de um. None se nao achar.
    """
    cur.execute("""SELECT lot.apt_in_sequencia
                     FROM apt_apontaordem_lote lot, apt_apontaordem apo
                    WHERE lot.apt_in_sequencia = apo.apt_in_sequencia
                      AND lot.ctl_in_codigo = :ctl
                      AND apo.apt_ch_status = 'A'
                    ORDER BY lot.apt_in_sequencia DESC
                    FETCH FIRST 1 ROW ONLY""", {'ctl': int(ctl_in_codigo)})
    linha = cur.fetchone()
    return linha[0] if linha else None


def _buscar_gru_in_codigo(cur, usuario, fil_in_codigo):
    """
    AJUSTE 2026-09-23: mesma consulta de api/api_view.py::GetDadosProducao.get_usuario_filial
    -- replicada aqui (em vez de round-trip HTTP) pra resolver GRU_IN_CODIGO na MESMA
    conexao/ida ao Oracle que ja abrimos pra gravar lote/demanda. So' leitura.
    usuario: Apt_Controle.CTL_ST_USUARIO (cracha/opd_st_alternativo). Devolve None se
    nao achar.
    """
    cur.execute("""SELECT gru.gru_in_codigo
                     FROM pro_cadoperador opd, pro_cadoperadorcmpesp pce, glo_grupo_usuario gru
                    WHERE opd.opd_tab_in_codigo = pce.opd_tab_in_codigo
                      AND opd.opd_pad_in_codigo = pce.opd_pad_in_codigo
                      AND opd.opd_in_codigo     = pce.opd_in_codigo
                      AND pce.gru_in_codigo     = gru.gru_in_codigo
                      AND opd.opd_st_alternativo = :pusuario
                      AND opd.opd_pad_in_codigo = pck_mega.achapadraodatabela(:pfil, 228, sysdate)""",
                {'pusuario': usuario, 'pfil': int(fil_in_codigo)})
    linha = cur.fetchone()
    return linha[0] if linha else None


def _apt_ch_status(cur, apt_in_sequencia):
    """So' leitura: status atual de apt_apontaordem pra esse apt_in_sequencia."""
    cur.execute("SELECT apt_ch_status FROM apt_apontaordem WHERE apt_in_sequencia = :apt",
                {'apt': apt_in_sequencia})
    linha = cur.fetchone()
    return linha[0] if linha else None


def _efetivar_apontamento(con, apt_in_sequencia, gru_in_codigo, data_apontamento=None):
    """
    AJUSTE 2026-09-23: chama apt_intprod2.p_efetivaapontamento (fonte conferida em
    apt_intprod2.sql:4685 -- PRAGMA AUTONOMOUS_TRANSACTION, commita sozinha, gera
    PRO_APONTAORDEM/movimentos de producao de verdade). NAO reimplementa a logica --
    so' chama a procedure, mesmo padrao ja usado em api/api_almoxa.py::apt_gerarBaixa
    (ref cursor posicional via con.cursor()). pCOMP_ST_NOME fixo 'APONTAMENTO'
    (decisao do usuario).

    AJUSTE 2026-09-23 (2): confirmacao real de sucesso -- decisao do usuario:
    apt_apontaordem.apt_ch_status virar 'E' (era 'A') pra esse apt_in_sequencia e'
    quem diz se a procedure efetivou de verdade, nao so' o texto da mensagem (que e'
    livre/informativo). A procedure ja' commitou sozinha (autonomous transaction),
    entao esse SELECT le o resultado final direto.
    Devolve (mensagem, efetivado): mensagem e' o texto de pRESULT (ou None); efetivado
    e' True so' se apt_ch_status == 'E' depois da chamada.
    """
    with con.cursor() as cur:
        # AJUSTE 2026-09-23 (3): "carimbar antes de efetivar" -- decisao do usuario.
        # Erro real confirmado testando ao vivo: ORA-01400 (nao pode inserir NULL em
        # PRO_APONTAORDEM.APO_DT_APONTAMENTO) -- a procedure le esse valor de
        # apt_apontaordem.apt_dt_encerramento (fonte, apt_intprod2.sql:4807), mas o
        # INSERT direto (gravar_lote/_criar_apontamento) nunca preenche essa coluna.
        # AJUSTE 2026-09-24: decisao do usuario -- a data vem da tela de confirmacao
        # (data_apontamento, editavel, padrao agora) e SEMPRE sobrescreve (e' a que a
        # procedure copia pra APO_DT_APONTAMENTO). Sem data informada, mantem o carimbo
        # antigo: SYSDATE so' se ainda estiver NULL.
        if data_apontamento is not None:
            cur.execute("""UPDATE apt_apontaordem SET apt_dt_encerramento = :dt
                            WHERE apt_in_sequencia = :apt""",
                        {'dt': data_apontamento, 'apt': apt_in_sequencia})
        else:
            cur.execute("""UPDATE apt_apontaordem SET apt_dt_encerramento = SYSDATE
                            WHERE apt_in_sequencia = :apt AND apt_dt_encerramento IS NULL""",
                        {'apt': apt_in_sequencia})
        con.commit()
        ref_cursor = con.cursor()
        sparams = (ref_cursor, apt_in_sequencia, 'APONTAMENTO', gru_in_codigo)
        cur.callproc('apt_intprod2.p_efetivaapontamento', sparams)
        linha = ref_cursor.fetchone()
        mensagem = linha[0] if linha else None
        status = _apt_ch_status(cur, apt_in_sequencia)
    return mensagem, (status == 'E')


def efetivar_apontamento_oracle(apt_in_sequencia, usuario, fil_in_codigo, conexao=None,
                                data_apontamento=None):
    """
    AJUSTE 2026-09-23: proximo passo depois de gravar_lote()/gravar_demanda() --
    decisao do usuario: so' chamar DEPOIS de ter certeza que lote(s)/demanda(s) ja
    foram gravados no Oracle (ver integracao_apontamento.gravar_e_encerrar_controle),
    pra gerar os movimentos de estoque de verdade. Resolve GRU_IN_CODIGO (a partir do
    usuario/cracha do Apt_Controle sendo encerrado + filial) e chama a procedure.
    conexao: conexao Oracle aberta (reaproveitada e NAO fechada aqui); se None, abre
    uma propria e fecha ao final. Devolve (mensagem, efetivado) -- ver
    _efetivar_apontamento; em caso de erro (usuario nao achado ou excecao na
    chamada), mensagem comeca com 'Erro:' e efetivado e' False.
    """
    def _rodar(con):
        with con.cursor() as cur:
            gru_in_codigo = _buscar_gru_in_codigo(cur, usuario, fil_in_codigo)
        if gru_in_codigo is None:
            return f'Erro: usuario {usuario} (filial {fil_in_codigo}) nao encontrado pra efetivar.', False
        try:
            return _efetivar_apontamento(con, apt_in_sequencia, gru_in_codigo, data_apontamento)
        except Exception as e:
            con.rollback()
            return f'Erro ao efetivar apontamento: {e}', False
    if conexao is None:
        with _abrir_conexao() as con:
            return _rodar(con)
    return _rodar(conexao)


def conciliar(lotes_locais, demandas_locais, dias=7, conexao=None):
    """
    Compara os registros locais com o Oracle. SOMENTE LEITURA.
    lotes_locais:    dicts com fil_in_codigo, ord_in_codigo, mvp_in_sequencia, ctl_in_codigo, status
                     (Apt_ApontaOrdem: mvp_in_sequencia = APT_IN_SEQUENCIA, status = APT_CH_STATUS)
    demandas_locais: dicts com fil_in_codigo, ord_in_codigo, mvd_in_sequencia, ctl_in_codigo, status
                     (Apt_Pro_Demandas: mvd_in_sequencia = MOV_IN_SEQUENCIA, status = MOV_ST_STATUS)
    A chave e (filial, ordem, sequencia, ctl_in_codigo): o ctl tem que existir e ser igual
    nos dois lados. Os locais passados devem cobrir o mesmo periodo (`dias`) -- senao
    'oracle_sem_local' lista linhas que so parecem faltar.
    Devolve {'lotes': {...}, 'demandas': {...}} com:
      local_sem_ctl       registros locais sem ctl_in_codigo (nao entram na comparacao)
      oracle_sem_ctl      chaves (fil, ord, seq) do Oracle com ctl_in_codigo nulo
      local_i_sem_oracle  marcado 'I' sem linha no Oracle com o mesmo ctl
      local_a_no_oracle   ainda 'A' mas ja no Oracle com o mesmo ctl
      oracle_sem_local    chaves (fil, ord, seq, ctl) do Oracle sem correspondente local
    So para demandas (status local 'C' = cancelada; Oracle dde_st_situacao 'C'):
      cancelada_local_ativa_oracle    local 'C' e Oracle ainda 'A' -> cancelar_demanda_oracle()
      cancelada_local_nao_cancelavel  local 'C' mas o Oracle nao esta 'A' nem 'C' (ex.: 'B' baixada)
      cancelada_oracle_ativa_local    Oracle 'C' e local ainda 'A'/'I' -> o local deve virar 'C'
                                      (esse PUT local e do integrador, fora deste arquivo)
    Demanda 'C' local que nunca foi ao Oracle nao aparece: nada a fazer no Oracle.
    """
    return _com_cursor(conexao, lambda cur: {
        'lotes': _conciliar_tipo(cur, 'lote', lotes_locais, dias),
        'demandas': _conciliar_tipo(cur, 'demanda', demandas_locais, dias),
    })
