# -*- coding: utf-8 -*-
#from django.shortcuts import render
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


# Create your views here.
#from apontamento.view_medidores import medicoes
from apontamento.custom_views import Listar_opcoes, User_logado, Login_inicial, IntProd
from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite, Login_inicial_sqlite
from apontamento.forms import FormUser, RegOcorForm, DemForm, RegLotForm, FormUser_sqlite


def home(request):
    template = "apontamento/home.html"
    return render(request, template)

#def desligar(valor):
#    os.system("kill chromium-browser")

def principal(request):
    v_lista = Listar_opcoes_sqlite()
    v_logado = v_lista.equipaLogado_sqlite()
    #v_logado = False	
    if v_logado:
	#medicoes()
        controle = v_lista.lis_controle_sqlite()
        tmpl = "apontamento/principal.html"
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
    ini_prod = IntProd();
    form = json.loads(ini_prod.listar_ocor())
    return render(request, template,{'form': form})

def insOcorrencia(request):
    template = 'apontamento/nova_ocorrencia.html'
    ini_prod = IntProd()
    lista = ini_prod.lis_ocor()
    if request.method == "POST":
        form = RegOcorForm(request.POST)
        if form.is_valid():
            ocorrencia = int(form.cleaned_data['ati_in_codigo'])
            tempo = int(form.cleaned_data['ati_in_tempo'])
            l_lista = []
            l_lista.append(ocorrencia)
            l_lista.append(tempo)
            ini_prod = IntProd()
            ini_prod.Ins_Ocor(l_lista)
            return redirect('ocorrencia')
    else:
        form = RegOcorForm()
    return render(request, template, {'form': form,'lista': lista})

def baixaDemanda(request):
    template = 'apontamento/demandas.html'
    ini_prod = IntProd();
    c_demanda  = json.loads(ini_prod.ord_listDemandas())
    return render(request, template, {'dem': c_demanda})

def insDemandas(request):
    """ A view of all bands. """
    template = 'apontamento/novademanda.html'
    ini_prod = IntProd();
    c_demanda = json.loads(ini_prod.ord_demandas())
    if request.method == "POST":
        form = DemForm(request.POST)
        if form.is_valid():
            l_demandas = []
            #print 'Valido'
            v_mvs_st_loteforne = form.cleaned_data['dem_st_lote']
            v_apt_re_quantidade = form.cleaned_data['dem_re_qtdlote']            
            l_demandas.append(v_mvs_st_loteforne)
            l_demandas.append(v_apt_re_quantidade)
            v_iserirlote = ini_prod.apt_inserirDemanda(l_demandas)
            return redirect('demanda')
        #else:
            #print 'Inválido'
    else:
        form = DemForm()
    var_get_search = request.GET.get('search_box')
    if var_get_search is not None:
        c_demanda = c_demanda.filter(name__icontains=var_get_search)
    return render(request, template, {'form': form, 'dem': c_demanda})

def listarlotes(request):
    template = 'apontamento/listar_lotes.html'
    ini_prod = IntProd()
    listLotes  = json.loads(ini_prod.list_lotes())
    return render(request, template, {'listLotes': listLotes})

def reglote(request):
    v_lista = Listar_opcoes_sqlite()
    v_logado = v_lista.equipaLogado_sqlite()
    if v_logado:
        litens = []
        litens_json = []
        var_a = []
        obj_itens = IntProd()
        lista = obj_itens.itens_ordem()
        itens = json.loads(lista)
        obj_ref = json.loads(obj_itens.itn_referencias())
        obj_atr = json.loads(obj_itens.itn_atributos())
        for itn in itens:
            var_id = itn['pro_in_codigo']
            var_nome = itn['pro_st_descricao']
            litens_json.append(dict(parent_id=0, id=itn['pro_in_codigo'], name=itn['pro_st_descricao'], type='I', lista='N'))
            litens.append((var_id, var_nome))
            for obj_ref1 in obj_ref:
                if (itn['rfc_in_codigo'] == obj_ref1['rfc_in_codigo']):                    
                    if obj_ref1['rat_ch_tipo'] == 'L':
                        litens_json.append(
                            dict(parent_id=itn['pro_in_codigo'], id=obj_ref1['ref_rat_value'], name=obj_ref1['rat_desc'], type=obj_ref1['rat_ch_tipo'], lista='N'))
                    else:
                        litens_json.append(
                            dict(parent_id=itn['pro_in_codigo'], id=obj_ref1['rat_in_codigo'], name=obj_ref1['rat_desc'], type=obj_ref1['rat_ch_tipo'], lista='N'))
        for obj_ref1 in obj_ref:
            for obj_atr1 in obj_atr:
                if obj_atr1['pai_rat_in_codigo'] == obj_ref1['rat_in_codigo']:
                    if not (obj_atr1['rat_in_codigo'] in var_a):
                        var_a.append(obj_atr1['rat_in_codigo'])
                        litens_json.append(dict(parent_id=obj_ref1['rat_in_codigo'],id=obj_atr1['rat_value'], name=obj_atr1['rat_st_descricao'], type=obj_atr1['rat_ch_tipo'],
                                        lista='S'))
        


        #lista.update(litens)
        dict_litens ={}
        dict_litens= json.dumps(litens_json)
        template = 'apontamento/reglote.html'
        if request.method == 'POST':
            lote_form = RegLotForm(data=request.POST)
            if lote_form.is_valid():
                #print 'valido'
                clote = lote_form.cleaned_data
                v_dlotes= []
                c_apontamento = json.loads(obj_itens.apt_inserirApt())
                for v_apontamento in c_apontamento:
                    v_apt = v_apontamento['apt_in_sequencia']
                v_quantidade = lote_form.cleaned_data['orl_re_qtdlote']
                v_qtdeconv = v_quantidade
                v_item = lote_form.cleaned_data['pro_in_codigo']
                v_obs = ''
                v_doc_origem = ''
                v_referencia = lote_form.cleaned_data['orl_st_referencia']
                v_usu_in_codigo = 1
                v_destino = ''
                v_dlotes.append(v_apt)
                v_dlotes.append(v_quantidade)
                v_dlotes.append(v_qtdeconv)
                v_dlotes.append(v_item)
                v_dlotes.append(v_obs)
                v_dlotes.append(v_doc_origem)
                v_dlotes.append(v_referencia)
                v_dlotes.append(v_usu_in_codigo)
                v_dlotes.append(v_destino)
                obj_itens.apt_inserirlote(v_dlotes)
                return redirect('listarlotes')
            #else:
            #    print ('Invalid')
        else:
            lote_form = RegLotForm()
        return render(request, template, {'lote_form': lote_form,'lista3': dict_litens,'lista': lista })
    else:
        tmpl = "apontamento/iniciar.html"
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

''' def incluir_apontamento(self,pApontamento):
        v_lista = []
        ord_in_codigo = pApontamento['ord_in_codigo']
        fil_in_codigo = pApontamento['fil_in_codigo']
        dict_atrib    = pApontamento['dict_atrib']
        v_lista_ini   = pApontamento['list_ordem']
        v_quantidade  = pApontamento['v_quantidade']
        v_item        = pApontamento['v_item']
        v_referencia  = pApontamento['v_referencia']
        v_refugo      = pApontamento['v_refugo']
        v_origem      = pApontamento['v_origem']
        lista         = pApontamento['lista']
        v_info        = pApontamento['infoadic']
        v_lista.append(ord_in_codigo)
        v_lista.append(fil_in_codigo)
        v_lista.append(v_lista_ini['ctl_in_codigo'])
        v_lista.append(v_lista_ini['cliente'])
        v_iniseq = IntAPI_sqlite(v_lista)
        c_seqmov = v_iniseq.seq_movprod_sqlite()        
        v_dlotes= []
        v_med= []
        v_pro_st_id = None
        v_ord_st_id = v_lista_ini['ord_st_id']
        v_referenciaDesc = formatar_caracteristicas(v_referencia,dict_atrib)        
        #Tipo de Ordens
        v_med.append(v_lista_ini['tpo_st_codigo'])
        payload = {'pro_pad_in_codigo': v_lista_ini['pro_pad_in_codigo'],
                   'pro_in_codigo': v_item}        
        funcao = 'itensOrdens/'
        app_url = geturl_sqlite(funcao)
        cr_itens = requests.get(app_url, params=payload).json()
        for rs_itens in cr_itens:
            v_pro_st_id = rs_itens['PRO_ST_ID']
            d_medidas = json.loads(rs_itens['PRO_ST_MEDIDAS'])
        if d_medidas:
            for rs_med in d_medidas:
                if rs_med['PRO_RE_COMPRIMENTO'] is None:
                    v_med.append(0)
                else:
                    v_med.append(rs_med['PRO_RE_COMPRIMENTO'])
                #busca largura do item pai para o produto 7376
                if ((rs_med['PRO_RE_LARGURA'] is None) or (rs_med['PRO_RE_LARGURA'] ==0)) and (v_item == 7376):
                    v_med.append(v_lista_ini['pai_pro_re_largura'])                                   
                elif rs_med['PRO_RE_LARGURA'] is None:
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
        v_med.append(v_quantidade)
        v_qtdeconv = converter_unidade(v_med)
        #converte refugo
        if v_refugo > 0:
            v_med[4]= v_refugo
            v_med[2]= v_lista_ini['pai_pro_re_largura']
            v_qtdeconvRef = converter_unidade(v_med)
        else:        
            v_qtdeconvRef = v_refugo
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
        v_dlotes.append(v_qtdeconvRef)
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
        if len(v_desc) < 28:
            string1 = v_desc
            string2 = ''
        else:
            v_sep = ' '
            #busca o primeiro indice da string
            v_idx = v_desc[1:28].rfind(v_sep)
            string1 = v_desc[0:v_idx+1]
            string2 = v_desc[v_idx+2:]
        #busca impressora
        host = None
        maquina_cod = ''
        maquina = None
        maquina_id = ''
        funcao = 'equipamento/'
        app_url = geturl_producao(funcao)
        payload = {'cliente': v_lista[3]}
        try:
            cr_printer = requests.get(app_url, params=payload).json()
            for rs_printer in cr_printer:
                host = rs_printer['PRINTER_ST_IP']
                maquina = rs_printer['MAQ_IN_CODIGO']
        except:
            host = "192.168.1.211"
        if host is None:
            host = "192.168.1.211"
        #Busca a Máquina vinculada ao equipamento
        if maquina is not None:
            funcao = 'maquina/'
            app_url = geturl_producao(funcao)
            payload = {'cmaq_seq': maquina}
            try:
                cr_maquina = requests.get(app_url, params=payload).json()
                if cr_maquina:
                    for rs_maquina in cr_maquina:
                        maquina_cod = rs_maquina['CMAQ_ST_CODIGO']
                        maquina_id = rs_maquina['CMAQ_ST_ID']
            except:
                pass
        #Busca informações das ordens
        l_info = []
        l_info.append(v_lista_ini['tpo_st_codigo'])            
        if v_info:
            if v_info['umidade'] is None:
                l_info.append(0)
            else:
                l_info.append(v_info['umidade'])
            if v_info['lote_ordem']is None:
                l_info.append(None)
            else:
                l_info.append(v_info['lote_ordem'])
            if v_info['destino']is None:
                l_info.append(None)
            else:
                l_info.append(v_info['destino'])
        else:
            l_info.append(0)
            l_info.append(None)
            l_info.append(None)        
        v_listEti.append(dict(ordem = v_lista[0],
        descr1 = string1,
        descr2 = string2,
        un = v_un,
        codbar = str_lote,
        umidade = l_info[1],
        qtde = v_dlotes[2],
        destino = l_info[3],
        lote = str_lote,
        data = str_eti,
        grupo = '',
        comprimento = v_med[1],
        largura = v_med[2],
        seqlote = str_seq,
        madeira = v_madeira,
        maquina = maquina_cod,
        espessura =v_med[3],
        impressora =host,
        loteordem = l_info[2],
        tipoordem = l_info[0],
        item = v_dlotes[3],
        origem = v_origem,
        pallet = v_referenciaDesc
        ))
        #print('apontamento Views 575',v_listEti)
        json_eti= {}
        json_eti = json.dumps(v_listEti)
        #print(json_eti)
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
                       "PRO_RE_QTDREFUGO":v_dlotes[10],
                       "PRO_RE_QTDCONV":v_dlotes[2],
                       "PRO_ST_LOTEORI":v_origem,
                       "PRO_ST_ID":v_pro_st_id,
                       "ORD_ST_ID":v_ord_st_id,
                       "CMAQ_ST_ID":maquina_id}
        #print('DADOS',dados)
        response = requests.post(api_producao, data=dados)
        #obj_itens.apt_inserirlote(v_dlotes)
        try:
            c_etiqueta = gera_etiqueta(json_eti)
        except:
            pass
        #guarda o ultimo apontamento na sessão
        return c_seqmov'''
