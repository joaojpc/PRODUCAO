# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from .serializer import *
from .models import *
from django.db.models import Sum

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import  ListAPIView
import json

from rest_framework import status
# Create your views here.
class ApontaDemandaListView(APIView):
    serializer_class = ApontaDemandaSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_ordem = v_data.get('ordem')
        v_filial = v_data.get('filial')
        v_lote = v_data.get('lote')
        v_status  = v_data.get('status')
        v_transacao  = v_data.get('ctl_in_codigo')
        pk = v_data.get('pk')
        v_total = v_data.get('total')
        if pk:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(MOV_IN_SEQUENCIA = pk), many=True)
        #ordem, filial e lote;
        elif v_total == 'S':
            total = Apt_Pro_Demandas.objects.filter(ORD_IN_CODIGO=v_ordem, FIL_IN_CODIGO=v_filial).aggregate(total=Sum('PRO_RE_QTDLOTE'))['total']
            return Response({'total_lote': total,'ordem': v_ordem,'filial': v_filial})
        elif v_ordem is not None and v_filial is not None and v_lote is not None:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(ORD_IN_CODIGO = v_ordem,FIL_IN_CODIGO = v_filial, PRO_ST_LOTE = v_lote), many=True)
        elif v_ordem is not None and v_filial is not None:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(ORD_IN_CODIGO = v_ordem,FIL_IN_CODIGO = v_filial), many=True)
        elif v_status is not None:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, CTL_IN_CODIGO = v_transacao, MOV_ST_STATUS = v_status).order_by('MOV_IN_SEQUENCIA'), many=True)
        elif v_ordem == None:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.all(), many=True)
        elif v_lote is not None:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(PRO_ST_LOTE = v_lote,PRO_RE_QTDLOTE = 9999), many=True)
        else:
            serializer = self.serializer_class(Apt_Pro_Demandas.objects.filter(ORD_IN_CODIGO = v_ordem,FIL_IN_CODIGO = v_filial), many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_data=request.GET
        v_transacao= v_data.get('ctl_in_codigo')
        v_sequencia= v_data.get('sequencia')
        status = v_data.get('status')
        item = v_data.get('item')
        v_pk = v_data.get('pk')
        if v_pk is not None:
            serializer = Apt_Pro_Demandas.objects.get(MOV_IN_SEQUENCIA = v_pk)
        else:
            serializer = Apt_Pro_Demandas.objects.get(CTL_IN_CODIGO = v_transacao, MOV_IN_SEQUENCIA = v_sequencia)        
        serializer.MOV_ST_STATUS =  status
        if item is not None:
            serializer.PRO_IN_CODIGO = item
        serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
    def delete(self, request, format=None):
        v_data=request.GET
        v_pk= v_data.get('pk')        
        serializer = Apt_Pro_Demandas.objects.get(MOV_IN_SEQUENCIA = v_pk)
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ApontaOrdemListView(APIView):
    serializer_class = ApontaOrdemSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_ordem = v_data.get('ordem')
        v_filial = v_data.get('filial')
        v_seqLote = v_data.get('sequencial')
        v_status  = v_data.get('status')
        v_transacao  = v_data.get('ctl_in_codigo')
        v_agrupa = v_data.get('group_by')
        v_resumo = v_data.get('gera_resumo')
        v_pk = v_data.get('pk')
        v_total = v_data.get('total')
        if v_pk is not None:
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(APT_IN_SEQUENCIA = v_pk), many=True)
        elif v_agrupa is not None:
            serializer = Apt_ApontaOrdem.objects.values('ORD_IN_CODIGO', 'PRO_IN_CODIGO','PRO_ST_DESCRICAO','PRO_ST_ID','ORD_ST_ID').annotate(TOTAL_PROD=Sum('PRO_RE_QTDCONV')).filter(ORD_IN_CODIGO=v_ordem, RES_ST_STATUS = 'N').order_by('PRO_IN_CODIGO')
            return Response(serializer)
        elif v_resumo is not None:   
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, APT_CH_STATUS = v_status, RES_ST_STATUS = v_resumo).order_by('APT_IN_SEQUENCIA'), many=True)
        elif v_total == 'S':
            total = Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO=v_ordem, FIL_IN_CODIGO=v_filial).aggregate(total=Sum('PRO_RE_QTDCONV'))['total']
            return Response({'total_ordem': total,'ordem': v_ordem})
        elif (v_status is not None) and (v_transacao is None):
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, APT_CH_STATUS = v_status).order_by('APT_IN_SEQUENCIA'), many=True)
        elif (v_transacao is not None) and (v_status is None):
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, CTL_IN_CODIGO = v_transacao).order_by('APT_IN_SEQUENCIA'), many=True)
        elif (v_transacao is not None) and (v_status is not None):
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, CTL_IN_CODIGO = v_transacao, APT_CH_STATUS = v_status).order_by('APT_IN_SEQUENCIA'), many=True)        
        elif (v_filial is not None) and (v_ordem is not None) and (v_seqLote is not None):
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, APT_IN_SEQUENCIA = v_seqLote).order_by('APT_IN_SEQUENCIA'), many=True)
        elif (v_filial is not None) and (v_ordem is not None):
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial).order_by('APT_IN_SEQUENCIA'), many=True)
        elif v_ordem is None:        
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.all(), many=True)            
        elif v_seqLote == None:
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial).order_by('APT_IN_SEQUENCIA'), many=True)
        else:
            serializer = self.serializer_class(Apt_ApontaOrdem.objects.filter(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO = v_filial, APT_IN_SEQUENCIA = v_seqLote).order_by('APT_IN_SEQUENCIA'), many=True)
        return Response(serializer.data)           
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_data=request.GET        
        v_transacao= v_data.get('ctl_in_codigo')
        v_sequencia= v_data.get('sequencia')
        status = v_data.get('status')
        v_resumo = v_data.get('gera_resumo')
        v_ordem = v_data.get('ordem')
        v_filial = v_data.get('filial')
        v_ord_id = v_data.get('ord_st_id')
        v_pro_id = v_data.get('pro_st_id')
        v_qtdeAjustada = v_data.get('qtde_re_ajustada')
        v_res_st_id = v_data.get('res_st_id')
        v_pk = v_data.get('pk')        
        if v_pk is not None:
            serializer = Apt_ApontaOrdem.objects.get(APT_IN_SEQUENCIA = v_pk)
            serializer.APT_CH_STATUS =  status
            serializer.save()        
        elif v_resumo is not None:
            serializer = Apt_ApontaOrdem.objects.get(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO= v_filial, RES_ST_STATUS = 'N', APT_CH_STATUS = status, APT_IN_SEQUENCIA = v_sequencia)
            serializer.RES_ST_STATUS =  v_resumo
            serializer.save()
        elif v_ord_id is not None:
            serializer = Apt_ApontaOrdem.objects.get(CTL_IN_CODIGO = v_transacao, APT_IN_SEQUENCIA = v_sequencia)
            serializer.ORD_ST_ID =  v_ord_id
            serializer.PRO_ST_ID =  v_pro_id
            serializer.save()
        elif v_res_st_id is not None:
            serializer = Apt_ApontaOrdem.objects.get(ORD_IN_CODIGO = v_ordem, FIL_IN_CODIGO= v_filial, CTL_IN_CODIGO = v_transacao, APT_IN_SEQUENCIA = v_sequencia, RES_ST_STATUS = 'N')
            serializer.RES_ST_ID =  v_res_st_id
            serializer.ORL_RE_QTDAJUSTADA =  v_qtdeAjustada
            serializer.RES_ST_STATUS =  'S'
            serializer.save()
        else:
            serializer = Apt_ApontaOrdem.objects.get(CTL_IN_CODIGO = v_transacao, APT_IN_SEQUENCIA = v_sequencia)
            serializer.APT_CH_STATUS =  status
            serializer.save()
        c_retorno = {'resultado': 'OK'}
        return Response(c_retorno)
    def delete(self, request, format=None):
        v_data=request.GET
        v_pk= v_data.get('pk')        
        serializer = Apt_ApontaOrdem.objects.get(APT_IN_SEQUENCIA = v_pk)
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ApontaOcorrenciaListView(APIView):
    serializer_class = ApontaOcorrenciaSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_ordem = v_data.get('ordem')
        if v_ordem == None:
            serializer = self.serializer_class(Apt_Ocorrencia.objects.all(), many=True)
        else:
            serializer = self.serializer_class(Apt_Ocorrencia.objects.filter(ATI_IN_ORDEM = v_ordem), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.dados)        
        if serializer.is_valid():            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)        
        
class ManProOrdensListView(APIView):
    serializer_class = ManProOrdensSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_ordem = v_data.get('ord_in_codigo')
        v_fil = v_data.get('fil_in_codigo')
        v_org = v_data.get('org_in_codigo')
        if v_ordem == None:
            serializer = self.serializer_class(apt_pro_ordens.objects.all(), many=True)
        elif v_fil == None:
            serializer = self.serializer_class(apt_pro_ordens.objects.filter(ORD_IN_CODIGO = v_ordem,ORG_IN_CODIGO = v_org), many=True)
        else:
            serializer = self.serializer_class(apt_pro_ordens.objects.filter(ORD_IN_CODIGO = v_ordem,FIL_IN_CODIGO = v_fil), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    def put(self, request, format=None):
        v_data=request.GET
        v_ordem= v_data.get('ord_in_codigo')
        v_org = v_data.get('org_in_codigo')
        v_seq = v_data.get('ord_seq_in_codigo')
        serializer = apt_pro_ordens.objects.filter(ORD_IN_CODIGO = v_ordem,ORG_IN_CODIGO = v_org,ORD_SEQ_IN_CODIGO = v_seq)
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManItensOrdens(APIView):
    serializer_class = ManItensOrdensSerializer
    def get(self, request, format=None):
        v_data=request.GET
        pro_pad = v_data.get('pro_pad_in_codigo')
        pro_in = v_data.get('pro_in_codigo')
        if pro_in == None:
            serializer = self.serializer_class(apt_itens_ordens.objects.all(), many=True)
        else:
            serializer = self.serializer_class(apt_itens_ordens.objects.filter(PRO_PAD_IN_CODIGO = pro_pad,
                                                                               PRO_IN_CODIGO = pro_in), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        
    def put(self, request, format=None):
        v_data=request.GET
        pro_pad = v_data.get('pro_pad_in_codigo')
        pro_in = v_data.get('pro_in_codigo')
        serializer = self.serializer_class(apt_itens_ordens.objects.filter(PRO_PAD_IN_CODIGO = pro_pad,
                                                                           PRO_IN_CODIGO = pro_in), many=True)        
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        dados = request.data
        pro_pad = dados['PRO_PAD_IN_CODIGO']
        pro_in = dados['PRO_IN_CODIGO']
        serializer = apt_itens_ordens.objects.filter(PRO_IN_CODIGO = pro_in,PRO_PAD_IN_CODIGO = pro_pad)
        if serializer:
            serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManProAtividade(APIView):
    serializer_class = ManProAtividadeSerializer
    def get(self, request, format=None):
        serializer = self.serializer_class(apt_pro_atividade.objects.all(), many=True)
        return Response(serializer.data)

class ManProAptSequencia(APIView):
    serializer_class = Resumo_OrdensSerializer
    def get(self, request, format=None):
        data = request.GET
        ord_id = data.get('ord_st_id')
        res_st_id = data.get('res_st_id')
        if res_st_id is not None:
            sq = Apt_ResumoOrdem.objects.values('RES_IN_CODIGO').order_by('-RES_IN_CODIGO').first()
            if sq is None:
                serializer = json.dumps({'RES_IN_CODIGO': 0})
            else:
                serializer = json.dumps(sq)
            return Response(serializer)
        elif ord_id is None:
            serializer = self.serializer_class(Apt_ResumoOrdem.objects.all(), many=True)
            return Response(serializer.data)
        else:
            serializer = self.serializer_class(Apt_ResumoOrdem.objects.filter(ORD_ST_ID = ord_id), many=True)
            return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
class AptEstFormatos(APIView):
    serializer_class = AptEstFormatosSerializer
    def get(self, request, format=None):
        v_data=request.GET
        fmt_id = v_data.get('fmt_st_id')
        fmt_cod = v_data.get('fmt_st_cod')
        pun_id = v_data.get('pun_st_id')
        pro_id = v_data.get('pro_st_id')
        if fmt_id is not None:
            serializer = self.serializer_class(Apt_EstFormatos.objects.filter(FMT_ST_ID = fmt_id, PRO_ST_ID = fmt_cod), many=True)
        if pro_id is not None:
            serializer = self.serializer_class(Apt_EstFormatos.objects.filter(PRO_ST_ID = fmt_cod), many=True)
        else:
            serializer = self.serializer_class(Apt_EstFormatos.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class AptProTipoOrdens(APIView):
    serializer_class = AptProTipoOrdensSerializer
    def get(self, request, format=None):
        v_data=request.GET
        tpo_st_id = v_data.get('tpo_st_id')
        tpo_st_codigo = v_data.get('tpo_st_codigo')
        if tpo_st_id is not None:
            serializer = self.serializer_class(Apt_ProTipoOrdens.objects.filter(TPO_ST_ID = tpo_st_id), many=True)
        elif tpo_st_codigo is not None:
            serializer = self.serializer_class(Apt_ProTipoOrdens.objects.filter(TPO_ST_CODIGO_TIPO = tpo_st_codigo), many=True)
        else:
            serializer = self.serializer_class(Apt_ProTipoOrdens.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
class AptProMaquinaConfig(APIView):
    serializer_class = AptProMaquinaConfigSerializer
    def get(self, request, format=None):
        v_data=request.GET
        cfg_st_id = v_data.get('cfg_st_id')
        if cfg_st_id is not None:
            serializer = self.serializer_class(Apt_ProMaquinaConfig.objects.filter(CFG_ST_ID = cfg_st_id), many=True)
        else:
            serializer = self.serializer_class(Apt_ProMaquinaConfig.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

class CarAtributosReferencia(APIView):
    serializer_class = CarAtributosReferenciaSerializer
    def get(self, request, format=None):
        v_data=request.GET
        v_car_id = v_data.get('car_st_id')
        v_rfc_in = v_data.get('rfc_in_codigo')
        v_car_gru = v_data.get('rat_bo_grupo')
        pai_in = v_data.get('pai_rat')
        rat_value= v_data.get('rat_value')
        if v_car_id is not None:
            serializer = self.serializer_class(Car_AtributosReferencia.objects.filter(CAR_ST_ID = v_car_id), many=True)
        elif rat_value is not None:
            serializer = self.serializer_class(Car_AtributosReferencia.objects.filter(RAT_VALUE=rat_value,RFC_IN_CODIGO = v_rfc_in).order_by('RAT_IN_CODIGO'), many=True)
        elif (v_rfc_in is not None) and (v_car_gru is None):
            serializer = self.serializer_class(Car_AtributosReferencia.objects.filter(RFC_IN_CODIGO = v_rfc_in).order_by('CAR_IN_PRIORIDADE'), many=True)
        elif v_car_gru is not None:
            serializer = self.serializer_class(Car_AtributosReferencia.objects.filter(RFC_IN_CODIGO = v_rfc_in,RAT_BO_GRUPO = v_car_gru).order_by('CAR_IN_PRIORIDADE'), many=True)
        elif pai_in is not None:
            serializer = self.serializer_class(Car_AtributosReferencia.objects.filter(PAI_RAT_IN_CODIGO=pai_in,RFC_IN_CODIGO = v_rfc_in,RAT_BO_GRUPO = v_car_gru).order_by('RAT_IN_CODIGO'), many=True)
        else:
            serializer = self.serializer_class(Car_AtributosReferencia.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

