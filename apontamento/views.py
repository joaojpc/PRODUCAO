# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
#import socket
#from django.contrib.auth.decorators import login_required#
import socket
import os

from django.http import Http404, HttpResponse
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
from secretstorage import item

#from apontamento.custom_views import Listar_opcoes, User_logado, Login_inicial, IntProd
from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite
from url_projeto import geturlapp, geturlapi, geturlprod, geturlest
from apontamento.api_view import IntAPI, trata_data_sqlite, IntOrdens, monta_produto, monta_ordem, get_client_ip, formatar_caracteristicas,prep_producao, Login_inicial_sqlite, IntAPI_sqlite, formatar_ordem, Controle

from apontamento.forms import FormUser, RegOcorForm, DemForm, RegLotForm, FormUser_sqlite, FormLogin, DemFormLocal, ListLotForm, LotesReceb, TrocarImpressora
from apontamento.formata_string import formatar_string
from apontamento.Etiqueta_precorte import gera_etiqueta

from .serializer import *
from .models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from rest_framework import status
from producao import settings

from datetime import datetime, date, timedelta
register = template.Library()

def converter_unidade(pParams):
    if pParams[0] == 'OP003':
        v_qtdeConv = pParams[4]
        if pParams[2] > 0:
            v_qtdeConv = round(pParams[4]*(pParams[2]/1000),3)
        else:
            v_qtdeConv = pParams[4]
    else:
        v_qtdeConv = pParams[4]
    return v_qtdeConv

def controledemanda(request):
    v_session = carrega_sessao(request)
    if 'ord_in_codigo' in request.session:        
        tmpl = "apontamento/controle_demanda.html",
        ord_in_codigo = request.session['ord_in_codigo']
        return render(request, tmpl,{'ord_in_codigo':ord_in_codigo})
    else:
        return redirect('demos_sessions')

def carrega_sessao(request):
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
    else:
        seq_in_operacao = None
    if 'usu_st_nome' in request.session:
        usu_st_nome = request.session['usu_st_nome']
    else:
        usu_st_nome = None
    if 'ctl_in_codigo' in request.session:
        ctl_in_codigo = request.session['ctl_in_codigo']
    else:
        ctl_in_codigo = None
    if 'cliente' in request.session:
        cliente = request.session['cliente']
    else:
        cliente = None
    if 'origem' in request.session:
        origem = request.session['origem']
    else:
        origem = None
    if 'fornecedor' in request.session:
        fornecedor = request.session['fornecedor']
    else:
        fornecedor = None
    if 'pro_st_descricao' in request.session:
        pro_st_descricao = request.session['pro_st_descricao'] 
    else:
        pro_st_descricao = None
    vreturn = {'ordem': ordem,'usuario': usuario, 'ord_in_codigo':ord_in_codigo,'fil_in_codigo':fil_in_codigo,
               'seq_in_operacao':seq_in_operacao,'usu_st_nome':usu_st_nome,'ctl_in_codigo':ctl_in_codigo,
               'cliente':cliente, 'fornecedor':fornecedor,'origem':origem, 'pro_st_descricao':pro_st_descricao}
    return vreturn    

def session_demo(request):
    v_logado = False
    v_session = carrega_sessao(request);
    ordem = v_session.get('ordem')
    usuario = v_session.get('usuario')
    ord_in_codigo = v_session.get('ord_in_codigo')
    fil_in_codigo = v_session.get('fil_in_codigo')
    seq_in_operacao = v_session.get('seq_in_operacao')
    usu_st_nome = v_session.get('usu_st_nome')
    ctl_in_codigo = v_session.get('ctl_in_codigo')
    cliente = v_session.get('cliente')  
    pro_st_descricao = v_session.get('pro_st_descricao')
    template = "apontamento/session.html",
    if not(request.session.has_key('ordem')):
        request.session.flush()
    form = FormLogin()
    if request.method == "GET":
        cliente = get_client_ip(request)
        if 'action' in request.GET:            
            #print(cliente)
            action = request.GET.get('action')
            if not(request.session.has_key('ordem')):
                request.session.flush()
                return redirect('demos_sessions')
            elif action == 'logout':
                #fazer integração dos apontamentos em aberto;                
                v_lista = []
                v_lista.append(fil_in_codigo)
                v_lista.append(ord_in_codigo)
                v_lista.append(seq_in_operacao)
                integrarProducao(v_lista)                
                #Fazer update na tabela de controle;
                if request.session.has_key('ordem'):
                    encerrar = Login_inicial_sqlite(ordem,usuario,cliente)
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
            cliente = get_client_ip(request)
            ordem = form.cleaned_data['ordem']
            usuario = form.cleaned_data['usuario']
            #Formata os dados do código de barras da ordem;
            r_ordem = json.loads(formatar_ordem(ordem))
            for v_ord in r_ordem:
                ord_in_codigo = v_ord['ordem']
                fil_in_codigo = v_ord['filial']
                seq_in_operacao = v_ord['operacao']
            iniciar = Login_inicial_sqlite(ordem,usuario,cliente)
            usuarios = json.loads(iniciar.apt_usuario_sqlite())
            for usu in usuarios:
                usu_st_nome = usu['opd_st_descricao']
                opd_in_codigo = usu['opd_in_codigo']
            if ordem is not None:
                #Define o controle de sessão
                request.session['ordem'] = ordem
                request.session['usuario'] = usuario
                request.session['ord_in_codigo'] = ord_in_codigo
                request.session['fil_in_codigo'] = fil_in_codigo
                request.session['seq_in_operacao'] = seq_in_operacao
                request.session['usu_st_nome'] = usu_st_nome
                request.session['cliente'] = cliente
                request.session['pro_st_descricao'] = pro_st_descricao
                #Verificar se o usuário já tem apontamento aberto para a ordem;
                cr_ini = json.loads(iniciar.userLogado_sqlite())
                for rs_ini in cr_ini:
                    v_logado = rs_ini['logado']
                    ctl_in_codigo = rs_ini['ctl_in_codigo']
                    pro_st_descricao = rs_ini['pro_st_descricao']
                if v_logado:
                    request.session['ctl_in_codigo'] = ctl_in_codigo
                    request.session['pro_st_descricao'] = pro_st_descricao
                else:
                    #if not(v_logado):
                    #criar novo apontamento para a ordem;
                    cr_ini = json.loads(iniciar.conectar_sqlite())
                    for rs_ini2 in cr_ini:
                        #print(rs_ini2)
                        if rs_ini2['logado']:
                            ctl_in_codigo = rs_ini2['ctl_in_codigo']
                            request.session['ctl_in_codigo'] = ctl_in_codigo
                            request.session['pro_st_descricao'] = pro_st_descricao
                funcao = 'ordens/'
                url = geturlapp(funcao)
                payload = {'fil_in_codigo': fil_in_codigo,'ord_in_codigo': ord_in_codigo}
                c_ordem = requests.get(url, params=payload).json()
                #f.write(str(c_ordem))                
                if not (c_ordem):
                    v_listOrd = []
                    v_listOrd.append(None)
                    v_listOrd.append(fil_in_codigo)
                    v_listOrd.append(ord_in_codigo)
                    v_listOrd.append('N')
                    ini = IntOrdens()
                    ini.buscaOrdens(v_listOrd)                
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
                                      'cliente':cliente,
                                      'controle':ctl_in_codigo,
                                      })
# Create your views here.
def home(request):
    v_session = carrega_sessao(request)
    template = "apontamento/home.html"
    return render(request, template)
def principal(request):
    v_session = carrega_sessao(request)
    filial = v_session.get('fil_in_codigo')
    if 'ordem' in request.session:        
        v_logado = True
        if v_logado:
            if filial == 3:
                tmpl = "apontamento/principal.html"
            elif filial == 312:
                tmpl = "apontamento/principal_zk.html"
            else:
                tmpl = "apontamento/principal.html"            
            if request.method == "POST":
                pass
            else:
                pass
            return render(request, tmpl)
        else:
            tmpl = "apontamento/home.html"
            return render(request, tmpl)
    else:
        request.session.flush()
        return redirect('demos_sessions')
        
def consulta(request):
    v_session = carrega_sessao(request)
    v_logado = True
    if v_logado:
        tmpl = "apontamento/consultas.html"
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

def testar_impressao(request):
    v_session = carrega_sessao(request)
    template= 'apontamento/impressao.html'
    form = ListLotForm()
    if 'apt_in_sequencia' in request.session:
        apt_in_sequencia = request.session['apt_in_sequencia']
    else:
        apt_in_sequencia = None
    if request.method == "POST":
        funcao = 'apontamentos/'
        api_listalotes = geturlapp(funcao)
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
                    #c_etiqueta = gera_etiqueta()
                    #c_etiqueta.etiqueta_pre(json.dumps(c_lote))
                    c_etiqueta = gera_etiqueta(json.dumps(c_lote))                    
        except:
            pass
        return redirect('listarlotes_sqllite')
    else:
        print('GET')
    return render(request, template, {'form': form,'apt_in_sequencia':apt_in_sequencia})

def loginControl_sqlite(request):
    v_session = carrega_sessao(request)
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
    v_session = carrega_sessao(request)
    template = "apontamento/listar_ocorrencias.html"
    v_ini = Listar_opcoes_sqlite();
    c_ini = json.loads(v_ini.lis_controle_sqlite())
    for v_cur in c_ini:
        v_equipamento = v_cur['ord_in_codigo']
    ini_prod = IntAPI();    
    form = json.loads(ini_prod.reg_ocorencias())    
    return render(request, template,{'form': form})

def insOcorrencia(request):
    v_session = carrega_sessao(request)
    template = 'apontamento/nova_ocorrencia.html'
    ini_prod = IntAPI()
    lista = ini_prod.listar_ocorencias()
    if request.method == "POST":
        form = RegOcorForm(request.POST)
        if form.is_valid():
            funcao = 'ocorrencias'
            api_ocorrencia = geturlapp(funcao)
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
    v_session = carrega_sessao(request)
    template = 'apontamento/demandas.html'
    ini_prod = IntAPI();
    c_demanda  = json.loads(ini_prod.empenho_demanda())
    return render(request, template, {'dem': c_demanda})

def baixaDemandaLocal(request):
    template = 'apontamento/demandalocal.html'
    v_session = carrega_sessao(request)
    v_ordem = v_session.get('ord_in_codigo')
    v_filial = v_session.get('fil_in_codigo')
    if 'ord_in_codigo' in request.session:
        ini_prod = IntAPI(v_session)
        req = {'ordem': v_ordem,'filial': v_filial}
        listLotes  = ini_prod.listar_demanda(req)
        return render(request, template, {'dem': listLotes})
    else:
        return redirect('demos_sessions')

# processo vinculado a api_view
def insDemandas(request):
    """ A view of all bands. """
    v_session = carrega_sessao(request)
    template = 'apontamento/novademanda.html'
    ini_prod = IntAPI()
    #c_demanda = json.loads(ini_prod.ord_demandas())
    c_demanda = json.loads(ini_prod.ordem_demandas())
    if request.method == "POST":
        form = DemForm(request.POST)
        if form.is_valid():
            l_demandas = []
            funcao = 'demandas/'            
            api_demandas = geturlapp(funcao)
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
            return redirect('insDemandaslocal')
        #else:
            #print 'Inválido'
    else:
        form = DemForm()
    var_get_search = request.GET.get('search_box')
    if var_get_search is not None:
        c_demanda = c_demanda.filter(name__icontains=var_get_search)
    return render(request, template, {'form': form, 'dem': c_demanda})



def insDemandaslocal(request):
    v_session = carrega_sessao(request)
    l_demandas = []
    v_filial = request.session['fil_in_codigo']
    v_ordem = request.session['ord_in_codigo']
    l_demandas.append(v_ordem)
    l_demandas.append(v_filial)
    l_demandas.append(request.session['ctl_in_codigo'])
    template = 'apontamento/novademandalocal.html'
    funcao = 'demandas/'
    api_demandas = geturlapp(funcao)
    if request.method == "POST":
        form = DemFormLocal(request.POST)
        if form.is_valid():
            #print('linha 482 Valido')
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
                #Busca id da máquina e da ordem
                funcao = 'controleApt/'
                url = geturlprod(funcao)
                payload = {'ord_in_codigo': l_demandas[0],'fil_in_codigo': l_demandas[1],'status': 'A'}
                #print(payload)
                c_rs = requests.get(url, params=payload).json()                
                for rs in c_rs:
                    l_demandas.append(rs['ORD_ST_ID'])
                    l_demandas.append(rs['CMAQ_ST_ID'])
                dados = {'FIL_IN_CODIGO': l_demandas[1],
                         'MOV_IN_SEQUENCIA': l_demandas[7],
                         'MOV_DT_INCLUSAO': l_demandas[6],
                         'PRO_IN_CODIGO': '',
                         'ORD_IN_CODIGO': l_demandas[0],
                         'PRO_RE_QTDLOTE': l_demandas[4],
                         'PRO_ST_LOTE': l_demandas[3],
                         'MOV_ST_STATUS': l_demandas[5],
                         'CTL_IN_CODIGO': l_demandas[2],
                         'ORD_ST_ID': l_demandas[8],
                         'CMAQ_ST_ID': l_demandas[9]}
                #print(dados)
                response = requests.post(api_demandas, data=dados)
                #print(requests.post)
            return redirect('insDemandaslocal')
        #else:
            #print 'Inválido'
    else:
        form = DemFormLocal()
    return render(request, template, {'form': form,'fil_in_codigo': v_filial,'ord_in_codigo': v_ordem})

def listarlotes_sqllite(request):
    v_session = carrega_sessao(request)
    if 'ord_in_codigo' in request.session:
        template = 'apontamento/listar_lotes.html'
        v_lista = []
        v_lista.append(request.session['ord_in_codigo'])
        v_lista.append(request.session['fil_in_codigo'])
        funcao = 'apontamentos'
        api_listalotes = geturlapp(funcao)
        payload = {'ordem': v_lista[0],'filial': v_lista[1],}
        vresponse = requests.get(api_listalotes, params=payload)
        listLotes = json.loads(vresponse.content)
        return render(request, template,{'listLotes': listLotes})
    else:
        return redirect('demos_sessions')
        
def listarlotes(request):
    v_session = carrega_sessao(request)
    template = 'apontamento/listar_lotes.html'
    ini_prod = IntAPI()
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    listLotes  = json.loads(ini_prod.listar_producao(v_lista))
    return render(request, template, {'listLotes': listLotes})

def reglote(request):
    v_session = carrega_sessao(request)
    pro_st_descricao = v_session.get('pro_st_descricao')
    #print('Linha 569 - views.py - pro_st_descricao: {}'.format(pro_st_descricao))
    v_lista = []
    v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    v_lista.append(request.session['ctl_in_codigo'])
    v_lista.append(request.session['cliente'])
    try:
        v_lista.append(request.session['origem'])
    except:
        v_lista.append('')
    try:
        v_lista.append(request.session['fornecedor'])
    except:
        v_lista.append('')
    v_df = True
    v_logado = True
    lote_form = RegLotForm()
    v_form = {'lote_form': lote_form}
    if v_logado:
        v_prep = prep_producao()
        #valida situação da ordem para exibir ou não o formulário de registro de lote;
        '''situacao_ordem = v_prep.valida_situacao_ordem(v_session)
        for s_ordem in situacao_ordem:
            if s_ordem['situacao']!= 'AB':
                return redirect('menu')'''
        if pro_st_descricao is None:
            pay_item = {'ordem': v_lista[0],'filial': v_lista[1],'retorno': 'descricao'}
            pro_st_descricao = v_prep.get_dadosOrdem(pay_item)
            request.session['pro_st_descricao'] = pro_st_descricao
        dados= v_prep.prepara_apontamento(v_lista)
        dados.update(v_form)
        v_ordem = {'list_ordem':json.loads(dados['ordem'])}
        lista = {'lista':dados['lista']}
        v_ord_infoadic = {'ord_infoadic':dados['ord_infoadic']}
        v_printer = {'equipamento':dados['equipamento']}
        v_maquina = {'maquina':dados['maquina']}
        template = 'apontamento/reglote.html'
        if request.method == 'POST':
            lote_form = RegLotForm(data=request.POST)
            #try:
            if lote_form.is_valid():
                v_retorno = lote_form.cleaned_data
                #print(v_retorno)
                try:
                    lote_ori = v_retorno.get('pro_st_loteori', '')
                    request.session['origem'] = int(lote_ori[8:16]) if len(lote_ori) == 22 else lote_ori

                except:
                    pass
                try:
                    request.session['fornecedor'] = lote_form.cleaned_data['pro_st_fornecedor']
                except:
                    pass
                #print(request.session['origem'])
                #print(request.session['fornecedor'])
                if request.session.get('usuario') == '0000041873':
                    return redirect('incluir_lote')
                v_aponta = dict(ord_in_codigo = v_lista[0],
                                fil_in_codigo = v_lista[1],
                                v_quantidade = lote_form.cleaned_data['orl_re_qtdlote'],
                                v_item = lote_form.cleaned_data['pro_in_codigo'],
                                v_referencia = lote_form.cleaned_data['orl_st_referencia'],
                                v_refugo = lote_form.cleaned_data['orl_re_qtdrefugo'],
                                v_origem = lote_form.cleaned_data['pro_st_loteori'],
                                v_fornecedor = lote_form.cleaned_data['pro_st_fornecedor']
                                )
                v_aponta.update(v_ordem)
                v_aponta.update(lista)
                v_aponta.update(v_ord_infoadic)
                v_aponta.update(v_printer)
                v_aponta.update(v_maquina)
                #v_aponta.update(v_conv)
                v_sequencia = v_prep.incluir_apontamento(v_aponta)
                request.session['apt_in_sequencia'] = v_sequencia
                return redirect('incluir_lote')

            # AJUSTE 2026-06-24: Retorno para form inválido
            # Motivo: Quando clean() levanta ValidationError, is_valid()=False não tinha return
            # Resultava em None → Erro 500. Agora renderiza template com form.errors
            # Não altera regra de negócio. Apenas garante exibição do erro "Leitura Inválida"
            dados['lote_form'] = lote_form
            return render(request, template, dados)
        else:
            return render(request, template, dados)

def manutencao(request):
    v_session = carrega_sessao(request)
    funcao = None
    payload = None
    get_urlapi = None
    get_urlprod = None
    get_urlapp = None
    if 'ord_in_codigo' in request.session:
        tmpl = "apontamento/manutencao.html"
        if request.method == "POST":
            pass
        else:
            if 'action' in request.GET:
                action = request.GET.get('action')
                if action == 'atividade':
                    funcao = 'itensOrdens/'
                    api_atividade = geturlapp(funcao)
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
                    seq_in = request.session['seq_in_operacao']
                    v_lista = []
                    v_lista.append(fil_in)
                    v_lista.append(ord_in)
                    v_lista.append(seq_in)
                    integrarProducao(v_lista)
                    return redirect('menu')
                if action == 'get_ordens':
                    #baixar ordens pendentes de integração
                    fil_in = request.session['fil_in_codigo']
                    ord_in = request.session['ord_in_codigo']
                    v_lista = []
                    if fil_in == 3:
                        v_lista.append(2)
                    elif fil_in == 312:
                        v_lista.append(311)
                    elif fil_in == 302:
                        v_lista.append(301)
                    else:
                        v_lista.append(2)                    
                    v_lista.append(fil_in)
                    v_lista.append(ord_in)
                    v_lista.append('N')
                    ini = IntOrdens()
                    ini.buscaOrdens(v_lista)
                    return redirect('menu')
                if action == 'get_tipoordens':
                    fil_in = v_session.get('fil_in_codigo')
                    gettipoordens(request)
                    getconfigaponta(request)
                    return redirect('menu')
                if action == 'get_atribref':
                    fil_in = v_session.get('fil_in_codigo')
                    getatributoref(request)
                    return redirect('menu')
        return render(request, tmpl)
    else:
        return redirect('demos_sessions')
    
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

def apontamento(request):
    #Busca equipamento vinculado ao ip;
    v_session = carrega_sessao(request)
    host = v_session.get('cliente')
    filial = v_session.get('fil_in_codigo')
    maquina = None
    funcao = 'equipamento/'
    app_url = geturlprod(funcao)
    payload = {'cliente': host,'filial':filial}
    try:
        cr_printer = requests.get(app_url, params=payload).json()
        if cr_printer:
            for rs_printer in cr_printer:
                maquina = rs_printer['MAQ_IN_CODIGO']
    except:
        maquina = 0
    if host is None:
        maquina = 0
    #Busca a Máquina vinculada ao equipamento
    if maquina != 0:
        funcao = 'maquina/'
        app_url = geturlprod(funcao)
        payload = {'cmaq_id': maquina}
        try:
            cr_maquina = requests.get(app_url, params=payload).json()
            if cr_maquina:
                for rs_maquina in cr_maquina:
                    if rs_maquina['MAQ_CH_APONTAMENTO']:
                        return redirect('demos_sessions')
                    else:
                        return redirect('incluir_lote')
        except:
            return redirect('demos_sessions')
    else:
        return redirect('demos_sessions')

def demandas(request):
    #Busca equipamento vinculado ao ip;
    v_session = carrega_sessao(request)
    host = v_session.get('cliente')
    filial = v_session.get('fil_in_codigo')
    maquina = None
    funcao = 'equipamento/'
    app_url = geturlprod(funcao)
    payload = {'cliente': host,'filial':filial}    
    try:
        cr_printer = requests.get(app_url, params=payload).json()
        for rs_printer in cr_printer:
            maquina = rs_printer['MAQ_IN_CODIGO']
    except:
        maquina = 0
    if host is None:
        maquina = 0
    #Busca a Máquina vinculada ao equipamento
    if maquina != 0:
        funcao = 'maquina/'
        app_url = geturlprod(funcao)
        payload = {'cmaq_id': maquina}        
        try:
            cr_maquina = requests.get(app_url, params=payload).json()
            if cr_maquina:
                for rs_maquina in cr_maquina:
                    if rs_maquina['MAQ_CH_DEMANDA']:
                        return redirect('controledemanda')
                    else:
                        return redirect('insDemandaslocal')
        except:
            return redirect('controledemanda')
    else:
        return redirect('controledemanda')

class ApontaControleListView(APIView):
    serializer_class = ApontaControleSerializer
    def get(self, request, format=None):
        ctl = request.GET.get('ctl_in_codigo')
        status = request.GET.get('status')
        ordem = request.GET.get('ord_in_codigo')
        filial = request.GET.get('fil_in_codigo')
        if ctl is not None:
            serializer = self.serializer_class(Apt_Controle.objects.filter(CTL_IN_CODIGO = ctl), many=True)
        elif ordem is not None:            
            serializer = self.serializer_class(Apt_Controle.objects.filter(CTL_ST_STATUS = status, ORD_IN_CODIGO = ordem, FIL_IN_CODIGO = filial), many=True)
        elif status is None:
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
        impressora = request.GET.get('impressora')
        serializer = Apt_Controle.objects.get(CTL_IN_CODIGO = v_transacao)
        #Altera a impressora do usuário;
        if impressora is not None:
            serializer.PRINTER_ST_IP =  impressora
            serializer.save()
        #Verificar o status do apontamento;
        elif serializer.CTL_DT_LOGOUT is not None:
            serializer.CTL_ST_STATUS =  status
            serializer.save()
        else:
            serializer.CTL_ST_STATUS =  status
            serializer.save()            
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
    
def integrarProducao(pparams):
    #busca Ordens Pendentes    
    funcao = 'controleApt/'
    fil_in = pparams[0]
    ord_in = pparams[1]
    seq_in = pparams[2]
    maq_id = ''
    ord_st_extenso =None
    get_urlprod = geturlprod(funcao)
    #settings.PAY = get_urlprod
    payload = {'fil_in_codigo': fil_in,'status': 'A', 'ord_in_codigo':ord_in}        
    try:        
        #Busca os apontamentos em aberto        
        c_rs = requests.get(get_urlprod, params=payload).json()        
        for rs in c_rs:
            v_dtapontamento = trata_data_sqlite(rs['CTL_DT_LOGIN'])
            str_now = v_dtapontamento.strftime('%Y-%m-%d')
            ord_st_extenso = rs['ORD_ST_EXTENSO']
            #Busca ordens pendentes de integração;
            funcao = 'apontamentos/'
            get_urlapp = geturlapp(funcao)
            payload = {'ordem': rs['ORD_IN_CODIGO'],'filial': rs['FIL_IN_CODIGO'],'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'A'}
            try:
                v_ordens = requests.get(get_urlapp, params=payload).json()
                #print(v_ordens)
                for r_ord in v_ordens:
                    maq_id = r_ord['CMAQ_ST_ID']
                    v_dadosProd = {'fil_in_codigo': r_ord['FIL_IN_CODIGO'],
                                   'ord_in_codigo': r_ord['ORD_IN_CODIGO'],
                                   'ctl_in_codigo': r_ord['CTL_IN_CODIGO'],
                                   'plf_in_sqoperacao': seq_in,
                                   'apt_dt_inclusao': str_now,
                                   'mvp_in_sequencia': r_ord['APT_IN_SEQUENCIA'],
                                   'apt_re_quantidade': r_ord['ORL_RE_QTDLOTE'],
                                   'apt_re_qtdeconvertida': r_ord['PRO_RE_QTDCONV'],
                                   'apt_re_qtderefugo': r_ord['PRO_RE_QTDREFUGO'],
                                   'pro_in_codigo': r_ord['PRO_IN_CODIGO'],
                                   'pro_st_obs': 'Lote integrado pelo ACB',
                                   'pro_st_docorigem': r_ord['PRO_ST_LOTEORI'],
                                   'pro_st_referencia': r_ord['ORL_ST_REFERENCIA'],
                                   'usu_in_codigo': 1,
                                   'pro_st_destino': 'I',
                                   'pro_st_lote': str(r_ord['PRO_ST_LOTE']),
                                   'pro_st_conversor': '0',
                                   'apt_dt_lote': r_ord['APT_DT_APONTAMENTO'],
                                   'cmaq_st_id': maq_id,
                                   'pro_st_id': r_ord['PRO_ST_ID'],
                                   'ord_st_id': r_ord['ORD_ST_ID'],
                                   'orl_re_qtdajustada': r_ord['ORL_RE_QTDAJUSTADA'],
                                   'ord_st_extenso':ord_st_extenso,
                                   'pro_st_fornecedor': r_ord['PRO_ST_FORNECEDOR']}
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
                                c_update_prod = requests.put(get_urlapp, params=payload)
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
                                  'plf_in_sqoperacao': seq_in,
                                  'apt_dt_inclusao': str_now,
                                  'mvd_in_sequencia': r_dem['MOV_IN_SEQUENCIA'],
                                  'pro_st_lote': str(r_dem['PRO_ST_LOTE']),
                                  'pro_re_qtdlote': r_dem['PRO_RE_QTDLOTE'],
                                  'cmaq_st_id': r_dem['CMAQ_ST_ID'],
                                  'ord_st_id': r_dem['ORD_ST_ID'],
                                  'ord_st_extenso':ord_st_extenso}
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
                                c_update_dem = requests.put(get_urlapp, params=payload)
                    except:                        
                        pass
            except:
                pass
        #faz Update da transação;
        payload = {'ctl_in_codigo': rs['CTL_IN_CODIGO'],'status': 'E'}
        #c_update = requests.put(get_urlprod, params=payload)
    except:
        pass

class CadOperador(APIView):
    serializer_class = CadastroOperadoresSerializer
    def get(self, request, format=None):
        v_operador = request.GET.get('operador')
        if v_operador == None:
            serializer = self.serializer_class(Apt_Pro_CadOperador.objects.all(), many=True)
        else:
            serializer = self.serializer_class(Apt_Pro_CadOperador.objects.filter(OPD_ST_CRACHA = v_operador), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class CadEquipamento(APIView):
    serializer_class = CadastroEquipamentosSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_cliente = v_data.get('cliente')
        v_filial = v_data.get('filial')
        if v_cliente == None:
            serializer = self.serializer_class(Apt_Equipamentos.objects.all(), many=True)
        elif not(v_filial is None):
            serializer = self.serializer_class(Apt_Equipamentos.objects.filter(EQP_ST_IPADDRESS = v_cliente, EQP_IN_FILIAL = v_filial), many=True)
        else:
            serializer = self.serializer_class(Apt_Equipamentos.objects.filter(EQP_ST_IPADDRESS = v_cliente), many=True)
        return Response(serializer.data)        
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class CadMaquina(APIView):
    serializer_class = CadastroMaquinasSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_maquina = v_data.get('cmaq_id')
        v_sequencia = v_data.get('cmaq_seq')
        v_centro = v_data.get('ctr_id')
        if (v_maquina is not None) and (v_centro is not None):
            serializer = self.serializer_class(Apt_Pro_CadMaquinas.objects.filter(CMAQ_ST_ID = v_maquina, CTR_ST_ID = v_centro), many=True)
        if (v_maquina is not None) and (v_centro is None):
            serializer = self.serializer_class(Apt_Pro_CadMaquinas.objects.filter(CMAQ_ST_ID = v_maquina), many=True)
        elif v_sequencia is not None:
            serializer = self.serializer_class(Apt_Pro_CadMaquinas.objects.filter(MAQ_IN_SEQUENCIA = v_sequencia), many=True)
        else:
            serializer = self.serializer_class(Apt_Pro_CadMaquinas.objects.all(), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

def total_prod(request):
    template = 'apontamento/fechamento.html'
    v_session = carrega_sessao(request);
    v_ordem = v_session.get('ord_in_codigo')
    if v_ordem is None:
        return redirect('demos_sessions')
    vparams = []
    vparams.append(v_ordem)
    vparams.append(v_session.get('fil_in_codigo'))
    vparams.append(v_session.get('ctl_in_codigo'))    
    #Busca dados da ordem
    funcao = 'ordens/'
    api_listalotes = geturlapp(funcao)
    payload = {'ord_in_codigo': vparams[0],'fil_in_codigo': vparams[1]}
    vresp = requests.get(api_listalotes, params=payload).json()
    for rs in vresp:
        vparams.append(rs['ORD_ST_ID'])
        v_itens = rs['PRO_ST_ITENS']                
    iniciar = IntAPI_sqlite(vparams)
    listLotes = iniciar.total_prod(vparams)
    funcao = 'apontamentos/'
    api_listalotes = geturlapp(funcao)
    payload = {'ordem': vparams[0],'filial': vparams[1]}
    vresponse = requests.get(api_listalotes, params=payload).json()
    for v_rs in vresponse:        
        if v_rs['PRO_ST_ID'] is None:
            for v_itn in v_itens:
                if v_rs['PRO_IN_CODIGO'] ==  v_itn['pro_in_codigo']:
                    payload = {'ctl_in_codigo': v_rs['CTL_IN_CODIGO'],'sequencia': v_rs['APT_IN_SEQUENCIA'], 'status': 'A','ord_st_id':vparams[3],'pro_st_id':v_itn['pro_st_id']}
                    c_tr = requests.put(api_listalotes, data=payload)    
    #print(vresponse)
    seq_resumo = 1
    #iniciar.seq_resumoprod()
    if request.method == 'POST':
        #print('Ok')
        return redirect('incluir_lote')
    else:
        return render(request, template,{'listLotes': listLotes, 'seq_prod': seq_resumo, 'lotes': json.dumps(vresponse)})
    return redirect('incluir_lote')

def resumoProd(request):
    template = 'apontamento/resumo_Prod.html'
    v_session = carrega_sessao(request);
    v_ordem = v_session.get('ord_in_codigo')
    if v_ordem is None:
        return redirect('demos_sessions')
    vparams = []
    vparams.append(v_ordem)
    vparams.append(v_session.get('fil_in_codigo'))
    iniciar = IntAPI_sqlite(vparams)
    vresumo = iniciar.apt_resumoProd()
    if request.method == 'POST':
        #print('Ok')
        return redirect('incluir_lote')
    else:
        return render(request, template,{'resumo': vresumo})
    return redirect('incluir_lote')

def integrarAponta(request):
    v_session = carrega_sessao(request)
    template = 'apontamento/integra_aponta.html'
    #Carrega os apontamentos em aberto;
    funcao = 'apontamentos/'
    plf_in_sqoperacao = v_session.get('seq_in_operacao')
    api_listalotes = geturlapp(funcao)
    payload = {'ordem': v_session.get('ord_in_codigo'),'filial': v_session.get('fil_in_codigo'),'status': 'A','ctl_in_codigo': v_session.get('ctl_in_codigo')}
    vresponse = requests.get(api_listalotes, params=payload).json()
    Lotes = json.dumps(vresponse)
    #busca demandas pendentes de integração para a ordem.
    funcao = 'demandas/'
    get_urlapp = geturlapp(funcao)
    payload = {'ordem': v_session.get('ord_in_codigo'),'filial': v_session.get('fil_in_codigo'),'ctl_in_codigo': v_session.get('ctl_in_codigo'),'status': 'A'}
    v_demanda = requests.get(get_urlapp, params=payload).json()
    v_baixas = json.dumps(v_demanda)
    if request.method == "GET":
        if 'action' in request.GET:
            print('Get')
            action = request.GET.get('action')
    elif request.method == 'POST':
        print('Post')
    return render(request, template,{'baixas': v_baixas, 'lotes': Lotes, 'plf_in_sqoperacao':plf_in_sqoperacao})

def gettipoordens(request):
    v_session = carrega_sessao(request)
    v_filial = v_session.get('fil_in_codigo')
    iniciar = IntAPI(v_session)
    listLotes = iniciar.get_tipo_ordens(v_filial)
def getconfigaponta(request):
    v_session = carrega_sessao(request)
    v_filial = v_session.get('fil_in_codigo')
    iniciar = IntAPI(v_session)
    listLotes = iniciar.get_config_aponta(v_filial)
def getatributoref(request):
    v_session = carrega_sessao(request)
    v_filial = v_session.get('fil_in_codigo')
    iniciar = IntAPI(v_session)
    listLotes = iniciar.get_referencia_atributos(v_filial)
                
def avisoRecebimento(request):
    v_data=request.GET
    v_id= v_data.get('id')
    template = 'recebimento/recebimento.html'
    #Carrega os apontamentos em aberto;
    funcao = 'avisorecebimento/'
    get_urlapi = geturlapi(funcao)
    payload = {'id': v_id}
    print(geturlapi,payload)
    vresponse = requests.get(get_urlapi, params=payload).json()
    Lotes = json.dumps(vresponse)
    print(Lotes)
    if request.method == "GET":
        if 'action' in request.GET:
            print('Get')
            action = request.GET.get('action')
    elif request.method == 'POST':
        print('Post')
    return render(request, template,{'itens': vresponse})

def lotesAviso(request):
    template= 'recebimento/lotes_aviso.html'
    form = LotesReceb()
    v_avr_st_nota = None
    v_fil_in_codigo = None
    v_mvl_st_lote = None
    v_retorno = None
    v_listEti = []
    if request.method == "POST":
        v_retorno = LotesReceb(request.POST)
        if v_retorno.is_valid():
            cd = v_retorno.cleaned_data
            v_avr_st_nota = cd['avr_st_nota']
            v_fil_in_codigo = cd['fil_in_codigo']
            v_mvl_st_lote = cd['mvl_st_lote']
            v_mvl_st_impressora = cd['mvl_st_impressora']
            v_listEti.append(v_avr_st_nota)
            v_listEti.append(v_fil_in_codigo)
            v_listEti.append(v_mvl_st_lote)
            v_listEti.append(v_mvl_st_impressora)
            v_prep = prep_producao()
            dados= v_prep.imprimirEtiquetaReceb(v_listEti)
            return render(request, template, {'form': form,'saldoitem': dados})
    return render(request, template, {'form': form})

def lotesInventario(request):
    template= 'recebimento/lotes_aviso.html'
    form = LotesReceb()
    v_avr_st_nota = None
    v_fil_in_codigo = None
    v_mvl_st_lote = None
    v_retorno = None
    v_listEti = []
    if request.method == "POST":
        v_retorno = LotesReceb(request.POST)
        if v_retorno.is_valid():
            cd = v_retorno.cleaned_data
            v_avr_st_nota = cd['avr_st_nota']
            v_fil_in_codigo = cd['fil_in_codigo']
            v_mvl_st_lote = cd['mvl_st_lote']
            v_mvl_st_impressora = cd['mvl_st_impressora']
            v_listEti.append(v_avr_st_nota)
            v_listEti.append(v_fil_in_codigo)
            v_listEti.append(v_mvl_st_lote)
            v_listEti.append(v_mvl_st_impressora)
            v_prep = prep_producao()
            dados= v_prep.imprimirEtiquetaInventario(v_listEti)
            return render(request, template, {'form': form,'saldoitem': dados})
    return render(request, template, {'form': form})

def ExcluirApontamento(request,pk):
    template = "apontamento/confirma_delete.html"
    v_session = carrega_sessao(request)
    v_pk = {'pk':pk}
    v_session.update(v_pk)
    ini_prod = IntAPI(v_session)
    try:
        lote = ini_prod.listar_producao()
        for itn in lote:
            v_lote = itn
        if request.method == "POST":
            ini_prod.delete_producao()
            return redirect('incluir_lote')
        return render(request, template, {'item':v_lote})
    except :
        raise Http404("lote não encontrado!")
    return redirect('incluir_lote')

def ExcluirDemanda(request,pk):
    template = "apontamento/confirma_delete_demanda.html"
    v_session = carrega_sessao(request)
    v_pk = {'pk':pk}
    v_session.update(v_pk)
    ini_prod = IntAPI(v_session)
    try:
        lote = ini_prod.listar_demanda(v_pk)
        for itn in lote:
            v_lote = itn
        if request.method == "POST":
            ini_prod.delete_demanda()
            return redirect('insDemandaslocal')
        return render(request, template, {'item':v_lote})
    except :
        raise Http404("lote não encontrado!")
    return redirect('insDemandaslocal')

def trocar_impressora(request):
    template = "apontamento/trocar_impressora.html"
    v_session = carrega_sessao(request)
    form = TrocarImpressora()
    v_ini = {'ctl':v_session.get('ctl_in_codigo')}
    init = Controle(v_ini)
    if 1==1:
        dados = init.getControle()
        if request.method == "POST":
            v_dados = TrocarImpressora(request.POST)
            if v_dados.is_valid():
                cd = v_dados.cleaned_data
                v_mvl_st_impressora = cd['mvl_st_impressora']
                v_update = {'impressora':v_mvl_st_impressora}
                v_retorno = init.putControle(v_update)
            else:
                print('invalido')
            return redirect('demos_sessions')
        return render(request, template, {'Titulo': 'Trocar Impressora',
                                          'form': form,
                                          'dados': dados
                                         })
    else:
        raise Http404("Dados não encontrados!")
    return redirect('demos_sessions')

#Imprimir arquivo;
'''f = open("validar.txt", "a")
f.write(e)
f.close()'''
#Imprimir arquivo Fim;
