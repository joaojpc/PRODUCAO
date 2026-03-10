# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from inventario.models import alm_Inventario, alm_InventarioItens

class InventarioAdmin(admin.ModelAdmin):
    model = alm_Inventario
    list_display = ('INV_IN_SEQUENCIA','INV_DT_MOVIMENTO','INV_ST_USUARIO','INV_CH_STATUS')
class InvItensAdmin(admin.ModelAdmin):
    model = alm_InventarioItens
    list_display = ('INV_IN_SEQUENCIA','ITI_IN_SEQUENCIA','ITI_ID_PRODUTO','ITI_RE_QUANTIDADE','ITI_CH_STATUS')
admin.site.register(alm_Inventario,InventarioAdmin)
admin.site.register(alm_InventarioItens,InvItensAdmin)
