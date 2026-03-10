# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import socket
# Create your models here.

def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip

class Apt_Equipamentos(models.Model):
    EQP_IN_CODIGO    = models.AutoField(primary_key=True,verbose_name='codigo')
    EQP_ST_NAME      = models.CharField(max_length=100,null=False, blank=False,verbose_name='Descrição')
    EQP_ST_IPADDRESS = models.CharField(max_length=20,null=False, blank=False,verbose_name='IP')
    EQP_IN_FILIAL    = models.IntegerField(null=True, blank=True,verbose_name='filial')
    MAQ_IN_CODIGO    = models.IntegerField(null=True, blank=True,verbose_name='maquina')
    PRINTER_ST_IP    = models.CharField(max_length=20,null=True, blank=True,verbose_name='impressora')    
    class Meta:
        db_table = u'Apt_Equipamentos'
    #def publish(self):
    #    self.EQP_ST_IPADDRESS = getEnderIP()
    #    self.save()

class Apt_Controle(models.Model):
    CTL_IN_CODIGO        = models.IntegerField(primary_key=True,verbose_name='codigo')
    CTL_ST_USUARIO       = models.CharField(max_length=20,verbose_name='usuario')
    ORD_IN_CODIGO        = models.IntegerField(null=True, blank=True,verbose_name='ordem')
    CTL_DT_LOGIN         = models.DateTimeField(null=False, blank=False,verbose_name='data acesso')
    CTL_ST_IPADDRESS     = models.CharField(max_length=20,null=False, blank=False)
    CTL_DT_LOGOUT        = models.DateTimeField(null=True, blank=True,verbose_name='data encerramento')
    ORD_ST_EXTENSO       = models.CharField(max_length=20,null=True, blank=True)
    CTL_ST_STATUS        = models.CharField(max_length=1,null=True, blank=True,verbose_name='status')
    APT_IN_SEQUENCIA     = models.IntegerField(null=True, blank=True,verbose_name='apontamento')
    APT_DT_ULTAPT        = models.DateTimeField(null=True, blank=True)
    FIL_IN_CODIGO        = models.IntegerField(null=True, blank=True,verbose_name='filial')
    ORD_ST_ID            = models.CharField(max_length=44,null=True, blank=True,verbose_name='id_ordem')
    CMAQ_ST_ID           = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_maquina')
    PRINTER_ST_IP        = models.CharField(max_length=20,null=True, blank=True)
    class Meta:
        db_table = u'Apt_Controle'

class Apt_Reg_Medidores(models.Model):
    CTL_IN_SEQUENCIA     = models.AutoField(primary_key=True)
    CTL_ST_USUARIO       = models.CharField(max_length=20,null=True, blank=True)
    ORD_IN_CODIGO        = models.IntegerField(null=True, blank=True)
    FIL_IN_CODIGO        = models.IntegerField(null=True, blank=True)
    CTL_DT_REGISTRO      = models.DateField(null=False, blank=False)
    CTL_ST_IPADDRESS     = models.CharField(max_length=20,null=False, blank=False)
    CTL_IN_CONSENERGIA   = models.DecimalField(null=False, max_digits=10, decimal_places=2)
    CTL_IN_PRODUTIVIDADE = models.DecimalField(null=False, max_digits=10, decimal_places=2)
    class Meta:
        db_table = u'Apt_Reg_Medidores'

class Apt_Pro_CadOperador(models.Model):
    OPD_IN_CODIGO      = models.AutoField(primary_key=True,verbose_name='codigo')
    OPD_ST_CRACHA      = models.CharField(max_length=20,null=False, blank=False,verbose_name='crachá')
    OPD_ST_NOME        = models.CharField(max_length=50,null=False, blank=False,verbose_name='nome')
    FIL_IN_CODIGO      = models.IntegerField(null=True, blank=True,verbose_name='filial')
    class Meta:
        db_table = u'Apt_Pro_CadOperador'
        
class Apt_Pro_CadMaquinas(models.Model):
    MAQ_IN_SEQUENCIA  = models.AutoField(primary_key=True)
    CTR_ST_ID         = models.CharField(max_length=13,null=False, blank=False)
    CMAQ_ST_ID        = models.CharField(max_length=13,null=False, blank=False)
    CTR_ST_NOME       = models.CharField(max_length=60,null=False, blank=False)
    CMAQ_ST_NOME      = models.CharField(max_length=100,null=False, blank=False)
    CMAQ_ST_CODIGO    = models.CharField(max_length=30,null=True, blank=True)
    MAQ_CH_APONTAMENTO = models.BooleanField(null=True, blank=True)
    MAQ_CH_DEMANDA    = models.BooleanField(null=True, blank=True)
    class Meta:
        db_table = u'Apt_Pro_CadMaquinas'
