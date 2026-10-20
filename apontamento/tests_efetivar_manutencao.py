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
            # AJUSTE 2026-10-20: protecoes do NMV -- releitura pela chave exata, itens do CTL no Mega
            # (espelho do que esta 'I' no app) e status do apontamento no Mega ('A' = aberto)
            'confirmar': patch('apontamento.apontamento.confirmar_no_oracle',
                               side_effect=lambda con, tipo, chaves: {k: 7001 for k in chaves}),
            'itens': patch('apontamento.apontamento.itens_do_ctl_no_oracle', side_effect=self._itens_mega),
            'status': patch('apontamento.apontamento._apt_ch_status', return_value='A'),
        }
        self.mocks = {k: p.start() for k, p in self.m.items()}
        for p in self.m.values():
            self.addCleanup(p.stop)

    @staticmethod
    def _itens_mega(con, fil, ord_, ctl):
        return {'lotes': {l.APT_IN_SEQUENCIA: 7001 for l in Apt_ApontaOrdem.objects.filter(
                    CTL_IN_CODIGO=ctl, APT_CH_STATUS='I')},
                'demandas': {d.MOV_IN_SEQUENCIA: 7001 for d in Apt_Pro_Demandas.objects.filter(
                    CTL_IN_CODIGO=ctl, MOV_ST_STATUS='I')}}


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
        self.mocks['status'].return_value = 'E'  # ja efetivado no Mega
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


class ProtecoesTests(_ComOracle):
    """AJUSTE 2026-10-20: protecoes copiadas do NMV validado (conexao testada, limite de tempo,
    'I' so depois de reler no Oracle, CTL inteiro conferido antes de efetivar)."""

    def test_sem_conexao_nada_gravado(self):
        _lote()
        self.mocks['abrir'].side_effect = ConnectionError('Nao foi possivel conectar ao Oracle.')
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 1)
        self.assertEqual(r['erro_oracle'], integ.MSG_SEM_CONEXAO)
        self.mocks['lote'].assert_not_called()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')

    def test_lock_vira_mensagem_e_nada_marcado(self):
        _lote()
        self.mocks['lote'].side_effect = Exception('DPY-4024: call timeout of 120000 ms exceeded')
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 1)
        self.assertEqual(r['erro_oracle'], integ.MSG_ORACLE_BLOQUEADO)
        self.con.rollback.assert_called_once()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')

    def test_limite_de_tempo_na_gravacao(self):
        _lote()
        tempos = []
        self.mocks['lote'].side_effect = lambda *a, **k: (tempos.append(self.con.call_timeout),
                                                          [{'mensagem': 'Ok', 'mensagem_sub': 'Ok',
                                                            'sequencia': 7001}])[1]
        integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 1)
        self.assertEqual(tempos, [integ.GRAVACAO_TIMEOUT_MS])
        self.assertEqual(self.con.call_timeout, 0)

    def test_nao_confirmado_no_oracle_nao_marca(self):
        _lote()
        _demanda()
        self.mocks['confirmar'].side_effect = lambda con, tipo, chaves: {}
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 1)
        self.assertIn('não foi possível confirmar', r['erro_oracle'])
        self.con.commit.assert_called_once()  # gravou no Oracle; o retry nao regrava
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'A')

    def test_item_no_mega_que_o_app_nao_tem_bloqueia_efetivar(self):
        _lote(status='I')
        self.mocks['itens'].side_effect = lambda con, fil, ord_, ctl: {'lotes': {1: 7001, 999: 7001}, 'demandas': {}}
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 2, datetime(2026, 10, 20, 17, 0))
        self.assertIn('cancelado(s) ou inexistente(s) no app: [999]', r['erro_oracle'])
        self.mocks['efetivar'].assert_not_called()

    def test_dois_apontamentos_abertos_bloqueia(self):
        _lote(1, status='I')
        _lote(2, status='I')
        self.mocks['itens'].side_effect = lambda con, fil, ord_, ctl: {'lotes': {1: 7001, 2: 7002}, 'demandas': {}}
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_ETAPA_UNICA, 1, datetime(2026, 10, 20, 17, 0))
        self.assertIn('mais de um apontamento aberto', r['erro_oracle'])
        self.mocks['efetivar'].assert_not_called()

    def test_apontamento_ja_efetivado_nao_conta(self):
        # particularidade PRODUCAO: 7001 efetivado pelo botao no meio do dia; 7002 aberto depois
        _lote(1, status='I')
        _lote(2, status='I')
        self.mocks['itens'].side_effect = lambda con, fil, ord_, ctl: {'lotes': {1: 7001, 2: 7002}, 'demandas': {}}
        self.mocks['status'].side_effect = lambda cur, apt: 'E' if apt == 7001 else 'A'
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_ETAPA_UNICA, 1, datetime(2026, 10, 20, 17, 0))
        self.assertEqual((r['erro_oracle'], r['apt_in_sequencia']), (None, 7002))


class CronDiretoTests(_ComOracle):
    """AJUSTE 2026-10-20: api_producao (cron) grava direto nas tabelas -- atividade 3, sem efetivar."""

    def setUp(self):
        super().setUp()
        import sys
        sys.modules.setdefault('fcntl', MagicMock())  # api_producao importa fcntl (so existe no Linux)
        import api_producao
        self.api = api_producao
        Apt_Controle.objects.filter(CTL_IN_CODIGO=CTL).update(CTL_ST_STATUS='A', ORD_ST_EXTENSO='0030000900010')
        sit = patch.object(api_producao.integrador, 'situacao_ordem', return_value='AB')
        self.situacao = sit.start()
        self.addCleanup(sit.stop)

    def _rodar(self):
        self.api.integrador([2, 3, None, None]).integraOrdensDireto()

    def test_grava_pendentes_sem_efetivar(self):
        _lote()
        _demanda()
        self._rodar()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'I')
        self.assertEqual(self.mocks['lote'].call_args[0][0]['plf_in_sqoperacao'], 10)  # do ORD_ST_EXTENSO
        self.mocks['efetivar'].assert_not_called()
        self.assertEqual(Apt_Controle.objects.get().CTL_ST_STATUS, 'A')  # nao encerra o CTL

    def test_sem_pendente_nao_abre_oracle(self):
        _lote(status='I')
        self._rodar()
        self.mocks['abrir'].assert_not_called()

    def test_lock_fica_para_o_proximo_ciclo(self):
        _lote()
        self.mocks['lote'].side_effect = Exception('DPY-4024: call timeout')
        self._rodar()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')

    def test_ordem_encerrada_no_mega_encerra_o_controle(self):
        _lote()
        self.situacao.return_value = 'EN'
        with patch.object(self.api.requests, 'put') as put:
            self._rodar()
        self.assertEqual(put.call_args.kwargs['params'], {'ctl_in_codigo': CTL, 'status': 'E'})
        self.mocks['lote'].assert_not_called()

    def test_controle_fechado_nao_entra(self):
        _lote()
        Apt_Controle.objects.update(CTL_ST_STATUS='F')
        self._rodar()
        self.mocks['abrir'].assert_not_called()


class AtividadesTests(_ComOracle):
    """AJUSTE 2026-10-20: rotina unica efetivar_apontamento, cada forma de efetivar e uma atividade."""

    def test_atividade_e_etapa_no_resultado(self):
        _lote()
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 1)
        self.assertEqual((r['atividade'], r['etapa'], r['ok']), (1, 1, 1))
        r = integ.efetivar_apontamento(SESSAO, integ.ATIVIDADE_DUAS_ETAPAS, 2, datetime(2026, 10, 20, 17, 0))
        self.assertEqual((r['atividade'], r['etapa'], r['efetivado_oracle']), (1, 2, True))

    def test_atividade_ou_etapa_inexistente(self):
        for atividade, etapa in ((9, 1), (integ.ATIVIDADE_DUAS_ETAPAS, 3), (integ.ATIVIDADE_ETAPA_UNICA, 2)):
            r = integ.efetivar_apontamento(SESSAO, atividade, etapa)
            self.assertIn('inexistente', r['erro_oracle'])
        self.mocks['abrir'].assert_not_called()

    def test_atividade_desligada_nao_grava(self):
        _lote()
        for chave, atividade in (('BOTAO_EFETIVAR_TODAS_OPS', integ.ATIVIDADE_DUAS_ETAPAS),
                                 ('FECHAMENTO_GRAVA_ORACLE', integ.ATIVIDADE_ETAPA_UNICA)):
            with patch.object(integ, chave, False):
                r = integ.efetivar_apontamento(SESSAO, atividade, 1)
            self.assertIn('desligada', r['erro_oracle'])
        self.mocks['abrir'].assert_not_called()
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'A')

    def test_chaves_ligadas(self):
        self.assertTrue(integ.atividade_ligada(integ.ATIVIDADE_DUAS_ETAPAS))
        self.assertTrue(integ.atividade_ligada(integ.ATIVIDADE_ETAPA_UNICA))  # fechamento grava no Mega


class FechamentoAtividade2Tests(_ComOracle):
    """Fechamento diario chama a atividade 2 (etapa unica) com a data da tela + hora fim."""

    def setUp(self):
        super().setUp()
        Apt_Controle.objects.filter(CTL_IN_CODIGO=CTL).update(CTL_ST_STATUS='A')
        from app.models import apt_pro_ordens
        apt_pro_ordens.objects.create(ORG_TAB_IN_CODIGO=1, ORG_PAD_IN_CODIGO=1, ORG_IN_CODIGO=2,
                                      ORG_TAU_ST_CODIGO='G', ORD_TAB_IN_CODIGO=218, ORD_SEQ_IN_CODIGO=1,
                                      ORD_IN_CODIGO=900, PRO_TAB_IN_CODIGO=100, PRO_PAD_IN_CODIGO=1,
                                      PRO_IN_CODIGO=2273, ORD_RE_QTDE_ORDEM=10, FIL_IN_CODIGO=3)

    def _fechar(self):
        from apontamento.api_view import Fechamento
        return Fechamento.registrar(900, '2026-10-20', '07:00', '17:00', 'OPER', qtd_produzida=1, filial=3,
                                    ctl_in_codigo=CTL, seq_in_operacao=1, ord_st_extenso='ORD-1')

    def test_grava_efetiva_com_a_data_da_tela_e_fecha(self):
        _lote()
        ok, dados, erro = self._fechar()
        self.assertEqual((ok, erro), (True, None))
        self.assertEqual(dados['oracle']['atividade'], integ.ATIVIDADE_ETAPA_UNICA)
        self.assertEqual(self.mocks['efetivar'].call_args.kwargs['data_apontamento'], datetime(2026, 10, 20, 17, 0))
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')
        self.assertEqual(Apt_Controle.objects.get().CTL_ST_STATUS, 'F')

    def test_erro_no_oracle_nao_fecha(self):
        _lote()
        self.mocks['efetivar'].return_value = ('Erro: ORA-1', False)
        ok, _dados, erro = self._fechar()
        self.assertFalse(ok)
        self.assertIn('não efetivado', erro)
        self.assertEqual(Apt_Controle.objects.get().CTL_ST_STATUS, 'A')

    def test_sem_conexao_nao_fecha(self):
        self.mocks['abrir'].side_effect = ConnectionError('Nao foi possivel conectar ao Oracle.')
        ok, _dados, erro = self._fechar()
        self.assertFalse(ok)
        self.assertIn('Oracle', erro)
        self.assertEqual(Apt_Controle.objects.get().CTL_ST_STATUS, 'A')

    def test_botao_ja_efetivou_fechamento_so_fecha(self):
        # atividade 1 ja gravou e efetivou: nada pendente e nada aberto no Mega -> fecha sem efetivar
        _lote(status='I')
        self.mocks['status'].return_value = 'E'  # apontamento do CTL ja efetivado pelo botao
        ok, _dados, erro = self._fechar()
        self.assertEqual((ok, erro), (True, None))
        self.mocks['efetivar'].assert_not_called()
        self.assertEqual(Apt_Controle.objects.get().CTL_ST_STATUS, 'F')


class ViewsEfetivarTests(_ComOracle):
    def _sessao(self):
        s = self.client.session
        s.update({'ctl_in_codigo': CTL, 'usuario': 'OPER', 'ord_in_codigo': 900, 'fil_in_codigo': 3,
                  'seq_in_operacao': 1, 'ordem': 'ORD-1'})
        s.save()

    def test_clique_sem_pendente_abre_confirmacao(self):
        self._sessao()
        _lote(status='I')  # ja integrado (apontamento 7001 aberto no Mega)
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
        _lote(status='I')  # ja integrado (apontamento 7001 aberto no Mega)
        resp = self.client.post(reverse('efetivar_mega_oracle'), {'data_apontamento': '2026-10-20T17:30'})
        self.assertRedirects(resp, reverse('manutencao'), fetch_redirect_response=False)
        self.mocks['efetivar'].assert_called_once()
