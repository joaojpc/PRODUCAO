# -*- coding: utf-8 -*-
"""AJUSTE 2026-11-11 (JPC): Fase 2 -- validacoes da integracao copiadas do ZK (decisoes do usuario):
B leitura da etiqueta (formato e lote todo ja lido), C validar antes de gravar / lote nao localizado,
E saldo livre, F apontamento por CTL, H demanda abre apontamento e CTL efetivado recusa demanda."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from apontamento import apontamento as ao
from apontamento import integracao_apontamento as io
from apontamento.forms import DemFormLocal
from app.models import Apt_Pro_Demandas

ORDEM = {'org_tab_in_codigo': 53, 'org_pad_in_codigo': 1, 'org_in_codigo': 2, 'org_tau_st_codigo': 'G',
         'ord_tab_in_codigo': 218, 'ord_seq_in_codigo': 2, 'ord_in_codigo': 74661, 'fil_in_codigo': 2,
         'tpo_tab_in_codigo': 1, 'tpo_pad_in_codigo': 1, 'tpo_st_codigo_tipo': 'OP001'}


def _aberto(seq, plf=10):
    return dict(ORDEM, apt_in_sequencia=seq, plf_in_sqoperacao=plf)


# ---------------------------------------------------------------- F: apontamento por CTL
class AbertoDoCtlTests(SimpleTestCase):
    def test_nao_entra_no_aberto_de_outro_ctl(self):
        abertos = [_aberto(20), _aberto(10)]
        self.assertIsNone(ao._aberto_do_ctl(abertos, {20: {7}, 10: {8}}, 10, 5))

    def test_usa_o_aberto_do_proprio_ctl(self):
        abertos = [_aberto(20), _aberto(10)]
        self.assertEqual(ao._aberto_do_ctl(abertos, {20: {7}, 10: {5}}, 10, 5)['apt_in_sequencia'], 10)

    def test_aberto_vazio_serve(self):
        self.assertEqual(ao._aberto_do_ctl([_aberto(20)], {20: set()}, 10, 5)['apt_in_sequencia'], 20)

    def test_operacao_diferente_nao_serve(self):
        self.assertIsNone(ao._aberto_do_ctl([_aberto(20, plf=30)], {20: set()}, 10, 5))

    def test_fluxo_lote_cria_novo_quando_o_aberto_e_de_outro_ctl(self):
        d = {'fil': 2, 'ord': 74661, 'mvp': 1, 'plf': 10, 'ctl': 5}
        with patch.object(ao, '_buscar_ordem', return_value=ORDEM), \
                patch.object(ao, '_lote_ja_integrado', return_value=False), \
                patch.object(ao, '_buscar_padroes', return_value={}), \
                patch.object(ao, '_tem_apontamento_aberto', return_value=True), \
                patch.object(ao, '_buscar_apontamento_aberto', return_value=_aberto(20)), \
                patch.object(ao, '_apontamento_aberto_do_ctl', return_value=None), \
                patch.object(ao, '_criar_apontamento', return_value=_aberto(99)) as criar, \
                patch.object(ao, '_gravar_dados_lote'):
            apt = ao._fluxo_lote(MagicMock(), MagicMock(), d)
        criar.assert_called_once()
        self.assertEqual(apt['apt_in_sequencia'], 99)


# ---------------------------------------------------------------- H: demanda abre apontamento
class ApontamentoDaDemandaTests(SimpleTestCase):
    D = {'fil': 2, 'ord': 74661, 'plf': 10, 'ctl': 5, 'mvd': 1}

    def _rodar(self, tem_aberto, do_ctl, efetivado, criar=True):
        with patch.object(ao, '_tem_apontamento_aberto', return_value=tem_aberto), \
                patch.object(ao, '_buscar_apontamento_aberto', return_value=_aberto(20) if tem_aberto else None), \
                patch.object(ao, '_apontamento_aberto_do_ctl', return_value=do_ctl), \
                patch.object(ao, '_ctl_com_apontamento_efetivado', return_value=efetivado), \
                patch.object(ao, '_buscar_padroes', return_value={}), \
                patch.object(ao, '_criar_apontamento', return_value=_aberto(99)) as cria:
            return ao._apontamento_da_demanda(MagicMock(), ORDEM, dict(self.D), criar=criar), cria

    def test_sem_aberto_a_demanda_abre_o_apontamento(self):
        apt, cria = self._rodar(False, None, False)
        self.assertEqual(apt['apt_in_sequencia'], 99)
        self.assertIsNone(cria.call_args[0][2]['maq'])  # centro sai da programacao (Fase 1)

    def test_usa_o_aberto_do_ctl(self):
        apt, cria = self._rodar(True, _aberto(20), False)
        self.assertEqual(apt['apt_in_sequencia'], 20)
        cria.assert_not_called()

    def test_ctl_efetivado_no_mega_recusa_demanda(self):
        with self.assertRaisesRegex(ValueError, 'já efetivado no Mega'):
            self._rodar(False, None, True)

    def test_aberto_de_outro_ctl_e_ctl_efetivado_recusa(self):
        with self.assertRaisesRegex(ValueError, 'não aceita nova demanda'):
            self._rodar(True, None, True)

    def test_dry_run_nao_cria(self):
        apt, cria = self._rodar(False, None, False, criar=False)
        cria.assert_not_called()
        self.assertIsNone(apt['apt_in_sequencia'])


# ---------------------------------------------------------------- E: saldo livre
def _emp(mega=None, app=None, app_9999=None, origem_mega=None):
    return {'mega': mega or {}, 'app': app or {}, 'app_9999': app_9999 or {},
            'origem_mega': origem_mega or {}, 'origem_app': {}}


ITEM = {'pro': 420, 'referencia': 'R', 'qtd_disponivel': 100}


def _d(qtd, mvd=1, lote='L1'):
    return {'fil': 2, 'ord': 74661, 'mvd': mvd, 'ctl': 5, 'lote': lote, 'qtd': qtd}


class SaldoLivreTests(SimpleTestCase):
    def test_9999_pega_o_saldo_livre(self):
        pc = {'empenhos': _emp(mega={(420, 'L1', 'R'): 30}), 'usado': {}}
        self.assertEqual(ao._saldo_livre(None, ITEM, _d(9999), pc), 70)

    def test_quantidade_que_cabe(self):
        pc = {'empenhos': _emp(), 'usado': {}}
        self.assertEqual(ao._saldo_livre(None, ITEM, _d(40), pc), 40)
        self.assertEqual(pc['usado'][(420, 'L1', 'R')], 40)

    def test_sem_saldo_livre_mostra_o_empenho(self):
        pc = {'empenhos': _emp(mega={(420, 'L1', 'R'): 90},
                               origem_mega={(420, 'L1', 'R'): [(74000, 12, 7, 90)]}), 'usado': {}}
        with self.assertRaisesRegex(ValueError, r'sem saldo livre.*OP 74000 CTL 12 demanda 7: 90'):
            ao._saldo_livre(None, ITEM, _d(20), pc)

    def test_o_que_a_gravacao_ja_usou_conta(self):
        pc = {'empenhos': _emp(), 'usado': {}}
        ao._saldo_livre(None, ITEM, _d(80, mvd=1), pc)
        with self.assertRaisesRegex(ValueError, 'nesta gravação: 80'):
            ao._saldo_livre(None, ITEM, _d(30, mvd=2), pc)

    def test_empenho_do_app_conta(self):
        pc = {'empenhos': _emp(app={'L1': [(420, 100)]}), 'usado': {}}
        with self.assertRaisesRegex(ValueError, 'sem saldo livre'):
            ao._saldo_livre(None, ITEM, _d(9999), pc)

    def test_9999_duplicado_na_mesma_ordem(self):
        pc = {'empenhos': _emp(), 'usado': {}}
        ao._saldo_livre(None, ITEM, _d(9999, mvd=1), pc)
        with self.assertRaisesRegex(ValueError, 'Demanda duplicada'):
            ao._saldo_livre(None, ITEM, _d(9999, mvd=2), pc)

    def test_9999_pendente_no_app_e_duplicada(self):
        pc = {'empenhos': _emp(app_9999={(2, 74661, 'L1'): [(420, 8)]}), 'usado': {}}
        with self.assertRaisesRegex(ValueError, r'seq\. 1, 8'):
            ao._saldo_livre(None, ITEM, _d(9999, mvd=1), pc)

    def test_validar_demanda_com_lote_usa_saldo_livre(self):
        d = dict(_d(9999), pro=0)
        with patch.object(ao, '_buscar_dados_baixa_demanda', return_value=dict(ITEM)), \
                patch.object(ao, '_demanda_ja_integrada', return_value=None), \
                patch.object(ao, '_resolver_demanda_dep', return_value=({}, None)), \
                patch.object(ao, '_saldo_livre', return_value=55) as livre:
            plano = ao._validar_demanda(MagicMock(), _aberto(20), {}, d, {}, {'empenhos': _emp(), 'usado': {}})
        livre.assert_called_once()
        self.assertEqual(plano['qtd_selecionada'], 55)


# ---------------------------------------------------------------- C: lote nao localizado
class _Cur:
    def __init__(self, linha):
        self.linha = linha

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self.linha


class LoteNaoLocalizadoTests(SimpleTestCase):
    def test_lote_de_apontamento_aberto(self):
        msg = ao._msg_lote_nao_localizado(_Cur((74600, 441606, 'A')), _d(9999), 74661)
        self.assertIn('alguém precisa efetivar no Mega o apontamento 441606 da OP 74600', msg)

    def test_lote_de_apontamento_efetivado(self):
        msg = ao._msg_lote_nao_localizado(_Cur((74600, 441606, 'E')), _d(9999), 74661)
        self.assertIn('situação E no Mega', msg)

    def test_lote_desconhecido(self):
        self.assertIn('Confira se a etiqueta', ao._msg_lote_nao_localizado(_Cur(None), _d(9999), 74661))

    def test_validar_demanda_usa_a_mensagem_clara(self):
        with patch.object(ao, '_buscar_dados_baixa_demanda', return_value=None), \
                patch.object(ao, '_msg_lote_nao_localizado', return_value='MSG CLARA'):
            with self.assertRaisesRegex(ValueError, 'MSG CLARA'):
                ao._validar_demanda(MagicMock(), _aberto(20), {}, dict(_d(9999), pro=0), {})


class ValidarAntesDeGravarTests(SimpleTestCase):
    CONTROLE = MagicMock(FIL_IN_CODIGO=2, ORD_IN_CODIGO=74661, CTL_IN_CODIGO=5)

    def _dem(self, lote):
        return MagicMock(PRO_ST_LOTE=lote)

    def test_agrupa_pelo_apontamento_de_origem(self):
        origens = {'L1': (74600, 441606, 'A'), 'L2': (74600, 441606, 'A'), 'L3': None}
        with patch('apontamento.apontamento.lotes_demanda_nao_encontrados', return_value=['L1', 'L2', 'L3']), \
                patch('apontamento.apontamento.origem_lote_oracle', side_effect=lambda cur, l: origens[l]):
            avisos = io.validar_antes_de_gravar(MagicMock(), self.CONTROLE,
                                                [self._dem('L1'), self._dem('L2'), self._dem('L3'), self._dem('*')])
        self.assertEqual(len(avisos), 2)
        self.assertTrue(any('apontamento 441606 da OP 74600 (2 lote(s): L1, L2)' in a for a in avisos))
        self.assertTrue(any('confira se a etiqueta' in a for a in avisos))

    def test_tudo_no_estoque_segue(self):
        with patch('apontamento.apontamento.lotes_demanda_nao_encontrados', return_value=[]):
            self.assertEqual(io.validar_antes_de_gravar(MagicMock(), self.CONTROLE, [self._dem('L1')]), [])

    def test_falha_nao_bloqueia(self):
        with patch('apontamento.apontamento.lotes_demanda_nao_encontrados', side_effect=RuntimeError('x')):
            self.assertEqual(io.validar_antes_de_gravar(MagicMock(), self.CONTROLE, [self._dem('L1')]), [])

    def test_com_aviso_nada_e_gravado(self):
        resultado = {'ok': 0, 'erro': 0, 'erros': [], 'erro_oracle': None}
        with patch.object(io, 'validar_antes_de_gravar', return_value=['efetivar o apontamento 1']), \
                patch.object(io, '_gravar_tudo_ou_nada') as gravar:
            gravou, _apt = io._gravar_pendentes(MagicMock(), {}, self.CONTROLE, [], [self._dem('L1')], resultado)
        self.assertFalse(gravou)
        gravar.assert_not_called()
        self.assertIn('Nada foi gravado. efetivar o apontamento 1', resultado['erro_oracle'])


# ---------------------------------------------------------------- B: leitura da etiqueta
class LeituraEtiquetaTests(TestCase):
    LOTE = '2026432301020005313832'

    def _form(self, lote, ordem='74661'):
        return DemFormLocal(data={'dem_st_lote': lote, 'dem_re_qtdlote': 9999, 'ord_in_codigo': ordem,
                                  'fil_in_codigo': '2'})

    def _erros(self, form):
        # as validacoes do PRODUCAO depois das novas consultam a API/Oracle -- aqui so as novas interessam
        with patch('apontamento.forms.IntAPI') as api, patch('apontamento.forms.prep_producao') as prep:
            api.return_value.listar_demanda.return_value = []
            prep.return_value.prepara_demandas.return_value = [{'com_in_codigo': 1}]
            prep.return_value.listar_saldo.return_value = [{'MVS_RE_QUANTIDADE': 1, 'PRO_IN_CODIGO': 1}]
            form.is_valid()
        return ' '.join(form.non_field_errors())

    def test_tamanho_invalido(self):
        self.assertIn('lote inválido!', self._erros(self._form('12345678')))

    def test_22_digitos_deslocado(self):
        self.assertIn('leia o código de novo', self._erros(self._form('4323010200053139282026')))

    def test_digitado_curto_passa(self):
        self.assertEqual(self._erros(self._form('123')), '')

    def test_lote_todo_ja_lido_em_outra_op(self):
        Apt_Pro_Demandas.objects.create(FIL_IN_CODIGO=2, MOV_IN_SEQUENCIA=225019, MOV_DT_INCLUSAO=date(2026, 11, 11),
                                        ORD_IN_CODIGO=74000, PRO_RE_QTDLOTE=9999, PRO_ST_LOTE=self.LOTE,
                                        MOV_ST_STATUS='I', CTL_IN_CODIGO=1)
        erro = self._erros(self._form(self.LOTE))
        self.assertIn('Leitura duplicada', erro)
        self.assertIn('ordem 74000 (seq. 225019)', erro)

    def test_lote_todo_cancelado_nao_conta(self):
        Apt_Pro_Demandas.objects.create(FIL_IN_CODIGO=2, MOV_IN_SEQUENCIA=225019, MOV_DT_INCLUSAO=date(2026, 11, 11),
                                        ORD_IN_CODIGO=74000, PRO_RE_QTDLOTE=9999, PRO_ST_LOTE=self.LOTE,
                                        MOV_ST_STATUS='C', CTL_IN_CODIGO=1)
        self.assertEqual(self._erros(self._form(self.LOTE)), '')

    def test_validacao_atual_do_producao_continua(self):
        with patch('apontamento.forms.IntAPI') as api, patch('apontamento.forms.prep_producao') as prep:
            api.return_value.listar_demanda.return_value = [{'x': 1}]
            prep.return_value.prepara_demandas.return_value = [{'com_in_codigo': 1}]
            prep.return_value.listar_saldo.return_value = [{'MVS_RE_QUANTIDADE': 1, 'PRO_IN_CODIGO': 1}]
            form = self._form(self.LOTE)
            form.is_valid()
        self.assertIn('Demanda Já baixada nessa ordem!', ' '.join(form.non_field_errors()))
