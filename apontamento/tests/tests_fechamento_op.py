# -*- coding: utf-8 -*-
# AJUSTE 2026-10-20 (JPC): testes do Fechar OP -- guia Acumulado da OP (um fechamento por OP/dia,
# total geral), data so a do controle, totais por CTL e "Deseja iniciar um novo apontamento?".
import json
from datetime import date, datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apontamento.api_view import Fechamento
from apontamento.models import Apt_Controle
from apontamento.services import controle_db
from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas, apt_pro_ordens

CTL = 700


def _controle(ctl, status='A', login=None, **fec):
    return Apt_Controle.objects.create(CTL_IN_CODIGO=ctl, CTL_ST_USUARIO='OPER', ORD_IN_CODIGO=900, FIL_IN_CODIGO=3,
                                       CTL_DT_LOGIN=login or timezone.now(), CTL_ST_IPADDRESS='1',
                                       CTL_ST_STATUS=status, ORD_ST_EXTENSO='0030000900010', **fec)


def _fechado(ctl, dia, ini, fim, prod, dem, liquido=60):
    return _controle(ctl, status='F', FEC_DT_APONTAMENTO=dia, FEC_HR_INICIO=ini, FEC_HR_FIM=fim,
                     FEC_RE_QTD_PRODUZIDA=prod, FEC_RE_QTD_DEMANDAS=dem, FEC_IN_TEMPO_LIQUIDO=liquido,
                     FEC_USU_INCLUSAO='OPER')


class AcumuladoTests(TestCase):
    def test_um_fechamento_por_dia_soma_os_controles(self):
        _fechado(1, date(2026, 10, 15), time(7, 0), time(12, 0), 4, 10, 270)
        _fechado(2, date(2026, 10, 15), time(13, 0), time(17, 0), 2, 5, 240)   # mesmo dia: soma
        _fechado(3, date(2026, 10, 16), time(7, 0), time(17, 0), 3, 0, 525)    # sem demanda
        ac = Fechamento.acumulado_op(controle_db().fechamentos_da_op(3, 900, exceto_ctl=CTL),
                                     date(2026, 10, 16), 1.5, 3)
        d15, d16 = ac['dias']
        self.assertEqual((d15['produzida'], d15['demandas'], d15['controles']), (6.0, 15.0, 2))
        self.assertEqual((d15['hr_inicio'], d15['hr_fim'], d15['tempo_txt']), ('07:00', '17:00', '8h 30m'))
        self.assertEqual(d15['rendimento'], 40.0)                      # 6 / 15 x 100
        self.assertIsNone(d16['rendimento'])                           # sem demanda
        self.assertTrue(ac['atual']['soma_ao_dia'])                    # ja existe fechamento em 16/10
        self.assertEqual(ac['atual']['rendimento'], 50.0)
        self.assertEqual((ac['total']['produzida'], ac['total']['demandas'], ac['total']['dias']), (10.5, 18.0, 2))
        self.assertEqual(ac['total']['rendimento'], round(10.5 / 18 * 100, 2))

    def test_fechamento_atual_fica_fora_da_lista(self):
        _fechado(CTL, date(2026, 10, 15), time(7, 0), time(17, 0), 4, 10)
        self.assertEqual(controle_db().fechamentos_da_op(3, 900, exceto_ctl=CTL), [])

    def test_so_a_data_do_controle(self):
        self.assertEqual(Fechamento.datas_permitidas(date(2026, 10, 19)), {date(2026, 10, 19)})

    def test_totais_por_ctl_e_nao_por_data(self):
        # particularidade PRODUCAO: lote apontado hoje no CTL de ontem entra no fechamento de ontem
        _controle(CTL)
        for seq, dia, ctl, st in ((1, date(2026, 10, 19), CTL, 'I'), (2, date(2026, 10, 20), CTL, 'A'),
                                  (3, date(2026, 10, 19), 701, 'A'), (4, date(2026, 10, 19), CTL, 'C')):
            Apt_ApontaOrdem.objects.create(FIL_IN_CODIGO=3, APT_IN_SEQUENCIA=seq, APT_DT_APONTAMENTO=dia,
                                           APT_CH_STATUS=st, ORD_IN_CODIGO=900, PRO_IN_CODIGO=1, ORL_RE_QTDLOTE=2,
                                           ORL_ST_REFERENCIA='x', CTL_IN_CODIGO=ctl, PRO_ST_LOTE=f'L{seq}')
        Apt_Pro_Demandas.objects.create(FIL_IN_CODIGO=3, MOV_IN_SEQUENCIA=9, MOV_DT_INCLUSAO=date(2026, 10, 20),
                                        ORD_IN_CODIGO=900, PRO_RE_QTDLOTE=5, PRO_ST_LOTE='D', MOV_ST_STATUS='A',
                                        CTL_IN_CODIGO=CTL)
        self.assertEqual(controle_db().get_totais_ctl(CTL), {'produzida': 4, 'demandas': 5})


class TelaFechamentoTests(TestCase):
    def setUp(self):
        apt_pro_ordens.objects.create(ORG_TAB_IN_CODIGO=1, ORG_PAD_IN_CODIGO=1, ORG_IN_CODIGO=2,
                                      ORG_TAU_ST_CODIGO='G', ORD_TAB_IN_CODIGO=218, ORD_SEQ_IN_CODIGO=1,
                                      ORD_IN_CODIGO=900, PRO_TAB_IN_CODIGO=100, PRO_PAD_IN_CODIGO=1,
                                      PRO_IN_CODIGO=2273, ORD_RE_QTDE_ORDEM=10, FIL_IN_CODIGO=3)
        self.ctl = _controle(CTL, login=timezone.make_aware(datetime(2026, 10, 19, 10, 0)))
        s = self.client.session
        s.update({'usuario': 'OPER', 'ordem': 'ORD-1', 'ord_in_codigo': 900, 'fil_in_codigo': 3,
                  'ctl_in_codigo': CTL, 'seq_in_operacao': 1, 'cliente': '1'})
        s.save()

    def test_abas_acumulado_e_aviso_de_soma(self):
        _fechado(1, date(2026, 10, 19), time(7, 0), time(9, 0), 1, 2)
        html = self.client.get(reverse('fechar_op_diario')).content.decode()
        self.assertIn('Acumulado da OP', html)
        self.assertIn('Total geral', html)
        self.assertIn('somado ao fechamento do dia', html)
        self.assertIn('readonly required', html)  # data travada na do controle

    def _post(self, data):
        ok = {'erro_oracle': None, 'erro': 0, 'erros': [], 'efetivado_oracle': True, 'atividade': 2}
        with patch('apontamento.integracao_apontamento.efetivar_apontamento', return_value=ok):
            return self.client.post(reverse('fechar_op_diario'), {
                'FEC_DT_DATA': data, 'FEC_HR_INICIO': '07:00', 'FEC_HR_FIM': '17:00',
                'FEC_RE_QTD_PRODUZIDA': '0', 'FEC_RE_QTD_DEMANDAS': '0'})

    def test_registra_e_pergunta_novo_apontamento(self):
        resp = self._post('2026-10-19')
        self.assertRedirects(resp, reverse('confirmar_novo_apontamento'), fetch_redirect_response=False)
        self.assertEqual(Apt_Controle.objects.get(CTL_IN_CODIGO=CTL).CTL_ST_STATUS, 'F')

    def test_data_diferente_da_do_controle_recusada(self):
        resp = self._post('2026-10-20')
        self.assertRedirects(resp, reverse('fechar_op_diario'), fetch_redirect_response=False)
        self.assertEqual(Apt_Controle.objects.get(CTL_IN_CODIGO=CTL).CTL_ST_STATUS, 'A')


class NovoApontamentoTests(TestCase):
    def setUp(self):
        s = self.client.session
        s.update({'usuario': 'OPER', 'ordem': '0030000900010', 'ord_in_codigo': 900, 'fil_in_codigo': 3,
                  'ctl_in_codigo': CTL, 'cliente': '1'})  # ordem = codigo de barras (13 digitos)
        s.save()

    def test_pergunta(self):
        self.assertContains(self.client.get(reverse('confirmar_novo_apontamento')), 'Deseja iniciar um novo apontamento?')

    def test_sim_abre_controle_novo_sem_login(self):
        novo = json.dumps([{'ctl_in_codigo': 701, 'logado': True, 'pro_st_descricao': 'Item'}])
        with patch('apontamento.views.Login_inicial_sqlite.conectar_sqlite', return_value=novo):
            resp = self.client.post(reverse('confirmar_novo_apontamento'), {'criar': 'sim'})
        self.assertRedirects(resp, reverse('menu'), fetch_redirect_response=False)
        self.assertEqual(self.client.session['ctl_in_codigo'], 701)

    def test_nao_encerra_a_sessao(self):
        resp = self.client.post(reverse('confirmar_novo_apontamento'), {'criar': 'nao'})
        self.assertRedirects(resp, reverse('demos_sessions'), fetch_redirect_response=False)
        self.assertNotIn('ctl_in_codigo', self.client.session)
