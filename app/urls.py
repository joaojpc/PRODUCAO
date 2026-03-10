# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from .views import *

helper_patterns = [
    url(r'^demandas/$', ApontaDemandaListView.as_view(), name='demandas'),
    url(r'^apontamentos/$', ApontaOrdemListView.as_view(), name='apontamentos'),
    url(r'^ocorrencias/$', ApontaOcorrenciaListView.as_view(), name='ocorrencias'),
    url(r'^ordens/$', ManProOrdensListView.as_view(), name='ordens'),
    url(r'^itensOrdens/$', ManItensOrdens.as_view(), name='itensOrdens'),
    url(r'^atividade/$', ManProAtividade.as_view(), name='atividade'),
    url(r'^seqApto/$', ManProAptSequencia.as_view(), name='seqApto'),
    url(r'^resordens/$', ManProAptSequencia.as_view(), name='resordens'),
    url(r'^conversores/$', AptEstFormatos.as_view(), name='conversores'),
    url(r'^tipoordens/$', AptProTipoOrdens.as_view(), name='tipoordens'),
    url(r'^configurar_aponta/$', AptProMaquinaConfig.as_view(), name='configurar_aponta'),
    url(r'^referencia/$', CarAtributosReferencia.as_view(), name='referencia'),
    ]
urlpatterns = helper_patterns
