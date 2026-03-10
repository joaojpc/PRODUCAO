# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import *

class InventarioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = alm_InventarioItens
        fields = ['ITI_IN_SEQUENCIA','ITI_ID_PRODUTO','ITI_RE_QUANTIDADE', 'ITI_CH_STATUS',
                  'MOV_IN_SEQUENCIA','INV_IN_SEQUENCIA','ITI_ST_TIPOMOV','MOI_IN_SEQUENCIA']

class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = alm_Inventario
        fields = ['INV_IN_SEQUENCIA','INV_ST_USUARIO','INV_DT_MOVIMENTO','INV_CH_STATUS',
                  'FIL_IN_CODIGO','INV_ID_CCUSTO','MOV_IN_SEQUENCIA']
