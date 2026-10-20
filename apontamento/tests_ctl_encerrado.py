# -*- coding: utf-8 -*-
# AJUSTE 2026-10-20 (JPC): CTL encerrado so para consulta -- apontamento, fechamento e baixa/cancelamento
# de demanda/lote bloqueados; consultas liberadas.
from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apontamento.models import Apt_Controle
from apontamento.views import MSG_CTL_ENCERRADO
from app.models import Apt_ApontaOrdem, Apt_Pro_Demandas

CTL = 800


class CtlEncerradoTests(TestCase):
    def setUp(self):
        Apt_Controle.objects.create(CTL_IN_CODIGO=CTL, CTL_ST_USUARIO='OPER', ORD_IN_CODIGO=900, FIL_IN_CODIGO=3,
                                    CTL_DT_LOGIN=timezone.now(), CTL_ST_IPADDRESS='1', CTL_ST_STATUS='F',
                                    ORD_ST_EXTENSO='0030000900010')
        s = self.client.session
        s.update({'usuario': 'OPER', 'ordem': '0030000900010', 'ord_in_codigo': 900, 'fil_in_codigo': 3,
                  'ctl_in_codigo': CTL, 'seq_in_operacao': 1, 'cliente': '1'})
        s.save()

    def _bloqueado(self, url, metodo='get'):
        resp = getattr(self.client, metodo)(url)
        self.assertRedirects(resp, reverse('menu'), fetch_redirect_response=False)
        msgs = [str(m) for m in resp.wsgi_request._messages]
        self.assertIn(MSG_CTL_ENCERRADO.format(ctl=CTL), msgs)

    def test_apontamento_e_demanda_bloqueados(self):
        for nome in ('incluir_lote', 'apontamento', 'incluirdemanda', 'demanda', 'demandalocal',
                     'insDemanda', 'insDemandaslocal', 'fechar_op_diario'):
            with self.subTest(nome):
                self._bloqueado(reverse(nome))

    def test_cancelar_lote_e_demanda_bloqueados(self):
        Apt_ApontaOrdem.objects.create(FIL_IN_CODIGO=3, APT_IN_SEQUENCIA=1, APT_DT_APONTAMENTO=date(2026, 10, 20),
                                       APT_CH_STATUS='I', ORD_IN_CODIGO=900, PRO_IN_CODIGO=1, ORL_RE_QTDLOTE=1,
                                       ORL_ST_REFERENCIA='x', CTL_IN_CODIGO=CTL, PRO_ST_LOTE='L1')
        Apt_Pro_Demandas.objects.create(FIL_IN_CODIGO=3, MOV_IN_SEQUENCIA=2, MOV_DT_INCLUSAO=date(2026, 10, 20),
                                        ORD_IN_CODIGO=900, PRO_RE_QTDLOTE=1, PRO_ST_LOTE='D', MOV_ST_STATUS='I',
                                        CTL_IN_CODIGO=CTL)
        self._bloqueado(reverse('deleteapt', args=[1]))
        self._bloqueado(reverse('deletedemanda', args=[2]))
        self.assertEqual(Apt_ApontaOrdem.objects.get().APT_CH_STATUS, 'I')
        self.assertEqual(Apt_Pro_Demandas.objects.get().MOV_ST_STATUS, 'I')

    def test_fechar_op_nao_cai_em_outro_ctl_aberto_da_op(self):
        Apt_Controle.objects.create(CTL_IN_CODIGO=801, CTL_ST_USUARIO='OUTRO', ORD_IN_CODIGO=900, FIL_IN_CODIGO=3,
                                    CTL_DT_LOGIN=timezone.now(), CTL_ST_IPADDRESS='2', CTL_ST_STATUS='A')
        self._bloqueado(reverse('fechar_op_diario'), 'post')
        self.assertEqual(Apt_Controle.objects.get(CTL_IN_CODIGO=801).CTL_ST_STATUS, 'A')

    def test_ctl_aberto_passa(self):
        Apt_Controle.objects.filter(CTL_IN_CODIGO=CTL).update(CTL_ST_STATUS='A')
        resp = self.client.get(reverse('fechar_op_diario'))
        self.assertNotIn(MSG_CTL_ENCERRADO.format(ctl=CTL), [str(m) for m in resp.wsgi_request._messages])

    def test_consulta_liberada(self):
        resp = self.client.get(reverse('menu'))
        self.assertNotIn(MSG_CTL_ENCERRADO.format(ctl=CTL), [str(m) for m in resp.wsgi_request._messages])
