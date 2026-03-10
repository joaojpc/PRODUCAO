# coding: utf-8

from rest_framework import serializers

from .models import *

class ApontaDemandaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Pro_Demandas
        fields = ['FIL_IN_CODIGO', 'MOV_IN_SEQUENCIA', 'MOV_DT_INCLUSAO','ORD_IN_CODIGO','PRO_RE_QTDLOTE',
                  'PRO_ST_LOTE', 'MOV_ST_STATUS', 'CTL_IN_CODIGO','ORD_ST_ID','CMAQ_ST_ID']

class ApontaOrdemSerializer(serializers.ModelSerializer):
    PRO_ST_ETIQUETA = serializers.JSONField()
    class Meta:
        model = Apt_ApontaOrdem
        fields = ['FIL_IN_CODIGO', 'APT_IN_SEQUENCIA', 'APT_DT_APONTAMENTO','APT_CH_STATUS',
                  'ORD_IN_CODIGO', 'PRO_IN_CODIGO','ORL_RE_QTDLOTE','ORL_ST_REFERENCIA',
                  'CTL_IN_CODIGO','PRO_ST_DESCRICAO','PRO_ST_LOTE','PRO_ST_SEQUENCIAL'
                  ,'PRO_ST_ETIQUETA','RFC_ST_DESCRICAO','PRO_RE_QTDREFUGO','PRO_RE_QTDCONV',
                  'PRO_ST_LOTEORI','CMAQ_ST_ID','ORD_ST_ID','PRO_ST_ID','RES_ST_STATUS','RES_ST_ID',
                  'ORL_RE_QTDAJUSTADA','PRO_ST_FORNECEDOR']

class ApontaOcorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apt_Ocorrencia
        fields = ['ATI_IN_SEQUENCIA','ATI_IN_CODIGO', 'ATI_DT_INCLUSAO', 'ATI_USU_INCLUSAO','ATI_IN_ORDEM',
                  'ATI_IN_ORDEM', 'ATI_IN_TEMPO']

class ManProOrdensSerializer(serializers.ModelSerializer):
    PRO_ST_ITENS = serializers.JSONField()
    PRO_ST_DEMANDAS = serializers.JSONField()
    PRO_ST_INFOADIC = serializers.JSONField()
    class Meta:
        model = apt_pro_ordens
        fields = ['ORG_TAB_IN_CODIGO','ORG_PAD_IN_CODIGO','ORG_IN_CODIGO','ORG_TAU_ST_CODIGO',
                  'ORD_TAB_IN_CODIGO','ORD_SEQ_IN_CODIGO','ORD_IN_CODIGO','PRO_TAB_IN_CODIGO',
                  'PRO_PAD_IN_CODIGO','PRO_IN_CODIGO','ORD_RE_QTDE_ORDEM','FIL_IN_CODIGO',
                  'TPO_ST_CODIGO', 'PRO_ST_ITENS','PRO_ST_DEMANDAS','PRO_ST_INFOADIC',
                  'PRO_ST_ID','ORD_ST_ID','TPO_ST_ID']

class ManItensOrdensSerializer(serializers.ModelSerializer):
    class Meta:
        PRO_ST_ATRIBUTOS = serializers.JSONField()
        PRO_ST_REFERENCIA = serializers.JSONField()
        PRO_ST_MEDIDAS = serializers.JSONField()
        PRO_ST_CONVERSOR = serializers.JSONField()
        model = apt_itens_ordens
        fields = ['TAB_IN_SEQUENCIA','PRO_TAB_IN_CODIGO','PRO_PAD_IN_CODIGO','PRO_IN_CODIGO',
                  'PRO_ST_DESCRICAO','UNI_ST_UNIDADE','RFC_IN_CODIGO','PRO_ST_ATRIBUTOS','PRO_ST_REFERENCIA','PRO_ST_MEDIDAS',
                  'MVS_ST_REFERENCIA','PRO_ST_ID','PRO_ST_CONVERSOR']

class ManProAtividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = apt_pro_atividade
        fields = ['TAB_IN_SEQUENCIA','ATI_TAB_IN_CODIGO','ATI_PAD_IN_CODIGO','ATI_IN_CODIGO','ATI_ST_NOME']

class ManProAptSequenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = apt_pro_atividade
        fields = ['TSEQ_IN_SEQUENCIA','TAB_IN_CODIGO']

class Resumo_OrdensSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Apt_ResumoOrdem
        fields = ['RES_ST_ID','RES_IN_CODIGO','RES_IN_SEQUENCIA','ORD_ST_ID','PRO_ST_ID','PRO_RE_QTDINFORMADA','RES_ST_STATUS',
                  'PRO_IN_CODIGO','PRO_ST_DESCRICAO','PRO_RE_QTDORIGINAL']

class AptEstFormatosSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Apt_EstFormatos
        fields = ['PUN_ST_ID','FMT_ST_ID','PRO_ST_ID','FMT_ST_CODIGO','FMT_ST_NOME','UNI_ST_UNIDADE','FMT_ST_FORMULA']

class AptProTipoOrdensSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Apt_ProTipoOrdens
        fields = ['TPO_ST_ID','TPO_ST_CODIGO_TIPO','TPO_ST_UNIDADE','TPO_ST_SELCONVERSOR','TPO_ST_OPERACAO','TPO_ST_NOME']

class AptProMaquinaConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Apt_ProMaquinaConfig
        fields = ['CFG_ST_ID','CTR_ST_ID','CMAQ_ST_ID','OPR_ST_ID','CUS_BO_NAOBAIXADEMANDA','CUS_BO_GERASEQPALLET',
                  'CUS_BO_CONVERSOR','CUS_BO_LOTES','OPR_ST_OPERACAO','CMAQ_ST_DESCRICAO','MAQ_ST_NOME']

class CarAtributosReferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Car_AtributosReferencia
        fields = ['CAR_ST_ID','RAT_ST_ID','RFC_ST_ID','PAI_RAT_IN_CODIGO','RAT_IN_CODIGO','RAT_ST_DESCRICAO',
                  'RAT_VALUE','RAT_CH_TIPO','CAR_IN_PRIORIDADE','RFC_IN_CODIGO','RAT_BO_GRUPO','CAR_BO_OBRIGATORIO',
                  'PAI_ST_DESCRICAO']

        
