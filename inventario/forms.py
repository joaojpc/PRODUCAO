# -*- coding: utf-8 -*-
import os

import socket
import json
from unicodedata import normalize
from django.utils import timezone
from django import forms

class FormInventario(forms.Form):
    bxi_id_produto = forms.CharField(max_length=20,label='Item')
    inv_re_quantidade = forms.FloatField(required=False,widget=forms.HiddenInput(), label='Saldo')
class FormLoginInventario(forms.Form):
    usuario = forms.CharField(max_length=20,required=False,widget=forms.HiddenInput(),label='Operador')
