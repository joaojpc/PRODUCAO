# coding: utf-8

from .serializer import DadosPessoaisSerializer, YourSerializer
from .models import DadosPessoais
from django.http.response import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser

from rest_framework import status

from django.shortcuts import render
from .custom_views import Login_inicial, IntProd
from .api_view import IntApi, GetDadosProducao, IntegrarProducao, GetDadosMaquina, GetDadosRecebimento
from .api_almoxa import *
from datetime import datetime
import json

# Codigo do projeto antigo

def portfolio_exibir(request):
    pessoa = DadosPessoais.objects.all()
    context = {'pessoa': pessoa}

    return render(request, 'portfolios/portfolio_exibir.html', context)

def trata_data(pDATA):
    str_date = pDATA
    data_arquivo2 = str_date.replace('T',' ')
    str_date = data_arquivo2.replace('.000Z','')
    date = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
    return date

class PortfolioListView(APIView):
    serializer_class = DadosPessoaisSerializer

    def get(self, request, format=None):
        serializer = self.serializer_class(DadosPessoais.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class PortfolioView(APIView):

    def get(self, request, pk, format=None):
        user = DadosPessoais.objects.get(pk=pk)
        serializer = DadosPessoaisSerializer(user)
        return Response(serializer.data)

class LoginList(APIView):
    def get(self, request, format=None):
        ordem = request.GET.get('ordem')
        usuario = request.GET.get('usuario')
        iniciar = Login_inicial(ordem,usuario)
        ordem_prod = json.loads(iniciar.ordem())
        response = Response(ordem_prod, status=status.HTTP_200_OK)
        return response
class Listardemandas(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('ordem'))
        ini_prod = IntApi(v_params)
        c_demanda = json.loads(ini_prod.ord_demandas())
        response = Response(c_demanda, status=status.HTTP_200_OK)
        return response
class Operordem(APIView):
    def get(self, request, format=None):
        dados = request.GET
        ini_prod = IntApi(dados)
        c_demanda = ini_prod.operacoes_ordem()
        response = Response(c_demanda, status=status.HTTP_200_OK)
        return response
class Listarocorrencias(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('ordem'))
        ini_prod = IntApi(v_params)
        c_ocorrencias = json.loads(ini_prod.lista_ocorrencia())
        response = Response(c_ocorrencias, status=status.HTTP_200_OK)
        return response
class Listarproducao(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('item'))
        ini_prod = IntApi(v_params)
        c_ocorrencias = json.loads(ini_prod.list_lotes())
        response = Response(c_ocorrencias, status=status.HTTP_200_OK)
        return response            
class Listaratributos(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('item'))
        ini_prod = GetDadosProducao()
        c_ocorrencias = json.loads(ini_prod.itn_atributos(v_params))
        response = Response(c_ocorrencias, status=status.HTTP_200_OK)
        return response
class Listarreferencias(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('item'))
        ini_prod = GetDadosProducao()
        c_ocorrencias = json.loads(ini_prod.itn_referencias(v_params))
        response = Response(c_ocorrencias, status=status.HTTP_200_OK)
        return response
class Itensordem(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('ordem'))
        ini_prod = GetDadosProducao()
        c_ocorrencias = json.loads(ini_prod.itens_ordem(v_params))
        response = Response(c_ocorrencias, status=status.HTTP_200_OK)
        return response
class Demandasempenho(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('filial'))
        v_params.append(request.GET.get('ordem'))
        ini_prod = IntApi(v_params)
        c_demandas = json.loads(ini_prod.ord_listDemandas())
        response = Response(c_demandas, status=status.HTTP_200_OK)
        return response

#buscar na base produção dados das Ordens
class GetManProOrdens(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('org_in_codigo'))
        v_params.append(request.GET.get('ord_seq_in_codigo'))
        v_params.append(request.GET.get('ord_in_codigo'))
        ini_get = GetDadosProducao()
        c_getOrdens = json.loads(ini_get.get_pro_ordens(v_params))
        response = Response(c_getOrdens, status=status.HTTP_200_OK)
        return response
class GetOrdensPendentes(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('org_in_codigo'))
        v_params.append(request.GET.get('fil_in_codigo'))
        v_params.append(request.GET.get('ord_in_codigo'))
        v_params.append(request.GET.get('param'))
        ini_get = GetDadosProducao()
        c_getOrdens = json.loads(ini_get.get_integracao(v_params))
        response = Response(c_getOrdens, status=status.HTTP_200_OK)
        return response
    def put(self, request, format=None):
        v_data=data=request.data
        v_params = []
        v_params.append(v_data['ORG_IN_CODIGO'])
        v_params.append(v_data['ORD_SEQ_IN_CODIGO'])
        v_params.append(v_data['ORD_IN_CODIGO'])
        v_params.append(v_data['param'])
        ini_get = GetDadosProducao()
        ini_get.put_pro_ordens(v_params)
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno, status=status.HTTP_200_OK)
class GetDemandaOrdens(APIView):
    def get(self, request, format=None):
        v_params = []
        v_params.append(request.GET.get('org_in_codigo'))
        v_params.append(request.GET.get('ord_seq_in_codigo'))
        v_params.append(request.GET.get('ord_in_codigo'))
        ini_get = GetDadosProducao()
        c_getOrdens = json.loads(ini_get.demandas_ordem(v_params))
        response = Response(c_getOrdens, status=status.HTTP_200_OK)
        return response
class GetCentroCustos(APIView):
    def get(self, request, format=None):
        dados = request.GET
        ini_get = GetDadosProducao()
        c_getCCusto = json.loads(ini_get.get_centro_custos(dados))
        response = Response(c_getCCusto, status=status.HTTP_200_OK)
        return response
class GetCadastroItens(APIView):
    def get(self, request, format=None):
        dados = request.GET
        ini_get = GetDadosProducao()
        #c_getProdutos = {}
        c_getProdutos = json.loads(ini_get.get_CadastroProdutos(dados))
        response = Response(c_getProdutos, status=status.HTTP_200_OK)
        return response
class IntegrarApontamento(APIView):
    def post(self, request, format=None):
        v_params = request.POST        
        ini_get = IntegrarProducao()
        c_getApontamento = json.loads(ini_get.apt_integrarlote(v_params))
        response = Response(data=c_getApontamento, status=status.HTTP_200_OK)
        #response = Response(status=status.HTTP_200_OK)
        return response

class IntegrarDemandas(APIView):
    def post(self, request, format=None):
        v_params = request.POST
        ini_get = IntegrarProducao()
        c_getaptodem = json.loads(ini_get.apt_integrarDemanda(v_params))
        response = Response(data=c_getaptodem, status=status.HTTP_200_OK)
        return response

class IntegrarRequisicao(APIView):
    def post(self, request, format=None):
        v_params = []
        v_reg = request.POST
        ini_get = Baixas()
        c_getaptodem = json.loads(ini_get.apt_inserirRequisicao(v_reg))
        #c_getaptodem = {'resultado': 'OK'}
        response = Response(data=c_getaptodem, status=status.HTTP_200_OK)
        return response
class BuscaSaldo(APIView):
    def get(self, request, format=None):
        v_item = request.GET
        ini_get = Consulta()
        c_getsaldo = json.loads(ini_get.lista_saldo(v_item))
        response = Response(c_getsaldo, status=status.HTTP_200_OK)
        return response
class IntegrarInventario(APIView):
    def post(self, request, format=None):
        v_dados = request.POST
        ini_get = Inventario()
        #c_retorno = {'resultado': 'OK'}
        c_retorno = ini_get.apt_inserirInventario(v_dados)
        return Response(c_retorno, status=status.HTTP_200_OK)

class DadosMaquina(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosMaquina()
        c_getMaquina = json.loads(ini_get.apt_GetDadosMaquina())
        response = Response(c_getMaquina, status=status.HTTP_200_OK)
        return response
    def put(self, request, format=None):
        v_data=data=request.data
        v_params = []
        v_params.append(v_data['CTR_ST_ID'])
        v_params.append(v_data['CMAQ_ST_ID'])
        ini_get = GetDadosMaquina()
        ini_get.apt_PutDadosMaquina(v_params)
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno, status=status.HTTP_200_OK)
class GetItenslocalizacao(APIView):
    def get(self, request, format=None):
        ini_get = Consulta()
        v_params = []
        #filial
        v_params.append(3)
        # status
        v_params.append('T')
        #id_produto
        v_params.append(request.GET.get('id'))
        c_getProdutos = json.loads(ini_get.get_CadastroProdLocal(v_params))
        response = Response(c_getProdutos, status=status.HTTP_200_OK)
        return response
    def put(self, request, format=None):
        v_data=data=request.data
        #print(v_data)
        v_params = []
        v_params.append(v_data['LOC_ID_PROALMFIL'])        
        ini_get = Consulta()
        c_retorno = ini_get.put_CadastroProdlocal(v_params)
        #c_retorno = {'resultado': 'OK'}
        return Response(c_retorno, status=status.HTTP_200_OK)
    
class PutItenslocalizacao(APIView):
    def put(self, request, format=None):
        v_data=data=request.data
        v_params = []
        v_params.append(v_data['LOC_ID_PROALMFIL'])        
        ini_get = Consulta()
        c_retorno = ini_get.put_CadastroProdlocal(v_params)
        #c_retorno = {'resultado': 'OK'}
        return Response(c_retorno, status=status.HTTP_200_OK)

class GetItensConversor(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        v_params = []
        #filial
        v_params.append(request.GET.get('filial'))
        #produto
        v_params.append(request.GET.get('item'))
        c_getProdutos = json.loads(ini_get.get_Prouni(v_params))
        response = Response(c_getProdutos, status=status.HTTP_200_OK)
        return response

class PostAponta(APIView):
    def post(self, request, format=None):
        dados = request.data
        #print(dados)
        c_retorno = {'resultado': 'OK'}
        ini_get = IntegrarProducao()
        c_getApontamento = json.loads(ini_get.apt_integraraponta(dados))
        return Response(c_getApontamento, status=status.HTTP_200_OK)
    def put(self, request, format=None):
        dados = request.data
        funcao = 'apontamentos/'
        url = 'http://192.168.0.24/app/apontamentos/'
        c_update_prod = requests.put(url, params=dados)
        return Response(c_update_prod, status=status.HTTP_200_OK)

class PostDemanda(APIView):
    def post(self, request, format=None):
        dados = request.data
        #print(dados)
        c_retorno = {'resultado': 'OK'}
        ini_get = IntegrarProducao()
        c_getApontamento = json.loads(ini_get.apt_integrarBaixas(dados))
        return Response(c_getApontamento, status=status.HTTP_200_OK)
    def put(self, request, format=None):
        dados = request.data
        funcao = 'apontamentos/'
        url = 'http://192.168.0.24/app/demandas/'
        c_update_prod = requests.put(url, params=dados)
        return Response(c_update_prod, status=status.HTTP_200_OK)
    
class GetProRecebimento(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosRecebimento()
        dados = request.GET
        c_get = ini_get.get_recebimento(dados)
        response = Response(c_get, status=status.HTTP_200_OK)
        return response    

class GetTipoOrdens(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        dados = request.GET
        c_getProdutos = ini_get.get_tipoOrdens(dados)
        response = Response(c_getProdutos, status=status.HTTP_200_OK)
        return response
class GetConfigAponta(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        dados = request.GET
        c_getProdutos = ini_get.get_configAponta(dados)
        response = Response(c_getProdutos, status=status.HTTP_200_OK)
        return response
class GetProConversor(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        dados = request.GET
        c_getConversor = ini_get.get_pro_conversor(dados)
        response = Response(c_getConversor, status=status.HTTP_200_OK)
        return response
class GetProReferencia(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        dados = request.GET
        c_get = ini_get.get_ref_atributos(dados)
        response = Response(c_get, status=status.HTTP_200_OK)
        return response
class GetLotesReceb(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosRecebimento()
        dados = request.GET
        c_get = ini_get.get_LotesReceb(dados)
        response = Response(c_get, status=status.HTTP_200_OK)
        return response
class GetLotesInventario(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosRecebimento()
        dados = request.GET
        c_get = ini_get.get_LotesInventario(dados)
        response = Response(c_get, status=status.HTTP_200_OK)
        return response
class GetSaldoLote(APIView):
    def get(self, request, format=None):
        ini_get = GetDadosProducao()
        dados = request.GET
        c_get = ini_get.get_saldo(dados)
        response = Response(c_get, status=status.HTTP_200_OK)
        return response
