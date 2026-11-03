# -*- coding: utf-8 -*-
"""AJUSTE 2026-11-03 (JPC): protecao contra duplo clique (js/anti_duplo_clique.js, trazida do NMV) em todos os
templates base. Neste projeto o arquivo existe em apontamento/static/js (desenvolvimento) e static/js (nginx): iguais."""
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.test import SimpleTestCase

BASES = ('apontamento/base.html',
         'apontamento/base_bs5.html',
         'almoxarifado/base_almoxa.html',
         'almoxarifado/base_controle.html',
         'inventario/base_inventario.html',
         'recebimento/base.html')
SCRIPT = "{% static 'js/anti_duplo_clique.js' %}"


class AntiDuploCliqueTests(SimpleTestCase):
    def test_todas_as_bases_incluem_o_script(self):
        for base in BASES:
            fonte = get_template(base).template.source
            self.assertIn(SCRIPT, fonte, base)
            self.assertIn('{% load static %}', fonte, base)
            self.assertLess(fonte.index(SCRIPT), fonte.index('</body>'), base)

    def test_arquivo_estatico_existe(self):
        caminho = finders.find('js/anti_duplo_clique.js')
        self.assertTrue(caminho)
        with open(caminho, encoding='utf-8') as f:
            js = f.read()
        self.assertEqual(js.count('{'), js.count('}'))
        self.assertEqual(js.count('('), js.count(')'))
        for trecho in ("addEventListener('submit'", "addEventListener('click'", "addEventListener('pageshow'",
                       'e.defaultPrevented', 'data-sem-trava', "'_blank'"):
            self.assertIn(trecho, js)

    def test_copia_servida_pelo_nginx_igual(self):
        with open(finders.find('js/anti_duplo_clique.js'), encoding='utf-8') as f:
            dev = f.read()
        with open(os.path.join(settings.STATIC_ROOT, 'js', 'anti_duplo_clique.js'), encoding='utf-8') as f:
            producao = f.read()
        self.assertEqual(dev, producao)
