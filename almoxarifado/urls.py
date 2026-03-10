# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from almoxarifado import views
from django.contrib import admin
from django.urls import path
#from graphs import BarView
#import os
from .views import CentroCustosListView, AlmoxaBaixaListView, AlmoxaBaixaItemListView, CadItensListView, CadItensAlmListView

admin.autodiscover()

helper_patterns = [
    url(r'^almoxarifado/$', views.principal, name='almoxarifado'),
    #url(r'^iniciar/$', views.loginControl_sqlite, name='iniciar'),
    url(r'^baixas/$', views.ListarBaixa, name='baixas'),
    url(r'^centrocustos/$', CentroCustosListView.as_view(), name='centrocustos'),
    url(r'^man_almoxa/$', views.man_almoxa, name='man_almoxa'),
    url(r'^iniciar_baixa/$', views.session_almoxa, name='iniciar_baixa'),
    url(r'^logout/$', views.LogOut, name='logout'),    
    url(r'^requisicao/$', AlmoxaBaixaListView.as_view(), name='requisicao'),
    url(r'^reqItem/$', AlmoxaBaixaItemListView.as_view(), name='reqItem'),
    url(r'^IncluirBaixa/$', views.IncluirBaixa, name='IncluirBaixa'),
    url(r'^produtos/$', CadItensListView.as_view(), name='produtos'),
    url(r'^etiquetaItem/$', views.EtiquetaItem, name='etiquetaItem'),
    url(r'^saldo/$', views.ListarSaldo, name='saldo'),
    url(r'^controla/$', views.ControlaAlmoxa, name='controla'),
    url(r'^ItemAlmoxa/$', CadItensAlmListView.as_view(), name='ItemAlmoxa'),
    path('deletebaixa/<int:pk>', views.ExcluirBaixa, name='deletebaixa'),
    
 ]
urlpatterns = helper_patterns
