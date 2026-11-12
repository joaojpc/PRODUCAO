# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from jsonfield import JSONField
# Create your models here.
class Apt_ApontaOrdem(models.Model):
    FIL_IN_CODIGO      = models.IntegerField(null=False, blank=False)
    APT_IN_SEQUENCIA   = models.IntegerField(primary_key=True,verbose_name='sequencial')
    APT_DT_APONTAMENTO = models.DateField(null=False, blank=False,verbose_name='data')
    APT_CH_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    ORD_IN_CODIGO      = models.IntegerField(null=False, blank=False,verbose_name='ordem')
    PRO_IN_CODIGO      = models.IntegerField(null=False, blank=False,verbose_name='item')
    ORL_RE_QTDLOTE     = models.DecimalField(null=False, max_digits=10, decimal_places=3,verbose_name='quantidade')
    ORL_ST_REFERENCIA  = models.CharField(max_length=250,null=False, blank=False)
    CTL_IN_CODIGO      = models.IntegerField(null=True, blank=True)
    PRO_ST_DESCRICAO   = models.CharField(max_length=70,null=True, blank=True)
    PRO_ST_LOTE        = models.CharField(max_length=22,null=False, blank=False,verbose_name='lote')
    PRO_ST_SEQUENCIAL  = models.CharField(max_length=6,null=True, blank=True)
    PRO_ST_ETIQUETA    = JSONField(null=True, blank=True)
    RFC_ST_DESCRICAO   = models.CharField(max_length=250,null=True, blank=True)
    PRO_RE_QTDREFUGO   = models.DecimalField(null=True, max_digits=10, decimal_places=3,verbose_name='refugo')
    PRO_RE_QTDCONV     = models.DecimalField(null=True, max_digits=10, decimal_places=3)
    PRO_ST_LOTEORI     = models.CharField(max_length=22,null=True, blank=True)
    PRO_ST_ID          = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_item')
    ORD_ST_ID          = models.CharField(max_length=44,null=True, blank=True,verbose_name='id_ordem')
    CMAQ_ST_ID         = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_maquina')
    RES_ST_STATUS      = models.CharField(max_length=1,null=True, blank=True, default='N')
    RES_ST_ID          = models.CharField(max_length=10,null=True, blank=True, verbose_name='seq_resumo')
    ORL_RE_QTDAJUSTADA = models.DecimalField(null=True, max_digits=10, decimal_places=3, default=0)
    PRO_ST_FORNECEDOR  = models.CharField(max_length=50,null=True, blank=True)
    # AJUSTE 2026-10-06: colunas lidas pela gravação direta no Oracle (apontamento/apontamento.py, copiado do MP) - JPC - João Castro
    MOV_IN_SEQUENCIA   = models.IntegerField(null=True, blank=True, verbose_name='seq_demanda')
    FMT_ST_CODIGO      = models.CharField(max_length=4,null=True, blank=True,verbose_name='conversor')
    APT_ST_OBSERV      = models.CharField(max_length=250,null=True, blank=True,verbose_name='observacoes')
    class Meta:
        db_table = u'Apt_ApontaOrdem'

class Apt_Pro_Demandas(models.Model):
    FIL_IN_CODIGO      = models.IntegerField(null=False, blank=False)
    MOV_IN_SEQUENCIA   = models.IntegerField(primary_key=True,verbose_name='sequencial')
    MOV_DT_INCLUSAO    = models.DateField(null=False, blank=False,verbose_name='data')
    PRO_IN_CODIGO      = models.IntegerField(null=True, blank=True,verbose_name='item')
    ORD_IN_CODIGO      = models.IntegerField(null=False, blank=False,verbose_name='ordem')
    PRO_RE_QTDLOTE     = models.DecimalField(null=False, max_digits=10, decimal_places=3,verbose_name='quantidade')
    PRO_ST_LOTE        = models.CharField(max_length=50,null=False, blank=False,verbose_name='lote')
    MOV_ST_STATUS      = models.CharField(max_length=1,null=False, blank=False,verbose_name='status')
    CTL_IN_CODIGO      = models.IntegerField(null=True, blank=True,verbose_name='controle')
    PRO_ST_ID          = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_item')
    ORD_ST_ID          = models.CharField(max_length=44,null=True, blank=True,verbose_name='id_ordem')
    CMAQ_ST_ID         = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_maquina')    
    class Meta:
        db_table = u'Apt_Pro_Demandas'

class Apt_Ocorrencia(models.Model):
    ATI_IN_SEQUENCIA = models.IntegerField(primary_key=True)
    ATI_IN_CODIGO   = models.IntegerField(null=False, blank=False)
    ATI_DT_INCLUSAO = models.DateTimeField(null=False, blank=False)
    ATI_USU_INCLUSAO = models.CharField(max_length=20,null=False, blank=False)
    ATI_IN_ORDEM = models.IntegerField(null=False, blank=False)
    ATI_IN_TEMPO = models.IntegerField(null=False, blank=False)
    class Meta:
        db_table = u'Apt_Ocorrencia'

class apt_pro_ordens(models.Model):
    # AJUSTE 2026-11-11 (JPC): PK = ORD_ST_ID, igual ao NMV/ZK (TAB_IN_SEQUENCIA removida, migracao 0047).
    # ORD_ST_ID nunca nulo: vazio e montado com apontamento.api_view.monta_ordem.
    ORG_TAB_IN_CODIGO = models.IntegerField( null=False, blank=False)
    ORG_PAD_IN_CODIGO = models.IntegerField(null=False, blank=False)
    ORG_IN_CODIGO     = models.IntegerField(null=False, blank=False)
    ORG_TAU_ST_CODIGO = models.CharField(max_length=3,null=False, blank=False)
    ORD_TAB_IN_CODIGO = models.IntegerField(null=False, blank=False)
    ORD_SEQ_IN_CODIGO = models.IntegerField(null=False, blank=False)
    ORD_IN_CODIGO     = models.IntegerField(null=False, blank=False,verbose_name='ordem')
    PRO_TAB_IN_CODIGO = models.IntegerField(null=False, blank=False)
    PRO_PAD_IN_CODIGO = models.IntegerField(null=False, blank=False)
    PRO_IN_CODIGO     = models.IntegerField(null=False, blank=False,verbose_name='item')
    ORD_RE_QTDE_ORDEM = models.DecimalField(null=False, max_digits=20, decimal_places=3,verbose_name='quantidade')
    FIL_IN_CODIGO     = models.IntegerField(null=True, blank=True,verbose_name='filial')
    TPO_ST_CODIGO     = models.CharField(max_length=5,null=True, blank=True,verbose_name='Tipo')
    PRO_ST_ITENS      = JSONField(null=True, blank=True)
    PRO_ST_DEMANDAS   = JSONField(null=True, blank=True)
    PRO_ST_INFOADIC   = JSONField(null=True, blank=True)
    PRO_ST_ID         = models.CharField(max_length=13,null=True, blank=True,verbose_name='ITEM')
    ORD_ST_ID         = models.CharField(max_length=44, primary_key=True, serialize=False, verbose_name='ORDEM')
    TPO_ST_ID         = models.CharField(max_length=12,null=True, blank=True,verbose_name='ID_TPO')
    class Meta:
        db_table = u'apt_pro_ordens'

    def save(self, *args, **kwargs):
        # AJUSTE 2026-11-11 (JPC): nunca gravar ORD_ST_ID nulo
        if not self.ORD_ST_ID:
            self.ORD_ST_ID = monta_ord_st_id(self.ORG_TAB_IN_CODIGO, self.ORG_PAD_IN_CODIGO, self.ORG_IN_CODIGO,
                                             self.ORG_TAU_ST_CODIGO, self.ORD_TAB_IN_CODIGO,
                                             self.ORD_SEQ_IN_CODIGO, self.ORD_IN_CODIGO)
        super().save(*args, **kwargs)


def monta_ord_st_id(org_tab, org_pad, org_in, org_tau, ord_tab, ord_seq, ord_in):
    """AJUSTE 2026-11-11 (JPC): mesmo formato de apontamento.api_view.monta_ordem (e do lpad do Oracle)."""
    from apontamento.api_view import monta_ordem
    return monta_ordem([org_tab, org_pad, org_in, str(org_tau), ord_tab, ord_seq, ord_in])


class apt_itens_ordens(models.Model):
    # AJUSTE 2026-11-11 (JPC): PK = PRO_ST_ID, igual ao NMV/ZK (TAB_IN_SEQUENCIA removida, migracao 0048).
    # PRO_ST_ID nunca nulo: vazio e montado com apontamento.api_view.monta_produto.
    PRO_TAB_IN_CODIGO  = models.IntegerField(null=False, blank=False)
    PRO_PAD_IN_CODIGO  = models.IntegerField(null=False, blank=False)
    PRO_IN_CODIGO      = models.IntegerField(null=False, blank=False)
    PRO_ST_DESCRICAO   = models.CharField(max_length=70,null=False, blank=False)
    UNI_ST_UNIDADE     = models.CharField(max_length=8,null=False, blank=False)
    RFC_IN_CODIGO      = models.IntegerField(null=False, blank=False)
    PRO_ST_ATRIBUTOS   = JSONField()
    PRO_ST_REFERENCIA  = JSONField()
    PRO_ST_MEDIDAS     = JSONField()
    # AJUSTE 2026-11-11 (JPC): JSON como no NMV/ZK ({"MVS_ST_REFERENCIA", "PRO_RE_CE", "PRO_RE_APROV"}, migracao
    # 0046); texto cru antigo continua legivel -- ler com app.services.referencia_padrao
    MVS_ST_REFERENCIA  = JSONField(null=True, blank=True)
    PRO_ST_ID          = models.CharField(max_length=13, primary_key=True, serialize=False, verbose_name='ITEM')
    PRO_ST_CONVERSOR   = JSONField()
    class Meta:
        db_table = u'apt_itens_ordens'

    def save(self, *args, **kwargs):
        # AJUSTE 2026-11-11 (JPC): nunca gravar PRO_ST_ID nulo
        if not self.PRO_ST_ID:
            self.PRO_ST_ID = monta_pro_st_id(self.PRO_TAB_IN_CODIGO, self.PRO_PAD_IN_CODIGO, self.PRO_IN_CODIGO)
        super().save(*args, **kwargs)


def monta_pro_st_id(pro_tab, pro_pad, pro_in):
    """AJUSTE 2026-11-11 (JPC): mesmo formato de apontamento.api_view.monta_produto (3+3+7)."""
    from apontamento.api_view import monta_produto
    return monta_produto([pro_tab, pro_pad, pro_in])

class apt_pro_atividade(models.Model):
    TAB_IN_SEQUENCIA   = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    ATI_TAB_IN_CODIGO  = models.IntegerField(null=False, blank=False)
    ATI_PAD_IN_CODIGO  = models.IntegerField(null=False, blank=False)
    ATI_IN_CODIGO      = models.IntegerField(null=False, blank=False,verbose_name='Codigo')
    ATI_ST_NOME        = models.CharField(max_length=60,null=False, blank=False,verbose_name='Atividade')
    class Meta:
        db_table = u'apt_pro_atividade'
        
class apt_tb_tabfilseqlote(models.Model):
    TSEQ_IN_SEQUENCIA = models.IntegerField(primary_key=True, serialize=False, verbose_name='SEQ')
    TAB_IN_CODIGO     = models.IntegerField(null=False, blank=False)
    class Meta:
        db_table = u'apt_tb_tabfilseqlote'
        
class Apt_ResumoOrdem(models.Model):
    RES_ST_ID           = models.CharField(primary_key=True, max_length=10,serialize=False, verbose_name='RES_ID')
    RES_IN_CODIGO       = models.IntegerField(null=False, blank=False, verbose_name='CODIGO')
    RES_IN_SEQUENCIA    = models.IntegerField(null=False, blank=False, verbose_name='SEQUENCIA')
    ORD_ST_ID           = models.CharField(max_length=42,null=False, blank=False,verbose_name='ORDEM')
    PRO_ST_ID           = models.CharField(max_length=13,null=False, blank=False,verbose_name='ID_ITEM')
    PRO_RE_QTDINFORMADA = models.DecimalField(null=False, max_digits=10, decimal_places=3)
    RES_ST_STATUS       = models.CharField(max_length=1,null=False, blank=False,verbose_name='STATUS')
    PRO_IN_CODIGO       = models.IntegerField(null=True, blank=True,verbose_name='ITEM')
    PRO_ST_DESCRICAO    = models.CharField(max_length=70,null=True, blank=True,verbose_name='DESCRICAO')
    PRO_RE_QTDORIGINAL  = models.DecimalField(null=True, max_digits=10, decimal_places=3)
    class Meta:
        db_table = u'Apt_ResumoOrdem'

class Apt_EstFormatos(models.Model):
    PUN_ST_ID           = models.CharField(primary_key=True, max_length=16,serialize=False,verbose_name='PUN_ID')
    FMT_ST_ID           = models.CharField(max_length=10,null=True, blank=True,verbose_name='FMT_ID')
    PRO_ST_ID           = models.CharField(max_length=13,null=True, blank=True,verbose_name='PRO_ID')
    FMT_ST_CODIGO       = models.CharField(max_length=4,null=True, blank=True,verbose_name='CONVERSOR')
    FMT_ST_NOME         = models.CharField(max_length=30,null=True, blank=True,verbose_name='DESCRICAO')
    UNI_ST_UNIDADE      = models.CharField(max_length=8,null=True, blank=True,verbose_name='UNIDADE')
    FMT_ST_FORMULA      = models.CharField(max_length=200,null=True, blank=True,verbose_name='FORMULA')
    class Meta:
        db_table = u'Apt_EstFormatos'
        
class Apt_ProTipoOrdens(models.Model):
    TPO_ST_ID = models.CharField(primary_key=True, max_length=15,serialize=False,verbose_name='TPO_ID')
    TPO_ST_CODIGO_TIPO = models.CharField(max_length=5,null=True, blank=True,verbose_name='TIPO DE ORDEM')
    TPO_ST_UNIDADE = models.CharField(max_length=8,null=True, blank=True,verbose_name='UNIDADE CONVERSOR')
    TPO_ST_SELCONVERSOR = models.BooleanField(default=True,null=True, blank=True,verbose_name='SELECIONAR CONVERSOR')
    TPO_ST_OPERACAO = models.CharField(max_length=1, default='N',null=True, blank=True,verbose_name='CONFIGURAR OPERACAO')
    TPO_ST_NOME = models.CharField(max_length=50, null=True, blank=True,verbose_name='DESCRIÇÃO')
    class Meta:
        db_table = u'Apt_ProTipoOrdens'
class Apt_ProMaquinaConfig(models.Model):
    CFG_ST_ID = models.CharField(primary_key=True, max_length=39,serialize=False,verbose_name='CFG_ID')
    CTR_ST_ID = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_centro')
    CMAQ_ST_ID = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_maquina')
    OPR_ST_ID = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_operacao')
    CUS_BO_NAOBAIXADEMANDA = models.CharField(default='N',max_length=1,null=False, blank=False,verbose_name='Não Baixa Demanda')
    CUS_BO_GERASEQPALLET = models.CharField(default='N',max_length=1,null=False, blank=False,verbose_name='Controla Sequencial de Pallet')
    CUS_BO_CONVERSOR = models.CharField(default='N',max_length=1,null=False, blank=False,verbose_name='Utiliza Conversor')
    CUS_BO_LOTES = models.CharField(default='N',max_length=1,null=False, blank=False,verbose_name='Gera Multiplos Lotes')
    OPR_ST_OPERACAO = models.CharField(max_length=100,null=True, blank=True,verbose_name='Descrição da operação')
    CMAQ_ST_DESCRICAO = models.CharField(max_length=100,null=True, blank=True,verbose_name='Descrição da máquina')
    MAQ_ST_NOME = models.CharField(max_length=60,null=True, blank=True,verbose_name='Centro de Trabalho')
    #OPR_IN_CODIGO = IntegerField(null=True, blank=True, verbose_name='operacão')
    #CMAQ_IN_CODIGO = IntegerField(null=True, blank=True, verbose_name='maquina')
    #MAQ_IN_CODIGO = IntegerField(null=True, blank=True, verbose_name='centro')
    class Meta:
        db_table = u'Apt_ProMaquinaConfig'

class Car_AtributosReferencia(models.Model):
    CAR_ST_ID = models.CharField(primary_key=True, max_length=26,serialize=False,verbose_name='CAR_ID')
    RAT_ST_ID = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_atributo')
    RFC_ST_ID = models.CharField(max_length=13,null=True, blank=True,verbose_name='id_referência')
    PAI_RAT_IN_CODIGO = models.IntegerField(null=False, blank=False, verbose_name='Atributo Pai')
    RAT_IN_CODIGO = models.IntegerField(null=False, blank=False, verbose_name='Atributo')
    RAT_ST_DESCRICAO = models.CharField(max_length=70,null=True, blank=True,verbose_name='Descrição')
    RAT_VALUE = models.CharField(max_length=100,null=True, blank=True,verbose_name='valores')
    RAT_CH_TIPO = models.CharField(max_length=1,null=True, blank=True,verbose_name='Tipo')
    CAR_IN_PRIORIDADE = models.IntegerField(null=True, blank=True, verbose_name='prioridade')
    RFC_IN_CODIGO = models.IntegerField(null=False, blank=False, verbose_name='Referência')
    RAT_BO_GRUPO = models.CharField(max_length=1,null=True, blank=True,verbose_name='Grupo')
    CAR_BO_OBRIGATORIO = models.CharField(max_length=1,null=True, blank=True,verbose_name='Obrigatorio',default='S')
    PAI_ST_DESCRICAO = models.CharField(max_length=70,null=True, blank=True,verbose_name='Nome_Pai')
    # AJUSTE 2026-11-11 (JPC): tipo do conteudo vindo do Mega (est_atributoreferencia); 'N' = numerico (do ZK)
    RAT_CH_TIPOCONTEUDO = models.CharField(max_length=1,null=True, blank=True,verbose_name='Tipo_Conteudo')
    class Meta:
        db_table = u'Car_AtributosReferencia'