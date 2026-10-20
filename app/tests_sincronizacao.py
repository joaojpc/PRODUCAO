# -*- coding: utf-8 -*-
# AJUSTE 2026-10-20 (JPC): testes da sincronizacao nova de ordens (copiada do NMV, ajustada ao PRODUCAO).
import json
import pathlib
import re
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from app import services as local
from app import sincronizacao as sync
from app.models import apt_itens_ordens, apt_pro_ordens

PEND = [{'org_in_codigo': 2, 'ord_seq_in_codigo': 1, 'ord_in_codigo': 900}]
ORD_ST_ID = '0010010000002ORD218001' + '0' * 17 + '900'
DADOS = [{'ORG_TAB_IN_CODIGO': 1, 'ORG_PAD_IN_CODIGO': 1, 'ORG_IN_CODIGO': 2, 'ORG_TAU_ST_CODIGO': 'ORD',
          'ORD_TAB_IN_CODIGO': 218, 'ORD_SEQ_IN_CODIGO': 1, 'ORD_IN_CODIGO': 900, 'PRO_TAB_IN_CODIGO': 100,
          'PRO_PAD_IN_CODIGO': 1, 'PRO_IN_CODIGO': 2273, 'ORD_RE_QTDE_ORDEM': 10.0, 'FIL_IN_CODIGO': 3,
          'TPO_ST_CODIGO_TIPO': 'OP001', 'ORD_RE_UMIDADE': 9, 'LOTE_ORDEM': '07/03/26', 'ORD_ST_DESTINO': None,
          'PRO_ST_ID': '1000010002273', 'ORD_ST_ID': ORD_ST_ID, 'TPO_ST_ID': '100001OP001', 'ORD_ST_ORIGEM': None}]
# itens como a apt_intprod2 devolve no PRODUCAO (chaves minusculas)
ITENS = [{'pro_pad_in_codigo': 1, 'pro_in_codigo': 2273, 'pro_st_descricao': 'Massaranduba Seca 25x80mm',
          'uni_st_unidade': 'M3', 'rfc_in_codigo': 5, 'pro_re_comprimento': Decimal('2.5'), 'pro_re_largura': 80,
          'pro_re_espessura': 25, 'pro_st_madeira': 'Massaranduba', 'mvs_st_referencia': 'Indefinido',
          'pro_st_id': '1000010002273', 'pro_re_perda': 0, 'tipo_item': 'Produto'}]
CARS = [{'CAR_ST_ID': '001001000073000100000005', 'RAT_ST_ID': '0010010000730', 'RFC_ST_ID': '0010010000005',
         'PAI_RAT_IN_CODIGO': 730, 'RAT_IN_CODIGO': 731, 'RAT_ST_DESCRICAO': 'Seca', 'RAT_VALUE': '0000730=731',
         'RAT_CH_TIPO': 'P', 'CAR_IN_PRIORIDADE': 1, 'RFC_IN_CODIGO': 5, 'RAT_BO_GRUPO_NEW': 'N',
         'RAT_BO_GRUPO': 'N', 'CAR_BO_OBRIGATORIO': None, 'PAI_ST_DESCRICAO': 'Umidade'}]
OPERADORES = [{'OPD_ST_CRACHA': '0000000001', 'OPD_ST_NOME': 'ANILDO', 'FIL_IN_CODIGO': 3},
              {'OPD_ST_CRACHA': '0000000007', 'OPD_ST_NOME': 'DOUGLAS', 'FIL_IN_CODIGO': 3}]


def _oracle(pend=PEND, conversor=(), maquinas=None, operadores=()):
    alvo = 'api.services.'
    mocks = {
        'sync_ordens_pendentes': MagicMock(return_value=list(pend)),
        'sync_dados_ordem': MagicMock(side_effect=lambda con, o, s, n: [dict(DADOS[0], ORD_IN_CODIGO=n)]),
        'sync_demandas_ordem': MagicMock(return_value=[{'com_in_codigo': 2112, 'com_st_descricao': 'Tabicada',
                                                         'uni_st_unidade': 'M3'}]),
        'sync_itens_ordem': MagicMock(return_value=[dict(i) for i in ITENS]),
        'sync_conversor': MagicMock(return_value=list(conversor)),
        'sync_atributos_item': MagicMock(return_value=[{'pai_rat_in_codigo': 1, 'rat_in_codigo': 3,
                                                         'rat_st_descricao': '3.0 x 1.3m', 'rat_value': 'x',
                                                         'rat_ch_tipo': 'P'}]),
        'sync_referencias_item': MagicMock(return_value=[]),
        'sync_caracteristicas_referencia': MagicMock(return_value=[dict(c) for c in CARS]),
        'sync_maquinas': MagicMock(return_value=maquinas or [{'CTR_ST_ID': '0', 'CMAQ_ST_ID': '0'}]),
        'sync_operadores': MagicMock(return_value=[dict(o) for o in operadores]),
    }
    patchers = [patch(alvo + nome, m) for nome, m in mocks.items()]
    return patchers, mocks


class _ComOracle(TestCase):
    def _ligar(self, **kw):
        patchers, mocks = _oracle(**kw)
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)
        return mocks

    def _plano(self):
        return sync.montar_plano(MagicMock(), 2, 3, 900, 'N')


class LerJsonTests(TestCase):
    def test_decodifica_qualquer_camada(self):
        obj = [{'CONVERSORES': None}]
        self.assertEqual(local.ler_json(json.dumps(json.dumps(json.dumps(obj)))), obj)
        self.assertEqual(local.ler_json(obj), obj)
        self.assertEqual(local.ler_json('Indefinido'), 'Indefinido')

    def test_referencia_padrao_antigo_e_novo(self):
        ref = '0000730=732;0001750=2187;'
        novo = {'MVS_ST_REFERENCIA': ref, 'PRO_RE_CE': None, 'PRO_RE_APROV': None}
        for valor in (ref, novo, json.dumps(novo), json.dumps(json.dumps(novo))):
            self.assertEqual(local.referencia_padrao(valor), ref)
        for vazio in (None, '', 'Indefinido', {'MVS_ST_REFERENCIA': None},
                      json.dumps({'MVS_ST_REFERENCIA': 'Indefinido'})):
            self.assertEqual(local.referencia_padrao(vazio), 'Indefinido')
        # chaves maiusculas (apt_itens_ordens) e minusculas (itens da ordem)
        self.assertEqual(local.referencia_json({'MVS_ST_REFERENCIA': ref, 'PRO_RE_CE': 1}),
                         {'MVS_ST_REFERENCIA': ref, 'PRO_RE_CE': 1, 'PRO_RE_APROV': None})
        self.assertEqual(local.referencia_json({'mvs_st_referencia': ref}),
                         {'MVS_ST_REFERENCIA': ref, 'PRO_RE_CE': None, 'PRO_RE_APROV': None})

    def test_json_texto_sem_barra(self):
        self.assertEqual(local.json_texto([{'d': 'Tábua'}]), '[{"d": "Tábua"}]')


class MontarPlanoTests(_ComOracle):
    """Mesmo resultado da buscaOrdens do PRODUCAO, montado direto do Oracle."""

    def test_mesmas_regras_da_rotina_antiga(self):
        self._ligar()
        plano = self._plano()
        self.assertEqual(plano['erros'], [])
        o = plano['ordens'][0]['linha']
        self.assertEqual(o['TPO_ST_CODIGO'], 'OP001')
        self.assertEqual(o['PRO_ST_INFOADIC'], {'umidade': 9, 'lote_ordem': '07/03/26', 'destino': None,
                                                'origem': None})
        # itens da ordem seguem com chaves minusculas; mvs_st_referencia no padrao novo (JSON padrao)
        self.assertEqual(o['PRO_ST_ITENS'][0]['pro_in_codigo'], 2273)
        self.assertEqual(o['PRO_ST_ITENS'][0]['mvs_st_referencia'],
                         {'MVS_ST_REFERENCIA': 'Indefinido', 'PRO_RE_CE': None, 'PRO_RE_APROV': None})
        item = plano['itens']['1000010002273']
        self.assertEqual(item['PRO_ST_CONVERSOR'], [{'CONVERSORES': None}])   # conversor vazio
        self.assertEqual(item['PRO_ST_MEDIDAS'][0]['PRO_RE_COMPRIMENTO'], 2.5)  # Decimal -> float (DRF)
        self.assertEqual(item['PRO_TAB_IN_CODIGO'], 100)                        # vem da ordem
        self.assertEqual(item['MVS_ST_REFERENCIA']['MVS_ST_REFERENCIA'], 'Indefinido')
        car = plano['caracteristicas'][CARS[0]['CAR_ST_ID']]
        self.assertEqual(car['CAR_BO_OBRIGATORIO'], 'S')                        # default do modelo
        self.assertNotIn('RAT_BO_GRUPO_NEW', car)

    def test_rfc_zero_nao_busca_atributos(self):
        # rotina antiga do PRODUCAO: rfc_in_codigo 0 grava os marcadores e nao busca caracteristicas
        m = self._ligar()
        m['sync_itens_ordem'].return_value = [dict(ITENS[0], rfc_in_codigo=0)]
        plano = self._plano()
        item = plano['itens']['1000010002273']
        self.assertEqual(item['PRO_ST_ATRIBUTOS'], [{'PRO_ST_ATRIBUTOS': None}])
        self.assertEqual(item['PRO_ST_REFERENCIA'], [{'PRO_ST_REFERENCIA': None}])
        self.assertEqual(plano['caracteristicas'], {})
        m['sync_atributos_item'].assert_not_called()

    def test_cache_por_produto_entre_ops(self):
        m = self._ligar(pend=PEND + [dict(PEND[0], ord_in_codigo=901)])
        plano = sync.montar_plano(MagicMock(), 2, None, None, None)
        self.assertEqual(len(plano['ordens']), 2)
        self.assertEqual(m['sync_conversor'].call_count, 1)
        self.assertEqual(m['sync_caracteristicas_referencia'].call_count, 1)

    def test_erro_em_uma_op_nao_derruba_as_outras(self):
        m = self._ligar(pend=PEND + [dict(PEND[0], ord_in_codigo=901)])
        m['sync_dados_ordem'].side_effect = lambda con, o, s, n: (
            (_ for _ in ()).throw(RuntimeError('ORA-1')) if n == 900 else [dict(DADOS[0], ORD_IN_CODIGO=n)])
        plano = sync.montar_plano(MagicMock(), 2, None, None, None)
        self.assertEqual([o['ord'] for o in plano['ordens']], [901])
        self.assertIn('OP 900: ORA-1', plano['erros'])

    def test_item_invalido_vira_erro(self):
        m = self._ligar()
        m['sync_itens_ordem'].return_value = [dict(ITENS[0], pro_st_descricao='x' * 71)]
        plano = self._plano()
        self.assertEqual(plano['itens'], {})
        self.assertIn('texto maior', plano['erros'][0])

    def test_ids_nulos_sao_montados(self):
        m = self._ligar()
        m['sync_dados_ordem'].side_effect = lambda con, o, s, n: [dict(DADOS[0], ORD_IN_CODIGO=n, ORD_ST_ID=None,
                                                                       PRO_ST_ID=None)]
        m['sync_itens_ordem'].return_value = [dict(ITENS[0], pro_st_id=None)]
        plano = self._plano()
        self.assertEqual(plano['ordens'][0]['linha']['ORD_ST_ID'], ORD_ST_ID)        # monta_ordem
        self.assertEqual(plano['ordens'][0]['linha']['PRO_ST_ID'], '1000010002273')  # monta_produto
        self.assertEqual(list(plano['itens']), ['1000010002273'])

    def test_maquinas_sempre_comparadas(self):
        maq = [{'CTR_ST_ID': '1', 'CMAQ_ST_ID': '2', 'CTR_ST_NOME': 'C', 'CMAQ_ST_NOME': 'M', 'CMAQ_ST_CODIGO': 'X'}]
        self._ligar(maquinas=maq + [dict(maq[0])] + [dict(maq[0], CTR_ST_ID='0')])
        self.assertEqual(len(self._plano()['maquinas']), 1)
        with connection.cursor() as cur:
            local.inserir_maquinas(cur, [dict(maq[0], MAQ_CH_APONTAMENTO=1, MAQ_CH_DEMANDA=0)])
        comp = sync.comparar(self._plano())
        self.assertEqual((comp['maquinas_novas'], comp['maquinas_diferentes']), (0, 0))


class CompararGravarTests(_ComOracle):
    def test_nada_gravado_so_comparando(self):
        self._ligar()
        with patch.object(sync, 'SYNC_ORDENS_GRAVA', False):
            resumo = sync.sincronizar_ordens(2, 3, 900, 'N', conexao=MagicMock())
        self.assertFalse(resumo['gravado'])
        self.assertEqual(resumo['ordens'][0]['situacao'], 'nova')
        self.assertEqual(resumo['itens']['novos'], 1)
        self.assertEqual(apt_pro_ordens.objects.count(), 0)
        self.assertEqual(apt_itens_ordens.objects.count(), 0)

    def test_botao_grava_com_a_chave_ligada(self):
        self._ligar()
        self.assertTrue(sync.SYNC_ORDENS_GRAVA)
        resumo = sync.sincronizar_ordens(2, 3, 900, 'N', conexao=MagicMock())
        self.assertEqual((resumo['gravado'], resumo['ops_gravadas']), (True, 1))
        self.assertEqual((apt_pro_ordens.objects.count(), apt_itens_ordens.objects.count()), (1, 1))

    def test_gravar_normalizado_e_comparar_igual(self):
        self._ligar()
        gravadas, erros = sync.gravar(self._plano())
        self.assertEqual((gravadas, erros), (1, []))
        with connection.cursor() as cur:
            cur.execute("SELECT PRO_ST_CONVERSOR, json_type(PRO_ST_CONVERSOR), PRO_ST_DESCRICAO, MVS_ST_REFERENCIA "
                        "FROM apt_itens_ordens")
            texto, tipo, desc, mvs = cur.fetchone()
        self.assertEqual((texto, tipo), ('[{"CONVERSORES": null}]', 'array'))  # sem '\'
        self.assertEqual(desc, 'Massaranduba Seca 25x80mm')
        self.assertEqual(json.loads(mvs)['MVS_ST_REFERENCIA'], 'Indefinido')  # JSON padrao na coluna texto
        self.assertEqual(apt_itens_ordens.objects.get().PRO_ST_CONVERSOR, [{'CONVERSORES': None}])
        comp = sync.comparar(self._plano())
        self.assertEqual(comp['ordens'][0]['situacao'], 'igual')
        self.assertEqual((comp['itens']['iguais'], comp['caracteristicas_novas']), (1, 0))
        # regravar igual nao mexe em nada (mesma PK, nao duplica)
        pk_ordem, pk_item = apt_pro_ordens.objects.get().pk, apt_itens_ordens.objects.get().pk
        sync.gravar(self._plano())
        self.assertEqual((apt_pro_ordens.objects.count(), apt_itens_ordens.objects.count()), (1, 1))
        self.assertEqual((apt_pro_ordens.objects.get().pk, apt_itens_ordens.objects.get().pk), (pk_ordem, pk_item))

    def test_formato_antigo_duplo_compara_igual(self):
        """Item gravado como a rotina antiga (texto JSON dentro de texto) conta como igual."""
        self._ligar()
        plano = self._plano()
        item = plano['itens']['1000010002273']
        antigo = {c: (json.dumps(json.dumps(item[c])) if c in local.JSON_ITEM else item[c]) for c in local.COLUNAS_ITEM}
        with connection.cursor() as cur:
            local.inserir(cur, 'apt_itens_ordens', local.COLUNAS_ITEM, set(), antigo)
        self.assertEqual(sync.comparar(plano)['itens']['iguais'], 1)

    def test_mvs_texto_antigo_vira_json(self):
        """Item gravado pelo Baixar Ordens (MVS_ST_REFERENCIA texto cru) e atualizado para o JSON padrao."""
        self._ligar()
        plano = self._plano()
        item = dict(plano['itens']['1000010002273'], MVS_ST_REFERENCIA='Indefinido')
        with connection.cursor() as cur:
            local.inserir(cur, 'apt_itens_ordens', local.COLUNAS_ITEM, local.JSON_ITEM - {'MVS_ST_REFERENCIA'}, item)
        comp = sync.comparar(plano)
        self.assertEqual(comp['itens']['diferentes'][0]['campos'], ['MVS_ST_REFERENCIA'])
        sync.gravar(plano)
        mvs = apt_itens_ordens.objects.get().MVS_ST_REFERENCIA
        self.assertEqual(local.referencia_padrao(mvs), 'Indefinido')
        self.assertIsInstance(json.loads(mvs), dict)

    def _sqls_gravados(self, plano):
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            sync.gravar(plano)
        return [q['sql'] for q in ctx.captured_queries
                if q['sql'].split()[0].upper() in ('INSERT', 'UPDATE', 'DELETE')]

    def test_igual_nao_grava_nada(self):
        self._ligar()
        sync.gravar(self._plano())
        self.assertEqual(self._sqls_gravados(self._plano()), [])

    def test_diferente_atualiza_so_as_colunas_mudadas(self):
        m = self._ligar()
        sync.gravar(self._plano())
        pk = apt_pro_ordens.objects.get().pk
        m['sync_dados_ordem'].side_effect = lambda con, o, s, n: [dict(DADOS[0], ORD_IN_CODIGO=n,
                                                                       ORD_RE_QTDE_ORDEM=30.779)]
        plano = self._plano()
        self.assertEqual(sync.comparar(plano)['ordens'][0]['campos'], ['ORD_RE_QTDE_ORDEM'])
        sqls = self._sqls_gravados(plano)
        self.assertEqual(len(sqls), 1)
        self.assertTrue(sqls[0].startswith('UPDATE apt_pro_ordens SET ORD_RE_QTDE_ORDEM ='))
        o = apt_pro_ordens.objects.get()
        self.assertEqual((o.pk, float(o.ORD_RE_QTDE_ORDEM)), (pk, 30.779))

    def test_duplicadas_saem_fica_a_menor_sequencia(self):
        # sem troca de PK (decisao do usuario): chave ORD_ST_ID/PRO_ST_ID, fica a menor TAB_IN_SEQUENCIA
        self._ligar()
        plano = self._plano()
        with connection.cursor() as cur:
            for _ in range(2):
                local.inserir(cur, 'apt_pro_ordens', local.COLUNAS_ORDEM, local.JSON_ORDEM, plano['ordens'][0]['linha'])
                local.inserir(cur, 'apt_itens_ordens', local.COLUNAS_ITEM, local.JSON_ITEM,
                              plano['itens']['1000010002273'])
        menor_ordem = apt_pro_ordens.objects.order_by('pk').first().pk
        menor_item = apt_itens_ordens.objects.order_by('pk').first().pk
        comp = sync.comparar(plano)
        self.assertEqual((comp['ordens'][0]['duplicadas'], comp['itens']['duplicados']), (1, 1))
        sync.gravar(plano)
        self.assertEqual(list(apt_pro_ordens.objects.values_list('pk', flat=True)), [menor_ordem])
        self.assertEqual(list(apt_itens_ordens.objects.values_list('pk', flat=True)), [menor_item])

    def test_caracteristica_diferente_atualizada(self):
        m = self._ligar()
        sync.gravar(self._plano())
        m['sync_caracteristicas_referencia'].return_value = [dict(CARS[0], RAT_ST_DESCRICAO='Verde')]
        plano = self._plano()
        self.assertEqual(sync.comparar(plano)['caracteristicas_diferentes'], 1)
        sync.gravar(plano)
        with connection.cursor() as cur:
            cur.execute('SELECT RAT_ST_DESCRICAO FROM Car_AtributosReferencia')
            self.assertEqual(cur.fetchall(), [('Verde',)])

    def test_maquina_diferente_preserva_flags_locais(self):
        maq = {'CTR_ST_ID': '1', 'CMAQ_ST_ID': '2', 'CTR_ST_NOME': 'C', 'CMAQ_ST_NOME': 'M', 'CMAQ_ST_CODIGO': 'X'}
        self._ligar(maquinas=[dict(maq, CMAQ_ST_NOME='M2')])
        with connection.cursor() as cur:
            local.inserir_maquinas(cur, [dict(maq, MAQ_CH_APONTAMENTO=0, MAQ_CH_DEMANDA=1)])
        sync.gravar(self._plano())
        with connection.cursor() as cur:
            cur.execute('SELECT CMAQ_ST_NOME, MAQ_CH_APONTAMENTO, MAQ_CH_DEMANDA FROM Apt_Pro_CadMaquinas')
            self.assertEqual(cur.fetchall(), [('M2', 0, 1)])

    def _operadores_locais(self):
        with connection.cursor() as cur:
            cur.execute('SELECT OPD_IN_CODIGO, OPD_ST_CRACHA, OPD_ST_NOME, FIL_IN_CODIGO FROM Apt_Pro_CadOperador '
                        'ORDER BY OPD_IN_CODIGO')
            return cur.fetchall()

    def test_operador_novo_e_gravado(self):
        self._ligar(operadores=OPERADORES)
        with connection.cursor() as cur:
            cur.execute("INSERT INTO Apt_Pro_CadOperador (OPD_ST_CRACHA, OPD_ST_NOME, FIL_IN_CODIGO) "
                        "VALUES ('0000000001', 'ANILDO', 3)")
        self.assertTrue(sync.SYNC_OPERADORES_GRAVA)
        resumo = sync.sincronizar_ordens(2, 3, 900, 'N', conexao=MagicMock())
        self.assertEqual((resumo['operadores_novos'], resumo['operadores_gravados']), (1, 1))
        self.assertEqual([r[1:] for r in self._operadores_locais()],
                         [('0000000001', 'ANILDO', 3), ('0000000007', 'DOUGLAS', 3)])
        resumo = sync.sincronizar_ordens(2, 3, 900, 'N', conexao=MagicMock())
        self.assertEqual((resumo['operadores_novos'], resumo['operadores_gravados']), (0, 0))

    def test_operador_nome_diferente_duplicado_e_vazio(self):
        self._ligar(operadores=OPERADORES[:1] + [{'OPD_ST_CRACHA': '', 'OPD_ST_NOME': 'X', 'FIL_IN_CODIGO': 3}])
        with connection.cursor() as cur:
            for nome in ('ANILDO ANTIGO', 'ANILDO ANTIGO'):  # duplicado
                cur.execute("INSERT INTO Apt_Pro_CadOperador (OPD_ST_CRACHA, OPD_ST_NOME, FIL_IN_CODIGO) "
                            "VALUES ('0000000001', %s, 3)", [nome])
            cur.execute("INSERT INTO Apt_Pro_CadOperador (OPD_ST_CRACHA, OPD_ST_NOME, FIL_IN_CODIGO) "
                        "VALUES ('0000000099', 'SO NO APP', 3)")
        menor = self._operadores_locais()[0][0]
        plano = self._plano()
        self.assertEqual(len(plano['operadores']), 1)            # cracha vazio nao entra
        self.assertEqual(sync.comparar(plano)['operadores_diferentes'], 1)
        sync.gravar_operadores(plano)
        self.assertEqual(self._operadores_locais(),
                         [(menor, '0000000001', 'ANILDO', 3),     # nome atualizado, duplicado saiu
                          (menor + 2, '0000000099', 'SO NO APP', 3)])  # nao apaga o que nao veio do Mega

    def test_sem_conexao(self):
        with patch('oracle_connection.getOracleConnection', return_value=None):
            resumo = sync.sincronizar_ordens(2, 3, 900, 'N')
        self.assertIn('Sem conexão', resumo['erro_conexao'])


class IsolamentoTests(TestCase):
    """Rotina nova isolada: so a view nova (e os leitores) usam; o Baixar Ordens segue com buscaOrdens."""

    def test_ninguem_mais_usa(self):
        base = pathlib.Path(settings.BASE_DIR)
        importa = re.compile(r'app import sincronizacao|app\.sincronizacao|app import services|app\.services')
        usos = sorted(str(p.relative_to(base)) for p in base.rglob('*.py')
                      if importa.search(p.read_text(encoding='utf-8', errors='ignore'))
                      and p.name not in ('sincronizacao.py', 'tests_sincronizacao.py')
                      and not {'prodenv', '.venv', 'venv'} & set(p.parts))
        self.assertEqual(usos, [str(pathlib.Path('apontamento/views.py'))])

    def test_view_renderiza_resumo(self):
        sessao = self.client.session
        sessao.update({'ord_in_codigo': 900, 'fil_in_codigo': 3})
        sessao.save()
        resumo = {'gravado': False, 'erros': [], 'ordens': [{'ord': 900, 'situacao': 'igual', 'campos': [],
                                                             'itens': 1}],
                  'itens': {'novos': 0, 'iguais': 1, 'diferentes': []}, 'caracteristicas_novas': 0,
                  'maquinas_novas': 0, 'tempo_ms': 5, 'erro_conexao': None}
        with patch('app.sincronizacao.sincronizar_ordens', return_value=resumo) as s:
            resp = self.client.get(reverse('sincronizar_ordens_nova'))
        self.assertContains(resp, 'Modo comparação')
        s.assert_called_once_with(2, 3, 900, 'N')
