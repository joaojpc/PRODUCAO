# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from almoxarifado.models import bxa_AlmoxaBaixa, bxi_AlmoxaBaixaItens, bxa_CentroCustos, est_CadItens, est_CadItemAlmoxa

class BaixaAdmin(admin.ModelAdmin):
    model = bxa_AlmoxaBaixa
    list_display = ('BXA_IN_SEQUENCIA','BXA_DT_APONTAMENTO','BXA_ST_USUARIO','BXA_IN_CCUSTO','BXA_CH_STATUS')
class BaixaItensAdmin(admin.ModelAdmin):
    model = bxi_AlmoxaBaixaItens
    list_display = ('BXA_IN_SEQUENCIA','BXI_IN_SEQUENCIA','BXI_ID_PRODUTO','BXI_RE_QUANTIDADE','BXI_CH_STATUS','BXI_ID_ALMOXA')

class CentroCustosAdmin(admin.ModelAdmin):
    model = bxa_CentroCustos
    list_display = ('CUS_ID_CCUSTO','CUS_IN_REDUZIDO','CUS_ST_EXTENSO','CUS_ST_DESCRICAO')

class CadastroItensAdmin(admin.ModelAdmin):
    model = est_CadItens
    list_display = ('PRO_IN_CODIGO','PRO_ST_DESCRICAO','UNI_ST_UNIDADE')
class ItensLocalAdmin(admin.ModelAdmin):
    model = est_CadItemAlmoxa
    list_display = ('LOC_ID_PRODUTO','ALM_IN_CODIGO','LOC_IN_CODIGO','ALM_ST_DESCRICAO','LOC_ST_DESCRICAO')
admin.site.register(bxa_AlmoxaBaixa,BaixaAdmin)
admin.site.register(bxi_AlmoxaBaixaItens,BaixaItensAdmin)
admin.site.register(bxa_CentroCustos,CentroCustosAdmin)
admin.site.register(est_CadItens,CadastroItensAdmin)
admin.site.register(est_CadItemAlmoxa,ItensLocalAdmin)
