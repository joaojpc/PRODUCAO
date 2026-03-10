# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
#from .forms import FormUser, BaixaForm 
#from .view_baixas import Baixas
import json

from .serializer import *
from .models import *
from .forms import *
from .api_view import *
from .etiqueta_produto import *

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import  ListAPIView

from rest_framework import status
from producao import settings
import requests

# Create your views here.

def session_almoxa(request):
    v_logado = False
    ccustoDesc = None
    ccusto = None
    requisicao = None
    usuario = None
    nomeusuario = None
    filial = None
    v_req = None
    id_usuario = None
    id_ccusto = None
    v_params = []
    if 'requisicao' in request.session:
        requisicao = request.session['requisicao']
    if 'usuario' in request.session:
        usuario = request.session['usuario']
    if 'filial' in request.session:
        filial = request.session['filial']
    if 'ccusto' in request.session:
        ccusto = request.session['ccusto']
    if 'ccustoDesc' in request.session:
        ccustoDesc = request.session['ccustoDesc']
    if 'nomeusuario' in request.session:
        nomeusuario =  request.session['nomeusuario']
    if 'idusuario' in request.session:
        id_usuario =  request.session['idusuario']
    if 'idccusto' in request.session:
        id_ccusto =  request.session['idccusto']
    template = "almoxarifado/iniciar_almoxa.html",
    form = FormLogin()
    if request.method == "GET":
        if 'action' in request.GET:
            action = request.GET.get('action')
            if action == 'logout':
                if request.session.has_key('usuario'):
                    request.session.flush()
                return redirect('iniciar_baixa')
            if action == 'trocar':
                if request.session.has_key('usuario'):
                    #Não faz update na tabela de controle;
                    request.session.flush()
                return redirect('iniciar_baixa')
    elif request.method == "POST":
        form = FormLogin(request.POST)
        #print(request.session.keys())
        if form.is_valid():
            id_usuario = form.cleaned_data['usuario']
            id_ccusto = form.cleaned_data['centrocusto']
            if form.cleaned_data['ordemservico'] == '':
                id_os = None
            else:
                id_os = form.cleaned_data['ordemservico']
            v_params = {'usuario':id_usuario,'centrocusto':id_ccusto,'ordemservico':id_os}
            # Efetua o login
            v_login = cria_login(v_params)
            requisicao = v_login.get('requisicao')
            nomeusuario = v_login.get('nomeusuario')
            filial      = v_login.get('filial')
            ccusto      = v_login.get('reduzido')
            ccustoDesc  = v_login.get('ccustoDesc')
            request.session['ccusto'] = ccusto
            request.session['usuario'] = nomeusuario
            request.session['filial'] = filial
            request.session['ccustoDesc'] = ccustoDesc
            request.session['requisicao'] = requisicao
            request.session['idusuario'] = id_usuario
            request.session['idccusto'] = id_ccusto
        #print('Inválido')
    return render(request, template, {'title': 'Requisição de Estoque',
                                      'form': form,
                                      'requisicao': requisicao,
                                      'usuario': nomeusuario,
                                      'filial': filial,
                                      'ccusto':ccusto,
                                      'ccustoDesc':ccustoDesc,
                                      })            

def principal(request):
    if request.session.has_key('requisicao'):
        #Não faz update na tabela de controle;
        request.session.flush()
    if request.session.has_key('inventario'):
        #Não faz update na tabela de controle;
        request.session.flush()
    tmpl = "almoxarifado/principal_almoxa.html"    
    return render(request, tmpl)
    '''if 'requisicao' in request.session:
        #Busca requisição em aberto para o usuário
        usuario = None
        ccusto = None
        if 'idusuario' in request.session:
            usuario = request.session['idusuario']
        if 'idccusto' in request.session:
            ccusto = request.session['idccusto']
        funcao = 'requisicao/'
        get_urlest = geturlest(funcao)
        v_usuario = request.GET.get('usuario')
        payload = {'usuario':usuario,'id_ccusto':ccusto,'status': 'A'}
        c_req = requests.get(get_urlest, params=payload).json()
        if not(c_req):
            request.session.flush()
            return redirect('iniciar_baixa')
        return render(request, tmpl)
    else:
        return redirect('iniciar_baixa')'''
def LogOut (request):
    request.session.flush()
    return redirect('iniciar_baixa')
    

def ListarBaixa(request):
    template = "almoxarifado/listar_baixa.html"
    v_listbxaitens  = []
    if request.session.has_key('requisicao'):    
        v_listbxaitens.append(request.session['requisicao'])
        v_listbxaitens.append(request.session['filial'])
        c_baixas = Listar_itensBaixa(v_listbxaitens)    
        if request.method == "POST":
            pass
        else:
            if 'action' in request.GET:
                action = request.GET.get('action')
                if action ==  'IntRequisicao':
                    Integrarequisicao(v_listbxaitens)
                    return redirect('almoxarifado')
        return render(request, template, {'reqitens': c_baixas})
    else:
        return redirect('iniciar_baixa')

def ExcluirBaixa(request,pk):
    template = "almoxarifado/confirma_delete.html"

    try:
        obj = get_object_or_404(bxi_AlmoxaBaixaItens, pk=pk)
        itn = Item_requisicao(obj.BXI_ID_PRODUTO)
        if itn:
            pass
        else:
            return redirect('baixas')
        for rs in itn:
            item = {'produto': rs['PRO_IN_CODIGO'],'Descrição': rs['PRO_ST_DESCRICAO'],'Quantidade': int(obj.BXI_RE_QUANTIDADE)}
        if request.method == "POST":
            if obj.BXI_CH_STATUS=='A':
                obj.delete()
            return redirect('IncluirBaixa')
        return render(request, template, {'object':obj, 'item':item})
    except bxi_AlmoxaBaixaItens.DoesNotExist:
        raise Http404("Requisição não encontrada")
    return redirect('IncluirBaixa')

def ListarSaldo(request):
    if 'filial' in request.session:
        pass
    else:
        return redirect('controla')        
    template= 'almoxarifado/lista_saldo.html'
    form = FormSaldo()
    v_produto = None
    v_filial = request.session['filial']
    if request.method == "POST":
        v_pro_in_codigo = FormSaldo(request.POST)
        if v_pro_in_codigo.is_valid():
            cd = v_pro_in_codigo.cleaned_data
            v_produto = cd['pro_in_codigo']            
            funcao = 'consultasaldo/'
            get_url = geturlapi(funcao)
            payload = {'id': v_produto, 'filial': v_filial}
            c_rs = requests.get(get_url, params=payload).json()
            return render(request, template, {'form': form,'saldoitem': c_rs})
    return render(request, template, {'form': form})

def ControlaAlmoxa(request):    
    if 'filial' in request.session:
        filial = request.session['filial']
        return redirect('almoxarifado')
    else:
        template = "almoxarifado/controle_estoque.html",
        form = FormLoginOperador()
        if request.method == "GET":
            if 'action' in request.GET:
                action = request.GET.get('action')
        elif request.method == "POST":
            rs_form = FormLoginOperador(request.POST)
            if rs_form.is_valid():
                cd = rs_form.cleaned_data
                id_usuario = cd['usuario']
                funcao = 'operador/'
                get_url = geturlprod(funcao)
                payload = {'operador': id_usuario}
                c_rs = requests.get(get_url, params=payload).json()
                if c_rs:
                    for rs in  c_rs:
                        request.session['filial'] = rs['FIL_IN_CODIGO']
                        request.session['usuario'] = rs['OPD_ST_NOME']
                return redirect('almoxarifado')
    return render(request, template, {'form': form})
def EtiquetaItem(request):
    if 'filial' in request.session:
        pass
    else:
        return redirect('controla')
    template= 'almoxarifado/etiqueta_item.html'
    form = FormEtiqueta()    
    v_item = []
    v_pro_in_codigo = None
    v_fil_in_codigo = request.session['filial']
    v_padrao = None
    v_produto = None
    if v_fil_in_codigo == 3:
        v_padrao = 1
    elif v_fil_in_codigo == 302:
        v_padrao = 302
    elif v_fil_in_codigo == 312:
        v_padrao = 302
    else:
        v_padrao = 1
    v_item.append(v_padrao)    
    if request.method == "POST":
        v_pro_in_codigo = FormEtiqueta(request.POST)
        if v_pro_in_codigo.is_valid():
            cd = v_pro_in_codigo.cleaned_data
            v_produto = cd['pro_in_codigo']        
        v_item.append(v_produto)
        funcao = 'produtos/'
        get_urlest = geturlest(funcao)
        payload = {'padrao':v_item[0],'codigo': v_item[1]}
        #Busca o item na tabela local
        c_prod = requests.get(get_urlest, params=payload).json()
        if not(c_prod):
            #baixa o cadastro do item
            pay = {'id':v_produto,'filial': v_fil_in_codigo}
            Buscar_CadastroProdutos(pay)
            c_prod = requests.get(get_urlest, params=payload).json()
        for rs in c_prod:
            v_item.append(rs['BXI_ID_PRODUTO'])
            v_item.append(rs['PRO_ST_DESCRICAO'])
            c_etiqueta = gera_etiqueta()
            c_etiqueta.etiqueta_item(v_item)
        return redirect('etiquetaItem')
    else:
        pass
    return render(request, template, {'form': form,})

def IncluirBaixa(request):
    v_listbxa  = []
    form = FormRequisicao()
    template = "almoxarifado/incluir_baixa.html"
    v_filial = request.session['filial']
    v_requisicao = request.session['requisicao']
    if request.method == "POST":
        form = FormRequisicao(request.POST)
        if form.is_valid():
            v_item = form.cleaned_data['bxi_id_produto']
            v_quantidade = form.cleaned_data['bxi_re_quantidade']
            v_destino = form.cleaned_data['bxi_id_almoxa']
            v_listbxa.append(v_requisicao)
            v_listbxa.append(v_item)
            v_listbxa.append(float(v_quantidade))
            v_listbxa.append(str(v_destino))
            v_listbxa.append(v_filial)
            c_bxaItens = incluirItem(v_listbxa)
            return redirect('IncluirBaixa')
        else:
            print('Inválido')
    return render(request, template, {'form': form, 'filial':v_filial, 'requisicao':v_requisicao})

def man_almoxa(request):
    tmpl = "almoxarifado/man_almoxa.html"
    if request.method == "POST":
        pass
    else:
        if 'action' in request.GET:
            action = request.GET.get('action')
            if action == 'IntCCusto':
                #Buscar Centro de Custos;
                Buscar_CentroCusto(1)
                return redirect('almoxarifado')
            elif action == 'GetProdutos':
                #Buscar Cadastro de Produtos;
                Buscar_CadastroProdutos(1)
                return redirect('almoxarifado')
            elif action == 'IntRequisicao':
                #Buscar Cadastro de Produtos;
                Integrarequisicao(0)
                return redirect('almoxarifado')
            else:
                return redirect('almoxarifado')
        else:
            return render(request, tmpl)
        return render(request, tmpl)

def SincCentroCustos(request):
    template = 'almoxarifado/manutencao.html'
    v_lista = []
    '''v_lista.append(request.session['ord_in_codigo'])
    v_lista.append(request.session['fil_in_codigo'])
    funcao = 'apontamentos'
    api_listalotes = geturl_sqlite(funcao)
    payload = {'ordem': v_lista[0],'filial': v_lista[1],}
    vresponse = requests.get(api_listalotes, params=payload)
    listLotes = json.loads(vresponse.content)
    return render(request, template,{'listLotes': listLotes})'''

class AlmoxaBaixaListView(APIView):
    serializer_class = AlmoxaBaixaSerializer
    def get(self, request, format=None):
        dados = request.GET
        v_sequencia = dados.get('sequencia')
        v_usuario = dados.get('usuario')
        v_ccusto = dados.get('id_ccusto')
        v_status = dados.get('status')
        v_filial = dados.get('filial')
        v_os =  dados.get('ordemservico')        
        if v_os is not None:
            serializer = self.serializer_class(bxa_AlmoxaBaixa.objects.filter(BXA_ST_USUARIO =v_usuario,CUS_ID_CCUSTO=v_ccusto,BXA_CH_STATUS=v_status,OS_ST_ID = v_os, FIL_IN_CODIGO=v_filial).order_by('BXA_IN_SEQUENCIA'), many=True)
        elif v_sequencia is not None:
            serializer = self.serializer_class(bxa_AlmoxaBaixa.objects.filter(BXA_IN_SEQUENCIA = v_sequencia, BXA_CH_STATUS=v_status,FIL_IN_CODIGO=v_filial).order_by('BXA_IN_SEQUENCIA'), many=True)
        elif v_usuario is not None:
            serializer = self.serializer_class(bxa_AlmoxaBaixa.objects.filter(BXA_ST_USUARIO =v_usuario,CUS_ID_CCUSTO=v_ccusto,BXA_CH_STATUS=v_status,FIL_IN_CODIGO=v_filial).order_by('BXA_IN_SEQUENCIA'), many=True)
        elif v_status is not None:
            serializer = self.serializer_class(bxa_AlmoxaBaixa.objects.filter(BXA_CH_STATUS=v_status,FIL_IN_CODIGO=v_filial).order_by('BXA_IN_SEQUENCIA'), many=True)
        else:
            serializer = self.serializer_class(bxa_AlmoxaBaixa.objects.all(), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_data=request.data
        try:
            v_requisicao = v_data['requisicao']
        except:
            v_requisicao = None
        v_sequencia= v_data['sequencia']
        status = v_data['status']
        v_filial = v_data.get('filial')
        serializer = bxa_AlmoxaBaixa.objects.get(BXA_IN_SEQUENCIA = v_sequencia, FIL_IN_CODIGO = v_filial)
        if v_requisicao is not None:
            serializer.REQ_IN_SEQUENCIA = v_requisicao
        serializer.BXA_CH_STATUS =  status        
        serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
    def delete(self, request, format=None):
        v_data=request.data
        v_sequencia = v_data.get('sequencia')        
        v_filial = v_data.get('filial')             
        serializer = bxa_AlmoxaBaixa.objects.get(BXA_IN_SEQUENCIA = v_sequencia, FIL_IN_CODIGO = v_filial)        
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AlmoxaBaixaItemListView(APIView):
    serializer_class = AlmoxaBaixaItensSerializer
    def get(self, request, format=None):
        dados = request.GET
        v_sequencia = dados.get('sequencia')
        v_sequencia_item = dados.get('seq_item')
        v_produto = dados.get('item')
        v_status = dados.get('status')
        v_filial = dados.get('filial')
        if v_produto is not None:
            serializer = self.serializer_class(bxi_AlmoxaBaixaItens.objects.filter(BXI_ID_PRODUTO = v_produto, BXI_CH_STATUS = v_status, FIL_IN_CODIGO = v_filial,BXA_IN_SEQUENCIA = v_sequencia).order_by('BXI_IN_SEQUENCIA'), many=True)
        elif v_sequencia is not None:
            serializer = self.serializer_class(bxi_AlmoxaBaixaItens.objects.filter(BXA_IN_SEQUENCIA = v_sequencia, FIL_IN_CODIGO = v_filial).order_by('BXI_IN_SEQUENCIA'), many=True)        
        elif v_status is not None:
            serializer = self.serializer_class(bxi_AlmoxaBaixaItens.objects.filter(BXA_IN_SEQUENCIA = v_sequencia, BXI_CH_STATUS = v_status, FIL_IN_CODIGO = v_filial).order_by('BXI_IN_SEQUENCIA'), many=True)
        elif v_sequencia_item is not None:
            serializer = self.serializer_class(bxi_AlmoxaBaixaItens.objects.filter(BXA_IN_SEQUENCIA = v_sequencia,BXI_IN_SEQUENCIA = v_sequencia_item, FIL_IN_CODIGO = v_filial, BXI_CH_STATUS = v_status).order_by('BXI_IN_SEQUENCIA'), many=True)        
        else:
            serializer = self.serializer_class(bxi_AlmoxaBaixaItens.objects.filter(FIL_IN_CODIGO = v_filial).order_by('BXI_IN_SEQUENCIA'), many=True)        
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_data=request.data
        v_requisicao = v_data['requisicao']
        v_item_req = v_data['item_req']
        v_sequencia = v_data['sequencia']
        v_sequencia_item = v_data['seq_item']
        status = v_data['status']
        v_filial = v_data['filial']
        serializer = bxi_AlmoxaBaixaItens.objects.get(BXA_IN_SEQUENCIA = v_sequencia,BXI_IN_SEQUENCIA = v_sequencia_item, FIL_IN_CODIGO = v_filial)
        serializer.BXI_CH_STATUS =  status
        serializer.REQ_IN_SEQUENCIA = v_requisicao
        serializer.REI_IN_SEQUENCIA =  v_item_req
        serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
    def delete(self,request, id,format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.delete()
            return Response(status=status.HTTP_200_OK)

class CentroCustosListView(APIView):
    serializer_class = CentroCustosSerializer
    def get(self, request, format=None):
        v_cus_id = request.GET.get('id_centrocusto')
        if v_cus_id is not None:
            serializer = self.serializer_class(bxa_CentroCustos.objects.filter(CUS_ID_CCUSTO = v_cus_id).order_by('CUS_IN_REDUZIDO'), many=True)
        else:
            serializer = self.serializer_class(bxa_CentroCustos.objects.all(), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class CadItensListView(APIView):
    serializer_class = CadItensSerializer
    def get(self, request, format=None):
        v_item = request.GET
        v_proId = v_item.get('item')
        v_codigo = v_item.get('codigo')
        v_padrao = v_item.get('padrao')        
        if v_proId is not None:
            serializer = self.serializer_class(est_CadItens.objects.filter(BXI_ID_PRODUTO = v_proId).order_by('BXI_ID_PRODUTO'), many=True)
        elif v_codigo is not None:
            serializer = self.serializer_class(est_CadItens.objects.filter(PRO_PAD_IN_CODIGO = v_padrao,PRO_IN_CODIGO = v_codigo).order_by('BXI_ID_PRODUTO'), many=True)
        else:
            serializer = self.serializer_class(est_CadItens.objects.all(), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class CadItensAlmListView(APIView):
    serializer_class = CadItensAlmSerializer
    def get(self, request, format=None):
        v_proId = request.GET.get('item')
        v_codigo = request.GET.get('item_almoxa')
        if v_proId is not None:
            serializer = self.serializer_class(est_CadItemAlmoxa.objects.filter(LOC_ID_PRODUTO = v_proId).order_by('LOC_ID_PRODUTO'), many=True)
        elif v_codigo is not None:
            serializer = self.serializer_class(est_CadItemAlmoxa.objects.filter(LOC_ID_PROALMFIL = v_codigo).order_by('LOC_ID_PRODUTO'), many=True)
        else:
            serializer = self.serializer_class(est_CadItemAlmoxa.objects.all(), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
