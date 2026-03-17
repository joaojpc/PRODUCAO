# -*- coding: utf-8 -*-
import os

import socket
import json
from unicodedata import normalize
from django.utils import timezone

from django import forms

#from apontamento.custom_views import Login_inicial, Listar_opcoes, IntProd
#from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, Login_inicial_sqlite
from .custom_views_sqlite import *
from apontamento.api_view import *

#from apontamento.models import Apt_controle, Lotes_Apt, Apt_ocorrencia
import requests
from django.http import HttpResponse

os.environ["NLS_LANG"] = ".AL32UTF8"
def remover_acentos(txt, codif='utf-8'):
    return normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore')

def get_ip():
    return socket.gethostbyname(socket.gethostname())

class FormLogin(forms.Form):
    usuario = forms.CharField(max_length=20,label='Operador')
    ordem = forms.CharField(max_length=20,label='Ordem de produção')
    def clean(self):
        usu_valid = False
        ord_valid = False
        cleaned_data = super(FormLogin,self).clean()
        v_usuario = self.cleaned_data.get("usuario")
        if len(v_usuario) != 10:
            raise forms.ValidationError("Erro na leitura do usuário, favor ler lovamente!")            
        v_ordem = self.cleaned_data.get("ordem")
        if len(v_ordem) != 14:
            raise forms.ValidationError("Erro na leitura da ordem, favor ler lovamente!")            
        iniciar = Login_inicial_sqlite(v_ordem,v_usuario,1)
        usuarios = json.loads(iniciar.apt_usuario_sqlite())
        for usu in usuarios:
            if usu['opd_st_alternativo'] == v_usuario:
                usu_valid = True
        if not usu_valid:
            raise forms.ValidationError("Usuário não cadastrado!")
        if not (v_ordem != 0 ) or v_ordem is None:
            raise forms.ValidationError(" Informar a ordem!")

class FormUser(forms.Form):
    ctl_in_usuario = forms.CharField(max_length=20,label='Operador')
    ord_in_codigo = forms.CharField(max_length=20,label='Ordem de produção')
    def clean(self):
        usu_valid = False
        ord_valid = False
        cleaned_data = super(FormUser,self).clean()
        usuario = self.cleaned_data.get("ctl_in_usuario")
        ordem = self.cleaned_data.get("ord_in_codigo")
        iniciar = Login_inicial_sqlite(ordem,usuario)
        usuarios = json.loads(iniciar.apt_usuario())        
        raise forms.ValidationError(usuario)
        if usuarios is None:
            raise forms.ValidationError("Nenhum Usuário cadastrado!")
        for usu in usuarios:
            #print (usu[2])
            if usu['opd_st_alternativo'] == usuario:
                usu_valid = True
                ordem_prod = json.loads(iniciar.ordem())
        if not usu_valid:
            raise forms.ValidationError("Usuário não cadastrado!")
        for op in ordem_prod:
            if op['ord_in_codigo'] == ordem:
                ord_valid = True
        if not ord_valid:
            raise forms.ValidationError(" Essa ordem de produção não está liberada!")
class FormUser_sqlite(forms.Form):
    ctl_in_usuario = forms.CharField(max_length=20,label='Operador')
    ord_in_codigo = forms.CharField(max_length=20,label='Ordem de produção')
    def clean(self):
        usu_valid = False
        ord_valid = False
        ordem = 0
        cleaned_data = super(FormUser_sqlite,self).clean()
        usuario = self.cleaned_data.get("ctl_in_usuario")
        ordem = self.cleaned_data.get("ord_in_codigo")
        iniciar = Login_inicial_sqlite(ordem,usuario)        
        usuarios = json.loads(iniciar.apt_usuario_sqlite())        
        for usu in usuarios:
            if usu['opd_st_alternativo'] == usuario:
                usu_valid = True
        if not usu_valid:
            raise forms.ValidationError("Usuário não cadastrado!")
        if not (ordem != 0 ) or ordem==None:
            raise forms.ValidationError(" Informar a ordem!")
			
class RegOcorForm(forms.Form):
    litens = []
    #c_ini= Listar_opcoes_sqlite()
    #v_logado = c_ini.equipaLogado_sqlite()
    v_logado = False
    if v_logado:
        obj_itens = IntAPI();
        itens = json.loads(obj_itens.listar_ocorencias())
        for itn in itens:
            litens.append((itn['ati_in_codigo'], itn['ati_st_nome']))
    ati_in_codigo = forms.ChoiceField(choices=(litens),label='Motivo da parada')
    ati_in_tempo = forms.CharField(required=False,widget=forms.HiddenInput(),label='Tempo parado')
class DemForm(forms.Form):
    dem_in_codigo = forms.IntegerField(label='Item',widget=forms.TextInput(attrs={'readonly':'True'}))
    dem_re_qtdlote = forms.FloatField(required=False,widget=forms.HiddenInput(), label='Quantidade do lote')
    dem_st_lote = forms.CharField (required=False, label='Lote demanda',widget=forms.TextInput(attrs={'readonly':'True'}))
    def clean(self):
        cleaned_data = super(DemForm, self).clean()
        #print(cleaned_data)
        qtde = self.cleaned_data.get("dem_re_qtdlote")
        if (qtde == ''):
            raise forms.ValidationError(" Quantidade obrigatória!")
        if (qtde is None):
            raise forms.ValidationError(" Quantidade obrigatória!")

class DemFormLocal(forms.Form):
    dem_st_lote = forms.CharField (max_length=24, required=True, label='Lote demanda')
    dem_re_qtdlote = forms.FloatField(required=False,widget=forms.HiddenInput(), label='Quantidade do lote')
    ord_in_codigo   = forms.CharField(required=False,widget=forms.HiddenInput(),label='Ordem')
    fil_in_codigo   = forms.CharField(required=False,widget=forms.HiddenInput(),label='Filial')
    def clean(self):
        cleaned_data = super(DemFormLocal, self).clean()
        #print(cleaned_data)
        qtde = self.cleaned_data.get("dem_re_qtdlote")
        loteDem = self.cleaned_data.get("dem_st_lote")
        ordem = self.cleaned_data.get("ord_in_codigo")
        filial = self.cleaned_data.get("fil_in_codigo")
        v_pro_in_codigo = None
        v_item_valid = False
        #Valida lote Já baixado
        req = {'ordem': ordem,'filial': filial, 'lote': loteDem}
        dados = IntAPI(req)        
        c_demanda = dados.listar_demanda(req) 
        dprod = prep_producao()
        cr_dem = dprod.prepara_demandas(req)
        if c_demanda:
            raise forms.ValidationError(" Demanda Já baixada nessa ordem!")
        #valida o item da demanda;
        for item in c_demanda:
            v_pro_in_codigo = item['PRO_IN_CODIGO']
        for rs_dem in cr_dem:
            if rs_dem['com_in_codigo'] == v_pro_in_codigo:
                v_item_valid = True
        if not v_item_valid:
            raise forms.ValidationError(" Este item não faz parte da demanda da ordem, favor inserir na ordem e baixar as informações novamente!")                    
        if (qtde == ''):
            raise forms.ValidationError(" Quantidade obrigatória!")
        if (qtde is None):
            raise forms.ValidationError(" Quantidade obrigatória!")        
        
class RegLotForm(forms.Form):
    pro_in_codigo = forms.IntegerField(label='Item',widget=forms.HiddenInput(attrs={'readonly':'True'}))    
    orl_st_referencia = forms.CharField(widget=forms.HiddenInput(),required=False)
    orl_re_qtdlote = forms.FloatField(required=False,widget=forms.HiddenInput(),label='Quantidade do Lote')
    orl_re_qtdrefugo = forms.FloatField(required=False,widget=forms.HiddenInput(),label='Quantidade Refugo')
    orl_st_observ   = forms.CharField(required=False,widget=forms.HiddenInput(),label='Observações')
    ord_in_codigo   = forms.CharField(required=False,widget=forms.HiddenInput(),label='Ordem')
    fil_in_codigo   = forms.CharField(required=False,widget=forms.HiddenInput(),label='Filial')
    pro_st_loteori  = forms.CharField(max_length=22,widget=forms.HiddenInput(),required=False, label='Origem')
    pro_st_fornecedor  = forms.CharField(max_length=50,widget=forms.HiddenInput(),required=False, label='Fornecedor')
    def clean(self):
        v_validarefer = False
        if v_validarefer:
            v_lista = []
            cleaned_data = super(RegLotForm, self).clean()
            lote_refer = self.cleaned_data.get("orl_st_referencia")
            lote_item  = self.cleaned_data.get("pro_in_codigo")
            ordem      = self.cleaned_data.get("ord_in_codigo")
            filial      = self.cleaned_data.get("fil_in_codigo")
            v_lista.append(ordem)
            v_lista.append(filial)
            obj_itens = IntAPI_sqlite();
            itens = json.loads(obj_itens.itens_ordem_sqlite(v_lista))
            # print('forms 141',itens)
            for itn in itens:
                #print (itn['pro_in_codigo'])
                if (itn['pro_in_codigo'] == lote_item):
                    if(itn['rfc_in_codigo'] != 0):
                        v_validarefer = True
            if (lote_refer == '') and (v_validarefer):
                raise forms.ValidationError(" Campo referência é obrigatório!")
class ListLotForm(forms.Form):
    lote_st_sequencial  = forms.CharField(required=False,label='Lote')

class LotesReceb(forms.Form):
    avr_st_nota = forms.CharField(max_length=20,label='Nota Fiscal')
    fil_in_codigo = forms.CharField(max_length=3,label='Filial')
    mvl_st_lote = forms.CharField(max_length=22,label='Lote')
    mvl_st_impressora = forms.CharField(max_length=15,label='impressora', initial='192.168.60.101')
    
class TrocarImpressora(forms.Form):
    mvl_st_impressora = forms.CharField(max_length=15,label='impressora')
