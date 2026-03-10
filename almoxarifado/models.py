# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from jsonfield import JSONField
# Create your models here.
class bxa_AlmoxaBaixa(models.Model):
    BXA_IN_SEQUENCIA   = models.IntegerField(primary_key=True,verbose_name='sequencial baixa')
    BXA_DT_APONTAMENTO = models.DateField(null=False, blank=False,verbose_name='data')
    BXA_ST_USUARIO     = models.CharField(max_length=20,verbose_name='usuario')
    BXA_IN_CCUSTO      = models.IntegerField(null=True, blank=True)
    BXA_CH_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    FIL_IN_CODIGO      = models.IntegerField(null=True, blank=True)
    CUS_ID_CCUSTO      = models.CharField(max_length=18,null=True, blank=True,verbose_name='id_ccusto')
    REQ_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True)
    OS_ST_ID           = models.CharField(max_length=17,null=True, blank=True,verbose_name='id_os')
    class Meta:
        db_table = u'bxa_AlmoxaBaixa'
class bxi_AlmoxaBaixaItens(models.Model):
    BXI_ID_REQUISICAO  = models.IntegerField(primary_key=True,verbose_name='id_sequencial')
    BXI_IN_SEQUENCIA   = models.IntegerField(verbose_name='sequencial Item')
    BXA_IN_SEQUENCIA   = models.IntegerField(verbose_name='Id Baixa')
    BXI_ID_PRODUTO     = models.CharField(max_length=22,null=False, blank=False,verbose_name='item')
    BXI_RE_QUANTIDADE  = models.DecimalField(null=False, max_digits=10, decimal_places=3,verbose_name='quantidade')
    BXI_CH_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    REQ_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True)
    REI_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True)
    BXI_ID_ALMOXA      = models.CharField(max_length=18,null=True, blank=True,verbose_name='DESTINO')
    FIL_IN_CODIGO      = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'bxi_AlmoxaBaixaItens'
class bxa_CentroCustos(models.Model):
    CUS_ID_CCUSTO  = models.CharField(primary_key=True,max_length=18,verbose_name='ID')
    CUS_TAB_IN_CODIGO = models.IntegerField(null=True, blank=True)
    CUS_PAD_IN_CODIGO = models.IntegerField(null=True, blank=True)
    CUS_IDE_ST_CODIGO = models.CharField(max_length=5,null=False, blank=False,verbose_name='IDE')
    CUS_IN_REDUZIDO   = models.IntegerField(null=True, blank=True)
    CUS_ST_EXTENSO    = models.CharField(max_length=25,null=False, blank=False,verbose_name='EXTENSO')
    CUS_ST_DESCRICAO  = models.CharField(max_length=100,null=False, blank=False,verbose_name='DESCRIÇÃO')
    class Meta:
        db_table = u'bxa_CentroCustos'

class est_CadItens(models.Model):
    BXI_ID_PRODUTO    = models.CharField(primary_key=True,max_length=13,null=False, blank=False,verbose_name='ITEM')
    PRO_TAB_IN_CODIGO = models.IntegerField(null=False, blank=False,verbose_name='TABELA')
    PRO_PAD_IN_CODIGO = models.IntegerField(null=False, blank=False,verbose_name='PADRÃO')
    PRO_IN_CODIGO     = models.IntegerField(null=False, blank=False,verbose_name='PRODUTO')
    PRO_ST_DESCRICAO  = models.CharField(max_length=70,null=True, blank=True,verbose_name='DESCRIÇÃO')
    UNI_ST_UNIDADE    = models.CharField(max_length=8,null=True, blank=True,verbose_name='UM')
    class Meta:
        db_table = u'est_CadItens'
        
class est_CadItemAlmoxa(models.Model):
    LOC_ID_PROALMFIL  = models.CharField(primary_key=True,max_length=38,null=False, blank=False,verbose_name='ID_PROALMFIL')
    LOC_ID_ALMOXA     = models.CharField(max_length=18,null=False, blank=False,verbose_name='ID_ALMOXA')
    LOC_ID_ORG        = models.CharField(max_length=16,null=False, blank=False,verbose_name='ID_ORG')
    LOC_ID_PRODUTO    = models.CharField(max_length=13,null=False, blank=False,verbose_name='ID_ITEM')
    LOC_IN_FILIAL     = models.IntegerField(null=False, blank=False,verbose_name='FILIAL')
    ALM_IN_CODIGO     = models.IntegerField(null=False, blank=False,verbose_name='ALMOXARIFADO')
    LOC_IN_CODIGO     = models.IntegerField(null=False, blank=False,verbose_name='LOCALIZAÇÃO')
    ALM_ST_DESCRICAO  = models.CharField(max_length=50,null=True, blank=True,verbose_name='DESC_ALMOXA')
    LOC_ST_DESCRICAO  = models.CharField(max_length=30,null=True, blank=True,verbose_name='DESC_LOCAL')
    class Meta:
        db_table = u'est_CadItemAlmoxa'
