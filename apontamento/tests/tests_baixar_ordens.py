# -*- coding: utf-8 -*-
"""AJUSTE 2026-11-11 (JPC): baixar ordens -- melhor do NMV/ZK no PRODUCAO. Telas entendem o JSON novo e o antigo,
nenhum botao novo aparece, item/ordem existente e atualizado, tipo da caracteristica nao e apagado, erros cercados
(coluna ausente no Mega, falha ao atualizar caracteristica) e o script de atualizacao em massa."""
import json
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from app.models import Car_AtributosReferencia, apt_itens_ordens, apt_pro_ordens


class TelaLotesJsonTests(SimpleTestCase):
    def _render(self, lista):
        return render_to_string('apontamento/js_html/js_prod.html', {'lista': lista, 'ord_in_codigo': 900})

    def test_lista_com_none_e_true_vai_como_json_valido(self):
        html = self._render([{'pro_in_codigo': 1, 'mvs_st_referencia': None, 'ativo': True}])
        bloco = html.split('id="itens-ordem"')[1].split('>', 1)[1].split('</script>')[0]
        self.assertEqual(json.loads(bloco), [{'pro_in_codigo': 1, 'mvs_st_referencia': None, 'ativo': True}])
        self.assertNotIn('litens = {{', html)
        self.assertNotIn("'mvs_st_referencia': None", html)  # nada de repr do Python no script

    def test_teclado_numerico_pelo_tipo_e_medidas_sem_tipo_continuam(self):
        html = self._render([])
        self.assertIn("criainput(v_descricaoRef, v_referencia[i].RAT_VALUE, null, v_referencia[i].RAT_CH_TIPOCONTEUDO)", html)
        self.assertIn("if (tipo == 'N' || (!tipo && medida))", html)
        self.assertIn("var_nome=='id_Comprimento'", html)  # 'id_ComprImento' nunca casava

    def test_regra_do_conversor_nao_mudou(self):
        html = self._render([])
        self.assertIn('v_conversor = v_conversor.filter(function(c) { return c && c.UNI_ST_FORMULA; });', html)


class ManutencaoSemBotaoNovoTests(TestCase):
    def test_mesmos_quatro_botoes(self):
        s = self.client.session
        s.update({'ord_in_codigo': 900, 'fil_in_codigo': 3})
        s.save()
        html = self.client.get('/prod/manutencao/').content.decode()
        for botao in ('Baixar Ordens', 'Encerrar', 'Integrar', 'Efetivar Apontamento'):
            self.assertIn(botao, html)
        for novo in ('Sincronizar Ordens (nova)', 'Centro de Trabalho', 'Conversor'):
            self.assertNotIn(novo, html)
        self.assertNotIn('Gravar no Oracle os lotes e demandas pendentes', html)  # o botao so abre a tela


class PostOrdensItensTests(TestCase):
    ITEM = {'PRO_TAB_IN_CODIGO': 100, 'PRO_PAD_IN_CODIGO': 1, 'PRO_IN_CODIGO': 2273, 'PRO_ST_DESCRICAO': 'Velha',
            'UNI_ST_UNIDADE': 'M3', 'RFC_IN_CODIGO': 0, 'PRO_ST_ATRIBUTOS': '[]', 'PRO_ST_REFERENCIA': '[]',
            'PRO_ST_MEDIDAS': '[]', 'MVS_ST_REFERENCIA': 'Indefinido', 'PRO_ST_CONVERSOR': '[{"CONVERSORES": null}]'}

    def test_item_novo_201_existente_atualizado_200_sem_duplicar(self):
        r = self.client.post('/app/itensOrdens/', self.ITEM)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(apt_itens_ordens.objects.get().PRO_ST_ID, '1000010002273')  # ID montado
        r = self.client.post('/app/itensOrdens/', dict(self.ITEM, PRO_ST_DESCRICAO='Nova'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(apt_itens_ordens.objects.count(), 1)
        self.assertEqual(apt_itens_ordens.objects.get().PRO_ST_DESCRICAO, 'Nova')

    def test_ordem_existente_atualizada(self):
        ordem = {'ORG_TAB_IN_CODIGO': 1, 'ORG_PAD_IN_CODIGO': 1, 'ORG_IN_CODIGO': 2, 'ORG_TAU_ST_CODIGO': 'G',
                 'ORD_TAB_IN_CODIGO': 218, 'ORD_SEQ_IN_CODIGO': 3, 'ORD_IN_CODIGO': 900, 'PRO_TAB_IN_CODIGO': 100,
                 'PRO_PAD_IN_CODIGO': 1, 'PRO_IN_CODIGO': 2273, 'ORD_RE_QTDE_ORDEM': '1', 'FIL_IN_CODIGO': 3,
                 'PRO_ST_ITENS': '[]', 'PRO_ST_DEMANDAS': '[]', 'PRO_ST_INFOADIC': '{}'}
        self.assertEqual(self.client.post('/app/ordens/', ordem).status_code, 201)
        self.assertEqual(self.client.post('/app/ordens/', dict(ordem, ORD_RE_QTDE_ORDEM='5')).status_code, 200)
        self.assertEqual(apt_pro_ordens.objects.count(), 1)
        self.assertEqual(float(apt_pro_ordens.objects.get().ORD_RE_QTDE_ORDEM), 5.0)

    def test_erro_inesperado_vira_409_nunca_500(self):
        with patch('app.views.apt_itens_ordens.objects.filter', side_effect=RuntimeError('disco')):
            r = self.client.post('/app/itensOrdens/', self.ITEM)
        self.assertEqual(r.status_code, 409)
        self.assertIn('disco', r.json()['erro'])


class CaracteristicaExistenteTests(TestCase):
    CAR = {'CAR_ST_ID': 'C1', 'RAT_ST_ID': 'R', 'RFC_ST_ID': 'F', 'PAI_RAT_IN_CODIGO': 1, 'RAT_IN_CODIGO': 2,
           'RAT_ST_DESCRICAO': 'Cor', 'RAT_VALUE': 'v', 'RAT_CH_TIPO': 'L', 'CAR_IN_PRIORIDADE': 1, 'RFC_IN_CODIGO': 9,
           'RAT_BO_GRUPO': 'N', 'CAR_BO_OBRIGATORIO': 'S', 'PAI_ST_DESCRICAO': 'P'}

    def test_atualiza_sem_apagar_o_tipo_gravado(self):
        from app.sincronizacao import atualizar_caracteristica_existente
        Car_AtributosReferencia.objects.create(**dict(self.CAR, RAT_ST_DESCRICAO='Antiga', RAT_CH_TIPOCONTEUDO='N'))
        campos = atualizar_caracteristica_existente(dict(self.CAR))  # get_referencia daqui nao manda o tipo
        self.assertEqual(campos, ['RAT_ST_DESCRICAO'])
        c = Car_AtributosReferencia.objects.get()
        self.assertEqual((c.RAT_ST_DESCRICAO, c.RAT_CH_TIPOCONTEUDO), ('Cor', 'N'))

    def test_falha_ao_atualizar_nao_derruba_a_baixa(self):
        from apontamento.api_view import _atualizar_caracteristica
        with patch('app.sincronizacao.atualizar_caracteristica_existente', side_effect=RuntimeError('x')):
            _atualizar_caracteristica({'CAR_ST_ID': 'C1'})  # nao levanta


class TipoNoMegaTests(SimpleTestCase):
    def test_sem_a_coluna_no_mega_le_sem_ela(self):
        from api import services as oracle
        chamadas = []

        def fake(con, fil, rfc, coluna):
            chamadas.append(coluna)
            if coluna:
                raise Exception('ORA-00904: "AR"."RAT_CH_TIPOCONTEUDO": invalid identifier')
            return [{'CAR_ST_ID': 'C1'}]
        with patch.object(oracle, '_caracteristicas_referencia', side_effect=fake):
            self.assertEqual(oracle.sync_caracteristicas_referencia(None, 3, 9), [{'CAR_ST_ID': 'C1'}])
        self.assertEqual(chamadas, [', ar.rat_ch_tipoconteudo', ''])

    def test_outro_erro_do_mega_nao_e_escondido(self):
        from api import services as oracle
        with patch.object(oracle, '_caracteristicas_referencia', side_effect=Exception('ORA-12541')):
            with self.assertRaises(Exception):
                oracle.sync_caracteristicas_referencia(None, 3, 9)


class ScriptAtualizarOrdensTests(TestCase):
    def setUp(self):
        for ordem in (900, 901):
            apt_pro_ordens.objects.create(ORG_TAB_IN_CODIGO=1, ORG_PAD_IN_CODIGO=1, ORG_IN_CODIGO=2,
                                          ORG_TAU_ST_CODIGO='G', ORD_TAB_IN_CODIGO=218, ORD_SEQ_IN_CODIGO=3,
                                          ORD_IN_CODIGO=ordem, PRO_TAB_IN_CODIGO=100, PRO_PAD_IN_CODIGO=1,
                                          PRO_IN_CODIGO=2273, ORD_RE_QTDE_ORDEM=1, FIL_IN_CODIGO=3)

    def _rodar(self, *args, encerradas=(), sinc=None):
        con = MagicMock()
        con.__enter__.return_value = con
        cur = MagicMock()
        cur.__enter__.return_value = cur
        cur.callfunc.side_effect = lambda nome, tipo, params: 'EN' if params[1] in encerradas else 'AB'
        con.cursor.return_value = cur
        saida = StringIO()
        with patch('app.sincronizacao.conexao_oracle_testada', return_value=con), \
                patch('app.sincronizacao.sincronizar_ordens', side_effect=sinc or (
                    lambda *a, **k: {'ordens': [{'situacao': 'diferente'}], 'itens': {'novos': 0, 'diferentes': [1]},
                                     'erros': []})) as s, \
                patch('app.sincronizacao.normalizar_itens_existentes', return_value=(4, [])) as norm, \
                patch('app.sincronizacao.atualizar_tipos_caracteristicas', return_value=(2, [])):
            call_command('atualizar_ordens_mega', *args, stdout=saida, stderr=StringIO())
        return s, norm, saida.getvalue()

    def test_atualiza_so_as_nao_encerradas_no_mega(self):
        s, norm, saida = self._rodar(encerradas=(901,))
        self.assertEqual([c.args[2] for c in s.call_args_list], [900])
        self.assertTrue(s.call_args.kwargs['gravar'])
        self.assertFalse(s.call_args.kwargs['normalizar'])  # normaliza uma vez so, antes
        norm.assert_called_once()
        self.assertIn('encerradas_mega        1', saida)
        self.assertIn('atualizadas            1', saida)

    def test_simular_nao_grava(self):
        s, norm, _saida = self._rodar('--simular')
        self.assertTrue(all(c.kwargs['gravar'] is False for c in s.call_args_list))
        norm.assert_not_called()

    def test_erro_numa_op_nao_derruba_as_outras(self):
        def sinc(org, fil, ordem, *a, **k):
            if ordem == 900:
                raise RuntimeError('falhou')
            return {'ordens': [{'situacao': 'igual'}], 'itens': {}, 'erros': []}
        s, _norm, saida = self._rodar(sinc=sinc)
        self.assertEqual(s.call_count, 2)
        self.assertIn('iguais                 1', saida)

    def test_sem_mega_nada_feito(self):
        with patch('app.sincronizacao.conexao_oracle_testada', return_value=None), \
                patch('app.sincronizacao.sincronizar_ordens') as s:
            call_command('atualizar_ordens_mega', stdout=StringIO(), stderr=StringIO())
        s.assert_not_called()
