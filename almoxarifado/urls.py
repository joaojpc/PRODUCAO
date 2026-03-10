# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from almoxarifado import views
from django.contrib import admin
from django.urls import path
#from graphs import BarView
#import os
from .views import CentroCustosListView, AlmoxaBaixaListView, AlmoxaBaixaItemListView, CadItensListView, CadItensAlmListView

admin.autodiscover()

helper_patterns = [
    path('almoxarifado/', views.principal, name='almoxarifado'),
    #path('iniciar/', views.loginControl_sqlite, name='iniciar'),
    path('baixas/', views.ListarBaixa, name='baixas'),
    path('centrocustos/', CentroCustosListView.as_view(), name='centrocustos'),
    path('man_almoxa/', views.man_almoxa, name='man_almoxa'),
    path('iniciar_baixa/', views.session_almoxa, name='iniciar_baixa'),
    path('logout/', views.LogOut, name='logout'),    
    path('requisicao/', AlmoxaBaixaListView.as_view(), name='requisicao'),
    path('reqItem/', AlmoxaBaixaItemListView.as_view(), name='reqItem'),
    path('IncluirBaixa/', views.IncluirBaixa, name='IncluirBaixa'),
    path('produtos/', CadItensListView.as_view(), name='produtos'),
    path('etiquetaItem/', views.EtiquetaItem, name='etiquetaItem'),
    path('saldo/', views.ListarSaldo, name='saldo'),
    path('controla/', views.ControlaAlmoxa, name='controla'),
    path('ItemAlmoxa/', CadItensAlmListView.as_view(), name='ItemAlmoxa'),
    path('deletebaixa/<int:pk>', views.ExcluirBaixa, name='deletebaixa'),
    
 ]
urlpatterns = helper_patterns
