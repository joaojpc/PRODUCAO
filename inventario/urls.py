# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from inventario import views
from django.contrib import admin
#from graphs import BarView
#import os
from .views import *
admin.autodiscover()
helper_patterns = [
    url(r'^inventario/$', views.principal, name='inventario'),
    url(r'^listainventario/$', views.ListarInventario, name='listainventario'),
    url(r'^invItem/$', ItensInventarioListView.as_view(), name='invItem'),
    url(r'^gravarinventario/$', InventarioView.as_view(), name='gravarinventario'),
    url(r'^invItens/$', views.InventarioItem, name='invItens'),
    url(r'^iniciar_inventario/$', views.session_inventario, name='iniciar_inventario'),
 ]
urlpatterns = helper_patterns
