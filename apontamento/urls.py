# -*- coding: utf-8 -*-
from django.urls import path
from apontamento import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static


from apontamento.views import ApontaControleListView, CadOperador, CadEquipamento, CadMaquina

admin.autodiscover()
urlpatterns = [
    #path('admin/', admin.site.urls),
    path('incluir_lote/', views.reglote, name='incluir_lote'),
    path('apontamento/', views.apontamento, name='apontamento'),
    path('incluirdemanda/', views.demandas, name='incluirdemanda'),
    path('menu/', views.principal, name='menu'),
    path('consulta/', views.consulta, name='consulta'),
    path('login/', views.loginControl_sqlite, name='login'),
    path('listarlotes/', views.listarlotes, name='listarlotes'),
    path('listarlotes_sqlite/', views.listarlotes_sqllite, name='listarlotes_sqllite'),
    #path('iniciar/', views.base, name='iniciar'),
    path('demanda/', views.baixaDemanda, name='demanda'),
    path('demandalocal/', views.baixaDemandaLocal, name='demandalocal'),
    path('home/', views.home, name='home'),
    path('controle/', views.protected_view, name='controle'),
    path('insDemanda/', views.insDemandas, name='insDemanda'),
    path('insDemandaslocal/', views.insDemandaslocal, name='insDemandaslocal'),
    path('ocorrencia/', views.ocorrencias, name='ocorrencia'),
    path('insOcorrencia/', views.insOcorrencia, name='insOcorrencia'),
    path('iniciar/', views.session_demo, name='demos_sessions'),
    #path('desligar/', views.desligar(10), name='desligar'),
    path('grafico/', views.grafico2, name='grafico'),
    #path('grafico2/', views.grafico2, name='grafico2'),
    #path('bar/', BarView.as_view(), name='bar'),
    #path('grafico3/', views.grafico3, name='grafico3'),
    #path('etiqueta/', views.etiqueta, name='etiqueta'),
    path('manutencao/', views.manutencao, name='manutencao'),
    path('controledemanda/', views.controledemanda, name='controledemanda'),
    path('testar_impressao/', views.testar_impressao, name='testar_impressao'),    
    path('operador/', CadOperador.as_view(), name='operador'),
    path('controleApt/', ApontaControleListView.as_view(), name='controleApt'),
    path('equipamento/', CadEquipamento.as_view(), name='equipamento'),
    path('maquina/', CadMaquina.as_view(), name='maquina'),    
    path('total_prod/', views.total_prod, name='total_prod'),
    path('resumo/', views.resumoProd, name='resumo'),
    path('integraraponta/', views.integrarAponta, name='integraraponta'),
    path('recebimento/', views.avisoRecebimento, name='recebimento'),
    path('lotesaviso/', views.lotesAviso, name='lotesaviso'),
    path('etiquetainventario/', views.lotesInventario, name='etiquetainventario'),
    path('impressora/', views.trocar_impressora, name='impressora'),
    #path('tipoordens/', views.gettipoordens, name='tipoordens'),
    path('deleteapt/<int:pk>', views.ExcluirApontamento, name='deleteapt'),
    path('deletedemanda/<int:pk>', views.ExcluirDemanda, name='deletedemanda'),
]
