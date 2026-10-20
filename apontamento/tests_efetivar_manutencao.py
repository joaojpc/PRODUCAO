# -*- coding: utf-8 -*-
# AJUSTE 2026-10-20 (JPC): testes do botao Efetivar Apontamento da manutencao (1o clique grava,
# 2o efetiva) e regressao do gravar_e_efetivar_controle usado pelo fechamento diario.
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apontamento import integracao_apontamento as integ
from apontamento.models import Apt_Controle
from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas

CTL = 555
SESSAO = {'ctl_in_codigo': CTL, 'usuario': 'OPER', 'seq_in_operacao': 1, 'ordem': 'ORD-1'}


def _lote(seq=1, status='A'):
    return Apt_ApontaOrdem.objects.create(
        FIL_IN_CODIGO=3, APT_IN_SEQUENCIA=seq, APT_DT_APONTAMENTO=date(2026, 10, 20), APT_CH_STATUS=status,
        ORD_IN_CODIGO=900, PRO_IN_CODIGO=2273, ORL_RE_QTDLOTE=1, ORL_ST_REFERENCIA='x', CTL_IN_CODIGO=CTL,
        PRO_ST_LOTE=f'L{seq}')


def _demanda(seq=10, status='A'):
    return Apt_Pro_Demandas.objects.create(
        FIL_IN_CODIGO=3, MOV_IN_SEQUENCIA=seq, MOV_DT_INCLUSAO=date(2026, 10, 20), ORD_IN_CODIGO=900,
        PRO_RE_QTDLOTE=1, PRO_ST_LOTE='D', MOV_ST_STATUS=status, CTL_IN_CODIGO=CTL)


class _ComOracle(TestCase):
    def setUp(self):
        Apt_Controle.objects.create(CTL_IN_CODIGO=CTL, CTL_ST_USUARIO='OPER', ORD_IN_CODIGO=900,
                                    CTL_DT_LOGIN=timezone.now(), CTL_ST_IPADDRESS='1', FIL_IN_CODIGO=3)
        con = MagicMock()
        con.__enter__.return_value = con
        self.con = con
        self.m = {
            'abrir': patch('apontamento.apontamento._abrir_conexao', return_value=con),
            'lote': patch('apontamento.apontamento.gravar_lote',
                          return_value=[{'mensagem': 'Ok', 'mensagem_sub': 'Ok', 'sequencia': 7001}]),
            'demanda': patch('apontamento.apontamento.gravar_demanda',
                             side_effect=lambda dados, **k: [{'mensagem': 'Ok', 'mvd': d['mvd_in_sequencia']}
                                                             for d in dados]),
            'efetivar': patch('apontamento.apontamento.efetivar_apontamento_oracle', return_value=('Ok', True)),
            'aberto': patch('apontamento.apontamento._apt_in_sequencia_do_ctl', return_value=7001),
        }
        self.mocks = {k: p.start() for k, p in self.m.items()}
        for p in self.m.values():
            self.addCleanup(p.stop)


class FechamentoRegressaoTests(_ComOracle):
    def test_grava_e_efetiva_como_antes(self):
        _lote()
        _demanda()
        r = integ.gravar_e_efetivar_controle(SESSAO, datetime(2026, 10, 20, 17, 0))
        self.assertEqual((r['ok'], r['erro'], r['efetivado_oracle'], r['erro_oracle']), (2, 0, True, None))
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'I')
        self.assertEqual(Apt_Controle.objects.get().APT_IN_SEQUENCIA, 7001)
        self.mocks['efetivar'].assert_called_once()
        self.assertEqual(self.mocks['efetivar'].call_args[0][0], 7001)
        self.con.commit.assert_called_once()

    def test_erro_na_gravacao_nao_efetiva(self):
        _lote()
        self.mocks['lote'].return_value = [{'mensagem': 'Erro', 'detalhe': 'ORA-1'}]
        r = integ.gravar_e_efetivar_controle(SESSAO, None)
        self.assertEqual(r['erro'], 1)
        self.assertIn('ORA-1', r['erros'][0])
        self.mocks['efetivar'].assert_not_called()
        self.con.rollback.assert_called_once()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')


class BotaoEfetivarTests(_ComOracle):
    def test_primeiro_clique_grava_sem_efetivar(self):
        _lote()
        r = integ.gravar_controle(SESSAO)
        self.assertEqual((r['pendentes'], r['ok'], r['erro_oracle']), (1, 1, None))
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')
        self.mocks['efetivar'].assert_not_called()

    def test_sem_pendente_nao_abre_oracle(self):
        _lote(status='I')
        r = integ.gravar_controle(SESSAO)
        self.assertEqual(r['pendentes'], 0)
        self.mocks['abrir'].assert_not_called()

    def test_conferir(self):
        _lote()
        self.assertEqual(integ.conferir_controle(SESSAO)['erro'], integ.MSG_PENDENTE)
        Apt_ApontaOrdem.objects.update(APT_CH_STATUS='I')
        self.assertEqual(integ.conferir_controle(SESSAO), {'erro': None, 'apt_in_sequencia': 7001})
        self.mocks['aberto'].return_value = None
        self.assertEqual(integ.conferir_controle(SESSAO)['erro'], integ.MSG_NADA_ABERTO)

    def test_segundo_clique_efetiva_com_a_data(self):
        _lote(status='I')
        data = datetime(2026, 10, 20, 17, 30)
        r = integ.efetivar_controle(SESSAO, data)
        self.assertEqual((r['efetivado_oracle'], r['apt_in_sequencia'], r['erro_oracle']), (True, 7001, None))
        self.assertEqual(self.mocks['efetivar'].call_args.kwargs['data_apontamento'], data)

    def test_segundo_clique_com_pendencia_nao_efetiva(self):
        _demanda()
        r = integ.efetivar_controle(SESSAO, datetime(2026, 10, 20, 17, 30))
        self.assertEqual(r['erro_oracle'], integ.MSG_PENDENTE)
        self.mocks['efetivar'].assert_not_called()


class ViewsEfetivarTests(_ComOracle):
    def _sessao(self):
        s = self.client.session
        s.update({'ctl_in_codigo': CTL, 'usuario': 'OPER', 'ord_in_codigo': 900, 'fil_in_codigo': 3,
                  'seq_in_operacao': 1, 'ordem': 'ORD-1'})
        s.save()

    def test_clique_sem_pendente_abre_confirmacao(self):
        self._sessao()
        resp = self.client.post(reverse('efetivar_apontamento_oracle'))
        self.assertRedirects(resp, reverse('efetivar_mega_oracle'), fetch_redirect_response=False)
        resp = self.client.get(reverse('efetivar_mega_oracle'))
        self.assertContains(resp, 'Efetivar no Mega')
        self.assertContains(resp, '7001')

    def test_clique_com_pendente_grava_e_volta(self):
        self._sessao()
        _lote()
        resp = self.client.post(reverse('efetivar_apontamento_oracle'))
        self.assertRedirects(resp, reverse('manutencao'), fetch_redirect_response=False)
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')

    def test_post_da_data_efetiva(self):
        self._sessao()
        resp = self.client.post(reverse('efetivar_mega_oracle'), {'data_apontamento': '2026-10-20T17:30'})
        self.assertRedirects(resp, reverse('manutencao'), fetch_redirect_response=False)
        self.mocks['efetivar'].assert_called_once()
