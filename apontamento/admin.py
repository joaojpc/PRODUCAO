# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from apontamento.models import Apt_Equipamentos, Apt_Controle, Apt_Reg_Medidores, Apt_Pro_CadOperador, Apt_Pro_CadMaquinas


# Register your models here.

class OperadorAdmin(admin.ModelAdmin):
    model = Apt_Pro_CadOperador
    list_display = ('OPD_IN_CODIGO','OPD_ST_NOME','OPD_ST_CRACHA')
class ControleAdmin(admin.ModelAdmin):
    model = Apt_Controle
    list_display = ('CTL_IN_CODIGO','ORD_IN_CODIGO','CTL_ST_STATUS','CTL_ST_USUARIO')
class EquipamentoAdmin(admin.ModelAdmin):
    model = Apt_Equipamentos
    list_display = ('EQP_IN_CODIGO','EQP_ST_NAME','EQP_ST_IPADDRESS','EQP_IN_FILIAL','MAQ_IN_CODIGO','PRINTER_ST_IP')        
class MaquinaAdmin(admin.ModelAdmin):
    model = Apt_Pro_CadMaquinas
    list_display = ('MAQ_IN_SEQUENCIA','CTR_ST_ID','CMAQ_ST_ID','CTR_ST_NOME','CMAQ_ST_NOME','MAQ_CH_APONTAMENTO',
                    'MAQ_CH_DEMANDA')
admin.site.register(Apt_Equipamentos,EquipamentoAdmin)
admin.site.register(Apt_Controle,ControleAdmin)
#admin.site.register(Apt_Reg_Medidores)
admin.site.register(Apt_Pro_CadOperador,OperadorAdmin)
admin.site.register(Apt_Pro_CadMaquinas,MaquinaAdmin)
