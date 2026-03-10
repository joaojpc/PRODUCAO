# coding: utf-8

from rest_framework import serializers
from .models import *

class ApontaControleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Controle
        fields = ['CTL_IN_CODIGO', 'CTL_ST_USUARIO', 'ORD_IN_CODIGO','CTL_DT_LOGIN','CTL_ST_IPADDRESS',
                  'CTL_DT_LOGOUT', 'ORD_ST_EXTENSO', 'CTL_ST_STATUS','APT_IN_SEQUENCIA','APT_DT_ULTAPT',
                  'FIL_IN_CODIGO', 'ORD_ST_ID', 'CMAQ_ST_ID','PRINTER_ST_IP']
class CadastroOperadoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Pro_CadOperador
        fields = ['OPD_IN_CODIGO', 'OPD_ST_CRACHA', 'OPD_ST_NOME','FIL_IN_CODIGO']

class CadastroEquipamentosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Equipamentos
        fields = ['EQP_ST_NAME', 'EQP_ST_IPADDRESS', 'EQP_IN_FILIAL','MAQ_IN_CODIGO','PRINTER_ST_IP']

class CadastroMaquinasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Pro_CadMaquinas
        fields = ['CTR_ST_ID', 'CMAQ_ST_ID','CTR_ST_NOME','CMAQ_ST_NOME','CMAQ_ST_CODIGO','MAQ_CH_APONTAMENTO','MAQ_CH_DEMANDA']
