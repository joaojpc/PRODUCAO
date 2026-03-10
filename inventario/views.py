# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render, redirect
#from .forms import FormUser, BaixaForm
#from .view_baixas import Baixas
import json

from .serializer import *
from .models import *
from .forms import *
from .api_view import *

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import  ListAPIView

from rest_framework import status
from producao import settings
import requests

# Create your views here.

def session_inventario(request):
    inventario = None
    nomeusuario = None
    filial = None
    id_usuario = None
    v_params = []
    if 'inventario' in request.session:
        inventario = request.session['inventario']
        if 'filial' in request.session:
            filial = request.session['filial']
        if 'nomeusuario' in request.session:
            nomeusuario =  request.session['nomeusuario']
        if 'id_usuario' in request.session:
            id_usuario =  request.session['id_usuario']
    else:
        request.session.flush()
    template = "inventario/iniciar_inventario.html",
    form = FormLoginInventario()
    if request.method == "GET":
        if 'action' in request.GET:
            action = request.GET.get('action')
            if action == 'logout':
                if request.session.has_key('nomeusuario'):
                    request.session.flush()
                return redirect('iniciar_inventario')
            if action == 'trocar':
                if request.session.has_key('nomeusuario'):
                    #Não faz update na tabela de controle;
                    request.session.flush()
                return redirect('iniciar_inventario')
    elif request.method == "POST":
        form = FormLoginInventario(request.POST)
        #print(request.session.keys())
        if form.is_valid():
            id_usuario = form.cleaned_data['usuario']
            v_params.append(id_usuario)
            #Busca Usuário
            v_usu = json.loads(lista_usuarios(id_usuario))
            for c_usu in v_usu:
                nomeusuario = c_usu['OPD_ST_NOME']
                filial = c_usu['FIL_IN_CODIGO']
                v_params.append(c_usu['FIL_IN_CODIGO'])
            #verifica se tem requisição em aberto para o usuário;
            cr_req = json.loads(buscaInventario(v_params))
            if cr_req:
                for v_cur in cr_req:
                    inventario = v_cur['INV_IN_SEQUENCIA']
            else:
                inventario = criarInventario(v_params)
            request.session['nomeusuario'] = nomeusuario
            request.session['filial'] = filial
            request.session['inventario'] = inventario
            request.session['id_usuario'] = id_usuario
        #print('Inválido')
    return render(request, template, {'title': 'Inventario de Estoque',
                                      'form': form,
                                      'inventario': inventario,
                                      'nomeusuario':nomeusuario,
                                      'id_usuario':id_usuario,
                                      'filial':filial,
                                      })

def principal(request):
    if request.session.has_key('inventario'):
        request.session.flush()
    tmpl = "inventario/principal_inventario.html"
    return render(request, tmpl)

def InventarioItem(request):
    v_listbxa  = []
    form = FormInventario()
    template = "inventario/invent_almoxa.html"
    if request.method == "POST":
        form = FormInventario(request.POST)
        if form.is_valid():
            v_item = form.cleaned_data['bxi_id_produto']
            v_quantidade = form.cleaned_data['inv_re_quantidade']
            v_listbxa.append(v_item)
            v_listbxa.append(float(v_quantidade))
            v_listbxa.append(request.session['inventario'])
            c_bxaItens = InventItem(v_listbxa)
            return redirect('invItens')
        else:
            print('Inválido')
    return render(request, template, {'form': form})
class ItensInventarioListView(APIView):
    serializer_class = InventarioItemSerializer
    def get(self, request, format=None):
        v_proId = request.GET.get('item')
        v_sequencia = request.GET.get('sequencia')
        v_status = request.GET.get('status')
        v_inventario = request.GET.get('inventario')
        if v_proId is not None:
            serializer = self.serializer_class(alm_InventarioItens.objects.filter(ITI_ID_PRODUTO = v_proId, ITI_CH_STATUS = v_status).order_by('ITI_IN_SEQUENCIA'), many=True)
        elif v_inventario is not None:
            serializer = self.serializer_class(alm_InventarioItens.objects.filter(INV_IN_SEQUENCIA = v_inventario, ITI_CH_STATUS = v_status).order_by('ITI_IN_SEQUENCIA'), many=True)
        elif v_sequencia is not None:
            serializer = self.serializer_class(alm_InventarioItens.objects.filter(ITI_IN_SEQUENCIA = v_sequencia, ITI_CH_STATUS = v_status).order_by('ITI_IN_SEQUENCIA'), many=True)
        elif v_status is not None:
            serializer = self.serializer_class(alm_InventarioItens.objects.filter(ITI_CH_STATUS = v_status).order_by('ITI_IN_SEQUENCIA'), many=True)
        else:
            serializer = self.serializer_class(alm_InventarioItens.objects.all(), many=True)
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
        status = v_data['status']
        v_sequencia= v_data['sequencia']
        v_item = v_data['item']
        v_invent = v_data['mov']
        v_mov = v_data['moi']
        v_qtde = v_data['quantidade']
        serializer = alm_InventarioItens.objects.get( ITI_IN_SEQUENCIA=v_sequencia)
        if v_mov == 0:
            serializer.ITI_RE_QUANTIDADE =  v_qtde
        else:
            serializer.ITI_CH_STATUS =  status
            serializer.MOV_IN_SEQUENCIA = v_invent
            serializer.MOI_IN_SEQUENCIA = v_mov
        serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)

def ListarInventario(request):
    v_listbxaitens  = []
    v_list_int  = []
    v_listbxaitens.append(None)
    c_baixas = Listar_itensInvent(v_listbxaitens)
    template = "inventario/lista_inventario.html"
    if request.method == "POST":
        return render(request, template, {'reqitens': c_baixas})
    else:
        if 'action' in request.GET:
            action = request.GET.get('action')
            if action ==  'IntInventario':
                v_list_int.append(request.session['inventario'])
                v_list_int.append(request.session['filial'])
                IntegraInventario(v_list_int)
                #Encerra a sessão ativa;
                request.session.flush()
                #Volta na tela de login do inventário;
                return redirect('iniciar_inventario')
                #return render(request, template, {'reqitens': c_baixas})
        return render(request, template, {'reqitens': c_baixas})

class InventarioView(APIView):
    serializer_class = InventarioSerializer
    def get(self, request, format=None):
        v_UsuId = None
        v_status = None
        v_filial = None
        v_seq = None
        if request.GET.get('usuario'):
            v_UsuId = request.GET.get('usuario')
        if request.GET.get('status'):
            v_status = request.GET.get('status')
        if request.GET.get('filial'):
            v_filial = int(request.GET.get('filial'))
        if request.GET.get('sequencia'):
            v_seq   = int(request.GET.get('sequencia'))
        if v_UsuId is not None:
            serializer = self.serializer_class(alm_Inventario.objects.filter(INV_ST_USUARIO = v_UsuId, INV_CH_STATUS = v_status, FIL_IN_CODIGO = v_filial).order_by('INV_IN_SEQUENCIA'), many=True)
        elif (v_seq is not None) and (v_seq != 0):
            serializer = self.serializer_class(alm_Inventario.objects.filter(INV_IN_SEQUENCIA = v_seq, FIL_IN_CODIGO = v_filial, INV_CH_STATUS = v_status).order_by('INV_IN_SEQUENCIA'), many=True)
        elif v_filial is not None:
            serializer = self.serializer_class(alm_Inventario.objects.filter(INV_CH_STATUS = v_status, FIL_IN_CODIGO = v_filial).order_by('INV_IN_SEQUENCIA'), many=True)
        else:
            serializer = self.serializer_class(alm_Inventario.objects.all(), many=True)
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
        v_mov = v_data['movimento']
        v_sequencia= v_data['sequencia']
        status = v_data['status']
        serializer = alm_Inventario.objects.get(INV_IN_SEQUENCIA = v_sequencia)
        serializer.INV_CH_STATUS =  status
        serializer.MOV_IN_SEQUENCIA = v_mov
        serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
