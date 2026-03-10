# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.urls import path
from apontamento import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static


from apontamento.views import ApontaControleListView, CadOperador, CadEquipamento, CadMaquina

admin.autodiscover()
urlpatterns = [
    #url(r'^admin/', admin.site.urls),
    url(r'^incluir_lote/$', views.reglote, name='incluir_lote'),
    url(r'^apontamento/$', views.apontamento, name='apontamento'),
    url(r'^incluirdemanda/$', views.demandas, name='incluirdemanda'),
    url(r'^menu/$', views.principal, name='menu'),
    url(r'^consulta/$', views.consulta, name='consulta'),
    url(r'^login/$', views.loginControl_sqlite, name='login'),
    url(r'^listarlotes/$', views.listarlotes, name='listarlotes'),
    url(r'^listarlotes_sqlite/$', views.listarlotes_sqllite, name='listarlotes_sqllite'),
    #url(r'^iniciar/$', views.base, name='iniciar'),
    url(r'^demanda/$', views.baixaDemanda, name='demanda'),
    url(r'^demandalocal/$', views.baixaDemandaLocal, name='demandalocal'),
    url(r'^home/$', views.home, name='home'),
    url(r'^controle/$', views.protected_view, name='controle'),
    url(r'^insDemanda/$', views.insDemandas, name='insDemanda'),
    url(r'^insDemandaslocal/$', views.insDemandaslocal, name='insDemandaslocal'),
    url(r'^ocorrencia/$', views.ocorrencias, name='ocorrencia'),
    url(r'^insOcorrencia/$', views.insOcorrencia, name='insOcorrencia'),
    url(r'^iniciar/$', views.session_demo, name='demos_sessions'),
    #url(r'^desligar/$', views.desligar(10), name='desligar'),
    url(r'^grafico/$', views.grafico2, name='grafico'),
    #url(r'^grafico2/$', views.grafico2, name='grafico2'),
    #url(r'^bar/$', BarView.as_view(), name='bar'),
    #url(r'^grafico3/$', views.grafico3, name='grafico3'),
    #url(r'^etiqueta/$', views.etiqueta, name='etiqueta'),
    url(r'^manutencao/$', views.manutencao, name='manutencao'),
    url(r'^controledemanda/$', views.controledemanda, name='controledemanda'),
    url(r'^testar_impressao/$', views.testar_impressao, name='testar_impressao'),    
    url(r'^operador/$', CadOperador.as_view(), name='operador'),
    url(r'^controleApt/$', ApontaControleListView.as_view(), name='controleApt'),
    url(r'^equipamento/$', CadEquipamento.as_view(), name='equipamento'),
    url(r'^maquina/$', CadMaquina.as_view(), name='maquina'),    
    url(r'^total_prod/$', views.total_prod, name='total_prod'),
    url(r'^resumo/$', views.resumoProd, name='resumo'),
    url(r'^integraraponta/$', views.integrarAponta, name='integraraponta'),
    url(r'^recebimento/$', views.avisoRecebimento, name='recebimento'),
    url(r'^lotesaviso/$', views.lotesAviso, name='lotesaviso'),
    url(r'^etiquetainventario/$', views.lotesInventario, name='etiquetainventario'),
    url(r'^impressora/$', views.trocar_impressora, name='impressora'),
    #url(r'^tipoordens/$', views.gettipoordens, name='tipoordens'),
    path('deleteapt/<int:pk>', views.ExcluirApontamento, name='deleteapt'),
    path('deletedemanda/<int:pk>', views.ExcluirDemanda, name='deletedemanda'),
]
