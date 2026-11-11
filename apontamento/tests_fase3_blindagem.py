# -*- coding: utf-8 -*-
"""AJUSTE 2026-11-11 (JPC): Fase 3 + blindagem -- cada caso real corrigido no MP, NMV e ZK vira teste aqui:
cancelamento espelhado app x Mega (tudo ou nada, nada se apaga), demandas com lote ja consumido (ZK OP 3500),
APT_APONTADEMANDA pela soma total (MP 8c07346), lote ja no estoque (MP be55c91), permissao do operador antes de
gravar (MP 69205), Mega bloqueado avisa na hora (MP CTL 131), trava por CTL (NMV OP 562), lote cancelado no Mega
fora da conferencia (NMV OP 545 / ZK OP 3453), listas/totais sem cancelados, log da integracao."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apontamento import apontamento as ao
from apontamento import integracao_apontamento as integ
from apontamento.models import Apt_Controle
from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas

CTL, FIL, ORD = 900, 3, 7700


def _lote(seq, status='A', ctl=CTL):
    return Apt_ApontaOrdem.objects.create(
        FIL_IN_CODIGO=FIL, APT_IN_SEQUENCIA=seq, APT_DT_APONTAMENTO=date(2026, 11, 11), APT_CH_STATUS=status,
        ORD_IN_CODIGO=ORD, PRO_IN_CODIGO=420, ORL_RE_QTDLOTE=10, PRO_RE_QTDCONV=10, ORL_ST_REFERENCIA='x',
        CTL_IN_CODIGO=ctl, PRO_ST_LOTE=f'L{seq}')


def _demanda(seq, status='A', lote='D1', qtd=5, ctl=CTL):
    return Apt_Pro_Demandas.objects.create(
        FIL_IN_CODIGO=FIL, MOV_IN_SEQUENCIA=seq, MOV_DT_INCLUSAO=date(2026, 11, 11), ORD_IN_CODIGO=ORD,
        PRO_RE_QTDLOTE=qtd, PRO_ST_LOTE=lote, MOV_ST_STATUS=status, CTL_IN_CODIGO=ctl)


class _Cur:
    """Cursor de teste: responde em ordem (linhas de fetchall/fetchone) e guarda o SQL executado."""

    def __init__(self, respostas=()):
        self.respostas, self.sql, self._linhas, self.rowcount = list(respostas), [], [], 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, binds=None):
        self.sql.append(' '.join(sql.split()))
        self._linhas = self.respostas.pop(0) if self.respostas else []
        self.rowcount = len(self._linhas)

    def fetchall(self):
        return list(self._linhas)

    def fetchone(self):
        return self._linhas[0] if self._linhas else None


def _con(cur=None):
    con = MagicMock()
    con.__enter__.return_value = con
    con.cursor.return_value = cur or _Cur()
    return con


# =============================================================== cancelamento espelhado (modelo ZK)
class CancelarSelecionadosTests(TestCase):
    def test_nao_integrado_so_marca_c_no_app_e_nao_apaga(self):
        _lote(1, 'A')
        with patch.object(integ, 'abrir_conexao_oracle_testada') as abrir:
            res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertTrue(res['ok'])
        abrir.assert_not_called()  # nada no Mega
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'C')  # continua la, cancelado

    def test_integrado_cancela_no_mega_e_no_app_com_um_commit(self):
        _lote(1, 'I')
        con = _con()
        with patch.object(integ, 'abrir_conexao_oracle_testada', return_value=(con, None)), \
                patch('apontamento.apontamento.cancelar_varios_cur',
                      return_value={'problemas': {}, 'cancelados': [1]}) as canc:
            res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertEqual((res['ok'], res['no_mega']), (True, [1]))
        self.assertEqual(canc.call_args[0][4], [(1, CTL)])  # chave exata seq + CTL
        con.commit.assert_called_once()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'C')

    def test_mega_ja_efetivado_nada_muda_nos_dois_lados(self):
        _demanda(5, 'I')
        con = _con()
        with patch.object(integ, 'abrir_conexao_oracle_testada', return_value=(con, None)), \
                patch('apontamento.apontamento.cancelar_varios_cur',
                      return_value={'problemas': {(5, CTL): ('nao_aberto', ['B'])}, 'cancelados': []}):
            res = integ.cancelar_selecionados('demanda', [5], FIL, ORD)
        self.assertFalse(res['ok'])
        self.assertIn('não está aberto(a) no Mega (status B)', res['erros'][0])
        con.rollback.assert_called_once()
        con.commit.assert_not_called()
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'I')

    def test_sem_conexao_nada_cancelado(self):
        _lote(1, 'I')
        with patch.object(integ, 'abrir_conexao_oracle_testada', return_value=(None, 'sem')):
            res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertEqual(res['erros'], [integ.MSG_CANC_SEM_CONEXAO])
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')

    def test_tudo_ou_nada_um_fora_da_op_nada_cancela(self):
        _lote(1, 'A')
        res = integ.cancelar_selecionados('lote', [1, 99], FIL, ORD)
        self.assertFalse(res['ok'])
        self.assertIn('não pertence a esta ordem/filial', res['erros'][0])
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')

    def test_ja_cancelado_nao_cancela_de_novo(self):
        _lote(1, 'C')
        res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertIn('status C', res['erros'][0])

    def test_falha_no_app_desfaz_o_mega(self):
        _lote(1, 'I')
        con = _con()
        with patch.object(integ, 'abrir_conexao_oracle_testada', return_value=(con, None)), \
                patch('apontamento.apontamento.cancelar_varios_cur', return_value={'problemas': {}, 'cancelados': [1]}), \
                patch.object(Apt_ApontaOrdem.objects, 'filter', side_effect=[Apt_ApontaOrdem.objects.all(),
                                                                             RuntimeError('disco')]):
            res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertFalse(res['ok'])
        con.commit.assert_not_called()
        con.rollback.assert_called()

    def test_ctl_sendo_gravado_nao_cancela(self):
        _lote(1, 'A')
        trava = MagicMock()
        trava.__enter__.return_value = False
        with patch.object(integ, '_trava_ctl', return_value=trava):
            res = integ.cancelar_selecionados('lote', [1], FIL, ORD)
        self.assertIn('já está sendo gravado', res['erros'][0])
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')


class CancelarVariosCurTests(SimpleTestCase):
    def test_problema_nao_altera_nada(self):
        cur = _Cur([[(1, CTL, 'A')]])  # so a chave 1 existe; a 2 nao
        res = ao.cancelar_varios_cur(cur, 'lote', FIL, ORD, [(1, CTL), (2, CTL)])
        self.assertEqual(res['problemas'], {(2, CTL): ('nao_localizado', [])})
        self.assertFalse([s for s in cur.sql if s.startswith('UPDATE') or s.startswith('DELETE')])

    def test_lote_cancela_e_apaga_a_sub(self):
        cur = _Cur([[(1, CTL, 'A')]])
        res = ao.cancelar_varios_cur(cur, 'lote', FIL, ORD, [(1, CTL)])
        self.assertEqual(res['cancelados'], [1])
        self.assertTrue(any(s.startswith("UPDATE APT_APONTAORDEM_LOTE SET APT_CH_STATUS = 'C'") for s in cur.sql))
        self.assertTrue(any(s.startswith('DELETE FROM PRO_ORDEMLOTESUB') for s in cur.sql))

    def test_demanda_recalcula_o_empenho(self):
        cur = _Cur([[(5, CTL, 'A')], [], [(441000,)]])
        ao.cancelar_varios_cur(cur, 'demanda', FIL, ORD, [(5, CTL)])
        self.assertTrue(any(s.startswith('UPDATE APT_APONTADEMANDA dde') for s in cur.sql))

    def test_status_fora_de_a_c_e_problema(self):
        cur = _Cur([[(5, CTL, 'B')]])
        res = ao.cancelar_varios_cur(cur, 'demanda', FIL, ORD, [(5, CTL)])
        self.assertEqual(res['problemas'][(5, CTL)], ('nao_aberto', ['B']))


class CancelarIndividualTests(TestCase):
    def setUp(self):
        Apt_Controle.objects.create(CTL_IN_CODIGO=CTL, CTL_ST_USUARIO='OPER', ORD_IN_CODIGO=ORD, FIL_IN_CODIGO=FIL,
                                    CTL_DT_LOGIN=timezone.now(), CTL_ST_IPADDRESS='1', CTL_ST_STATUS='A')
        s = self.client.session
        s.update({'ctl_in_codigo': CTL, 'usuario': 'OPER', 'ord_in_codigo': ORD, 'fil_in_codigo': FIL,
                  'seq_in_operacao': 1, 'ordem': 'X'})
        s.save()

    def test_cancelar_lote_nao_apaga(self):
        _lote(1, 'A')
        with patch('apontamento.views.IntAPI') as api:
            api.return_value.listar_producao.return_value = [{'APT_IN_SEQUENCIA': 1}]
            self.client.post(reverse('deleteapt', args=[1]))
            api.return_value.delete_producao.assert_not_called()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'C')

    def test_cancelar_demanda_nao_apaga(self):
        _demanda(5, 'A')
        with patch('apontamento.views.IntAPI') as api:
            api.return_value.listar_demanda.return_value = [{'MOV_IN_SEQUENCIA': 5}]
            self.client.post(reverse('deletedemanda', args=[5]))
            api.return_value.delete_demanda.assert_not_called()
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'C')

    def test_cancelar_selecionados_pela_tela(self):
        _lote(1, 'A')
        _lote(2, 'A')
        resp = self.client.post(reverse('cancelar_selecionados', args=['lote']), {'sel': ['1', '2']})
        self.assertContains(resp, 'Confirma o cancelamento?')
        resp = self.client.post(reverse('cancelar_selecionados', args=['lote']), {'sel': ['1', '2'], 'confirmar': '1'})
        self.assertRedirects(resp, reverse('efetivar_mega_oracle'), fetch_redirect_response=False)
        self.assertEqual(set(Apt_ApontaOrdem.objects.values_list('APT_CH_STATUS', flat=True)), {'C'})


# =============================================================== nada muda para o operador: cancelado fora das listas
class ListasSemCanceladosTests(TestCase):
    def test_api_local_nao_mostra_nem_soma_cancelados(self):
        _lote(1, 'A')
        _lote(2, 'C')
        _demanda(5, 'A', qtd=5)
        _demanda(6, 'C', qtd=7)
        base = {'ordem': ORD, 'filial': FIL}
        lotes = self.client.get('/app/apontamentos/', dict(base, ctl_in_codigo=CTL)).json()
        self.assertEqual([l['APT_IN_SEQUENCIA'] for l in lotes], [1])
        self.assertEqual(float(self.client.get('/app/apontamentos/', dict(base, total='S')).json()['total_ordem']), 10)
        dems = self.client.get('/app/demandas/', base).json()
        self.assertEqual([d['MOV_IN_SEQUENCIA'] for d in dems], [5])
        self.assertEqual(float(self.client.get('/app/demandas/', dict(base, total='S')).json()['total_lote']), 5)

    def test_releitura_de_lote_cancelado_na_mesma_op(self):
        _demanda(6, 'C', lote='LX')
        dems = self.client.get('/app/demandas/', {'ordem': ORD, 'filial': FIL, 'lote': 'LX'}).json()
        self.assertEqual(dems, [])  # "Demanda Ja baixada nessa ordem!" nao dispara para a cancelada


# =============================================================== demandas com lote ja consumido (ZK OP 3500)
class LotesConsumidosTests(TestCase):
    def test_lote_com_saldo_zero_e_consumido_com_onde(self):
        cur = _Cur([[('D1', 420, 0)], [], [('D1', 7000, 12, 3, 5)]])
        res = ao.lotes_consumidos_cur(cur, ['D1'])
        self.assertEqual(res['D1']['consumo'], [(7000, 12, 3, 5.0)])

    def test_lote_de_apontamento_aberto_fica_de_fora(self):
        cur = _Cur([[('D1', 420, 0)], [('D1',)]])
        self.assertEqual(ao.lotes_consumidos_cur(cur, ['D1']), {})

    def test_lote_com_saldo_nao_entra(self):
        cur = _Cur([[('D1', 420, 3)], []])
        self.assertEqual(ao.lotes_consumidos_cur(cur, ['D1']), {})

    def test_ok_com_lista_mudada_nao_cancela(self):
        _demanda(5, 'A')
        with patch.object(integ, 'conferir_lotes_consumidos', return_value=([{'seq': 6}], None)), \
                patch.object(integ, 'cancelar_selecionados') as canc:
            res = integ.cancelar_demandas_consumidas(CTL, FIL, ORD, ['5'])
        self.assertEqual(res['erros'], [integ.MSG_CONSUMIDAS_MUDOU])
        canc.assert_not_called()

    def test_oracle_fora_nao_trava_a_gravacao(self):
        with patch.object(integ, 'abrir_conexao_oracle_testada', return_value=(None, 'sem conexao')):
            self.assertEqual(integ.conferir_lotes_consumidos(CTL), ([], 'sem conexao'))


# =============================================================== APT_APONTADEMANDA pela soma total (MP 8c07346)
class ApontaDemandaSomaTotalTests(SimpleTestCase):
    def test_soma_le_todas_as_linhas_do_componente(self):
        cur = _Cur([[(42.5,)]])
        total = ao._soma_estoque_componente(cur, {'apt_in_sequencia': 1, 'com_tab_in_codigo': 100,
                                                  'com_pad_in_codigo': 2, 'com_in_codigo': 420})
        self.assertEqual(total, 42.5)
        self.assertIn("NVL(dde_st_situacao, 'A') <> 'C'", cur.sql[0])

    def test_componente_sem_apontademanda_e_detectado(self):
        cur = _Cur([[(420,), (421,)]])
        self.assertEqual(ao.componentes_sem_apontademanda(cur, 1), [420, 421])

    def test_criar_faltante_agrega_a_estoque(self):
        cur = _Cur()
        ao._criar_apontademanda_faltante(cur, 1, [420])
        self.assertTrue(cur.sql[0].startswith('INSERT INTO apt_apontademanda'))
        self.assertIn('SUM(e.apt_re_qtdeselecionada)', cur.sql[0])


# =============================================================== lote ja no estoque nao duplica (MP be55c91)
class LoteNoEstoqueTests(SimpleTestCase):
    def test_lote_no_estoque_bloqueia_a_gravacao(self):
        d = {'fil': FIL, 'ord': ORD, 'mvp': 1, 'plf': 10, 'ctl': CTL, 'lote': 'L1'}
        with patch.object(ao, '_buscar_ordem', return_value={'x': 1}), \
                patch.object(ao, '_lote_ja_integrado', return_value=False), \
                patch.object(ao, '_lote_no_estoque', return_value=True), \
                patch.object(ao, '_criar_apontamento') as criar:
            with self.assertRaisesRegex(ValueError, 'ja foi apontado'):
                ao._fluxo_lote(MagicMock(), MagicMock(), d)
        criar.assert_not_called()

    def test_lote_gerado_sem_numero_nao_consulta(self):
        self.assertFalse(ao._lote_no_estoque(MagicMock(), None))


# =============================================================== protecoes antes de gravar (MP / NMV / ZK)
class ProtecoesGravacaoTests(SimpleTestCase):
    CONTROLE = MagicMock(CTL_IN_CODIGO=CTL, FIL_IN_CODIGO=FIL, ORD_IN_CODIGO=ORD, CTL_ST_USUARIO='OPER')

    def _resultado(self):
        return {'ok': 0, 'erro': 0, 'erros': [], 'erro_oracle': None}

    def test_operador_sem_permissao_nada_gravado(self):
        r = self._resultado()
        with patch('apontamento.apontamento.operador_tem_permissao', return_value=False), \
                patch.object(integ, '_gravar_tudo_ou_nada') as gravar:
            gravou, _ = integ._gravar_pendentes(_con(), {'usuario': 'X'}, self.CONTROLE, [1], [], r,
                                                conferir_operador=True)
        self.assertFalse(gravou)
        self.assertIn('sem permissão no Mega', r['erro_oracle'])
        gravar.assert_not_called()

    def test_cron_nao_confere_operador(self):
        with patch('apontamento.apontamento.operador_tem_permissao') as perm, \
                patch.object(integ, 'validar_antes_de_gravar', return_value=['x']):
            integ._gravar_pendentes(_con(), {}, self.CONTROLE, [], [], self._resultado())
        perm.assert_not_called()

    def test_mega_bloqueado_avisa_na_hora(self):
        r = self._resultado()
        cur = MagicMock()
        cur.__enter__.return_value = cur
        cur.execute.side_effect = [Exception('ORA-00054: resource busy'), None]
        cur.fetchall.return_value = [('MEGA', 'srv', 'mega.exe')]
        con = _con()
        con.cursor.return_value = cur
        with patch.object(integ, 'validar_antes_de_gravar', return_value=[]), \
                patch.object(integ, '_gravar_tudo_ou_nada') as gravar:
            gravou, _ = integ._gravar_pendentes(con, {}, self.CONTROLE, [MagicMock()], [], r)
        self.assertFalse(gravou)
        self.assertIn('bloqueada no Mega', r['erro_oracle'])
        self.assertIn('usuário MEGA', r['erro_oracle'])
        gravar.assert_not_called()
        con.rollback.assert_called()

    def test_trava_ocupada_nada_feito(self):
        r = self._resultado()
        trava = MagicMock()
        trava.__enter__.return_value = False
        with patch.object(integ, '_trava_ctl', return_value=trava), \
                patch.object(integ, '_gravar_tudo_ou_nada') as gravar:
            gravou, _ = integ._gravar_pendentes(_con(), {}, self.CONTROLE, [1], [], r)
        self.assertFalse(gravou)
        self.assertIn('já está sendo gravado', r['erro_oracle'])
        gravar.assert_not_called()

    def test_trava_que_falha_nao_trava_o_fluxo(self):
        with patch.object(integ, 'TRAVA_CTL', '/pasta/que/nao/existe/{ctl}.lock'), \
                patch('os.open', side_effect=PermissionError('negado')):
            with integ._trava_ctl(1) as livre:
                self.assertTrue(livre)


# =============================================================== conferencia do CTL (NMV a66c375 / ZK 3560ce0)
class ConferenciaLoteCanceladoNoMegaTests(SimpleTestCase):
    def test_lote_cancelado_no_mega_nao_conta(self):
        cur = _Cur([[], []])
        ao.itens_do_ctl_no_oracle(_con(cur), FIL, ORD, CTL)
        self.assertIn("NVL(apt_ch_status, '?') <> 'C'", cur.sql[0])
        self.assertIn("NVL(dde_st_situacao, 'A') <> 'C'", cur.sql[1])


# =============================================================== tela Efetivar: totalizador e CTL vazio
class TelaEfetivarTests(TestCase):
    def test_totalizador_sem_cancelados_e_9999_a_parte(self):
        lotes = [_lote(1, 'A'), _lote(2, 'C')]
        dems = [_demanda(5, 'A', qtd=5), _demanda(6, 'I', qtd=9999), _demanda(7, 'C', qtd=3)]
        t = integ.totais_efetivar(lotes, dems)
        self.assertEqual((t['lotes'], float(t['lotes_qtd'])), (1, 10.0))
        self.assertEqual((t['demandas'], float(t['demandas_qtd']), t['demandas_9999']), (1, 5.0, 1))

    def test_situacao_da_op_no_mega(self):
        cur = _Cur([[(441000, date(2026, 11, 10), 'E')], [(441000, 12)]])
        res = ao.situacao_op_no_mega(cur, FIL, ORD)
        self.assertEqual(res, [{'apt': 441000, 'data': '10/11/2026', 'situacao': 'efetivado', 'efetivado': True,
                                'controles': [12]}])


# =============================================================== log da integracao
class LogIntegracaoTests(SimpleTestCase):
    def test_log_nunca_levanta_excecao(self):
        with patch.object(integ, '_logger_integracao', side_effect=OSError('disco cheio')):
            integ.registrar_evento('integracao', erro='x', ctl=1)  # nao levanta

    def test_erro_vai_como_error_e_com_campos(self):
        logger = MagicMock()
        with patch.object(integ, '_logger_integracao', return_value=logger):
            integ.registrar_evento('cancelar', erro=['a', 'b'], ctl=7, vazio=None)
        texto = logger.error.call_args[0][0]
        self.assertEqual(texto, 'evento=cancelar ctl=7 erro=a | b')

    def test_cron_sem_nada_nao_polui_o_log(self):
        with patch.object(integ, 'registrar_evento') as reg:
            integ._registrar_resultado({}, integ.ATIVIDADE_CRON, 1, {'pendentes': 0, 'ok': 0})
        reg.assert_not_called()
