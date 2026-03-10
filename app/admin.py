# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from app.models import apt_pro_atividade, Apt_ApontaOrdem, Apt_Pro_Demandas, apt_pro_ordens, apt_itens_ordens

class OrdensAdmin(admin.ModelAdmin):
    model = apt_pro_ordens
    list_display = ('ORD_IN_CODIGO','PRO_IN_CODIGO','ORD_RE_QTDE_ORDEM','FIL_IN_CODIGO')
class AptoAdmin(admin.ModelAdmin):
    model = Apt_ApontaOrdem
    list_display = ('APT_IN_SEQUENCIA','ORD_IN_CODIGO','PRO_IN_CODIGO','PRO_ST_LOTE','ORL_RE_QTDLOTE','PRO_RE_QTDREFUGO')
class DemandaAdmin(admin.ModelAdmin):
    model = Apt_ApontaOrdem
    list_display = ('MOV_IN_SEQUENCIA','ORD_IN_CODIGO','PRO_ST_LOTE','PRO_RE_QTDLOTE')
class AtividadeAdmin(admin.ModelAdmin):
    model = apt_pro_atividade
    list_display = ('ATI_IN_CODIGO','ATI_ST_NOME')        
admin.site.register(apt_pro_ordens,OrdensAdmin)
admin.site.register(apt_pro_atividade,AtividadeAdmin)
admin.site.register(Apt_ApontaOrdem,AptoAdmin)
admin.site.register(Apt_Pro_Demandas,DemandaAdmin)
'''@admin.register(apt_pro_atividade)
@admin.register(Apt_ApontaOrdem)
@admin.register(Apt_Pro_Demandas)
@admin.register(apt_pro_ordens)
@admin.register(apt_itens_ordens)
@admin.register(OrdensAdmin)

class AtividadeAdmin(admin.ModelAdmin):
    pass

'''

