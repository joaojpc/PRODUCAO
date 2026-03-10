# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from jsonfield import JSONField
# Create your models here.
class alm_Inventario(models.Model):
    INV_IN_SEQUENCIA   = models.IntegerField(primary_key=True,null=False,blank=False,verbose_name='Id')
    INV_ST_USUARIO     = models.CharField(max_length=20,verbose_name='usuario')
    INV_DT_MOVIMENTO   = models.DateField(null=True, blank=True,verbose_name='data')
    INV_CH_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    FIL_IN_CODIGO      = models.IntegerField(null=True, blank=True,verbose_name='filial')
    INV_ID_CCUSTO      = models.CharField(null=True, blank=True, max_length=18,verbose_name='centro de custo')
    MOV_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True,verbose_name='sequencial')
    class Meta:
        db_table = u'alm_Inventario'
class alm_InventarioItens(models.Model):
    ITI_IN_SEQUENCIA   = models.IntegerField(primary_key=True,null=False,blank=False,verbose_name='Id')
    ITI_ID_PRODUTO     = models.CharField(max_length=22,null=False, blank=False,verbose_name='item')
    ITI_RE_QUANTIDADE  = models.DecimalField(null=False, max_digits=10, decimal_places=3,verbose_name='quantidade')
    ITI_CH_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    MOV_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True,verbose_name='sequencial')
    INV_IN_SEQUENCIA   = models.IntegerField(verbose_name='id inventario')
    #INV_IN_SEQUENCIA   = models.ForeignKey(alm_Inventario, on_delete=models.CASCADE,verbose_name='id inventario')
    ITI_ST_TIPOMOV     = models.CharField(max_length=3,null=True, blank=True,verbose_name='Tipo')
    MOI_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True,verbose_name='sequencial_item')
    #SDI = Saida Inventário; EDI = Entrada Inventário;
    class Meta:
        db_table = u'alm_InventarioItens'        

