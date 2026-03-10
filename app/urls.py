# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path
from .views import *

helper_patterns = [
    path('demandas/', ApontaDemandaListView.as_view(), name='demandas'),
    path('apontamentos/', ApontaOrdemListView.as_view(), name='apontamentos'),
    path('ocorrencias/', ApontaOcorrenciaListView.as_view(), name='ocorrencias'),
    path('ordens/', ManProOrdensListView.as_view(), name='ordens'),
    path('itensOrdens/', ManItensOrdens.as_view(), name='itensOrdens'),
    path('atividade/', ManProAtividade.as_view(), name='atividade'),
    path('seqApto/', ManProAptSequencia.as_view(), name='seqApto'),
    path('resordens/', ManProAptSequencia.as_view(), name='resordens'),
    path('conversores/', AptEstFormatos.as_view(), name='conversores'),
    path('tipoordens/', AptProTipoOrdens.as_view(), name='tipoordens'),
    path('configurar_aponta/', AptProMaquinaConfig.as_view(), name='configurar_aponta'),
    path('referencia/', CarAtributosReferencia.as_view(), name='referencia'),
    ]
urlpatterns = helper_patterns
