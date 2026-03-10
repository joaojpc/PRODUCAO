# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
#import socket
#from django.contrib.auth.decorators import login_required#
import socket
import os

from django.http import HttpResponse
#from pandas import json
from unicodedata import normalize

from django.shortcuts import render, redirect

# Create your views here.
from django.utils import timezone
import time
from datetime import datetime, date

from django.shortcuts import render

from django import template
import requests

#from apontamento.custom_views import Listar_opcoes, User_logado, Login_inicial, IntProd
from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite, Login_inicial_sqlite, formatar_ordem, IntAPI_sqlite
from apontamento.api_view import IntAPI, geturl_local, geturlapp, geturl_sqlite, geturlapi, geturl_api_sqlite, geturl_producao

from apontamento.forms import FormUser, RegOcorForm, DemForm, RegLotForm, FormUser_sqlite, FormLogin, DemFormLocal, ListLotForm
from apontamento.formata_string import formatar_string
from apontamento.Etiqueta_precorte import gera_etiqueta

from .serializer import *
from .models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from rest_framework import status

from datetime import datetime, date, timedelta
register = template.Library()

def converter_unidade(pParams):
    if pParams[0] == 'OP003':
        if pParams[2] > 0:
            v_qtdeConv = round(pParams[4]*(pParams[2]/1000),3)
        else:
            v_qtdeConv = pParams[4]
    else:
        v_qtdeConv = pParams[4]
    return v_qtdeConv

def formatar_caracteristicas(preferencia,patrib):
    v_lista = preferencia.split(";")
    v_atrib = json.loads(patrib)
    v_retorno = None;
    for l_atr in v_atrib:
        for c_rs in v_lista:
            if c_rs == l_atr['id']:
                if v_retorno is None:
                    v_retorno = l_atr['name']
                else:
                    v_retorno += ' / '
                    v_retorno += l_atr['name']
                break
    return v_retorno

def controledemanda(request):
    if 'ord_in_codigo' in request.session:
        ord_in_codigo = request.session['ord_in_codigo']
        tmpl = "apontamento/controle_demanda.html",
        ord_in_codigo = request.session['ord_in_codigo']
        return render(request, tmpl,{'ord_in_codigo':ord_in_codigo})
    else:
        return redirect('demos_sessions')    
def session_demo(request):
    v_logado = False
    if 'ordem' in request.session:
        ordem = request.session['ordem']
    else:
        ordem = None
    if 'usuario' in request.session:
        usuario = request.session['usuario']
    else:
        usuario = None
    if 'ord_in_codigo' in request.session:
        ord_in_codigo = request.session['ord_in_codigo']
    else:
        ord_in_codigo = None
    if 'fil_in_codigo' in request.session:
        fil_in_codigo = request.session['fil_in_codigo']
    else:
        fil_in_codigo = None
    if 'seq_in_operacao' in request.session:
        seq_in_operacao = request.session['seq_in_operacao']
    if 'usu_st_nome' in request.session:
        usu_st_nome = request.session['usu_st_nome']
    else:
        usu_st_nome = None
    if 'ctl_in_codigo' in request.session:
        ctl_in_codigo = request.session['ctl_in_codigo']
    else:
        ctl_in_codigo = None
    template = "apontamento/session.html",
    form = FormLogin()
    if request.method == "GET":
        if 'action' in request.GET:
            action = request.GET.get('action')
            if action == 'logout':
                #Fazer update na tabela de controle;
                if request.session.has_key('ordem'):
                    encerrar = Login_inicial_sqlite(ordem,usuario)
                    encerrar.descontar_sqlite()
                    request.session.flush()
                return redirect('demos_sessions')
            if action == 'trocar':
                if request.session.has_key('ordem'):
                    #Não faz update na tabela de controle;
                    request.session.flush()
                return redirect('demos_sessions')
        if 'ordem' in request.session:
            ordem = request.session['ordem']
            #print(request.session.get_expiry_age())
            #print(request.session.get_expiry_date())
    elif request.method == "POST":
        form = FormLogin(request.POST)
        #print(request.session.keys())
        if form.is_valid():
            ordem = form.cleaned_data['ordem']
            usuario = form.cleaned_data['usuario']
            #Formata os dados do código de barras da ordem;
            r_ordem = json.loads(formatar_ordem(ordem))
            for v_ord in r_ordem:
                ord_in_codigo = v_ord['ordem']
                fil_in_codigo = v_ord['filial']
                seq_in_operacao = v_ord['operacao']
            iniciar = Login_inicial_sqlite(ordem,usuario)
            usuarios = json.loads(iniciar.apt_usuario_sqlite())
            for usu in usuarios:
                usu_st_nome = usu['opd_st_descricao']
                opd_in_codigo = usu['opd_in_codigo']
            if ordem is not None:
                request.session['ordem'] = ordem
                request.session['usuario'] = usuario
                request.session['ord_in_codigo'] = ord_in_codigo
                request.session['fil_in_codigo'] = fil_in_codigo
                request.session['seq_in_operacao'] = seq_in_operacao
                request.session['usu_st_nome'] = usu_st_nome
                #Verificar se o usuário já tem apontamento aberto para a ordem;
                cr_ini = json.loads(iniciar.userLogado_sqlite())
                for rs_ini in cr_ini:
                    v_logado = rs_ini['logado']
                if not(v_logado):
                    #criar novo apontamento para a ordem;
                    iniciar.conectar_sqlite()
                cr_ini2 = json.loads(iniciar.userLogado_sqlite())
                for rs_ini2 in cr_ini2:
                    ctl_in_codigo = rs_ini2['ctl_in_codigo']
                    request.session['ctl_in_codigo'] = ctl_in_codigo
                return redirect('menu')
            else:
                #print(request.session.keys())
                request.session.update({
                'ordem': None,
                'usuario': None})
                ordem = None
                usuario = None
    return render(request, template, {'demo_title': 'Session in Django',
                                      'form': form,
                                      'ordem': ordem,
                                      'usuario':usuario,
                                      'ord_in_codigo':ord_in_codigo,
                                      })
# Create your views here.
def home(request):
    template = "apontamento/home.html"
    return render(request, template)
def principal(request):
    v_logado = True
    if v_logado:
        tmpl = "apontamento/principal.html"
        if request.method == "POST":
            pass
        else:
            pass
        return render(request, tmpl)
    else:
        tmpl = "apontamento/home.html"
        return render(request, tmpl)
def protected_view(request):
    template = 'apontamento/equipamento.html'
    v_lista = Listar_opcoes_sqlite()
    v_logado = v_lista.equipaLogado_sqlite()
    if v_logado:
        controle = json.loads(v_lista.lis_resumo_sqlite())
        return render(request, template, {'controle': controle})
    else:
        template = "apontamento/home.html"
        return render(request, template)

def loginControl(request):
    v_lista = Listar_opcoes()
    v_logado = v_lista.equipaLogado()
    if v_logado:
        v_encerra = User_logado()
        desconectar = v_encerra.descontar()
    template= 'apontamento/login.html'
    if request.method == "POST":
        form = FormUser(request.POST)
        if form.is_valid():
            ordem = form.cleaned_data['ord_in_codigo']
            usuario = form.cleaned_data['ctl_in_usuario']
            l_lista = []
            l_lista.append(ordem)
            l_lista.append(usuario)
            v_encerra = User_logado()
            v_encerra.conectar(l_lista)
            return redirect('menu')
    else:
        form = FormUser()
    return render(request, template, {'form': form})

def testar_impressao(request):
    template= 'apontamento/impressao.html'
    form = ListLotForm()
    if 'apt_in_sequencia' in request.session:
        apt_in_sequencia = request.session['apt_in_sequencia']
    else:
        apt_in_sequencia = None
    if request.method == "POST":
        funcao = 'apontamentos'
        api_listalotes = geturl_sqlite(funcao)
        v_seqlote = ListLotForm(request.POST)
        v_seq = None
        if v_seqlote.is_valid():
            cd = v_seqlote.cleaned_data
            v_seq = cd['lote_st_sequencial']
        else:
            v_seq = None
        try:
            if v_seq is not None:
                v_lote = []
                v_lote.append(request.session['ord_in_codigo'])
                v_lote.append(request.session['fil_in_codigo'])
                v_lote.append(v_seq)
                payload = {'ordem': v_lote[0],'filial': v_lote[1],'sequencial': int(v_lote[2])}
                vresponse = requests.get(api_listalotes, params=payload)
                cr = json.loads(vresponse.content)
                for rs in cr:
                    c_lote = rs['PRO_ST_ETIQUETA']
                    c_etiqueta = gera_etiqueta()
                    c_etiqueta.etiqueta_pre(json.dumps(c_lote))
        except:
            pass
        return redirect('listarlotes_sqllite')
    else:
        print('GET')
    return render(request, template, {'form': form,'apt_in_sequencia':apt_in_sequencia})

def loginControl_sqlite(request):
    v_lista = Listar_opcoes_sqlite()
    v_logado = v_lista.equipaLogado_sqlite()
    if v_logado:
        v_encerra = User_logado_sqlite()
        desconectar = v_encerra.descontar_sqlite()
    template= 'apontamento/login.html'
    if request.method == "POST":
        form = FormUser_sqlite(request.POST)
        if form.is_valid():
            ordem = form.cleaned_data['ord_in_codigo']
            usuario = form.cleaned_data['ctl_in_usuario']
            l_lista = []
            l_lista.append(ordem)
            l_lista.append(usuario)
            v_encerra = User_logado_sqlite()
            v_encerra.conectar_sqlite(l_lista)            
            return redirect('menu')
    else:
        form = FormUser_sqlite()
    return render(request, template, {'form': form})

def ocorrencias(request):
    template = "apontamento/listar_ocorrencias.html"    
    v_ini = Listar_opcoes_sqlite();
    c_ini = json.loads(v_ini.lis_controle_sqlite())
    for v_cur in c_ini:
        v_equipamento = v_cur['ord_in_codigo']
    ini_prod = IntAPI();    
    form = json.loads(ini_prod.reg_ocorencias())    
    return render(request, template,{'form': form})

def insOcorrencia(request):
    template = 'apontamento/nova_ocorrencia.html'
    ini_prod = IntAPI()
    lista = ini_prod.listar_ocorencias()
    if request.method == "POST":
        form = RegOcorForm(request.POST)
        if form.is_valid():
            funcao = 'ocorrencias'
            api_ocorrencia = geturl_local(funcao)
            ocorrencia = int(form.cleaned_data['ati_in_codigo'])
            tempo = int(form.cleaned_data['ati_in_tempo'])
            row_now = timezone.now()
            str_now = row_now.strftime('%Y-%m-%d %H:%M:%S')            
            l_lista = []            
            l_lista.append(ocorrencia)
            l_lista.append(tempo)
            l_lista.append(str_now)
            ini_prod = IntAPI()
            ini_prod.gravar_ocorrencia(l_lista)
            
            '''v_iniseq = Listar_opcoes_sqlite()
            c_seqati = json.loads(v_iniseq.seq_ocor_sqlite())
            for r_seq in c_seqati:
                l_lista.append(r_seq['sequencia'])
                l_lista.append(r_seq['usuario'])
                l_lista.append(r_seq['ordem'])
                
            dados = data = {"ATI_IN_SEQUENCIA": l_lista[3],
                            "ATI_IN_CODIGO": l_lista[0],
                            "ATI_DT_INCLUSAO": l_lista[2],
                            "ATI_USU_INCLUSAO": l_lista[4],
                            "ATI_IN_ORDEM": l_lista[5],
                            "ATI_IN_TEMPO": l_lista[1]}            
            response = requests.post(api_ocorrencia, data=dados)'''
            return redirect('ocorrencia')
    else:
        form = RegOcorForm()
    return render(request, template, {'form': form,'lista': lista})

def baixaDemanda(request):
    template = 'apontamento/demandas.html'
    ini_prod = IntAPI();
    c_demanda  = json.loads(ini_prod.empenho_demanda())
    return render(request, template, {'dem': c_demanda})

def baixaDemandaLocal(request):
    template = 'apontamento/demandalocal.html'
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    funcao = 'demandas'
    api_listalotes = geturl_sqlite(funcao)
    payload = {'ordem': v_lista[0],'filial': v_lista[1],}
    c_demanda = requests.get(api_listalotes, params=payload).json()
    return render(request, template, {'dem': c_demanda})

# processo vinculado a api_view
def insDemandas(request):
    """ A view of all bands. """
    template = 'apontamento/novademanda.html'
    ini_prod = IntAPI()
    #c_demanda = json.loads(ini_prod.ord_demandas())
    c_demanda = json.loads(ini_prod.ordem_demandas())
    if request.method == "POST":
        form = DemForm(request.POST)
        if form.is_valid():
            l_demandas = []
            funcao = 'demandas'            
            api_demandas = geturl_local(funcao)
            #print 'Valido'
            v_dem_in_codigo = form.cleaned_data['dem_in_codigo']
            v_mvs_st_loteforne = form.cleaned_data['dem_st_lote']
            v_apt_re_quantidade = form.cleaned_data['dem_re_qtdlote']
            l_demandas.append(v_dem_in_codigo)
            l_demandas.append(v_mvs_st_loteforne)
            l_demandas.append(v_apt_re_quantidade)
            v_iniseq = Listar_opcoes_sqlite()
            c_seqmov = json.loads(v_iniseq.seq_movdem_sqlite())
            row_now = timezone.now()
            str_now = row_now.strftime('%Y-%m-%d')
            mov_status = 'A'
            l_demandas.append(str_now)
            l_demandas.append(mov_status)
            for r_seq in c_seqmov:
                l_demandas.append(r_seq['sequencia'])
                l_demandas.append(r_seq['filial'])
                l_demandas.append(r_seq['ordem'])
            dados = data = {"FIL_IN_CODIGO": l_demandas[6],
                            "MOV_IN_SEQUENCIA": l_demandas[5],
                            "PRO_IN_CODIGO": l_demandas[0],
                            "ORD_IN_CODIGO": l_demandas[7],
                            "PRO_RE_QTDLOTE": l_demandas[2],
                            "PRO_ST_LOTE": l_demandas[1],
                            "MOV_ST_STATUS": l_demandas[4],
                            "MOV_DT_INCLUSAO": l_demandas[3]}
            #print(dados)
            response = requests.post(api_demandas, data=dados)
            #print(requests.post)
            return redirect('demanda')
        #else:
            #print 'Inválido'
    else:
        form = DemForm()
    var_get_search = request.GET.get('search_box')
    if var_get_search is not None:
        c_demanda = c_demanda.filter(name__icontains=var_get_search)
    return render(request, template, {'form': form, 'dem': c_demanda})

def insDemandaslocal(request):
    l_demandas = []
    l_demandas.append(request.session['ord_in_codigo'])
    l_demandas.append(request.session['fil_in_codigo'])
    l_demandas.append(request.session['ctl_in_codigo'])
    template = 'apontamento/novademandalocal.html'
    funcao = 'demandas/'
    api_demandas = geturl_sqlite(funcao)
    if request.method == "POST":
        form = DemFormLocal(request.POST)
        if form.is_valid():
            #print 'Valido'            
            v_mvs_st_loteforne = form.cleaned_data['dem_st_lote']
            v_apt_re_quantidade = form.cleaned_data['dem_re_qtdlote']
            l_demandas.append(v_mvs_st_loteforne)            
            l_demandas.append(v_apt_re_quantidade)
            #Valida lote já baixado
            payload = {'ordem': l_demandas[0],'filial': l_demandas[1],'lote': l_demandas[3]}
            c_demanda = requests.get(api_demandas, params=payload).json()
            if not c_demanda:
                v_iniseq = IntAPI_sqlite(l_demandas)
                v_seqmov = v_iniseq.seq_movdem_sqlite()
                row_now = timezone.now()
                str_now = row_now.strftime('%Y-%m-%d')
                mov_status = 'A'
                l_demandas.append(mov_status)
                l_demandas.append(str_now)
                l_demandas.append(v_seqmov)    
                dados = data = {"FIL_IN_CODIGO": l_demandas[1],
                            "MOV_IN_SEQUENCIA": l_demandas[7],
                            "MOV_DT_INCLUSAO": l_demandas[6],
                            "PRO_IN_CODIGO": '',
                            "ORD_IN_CODIGO": l_demandas[0],
                            "PRO_RE_QTDLOTE": l_demandas[4],
                            "PRO_ST_LOTE": l_demandas[3],
                            "MOV_ST_STATUS": l_demandas[5],
                            "CTL_IN_CODIGO": l_demandas[2]}
                #print(dados)
                response = requests.post(api_demandas, data=dados)
                #print(requests.post)
            return redirect('demandalocal')
        #else:
            #print 'Inválido'
    else:
        form = DemFormLocal()
    return render(request, template, {'form': form})

def listarlotes_sqllite(request):
    template = 'apontamento/listar_lotes.html'
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    funcao = 'apontamentos'
    api_listalotes = geturl_sqlite(funcao)
    payload = {'ordem': v_lista[0],'filial': v_lista[1],}
    vresponse = requests.get(api_listalotes, params=payload)
    listLotes = json.loads(vresponse.content)
    return render(request, template,{'listLotes': listLotes})

def listarlotes(request):
    template = 'apontamento/listar_lotes.html'
    ini_prod = IntAPI()
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    listLotes  = json.loads(ini_prod.listar_producao(v_lista))
    return render(request, template, {'listLotes': listLotes})

def reglote(request):
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    v_lista.append(request.session['ctl_in_codigo'])
    v_logado = True
    if v_logado:
        litens = []
        litens_json = []
        litens_atrib = []
        var_a = []
        funcao = 'ordens/'
        d2 = {}
        app_itens = geturl_sqlite(funcao)
        payload = {'org_in_codigo': None,
                   'ord_in_codigo': v_lista[0],
                   'fil_in_codigo': v_lista[1]}
        c_appitens = requests.get(app_itens, params=payload).json()
        for r_appitens in c_appitens:
            d2 = r_appitens['PRO_ST_ITENS']
            v_lista.append(r_appitens['PRO_PAD_IN_CODIGO'])
            v_lista.append(r_appitens['TPO_ST_CODIGO'])
        try:
            lista = d2
            for itn in d2:
                #Busca atributos
                funcao = 'itensOrdens/'
                app_itensOrdens = geturl_sqlite(funcao)
                payload = {'pro_pad_in_codigo': itn['pro_pad_in_codigo'],
                           'pro_in_codigo': itn['pro_in_codigo'],
                           'rfc_in_codigo': itn['rfc_in_codigo']}
                c_appatribref = requests.get(app_itensOrdens, params=payload).json()
                for r_ref in c_appatribref:
                    d_ref = json.loads(r_ref['PRO_ST_REFERENCIA'])
                    d_atrib = json.loads(r_ref['PRO_ST_ATRIBUTOS'])
                    #print('Passou aqui', d_medidas['PRO_RE_COMPRIMENTO'])
                #Busca Medidas do Item
                if itn['rfc_in_codigo']!=0:
                    var_id = itn['pro_in_codigo']
                    var_nome = itn['pro_st_descricao']
                    litens_json.append(dict(parent_id=0, id=itn['pro_in_codigo'], name=itn['pro_st_descricao'], type='I', lista='N'))
                    litens.append((var_id, var_nome))
                    for obj_ref1 in d_ref:
                        if (itn['rfc_in_codigo'] == obj_ref1['rfc_in_codigo']):
                            if obj_ref1['rat_ch_tipo'] == 'L':
                                litens_json.append(
                                    dict(parent_id=itn['pro_in_codigo'], id=obj_ref1['ref_rat_value'], name=obj_ref1['rat_desc'], type=obj_ref1['rat_ch_tipo'], lista='N'))
                            else:
                                litens_json.append(
                                    dict(parent_id=itn['pro_in_codigo'], id=obj_ref1['rat_in_codigo'], name=obj_ref1['rat_desc'], type=obj_ref1['rat_ch_tipo'], lista='N'))
                    for obj_ref1 in d_ref:
                        for obj_atr1 in d_atrib:
                            if obj_atr1['pai_rat_in_codigo'] == obj_ref1['rat_in_codigo']:
                                if not (obj_atr1['rat_in_codigo'] in var_a):
                                    var_a.append(obj_atr1['rat_in_codigo'])
                                    litens_atrib.append(dict(parent_id=obj_ref1['rat_in_codigo'],id=obj_atr1['rat_value'], name=obj_atr1['rat_st_descricao'], type=obj_atr1['rat_ch_tipo'],
                                                        lista='S'))
                else:
                    var_id = itn['pro_in_codigo']
                    var_nome = itn['pro_st_descricao']
                    litens.append((var_id, var_nome))
                    litens_json.append(dict(parent_id=0, id=itn['pro_in_codigo'], name=itn['pro_st_descricao'], type='I', lista='N'))
                    litens_atrib.append(dict(parent_id=None,id=None, name=None, type=None, lista='S'))
            dict_litens ={}
            dict_litens= json.dumps(litens_json)

            dict_atrib ={}
            dict_atrib = json.dumps(litens_atrib)
            template = 'apontamento/reglote.html'
            if request.method == 'POST':
                lote_form = RegLotForm(data=request.POST)
                #try:
                if lote_form.is_valid():
                    #print('valido')
                    clote = lote_form.cleaned_data
                    v_dlotes= []
                    v_med= []
                    v_quantidade = lote_form.cleaned_data['orl_re_qtdlote']
                    v_item = lote_form.cleaned_data['pro_in_codigo']
                    v_referencia = lote_form.cleaned_data['orl_st_referencia']
                    v_referenciaDesc = formatar_caracteristicas(v_referencia,dict_atrib)
                    #Tipo de Ordens
                    v_med.append(v_lista[4])
                    funcao = 'itensOrdens/'
                    app_url = geturl_sqlite(funcao)
                    payload = {'pro_pad_in_codigo': v_lista[3],
                                'pro_in_codigo': v_item}
                    cr_itens = requests.get(app_url, params=payload).json()
                    for rs_itens in cr_itens:
                        d_medidas = json.loads(rs_itens['PRO_ST_MEDIDAS'])
                    if d_medidas:
                        for rs_med in d_medidas:
                            if rs_med['PRO_RE_COMPRIMENTO'] is None:
                                v_med.append(0)
                            else:
                                v_med.append(rs_med['PRO_RE_COMPRIMENTO'])
                            if rs_med['PRO_RE_LARGURA'] is None:
                                v_med.append(0)
                            else:
                                v_med.append(rs_med['PRO_RE_LARGURA'])
                            if rs_med['PRO_RE_ESPESSURA'] is None:
                                v_med.append(0)
                            else:
                                v_med.append(rs_med['PRO_RE_ESPESSURA'])
                    else:
                        v_med.append(0)
                        v_med.append(0)
                        v_med.append(0)
                    #print(v_quantidade)
                    v_med.append(v_quantidade)
                    v_qtdeconv = converter_unidade(v_med)
                    v_obs = ''
                    v_doc_origem = ''
                    v_usu_in_codigo = 1
                    v_apt = 1
                    v_destino = ''
                    mov_status = 'A'
                    v_desc = ''
                    v_un   = ''
                    v_madeira = ''
                    for r_desc in lista:
                        if (r_desc['pro_in_codigo'] == v_item):
                            v_desc = r_desc['pro_st_descricao']
                            v_un = r_desc['uni_st_unidade']
                            v_madeira = r_desc['pro_st_madeira']
                    v_dlotes.append(v_apt)
                    v_dlotes.append(v_quantidade)
                    v_dlotes.append(v_qtdeconv)
                    v_dlotes.append(v_item)
                    v_dlotes.append(v_obs)
                    v_dlotes.append(v_doc_origem)
                    v_dlotes.append(v_referencia)
                    v_dlotes.append(v_usu_in_codigo)
                    v_dlotes.append(v_destino)
                    v_dlotes.append(mov_status)
                    v_iniseq = IntAPI_sqlite(v_lista)
                    c_seqmov = v_iniseq.seq_movprod_sqlite()
                    row_now = timezone.now()
                    #monta o lote;
                    str_seq = str(c_seqmov)
                    str_now = row_now.strftime('%Y-%m-%d')
                    str_eti = row_now.strftime('%d/%m/%Y')
                    str_ano = row_now.strftime('%Y')
                    str_sem = row_now.strftime('%U')
                    str_dia = row_now.strftime('%d')
                    str_doc = str(v_lista[0])
                    str_sem = str(str_sem.zfill(2))
                    str_dia = str(str_dia.zfill(2))
                    str_seq = str(str_seq.zfill(6))
                    str_doc = str(str_doc.zfill(8))
                    str_lote = str_ano+str_sem+str_dia+str_doc+str_seq
                    #imprimir etiqueta
                    v_listEti = []
                    # trata a descrição do item
                    #txt = "Guaiuvira Pré-Cortada 13,5x146x1200mm  Mult. Legnetto"
                    if len(v_desc) < 40:
                        string1 = v_desc
                        string2 = ''
                    else:
                        v_sep = ' '
                        #busca o primeiro indice da string
                        v_idx = v_desc[1:40].rfind(v_sep)
                        string1 = v_desc[0:v_idx+1]
                        string2 = v_desc[v_idx+2:]
                    v_listEti.append(dict(ordem = v_lista[0],
                    descr1 = string1,
                    descr2 = string2,
                    un = v_un,
                    codbar = str_lote,
                    umidade = '',
                    qtde = v_dlotes[2],
                    destino = '',
                    lote = str_lote,
                    data = str_eti,
                    grupo = '',
                    comprimento = v_med[1],
                    largura = v_med[2],
                    seqlote = str_seq,
                    madeira = v_madeira,
                    maquina = '',
                    espessura =v_med[3]))
                    #print('apontamento Views 575',v_listEti)
                    json_eti= {}
                    json_eti = json.dumps(v_listEti)
                    funcao = 'apontamentos/'
                    api_producao = geturl_sqlite(funcao)
                    dados = data = {"FIL_IN_CODIGO": v_lista[1],
                                    "APT_IN_SEQUENCIA": c_seqmov,
                                    "APT_DT_APONTAMENTO": str_now,
                                    "APT_CH_STATUS": mov_status,
                                    "ORD_IN_CODIGO": v_lista[0],
                                    "PRO_IN_CODIGO": v_dlotes[3],
                                    "ORL_RE_QTDLOTE": v_dlotes[2],
                                    "ORL_ST_REFERENCIA": v_dlotes[6],
                                    "CTL_IN_CODIGO" : v_lista[2],
                                    "PRO_ST_DESCRICAO" : v_desc,
                                    "PRO_ST_LOTE":str(str_lote),
                                    "PRO_ST_SEQUENCIAL": str_seq,
                                    "PRO_ST_ETIQUETA": json_eti,
                                    "RFC_ST_DESCRICAO":v_referenciaDesc,
                                    "PRO_RE_QTDREFUGO":0}
                    #print('DADOS',dados)
                    response = requests.post(api_producao, data=dados)
                    #obj_itens.apt_inserirlote(v_dlotes)
                    c_etiqueta = gera_etiqueta()
                    try:
                        c_etiqueta.etiqueta_pre(json_eti)
                    except:
                        pass
                    #guarda o ultimo apontamento na sessão
                    request.session['apt_in_sequencia'] = c_seqmov
                    return redirect('listarlotes_sqllite')
                else:
                    print ('Invalid')
                #except:
                    #return redirect('listarlotes_sqllite')
            else:
                lote_form = RegLotForm()
            return render(request, template, {'lote_form': lote_form,
                                              'lista3': dict_litens,
                                              'lista': lista,
                                              'lista4': dict_atrib,
                                              'ord_in_codigo': v_lista[0],
                                              'fil_in_codigo': v_lista[1]
                                              })
        except:
            pass
    else:
        tmpl = "apontamento/iniciar.html"
        return render(request, tmpl)

def manutencao(request):
    tmpl = "apontamento/manutencao.html"
    if request.method == "POST":
        pass
    else:
         if 'action' in request.GET:
            action = request.GET.get('action')
            if action == 'atividade':
                funcao = 'itensOrdens/'
                api_atividade = geturl_sqlite(funcao)
                payload = {'pro_in': None}
                c_atividade = requests.get(api_atividade, params=payload).json()
                for c_a in c_atividade:
                    pass
                    #print(c_a['PRO_ST_REFERENCIA'])
            if action == 'integrarProducao':
                #busca Ordens Pendentes
                funcao = 'controleApt/'
                fil_in = request.session['fil_in_codigo']
                ord_in = request.session['ord_in_codigo']
                get_urlprod = geturl_producao(funcao)
                payload = {'fil_in_codigo': fil_in,'status': 'A', 'ord_in_codigo':ord_in}
                try:
                    #Busca os apontamentos em aberto
                    c_rs = requests.get(get_urlprod, params=payload).json()
                    for rs in c_rs:
                        v_dtapontamento = trata_data_sqlite(rs['CTL_DT_LOGIN'])
                        str_now = v_dtapontamento.strftime('%Y-%m-%d')
                        #Busca ordens pendentes de integração;
                        funcao = 'apontamentos/'
                        get_urlapp = geturlapp(funcao)
                        payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
                        try:
                            v_ordens = requests.get(get_urlapp, params=payload).json()
                            #print(v_ordens)
                            for r_ord in v_ordens:
                                #print(r_ord)
                                v_dadosProd = {'fil_in_codigo': r_ord['FIL_IN_CODIGO'],
                                               'ord_in_codigo': r_ord['ORD_IN_CODIGO'],
                                               'ctl_in_codigo': r_ord['CTL_IN_CODIGO'],
                                               'apt_dt_inclusao': str_now,
                                               'mvp_in_sequencia': r_ord['APT_IN_SEQUENCIA'],
                                               'apt_re_quantidade': r_ord['ORL_RE_QTDLOTE'],
                                               'apt_re_qtdeconvertida': r_ord['ORL_RE_QTDLOTE'],
                                               'apt_re_qtderefugo': r_ord['PRO_RE_QTDREFUGO'],
                                               'pro_in_codigo': r_ord['PRO_IN_CODIGO'],
                                               'pro_st_obs': 'Lote integrado pelo ACB',
                                               'pro_st_docorigem': r_ord['ORD_IN_CODIGO'],
                                               'pro_st_referencia': r_ord['ORL_ST_REFERENCIA'],
                                               'usu_in_codigo': 1,
                                               'pro_st_destino': 'I',
                                               'pro_st_lote': r_ord['PRO_ST_LOTE'],
                                               'pro_st_conversor': '0',
                                               'apt_dt_lote': r_ord['APT_DT_APONTAMENTO']
                                               }
                                funcao = 'post_producao/'
                                get_urlapi = geturlapi(funcao)
                                try:
                                    # Grava os dados no Mega
                                    resp_Prod = requests.post(get_urlapi, data=v_dadosProd).json()
                                    for rs_prod in resp_Prod:
                                        if (rs_prod['mensagem'] == 'Ok') and (rs_prod['mensagem_sub'] == 'Ok'):
                                            #faz Update da transação da ordem;
                                            funcao = 'apontamentos/'
                                            get_urlapp = geturlapp(funcao)
                                            payload = {'ctl_in_codigo': r_ord['CTL_IN_CODIGO'],'sequencia': r_ord['APT_IN_SEQUENCIA'],'status': 'I'}
                                            #c_update_prod = requests.put(get_urlapp, params=payload)
                                except:
                                    pass
                        except:
                            pass
                        #busca demandas pendentes de integração para a ordem.
                        funcao = 'demandas/'
                        get_urlapp = geturlapp(funcao)
                        payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
                        try:
                            v_demanda = requests.get(get_urlapp, params=payload).json()
                            for r_dem in v_demanda:
                                v_dadosDem = {'fil_in_codigo': r_dem['FIL_IN_CODIGO'],
                                              'ord_in_codigo': r_dem['ORD_IN_CODIGO'],
                                              'ctl_in_codigo': r_dem['CTL_IN_CODIGO'],
                                              'apt_dt_inclusao': str_now,
                                              'mvd_in_sequencia': r_dem['MOV_IN_SEQUENCIA'],
                                              'pro_st_lote': r_dem['PRO_ST_LOTE'],
                                              'pro_re_qtdlote': r_dem['PRO_RE_QTDLOTE']}
                                funcao = 'post_demanda/'
                                get_urlapi = geturlapi(funcao)
                                try:
                                    # Grava os dados no Mega
                                    resp_Dem = requests.post(get_urlapi, data=v_dadosDem).json()
                                    for rs_dem in resp_Dem:
                                        if rs_dem['mensagem'] == 'Ok':
                                            #faz Update da transação de demanda;
                                            funcao = 'demandas/'
                                            get_urlapp = geturlapp(funcao)
                                            payload = {'ctl_in_codigo': r_dem['CTL_IN_CODIGO'],'sequencia': r_dem['MOV_IN_SEQUENCIA'],'status': 'I', 'item': rs_dem['item']}
                                            #c_update_dem = requests.put(get_urlapp, params=payload)
                                except:
                                    pass
                        except:
                            pass
                    #faz Update da transação;
                    payload = {'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'E'}
                    #c_update = requests.put(get_urlprod, params=payload)
                except:
                    pass
            if action == 'get_ordens':
                #baixar ordens pendentes de integração
                funcao = 'GetOrdensPendentes/'
                try:
                    api_ordenspendentes = geturl_api_sqlite(funcao)
                    payload = {'org_in_codigo': 2}
                    vresponse = requests.get(api_ordenspendentes, params=payload).json()
                    #Se encontrar ordem pendente segue continua;
                    if vresponse:
                        for ord in vresponse:
                            #busca dados das Ordens
                            funcao = 'GetManProOrdens/'
                            try:
                                api_getordens = geturl_api_sqlite(funcao)
                                payload = {'org_in_codigo': ord['org_in_codigo'],
                                           'ord_seq_in_codigo': ord['ord_seq_in_codigo'],
                                           'ord_in_codigo': ord['ord_in_codigo']}
                                c_getordens = requests.get(api_getordens, params=payload).json()
                                #Se encontrar a ordem segue adiante;
                                if c_getordens:
                                    for d_ord in c_getordens:
                                        v_itn = False
                                        v_dem = False
                                        #Busca Itens da Ordem
                                        funcao = 'itensordem/'
                                        uri = geturl_api_sqlite(funcao)
                                        payload_itens = {'ordem': d_ord['ORD_IN_CODIGO'],'filial': d_ord['FIL_IN_CODIGO']}
                                        c_get_itens = requests.get(uri, params=payload_itens).json()
                                        funcao = 'get_demandaordens/'
                                        uri = geturl_api_sqlite(funcao)
                                        c_get_demandas = requests.get(uri, params=payload).json()
                                        if c_get_itens:
                                            v_itn = True
                                        v_dados = data = {'ORG_TAB_IN_CODIGO':d_ord['ORG_TAB_IN_CODIGO'],
                                                          'ORG_PAD_IN_CODIGO':d_ord['ORG_PAD_IN_CODIGO'],
                                                          'ORG_IN_CODIGO':d_ord['ORG_IN_CODIGO'],
                                                          'ORG_TAU_ST_CODIGO':d_ord['ORG_TAU_ST_CODIGO'],
                                                          'ORD_TAB_IN_CODIGO':d_ord['ORD_TAB_IN_CODIGO'],
                                                          'ORD_SEQ_IN_CODIGO':d_ord['ORD_SEQ_IN_CODIGO'],
                                                          'ORD_IN_CODIGO':d_ord['ORD_IN_CODIGO'],
                                                          'PRO_TAB_IN_CODIGO':d_ord['PRO_TAB_IN_CODIGO'],
                                                          'PRO_PAD_IN_CODIGO':d_ord['PRO_PAD_IN_CODIGO'],
                                                          'PRO_IN_CODIGO':d_ord['PRO_IN_CODIGO'],
                                                          'ORD_RE_QTDE_ORDEM':d_ord['ORD_RE_QTDE_ORDEM'],
                                                          'FIL_IN_CODIGO':d_ord['FIL_IN_CODIGO'],
                                                          'TPO_ST_CODIGO':d_ord['TPO_ST_CODIGO_TIPO'],
                                                          'PRO_ST_ITENS':json.dumps(c_get_itens),
                                                          'PRO_ST_DEMANDAS':json.dumps(c_get_demandas)}
                                        #grava na tabela local => api => models.py man_pro_ordens
                                        funcao = 'ordens/'
                                        #print(v_dados)
                                        dadosOrdens = geturl_sqlite(funcao)
                                        #Apaga as ordens
                                        c_apagaordem = requests.put(dadosOrdens, params=payload)
                                        c_response = requests.post(dadosOrdens, data=v_dados)
                                        # faz update nas ordens atualizadas;
                                        v_lista_ordens = []
                                        v_lista_ordens.append(d_ord['ORG_IN_CODIGO'])
                                        v_lista_ordens.append(d_ord['ORD_SEQ_IN_CODIGO'])
                                        v_lista_ordens.append(d_ord['ORD_IN_CODIGO'])
                                        v_update_ordem = data = {'ORG_IN_CODIGO': d_ord['ORG_IN_CODIGO'],
                                                                 'ORD_SEQ_IN_CODIGO': d_ord['ORD_SEQ_IN_CODIGO'],
                                                                 'ORD_IN_CODIGO': d_ord['ORD_IN_CODIGO']}
                                        funcao = 'GetOrdensPendentes/'
                                        api_ordenspendentes = geturl_api_sqlite(funcao)
                                        do_response = requests.put(api_ordenspendentes, data=v_update_ordem)
                                        #Busca Itens da ordem
                                        if c_get_itens:
                                            for d_itens in c_get_itens:
                                                #verifica se existe o item cadastrado
                                                funcao = 'itensOrdens/'
                                                app_itens = geturl_sqlite(funcao)
                                                payload = {'pro_pad_in_codigo': d_itens['pro_pad_in_codigo'],
                                                           'pro_in_codigo': d_itens['pro_in_codigo'],
                                                           'rfc_in_codigo':d_itens['rfc_in_codigo']}
                                                c_appitens = requests.get(app_itens, params=payload).json()
                                                pro_medidas = []
                                                pro_medidas.append(dict(PRO_RE_COMPRIMENTO = d_itens['pro_re_comprimento'],
                                                                        PRO_RE_LARGURA = d_itens['pro_re_largura'],
                                                                        PRO_RE_ESPESSURA = d_itens['pro_re_espessura']
                                                                       ))
                                                if d_itens['rfc_in_codigo']!=0:
                                                    #Busca atributos dos Itens
                                                    funcao = 'listaatributos/'
                                                    uri = geturl_api_sqlite(funcao)
                                                    payload = {'item': d_itens['pro_in_codigo'],'filial': d_ord['FIL_IN_CODIGO']}
                                                    c_get_atrib = requests.get(uri, params=payload).json()
                                                    #Busca Características dos Itens
                                                    funcao = 'listareferencias/'
                                                    uri = geturl_api_sqlite(funcao)
                                                    payload = {'item': d_itens['pro_in_codigo'],'filial': d_ord['FIL_IN_CODIGO']}
                                                    c_get_ref = requests.get(uri, params=payload).json()
                                                    #grava itens na tabela
                                                    v_dados_produtos = data = {'PRO_TAB_IN_CODIGO': d_ord['PRO_TAB_IN_CODIGO'],
                                                                               'PRO_PAD_IN_CODIGO': d_ord['PRO_PAD_IN_CODIGO'],
                                                                               'PRO_IN_CODIGO': d_itens['pro_in_codigo'],
                                                                               'PRO_ST_DESCRICAO': d_itens['pro_st_descricao'],
                                                                               'UNI_ST_UNIDADE': d_itens['uni_st_unidade'],
                                                                               'RFC_IN_CODIGO': d_itens['rfc_in_codigo'],
                                                                               'PRO_ST_ATRIBUTOS': json.dumps(c_get_atrib),
                                                                               'PRO_ST_REFERENCIA': json.dumps(c_get_ref),
                                                                               'PRO_ST_MEDIDAS': json.dumps(pro_medidas)
                                                                               }
                                                else:
                                                    lista_atrb = []
                                                    lista_atrb.append(dict(PRO_ST_ATRIBUTOS = None,))
                                                    lista_ref = []
                                                    lista_ref.append(dict(PRO_ST_REFERENCIA = None,))
                                                    v_dados_produtos = data = {'PRO_TAB_IN_CODIGO': d_ord['PRO_TAB_IN_CODIGO'],
                                                                               'PRO_PAD_IN_CODIGO': d_ord['PRO_PAD_IN_CODIGO'],
                                                                               'PRO_IN_CODIGO': d_itens['pro_in_codigo'],
                                                                               'PRO_ST_DESCRICAO': d_itens['pro_st_descricao'],
                                                                               'UNI_ST_UNIDADE': d_itens['uni_st_unidade'],
                                                                               'RFC_IN_CODIGO': d_itens['rfc_in_codigo'],
                                                                               'PRO_ST_ATRIBUTOS': json.dumps(lista_atrb),
                                                                               'PRO_ST_REFERENCIA': json.dumps(lista_ref),
                                                                               'PRO_ST_MEDIDAS': json.dumps(pro_medidas)
                                                                               }
                                                #verifica se existe o item cadastrado
                                                funcao = 'itensOrdens/'
                                                app_itens = geturl_sqlite(funcao)
                                                payload = {'pro_pad_in_codigo': d_itens['pro_pad_in_codigo'],
                                                           'pro_in_codigo': d_itens['pro_in_codigo'],
                                                           'rfc_in_codigo':d_itens['rfc_in_codigo']}
                                                c_appitens = requests.get(app_itens, params=payload).json()
                                                if not c_appitens:
                                                    funcao = 'itensOrdens/'
                                                    uri = geturl_sqlite(funcao)
                                                    respio = requests.post(uri, data=v_dados_produtos)
                            except:
                                pass
                except:
                    pass

    return render(request, tmpl)
def grafico(request):
    template = "apontamento/highcharts/charts.html"
    return render(request, template)
def grafico2(request):
    template = "apontamento/highcharts/example2.html"
    return render(request, template)

def grafico3(request):
    template = "apontamento/highcharts/example3.html"
    return render(request, template)

def etiqueta(request):
    template = "apontamento/etiqueta.html"
    return render(request, template)

class ApontaControleListView(APIView):
    serializer_class = ApontaControleSerializer
    def get(self, request, format=None):
        status = request.GET.get('status')
        ordem = request.GET.get('ord_in_codigo')
        filial = request.GET.get('fil_in_codigo')
        if ordem is not None:            
            serializer = self.serializer_class(Apt_Controle.objects.filter(CTL_ST_STATUS = status, ORD_IN_CODIGO = ordem, FIL_IN_CODIGO = filial), many=True)
        elif status == None:        
            serializer = self.serializer_class(Apt_Controle.objects.all(), many=True)
        else:
            serializer = self.serializer_class(Apt_Controle.objects.filter(CTL_ST_STATUS = status), many=True)
        return Response(serializer.data)    
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_transacao= request.GET.get('ctl_in_codigo')
        status = request.GET.get('status')
        serializer = Apt_Controle.objects.get(CTL_IN_CODIGO = v_transacao)
        #Verificar o status do apontamento;
        if serializer.CTL_DT_LOGOUT is not None:
            serializer.CTL_ST_STATUS =  status
            serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)        
