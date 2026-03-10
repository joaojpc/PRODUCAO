# coding: utf-8

from rest_framework import serializers

from .models import *

class AlmoxaBaixaSerializer(serializers.ModelSerializer):
    class Meta:
        model = bxa_AlmoxaBaixa
        fields = ['BXA_IN_SEQUENCIA', 'BXA_DT_APONTAMENTO', 'BXA_ST_USUARIO','BXA_IN_CCUSTO','BXA_CH_STATUS',
                  'FIL_IN_CODIGO','CUS_ID_CCUSTO','REQ_IN_SEQUENCIA','OS_ST_ID']
class AlmoxaBaixaItensSerializer(serializers.ModelSerializer):
    class Meta:
        model = bxi_AlmoxaBaixaItens
        fields = ['BXI_ID_REQUISICAO','BXI_IN_SEQUENCIA','BXA_IN_SEQUENCIA', 'BXI_ID_PRODUTO', 'BXI_RE_QUANTIDADE','BXI_CH_STATUS'
                  ,'REQ_IN_SEQUENCIA','REI_IN_SEQUENCIA','BXI_ID_ALMOXA','FIL_IN_CODIGO']
class CentroCustosSerializer(serializers.ModelSerializer):
    class Meta:
        model = bxa_CentroCustos
        fields = ['CUS_ID_CCUSTO','CUS_TAB_IN_CODIGO', 'CUS_PAD_IN_CODIGO', 'CUS_IDE_ST_CODIGO','CUS_IN_REDUZIDO',
                  'CUS_ST_EXTENSO','CUS_ST_DESCRICAO']

class CadItensSerializer(serializers.ModelSerializer):
    class Meta:
        model = est_CadItens
        fields = ['BXI_ID_PRODUTO','PRO_TAB_IN_CODIGO', 'PRO_PAD_IN_CODIGO', 'PRO_IN_CODIGO','PRO_ST_DESCRICAO','UNI_ST_UNIDADE']

class CadItensAlmSerializer(serializers.ModelSerializer):
    class Meta:
        model = est_CadItemAlmoxa
        fields = ['LOC_ID_PROALMFIL','LOC_ID_ALMOXA', 'LOC_ID_ORG', 'LOC_ID_PRODUTO',
                  'LOC_IN_FILIAL','ALM_IN_CODIGO','LOC_IN_CODIGO','ALM_ST_DESCRICAO','LOC_ST_DESCRICAO']
        

