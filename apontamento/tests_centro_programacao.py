# -*- coding: utf-8 -*-
"""AJUSTE 2026-11-11 (JPC): adaptado do NMV (apontamento/tests/tests_centro_programacao.py) -- centro do
apontamento pela programacao da OP no Mega (pro_prog_ordem), na criacao do cabecalho e antes da procedure
de efetivar. Caso PRODUCAO: OPs 74615/74639/74640/74651/74652/74661 (filial 2) com APT_MAQ_IN_CODIGO
vazio (acertado a mao para 140202). Caso NMV: OP 540, centro 140101 x programacao 140203 / operacao 6."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apontamento import apontamento as ao
from apontamento import integracao_apontamento as io

_CAB = ('org_tab_in_codigo', 'org_pad_in_codigo', 'org_in_codigo', 'org_tau_st_codigo', 'ord_tab_in_codigo',
        'ord_seq_in_codigo', 'ord_in_codigo', 'fil_in_codigo', 'plf_in_sqoperacao', 'apt_maq_in_codigo',
        'apt_cmaq_in_codigo', 'apt_ch_status')


class _Cursor:
    """Responde em ordem: cada execute consome a proxima resposta (colunas, linhas)."""

    def __init__(self, respostas):
        self.respostas, self.executados, self.description, self._linhas = list(respostas), [], None, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, binds=None):
        self.executados.append((' '.join(sql.split()), binds))
        colunas, self._linhas = self.respostas.pop(0) if self.respostas else ((), [])
        self.description = [(c,) for c in colunas]
        self.rowcount = len(self._linhas)

    def fetchone(self):
        return self._linhas[0] if self._linhas else None

    def fetchall(self):
        return list(self._linhas)


def _cabecalho(maq, cmaq, status='A'):
    return (tuple(c.upper() for c in _CAB), [(53, 1, 2, 'G', 218, 2, 74661, 2, 10, maq, cmaq, status)])


_PROG = (('MAQ_TAB_IN_CODIGO', 'MAQ_PAD_IN_CODIGO', 'MAQ_IN_CODIGO', 'OPR_IN_CODIGO'), [(207, 2, 140202, 6)])


def _con(cursor):
    con = MagicMock()
    con.cursor.return_value = cursor
    return con


class AlinharCentroProgramacaoTests(SimpleTestCase):
    def test_centro_vazio_vai_para_o_da_programacao(self):
        # caso PRODUCAO: cabecalho gravado sem centro
        cur = _Cursor([_cabecalho(None, None), _PROG, ((), [])])
        r = ao.alinhar_centro_programacao(_con(cur), 442365)
        self.assertIsNone(r['erro'])
        self.assertIn('centro vazio -> 140202', r['aviso'])
        sql, binds = cur.executados[-1]
        self.assertTrue(sql.startswith('UPDATE apt_apontaordem SET apt_maq_in_codigo = :maq'))
        self.assertEqual(binds, {'maq': 140202, 'cmaq': None, 'apt': 442365})

    def test_centro_antigo_vai_para_o_da_programacao(self):
        # caso NMV (OP 540): centro diferente e maquina incompativel com o centro programado
        cur = _Cursor([_cabecalho(140101, 1), _PROG, (('C',), [(0,)]), ((), [])])
        r = ao.alinhar_centro_programacao(_con(cur), 442365)
        self.assertIn('centro 140101 -> 140202', r['aviso'])
        self.assertIn('máquina 1 -> vazia', r['aviso'])
        self.assertEqual(cur.executados[-1][1], {'maq': 140202, 'cmaq': None, 'apt': 442365})

    def test_maquina_compativel_com_o_centro_fica(self):
        cur = _Cursor([_cabecalho(140101, 5), _PROG, (('C',), [(1,)]), ((), [])])
        r = ao.alinhar_centro_programacao(_con(cur), 442365)
        self.assertEqual(cur.executados[-1][1], {'maq': 140202, 'cmaq': 5, 'apt': 442365})
        self.assertNotIn('máquina', r['aviso'])

    def test_ja_alinhado_nao_grava(self):
        cur = _Cursor([_cabecalho(140202, 5), _PROG, (('C',), [(1,)])])
        self.assertEqual(ao.alinhar_centro_programacao(_con(cur), 442365), {'aviso': None, 'erro': None})
        self.assertFalse([s for s, _b in cur.executados if s.startswith('UPDATE')])

    def test_maquina_vazia_e_centro_certo_nao_grava(self):
        cur = _Cursor([_cabecalho(140202, None), _PROG])
        self.assertEqual(ao.alinhar_centro_programacao(_con(cur), 442365), {'aviso': None, 'erro': None})

    def test_sem_programacao_bloqueia(self):
        cur = _Cursor([_cabecalho(None, None), ((), [])])
        r = ao.alinhar_centro_programacao(_con(cur), 442365)
        self.assertIsNone(r['aviso'])
        self.assertIn('sem centro na programação do Mega', r['erro'])

    def test_apontamento_ja_efetivado_nao_mexe(self):
        cur = _Cursor([_cabecalho(None, None, status='E')])
        self.assertEqual(ao.alinhar_centro_programacao(_con(cur), 442365), {'aviso': None, 'erro': None})
        self.assertEqual(len(cur.executados), 1)


class CriarApontamentoCentroTests(SimpleTestCase):
    ORDEM = {'org_tab_in_codigo': 53, 'org_pad_in_codigo': 1, 'org_in_codigo': 2, 'org_tau_st_codigo': 'G',
             'ord_tab_in_codigo': 218, 'ord_seq_in_codigo': 2, 'ord_in_codigo': 74661, 'fil_in_codigo': 2,
             'tpo_tab_in_codigo': 1, 'tpo_pad_in_codigo': 1, 'tpo_st_codigo_tipo': 'OP001'}
    D = {'plf': 10, 'extenso': '00200746610100', 'ctl': 525, 'maq': None, 'dt_apt': None}

    def test_cabecalho_nasce_com_o_centro_da_programacao(self):
        cur = _Cursor([(('A',), [(1,)]), (('M',), [(1,)])])  # ati_in_codigo, max+1
        with patch.object(ao, 'programacao_da_operacao', return_value={'maq': 140202, 'opr': 6}) as prog, \
                patch.object(ao, '_insert') as inserir:
            ao._criar_apontamento(cur, self.ORDEM, dict(self.D), {'ati_pad': 1})
        self.assertEqual(prog.call_args[0][1]['plf_in_sqoperacao'], 10)
        self.assertEqual(inserir.call_args[0][2]['apt_maq_in_codigo'], 140202)

    def test_maquina_informada_no_payload_e_respeitada(self):
        cur = _Cursor([(('A',), [(1,)]), (('M',), [(1,)])])
        with patch.object(ao, 'programacao_da_operacao') as prog, patch.object(ao, '_insert') as inserir:
            ao._criar_apontamento(cur, self.ORDEM, dict(self.D, maq=140999), {'ati_pad': 1})
        prog.assert_not_called()
        self.assertEqual(inserir.call_args[0][2]['apt_maq_in_codigo'], 140999)

    def test_sem_programacao_nao_cria(self):
        cur = _Cursor([(('A',), [(1,)])])
        with patch.object(ao, 'programacao_da_operacao', return_value=None), patch.object(ao, '_insert') as inserir:
            with self.assertRaises(ValueError):
                ao._criar_apontamento(cur, self.ORDEM, dict(self.D), {'ati_pad': 1})
        inserir.assert_not_called()


class AlinharCentroDoApontamentoTests(SimpleTestCase):
    def test_ajuste_commita_e_avisa(self):
        con = MagicMock()
        with patch('apontamento.apontamento.alinhar_centro_programacao',
                   return_value={'aviso': 'Apontamento 442365 ajustado', 'erro': None}):
            self.assertEqual(io.alinhar_centro_do_apontamento(con, 442365), ('Apontamento 442365 ajustado', None))
        con.commit.assert_called_once()

    def test_sem_ajuste_nao_commita(self):
        con = MagicMock()
        with patch('apontamento.apontamento.alinhar_centro_programacao',
                   return_value={'aviso': None, 'erro': None}):
            self.assertEqual(io.alinhar_centro_do_apontamento(con, 442365), (None, None))
        con.commit.assert_not_called()

    def test_erro_faz_rollback(self):
        con = MagicMock()
        with patch('apontamento.apontamento.alinhar_centro_programacao',
                   return_value={'aviso': None, 'erro': 'sem centro'}):
            self.assertEqual(io.alinhar_centro_do_apontamento(con, 442365), (None, 'sem centro'))
        con.rollback.assert_called_once()
        con.commit.assert_not_called()

    def test_excecao_vira_erro_sem_efetivar(self):
        con = MagicMock()
        with patch('apontamento.apontamento.alinhar_centro_programacao', side_effect=RuntimeError('ORA-x')):
            aviso, erro = io.alinhar_centro_do_apontamento(con, 442365)
        self.assertIsNone(aviso)
        self.assertIn('Nada foi efetivado', erro)
        con.rollback.assert_called_once()
