# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.urls import path
from inventario import views
from django.contrib import admin
#from graphs import BarView
#import os
from .views import *
admin.autodiscover()
helper_patterns = [
    path('inventario/', views.principal, name='inventario'),
    path('listainventario/', views.ListarInventario, name='listainventario'),
    path('invItem/', ItensInventarioListView.as_view(), name='invItem'),
    path('gravarinventario/', InventarioView.as_view(), name='gravarinventario'),
    path('invItens/', views.InventarioItem, name='invItens'),
    path('iniciar_inventario/', views.session_inventario, name='iniciar_inventario'),
 ]
urlpatterns = helper_patterns
