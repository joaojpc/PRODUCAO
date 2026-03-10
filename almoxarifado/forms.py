# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

import socket
import json
from unicodedata import normalize
from django.utils import timezone

from django import forms
from almoxarifado.api_view import *

class FormLogin(forms.Form):
    usuario = forms.CharField(max_length=20,label='Operador')
    centrocusto = forms.CharField(max_length=20,label='Centro de custos')
    ordemservico = forms.CharField(max_length=17,label='Ordem de Serviço',required=False)
    def clean(self):
        user_valid = False
        ccusto_valid = False
        cleaned_data = super(FormLogin,self).clean()
        v_user = self.cleaned_data.get("usuario")
        v_ccusto = self.cleaned_data.get("centrocusto") 
        cr_itn = lista_usuarios(v_user)
        if cr_itn:
            user_valid = True
            #for rs_itn in cr_itn:
            #    if rs_itn['OPD_ST_CRACHA'] == v_user:
            #        item_valid = True
        if not user_valid:
            raise forms.ValidationError("Usuário não cadastrado!")
        cr_cc = lista_ccusto(v_ccusto)
        if cr_cc:
            ccusto_valid = True
            #for rs_cc in cr_cc:
            #    if rs_itn['CUS_ID_CCUSTO'] == v_ccusto:
            #        ccusto_valid = True
        if not ccusto_valid:
            raise forms.ValidationError("Centro de custos não cadastrado!")
class FormRequisicao(forms.Form):
    bxi_id_produto = forms.CharField(max_length=20,label='Item')
    bxi_re_quantidade = forms.FloatField(required=False,widget=forms.HiddenInput(), label='Quantidade')
    bxi_id_almoxa = forms.CharField(max_length=18,required=False,widget=forms.HiddenInput(),label='Destino')
    def clean(self):
        item_valid = False
        cleaned_data = super(FormRequisicao,self).clean()
        v_item = self.cleaned_data.get("bxi_id_produto")
        cr_itn = Item_requisicao(v_item)
        for rs_itn in cr_itn:
            if rs_itn['BXI_ID_PRODUTO'] == v_item:
                item_valid = True
        if not item_valid:
            raise forms.ValidationError("Item não cadastrado!")
class FormEtiqueta(forms.Form):
    pro_in_codigo = forms.CharField(max_length=20,label='Item')
class FormSaldo(forms.Form):
    pro_in_codigo = forms.CharField(max_length=20,label='Item')
class FormLoginOperador(forms.Form):
    usuario = forms.CharField(max_length=20,required=False,label='Operador')    
