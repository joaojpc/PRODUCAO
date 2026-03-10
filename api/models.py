# coding: utf-8
from django.db import models

class DadosPessoais(models.Model):
    name = models.CharField(max_length=50, verbose_name='Nome')
    adress = models.CharField(max_length=100, verbose_name='Endereço')
    city = models.CharField(max_length=50, verbose_name='Cidade')
    cep = models.CharField(max_length=50, verbose_name='Cep')
    phone = models.CharField(max_length=20, verbose_name='Telefone')
    mobile = models.CharField(max_length=20, verbose_name='Celular')

    about = models.TextField(max_length=255, verbose_name='Sobre')
    data_nascimento = models.CharField(max_length=255, default='01 de janeiro de 2000', verbose_name='Data Nascimento')
    email = models.EmailField(verbose_name='Email')

    conhecimentos = models.TextField(max_length=255, verbose_name='Conhecimentos')
    github = models.CharField(max_length=100, default='http://github.com/SeuGit', verbose_name='Github')
    current_position = models.CharField(max_length=100, verbose_name='Cargo atual')
    empresa = models.CharField(max_length=100, verbose_name='Empresa')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Dados Pessoais'
        verbose_name_plural = 'Dados Pessoais'
class APT_APONTAORDEM(models.Model):
    apt_in_sequencia = models.AutoField(primary_key=True)
    apt_dt_apontamento = models.DateField(null=False, blank=False)
    apt_ati_tab_in_codigo = models.IntegerField(null=False, blank=False)
    apt_ati_pad_in_codigo = models.IntegerField(null=False, blank=False)
    apt_ati_in_codigo     = models.IntegerField(null=False, blank=False)
    apt_ch_status         = models.CharField(max_length=1,null=False, blank=False)
    org_tab_in_codigo   = models.IntegerField(null=False, blank=False)
    org_pad_in_codigo   = models.IntegerField(null=False, blank=False)
    org_in_codigo       = models.IntegerField(null=False, blank=False)
    org_tau_st_codigo   = models.CharField(max_length=3,null=False, blank=False)
    fil_in_codigo       = models.IntegerField(null=False, blank=False)
    ord_tab_in_codigo   = models.IntegerField(null=False, blank=False)
    ord_seq_in_codigo   = models.IntegerField(null=False, blank=False)
    ord_in_codigo       = models.IntegerField(null=False, blank=False)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Apontamentos Ordens'
        verbose_name_plural = 'Apontamentos Ordens'
