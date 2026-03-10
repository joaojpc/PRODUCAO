# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import socket
import json
import sys
import sqlite3
import cx_Oracle as cxo

from django.utils import timezone
#from apontamento.Etiqueta_precorte import gera_etiqueta
#from apontamento.custom_views_sqlite import Listar_opcoes_sqlite, User_logado_sqlite, Login_inicial_sqlite


def getOracleConnection():
    username = 'mgcustom'
    password = 'supcustom'
    #server   = '@192.168.0.8:1521/'
    server   = '@10.101.235.105:1521/'
    #databaseName = 'megag'
    databaseName = 'ORCL_gru1x6.subnetskydbindu.vcnrootautoskyo.oraclevcn.com'
    try:
        conn = cxo.connect(username+'/'+password+server+databaseName)
        #print ('Conectado: \n')
    except cxo.DatabaseError:
        print ('Falha ao conectar no banco de dados: \n')
        exit (1)
    return conn;

'''def getSqliteConnection(dbname):
    try:
        conn = psycopg2.connect(
        host="localhost",
        database="producao",
        user="prod",
        password="supprod")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')    
    return conn;'''

def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip

class User_logado:
    def __init__(self):
        self.ender_ip = getEnderIP()
        self.dbname = 'Producao.db'
        v_preparar = Listar_opcoes()
        equipamento = json.loads(v_preparar.lis_controle())
        for v_equip in equipamento:
            self.ini_filial = v_equip['eqp_in_filial']
            self.usuario_in =v_equip['ctl_in_usuario']
            self.seq_controle = v_equip['ctl_in_codigo']
    def userLogado(self):
        logado = False
        if self.usuario_in:
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select apc.*
                             from intprod.apt_controle apc
                            where apc.ctl_in_usuario = :ctl_in_usuario
                             and apc.ctl_logout is null''')
            cur.prepare(selectSQL)
            cur.execute(None, {'ctl_in_usuario': self.usuario_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            for rs in c_rs:
                logado = True
        return logado

    def descontar(self):
        con = getOracleConnection()
        cur = con.cursor()
        row_now = timezone.now()
        str_now = row_now.strftime('%Y/%m/%d %H:%M:%S')
        ExecSQL =('''update intprod.apt_controle apc
                          set apc.ctl_logout = to_date(ctl_logout)
                        where apc.ctl_in_usuario = :ctl_in_usuario
                          and apc.ctl_in_codigo  = :ctl_in_codigo''')
        cur.prepare(ExecSQL)
        cur.execute(None, {'ctl_logout':str_now,'ctl_in_usuario':self.usuario_in,'ctl_in_codigo':self.seq_controle})
        cur = con.prepareStatement(ExecSQL)
        cur.close
        con.close
        return True
    def conectar(self, pparams):
        v_lista = []
        v_lista.append(pparams)
        for v_obj in v_lista:
            ordem = v_obj[0]
            usuario = v_obj[1]
        con = getOracleConnection()
        cur = con.cursor()
        row_now = timezone.now()
        str_now = row_now.strftime('%Y/%m/%d %H:%M:%S')
        insertTableSQL = ('''insert into intprod.apt_controle
                            (CTL_IN_CODIGO,CTL_IN_USUARIO,ORD_IN_CODIGO,CTL_LOGIN,CTL_MAQ_IP)
                            values
                            (:ctl_in_codigo,:ctl_in_usuario,:ord_in_codigo,to_date(str_now),:ctl_maq_ip)''')
        iniciar = Login_inicial(ordem,usuario)
        sequencia = iniciar.seq_initapt()
        cur.prepare(insertTableSQL)
        cur.execute(None, {'ctl_in_codigo':sequencia,'ctl_in_usuario':usuario,'ord_in_codigo':ordem,'ctl_login':str_now,'ctl_maq_ip': self.ender_ip})
        cur.close
        con.close

class Listar_opcoes:
    def __init__(self):
        self.ender_ip = getEnderIP()
        c_dados = json.loads(self.lis_controle())
        for v_ini in c_dados:
            self.ini_filial = v_ini['eqp_in_filial']
            self.ini_ordem = v_ini['ord_in_codigo']
    def equipaLogado(self):
        logado = False
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select apc.*
                     from intprod.apt_controle apc
                    where apc.ctl_maq_ip = :ender_ip
                      and apc.ctl_logout is null''')
        cur.prepare(selectSQL)
        cur.execute(None, {'ender_ip': self.ender_ip})
        c_rs = cur.fetchall()
        cur.close
        con.close
        for rs in c_rs:
            logado = True
        return logado

    def lis_controle(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select t.eqp_in_codigo,
                                      t.eqp_st_name,
                                      t.eqp_st_ipaddress, 
                                      t.eqp_in_filial,
                                      t.maq_in_codigo,
                                      c.ctl_in_usuario,
                                      c.ord_in_codigo,
                                      to_char(c.ctl_login,'DD/MM/YYYY HH24:MI') ctl_login,
                                      c.ctl_in_codigo,
                                      c.ctl_in_consenergia,
                                      c.ctl_in_produtividade
                                 from intprod.apt_equipamentos t,
                                      intprod.apt_controle c
                                where c.ctl_maq_ip = t.eqp_st_ipaddress 
                                  and c.ctl_maq_ip = :ender_ip
                                  and c.ctl_logout is null''')
        cur.prepare(selectSQL)
        cur.execute(None, {'ender_ip': self.ender_ip})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(eqp_in_codigo = rs[0],
                              eqp_st_name = rs[1],
                              eqp_st_ipaddress = rs[2],
                              eqp_in_filial = int(rs[3]),
                              maq_in_codigo = rs[4],
                              ctl_in_usuario= rs[5],
                              ord_in_codigo= int(rs[6]),
                              ctl_login = rs[7],
                              ctl_in_codigo = int(rs[8]),
                              ctl_in_consenergia = rs[9],
                              ctl_in_produtividade = rs[10]))
        json_litens ={}
        json_litens = json.dumps(lista)
        return json_litens

class Login_inicial:
    def __init__(self,p_ordem,p_usuario):
        self.ender_ip = getEnderIP()
        self.ordem_in = p_ordem
        self.usuario_in = p_usuario
        print(self.ender_ip)
        con = getOracleConnection()
        cur = con.cursor()	
        selectSQL = ('''select *
                         from intprod.apt_equipamentos eqp
                        where eqp.eqp_st_ipaddress = :ender_ip''')
        cur.prepare(selectSQL)
        cur.execute(None, {'ender_ip': self.ender_ip})
        c_rs = cur.fetchall()
        cur.close
        con.close
        self.equipamento_cad = 'N'
        for rs in c_rs:
            self.usu_filial = int(rs[3])
            self.equipamento_cad = 'S'

    def apt_usuario(self):
        if self.equipamento_cad == 'S':
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select opd.opd_pad_in_codigo,
                              opd.opd_in_codigo,
                              opd.opd_st_alternativo,
                              opd.opd_st_descricao
                         from mgman.pro_cadoperador opd
                         where opd.opd_st_alternativo = :usuario 
                       order by opd_in_codigo''')
            cur.prepare(selectSQL)
            cur.execute(None, {'usuario': self.usuario_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(opd_pad_in_codigo = int(rs[0]),
                              opd_in_codigo = rs[1],
                              opd_st_alternativo = rs[2],
                              opd_st_descricao = rs[3]))
            usuarios ={}
            usuarios = json.dumps(lista)
            return usuarios

    def seq_initapt(self):
        if self.equipamento_cad == 'S':
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL =('''select nvl(max(apc.ctl_in_codigo),0)+1 as crl_in_codigo
                     from intprod.apt_controle apc''')
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.usu_filial,'ord_in':self.ordem_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            for rs in c_rs:
                sequencia = int(rs[0])
            return sequencia
    def ordem(self):
        if self.equipamento_cad == 'S':
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select op.org_in_codigo,
                              op.fil_in_codigo,                                     
                              op.ord_in_codigo,
                              op.ord_st_situacao        
                         from mgman.pro_ordens op
                        where op.fil_in_codigo = :fil_in
                          and op.ord_in_codigo = :ord_in
                          and op.ord_st_situacao = 'AB'                           
                           order by ord_in_codigo''')
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.usu_filial,'ord_in':self.ordem_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(org_in_codigo = int(rs[0]),
                              fil_in_codigo = int(rs[1]),
                              ord_in_codigo = int(rs[2]),
                              ord_st_situacao = rs[3]))
            ordens= {}
            ordens = json.dumps(lista)
            return ordens

class IntProd:
    def __init__(self):
        self.equip_logado = 'N'
        self.dbname = 'Producao.db'
        v_lista = Listar_opcoes_sqlite()
        c_controle = json.loads(v_lista.lis_controle_sqlite())
        for v_controle in c_controle:
            self.fil_in = v_controle['eqp_in_filial']
            self.ordem_in = v_controle['ord_in_codigo']
            self.usuario = v_controle['ctl_in_usuario']
            self.seq_controle = v_controle['ctl_in_codigo']
            self.maquina = v_controle['maq_in_codigo']
            self.equip_logado = 'S'
        if (self.equip_logado == 'S'):
            c_operacoes = json.loads(self.operacoes_ordem())
            for v_operacoes in c_operacoes:
                self.pro_in = v_operacoes['pro_in_codigo']
                self.org_in = v_operacoes['org_in_codigo']

    def operacoes_ordem(self):
        v_params = []
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            v_params.append(self.fil_in)
            v_params.append(self.ordem_in)
            selectSQL =('''select ord.org_tab_in_codigo,
                              ord.org_pad_in_codigo,
                              ord.org_in_codigo,
                              ord.org_tau_st_codigo,
                              ord.ord_tab_in_codigo,
                              ord.ord_seq_in_codigo,
                              ord.ord_in_codigo,
                              ord.pro_tab_in_codigo,
                              ord.pro_pad_in_codigo,
                              ord.pro_in_codigo,
                              pgo.plf_in_sqoperacao
                         from mgman.pro_ordens ord,
                              mgman.pro_prog_ordem pgo
                        where ord.org_tab_in_codigo = pgo.org_tab_in_codigo
                          and ord.org_pad_in_codigo = pgo.org_pad_in_codigo
                          and ord.org_in_codigo = pgo.org_in_codigo
                          and ord.org_tau_st_codigo = pgo.org_tau_st_codigo
                          and ord.ord_tab_in_codigo = pgo.ord_tab_in_codigo
                          and ord.ord_seq_in_codigo = pgo.ord_seq_in_codigo
                          and ord.ord_in_codigo = pgo.ord_in_codigo
                          and ord.fil_in_codigo = :fil_in
                          and ord.ord_in_codigo = :ord_in''')
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.usuario,'ord_in':self.ordem_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(org_in_codigo = int(rs[2]),
                              ord_in_codigo = int(rs[6]),
                              pro_in_codigo = int(rs[9]),
                              plf_in_sqoperacao = rs[2]))
            operacoes= {}
            operacoes = json.dumps(lista)
            return operacoes
    def ord_demandas(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (self.fil_in,self.ordem_in,ref_cursor)
            cur.callproc('apt_intprod.apt_retornademandadisp',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(pro_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              mvs_re_quantidade = rs[2],
                              mvs_st_loteforne = rs[3],
                              mvs_st_referenciadesc = rs[4],
                              conversor = float(rs[5]),
                              mvs_st_referencia = rs[6]))
            json_demandas= {}
            json_demandas = json.dumps(lista)
            return json_demandas
    def ord_listDemandas(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =('''select dem.com_in_codigo,
                              pro.pro_st_descricao,
                              dem.apt_re_qtdeselecionada,
                              dem.mvs_st_loteforne,
                              mgadm.adm_pck_util.f_formatacaract(dem.mvs_st_referencia) as mvs_st_referencia_desc                               
                         from mgcustom.apt_apontademanda_estoque dem,
                              mgadm.est_produtos pro
                        where pro.pro_tab_in_codigo = dem.com_tab_in_codigo
                          and pro.pro_pad_in_codigo = dem.com_pad_in_codigo
                          and pro.pro_in_codigo = dem.com_in_codigo
                          and dem.ord_in_codigo     = :ord_in
                          and dem.com_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in,100,sysdate)''')
        cur.prepare(selectSQL)
        cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(com_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              apt_re_qtdeselecionada = float(rs[2]),
                              mvs_st_loteforne = rs[3],
                              mvs_st_referencia_desc = rs[4]))
        json_baixas= {}
        json_baixas = json.dumps(lista)
        return json_baixas

    def apt_inserirDemanda(self, pparams):
        if (self.equip_logado == 'S'):
            v_listlote = []
            v_listlote.append(pparams)
            for v_obj in v_listlote:
                v_mvs_st_loteforne = v_obj[0]
                v_apt_re_quantidade = float(v_obj[1])
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (ref_cursor,self.org_in,self.fil_in,self.ordem_in,v_mvs_st_loteforne,v_apt_re_quantidade)
            cur.callproc('apt_intprod.p_inseredemanda_lotes',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            for ret in c_rs:
                result = ret[0]
            return result

    def list_lotes(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL =(''' select apl.pro_in_codigo,
                               pro.pro_st_descricao,
                               apl.orl_re_qtdlote,
                               apl.orl_re_unidade,
                               apl.orl_st_lotefabricacao,
                               nvl(mgadm.adm_pck_util.f_formatacaract(apl.orl_st_referencia),'*') as mvs_st_referencia_desc,
                               apl.orl_st_referencia
                        from mgcustom.apt_apontaordem_lote apl,
                             mgadm.est_produtos pro
                       where pro.pro_tab_in_codigo = apl.pro_tab_in_codigo
                         and pro.pro_pad_in_codigo = apl.pro_pad_in_codigo
                         and pro.pro_in_codigo = apl.pro_in_codigo
                         and apl.ord_in_codigo = :ord_in
                         and apl.fil_in_codigo  = :fil_in
                         order by to_number(apl.orl_st_slotefabricacao)''')
        cur.prepare(selectSQL)
        cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(pro_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              orl_re_qtdlote = float(rs[2]),
                              orl_re_unidade = rs[3],
                              orl_st_lotefabricacao = rs[4],
                              mvs_st_referencia_desc = rs[5],
                              orl_st_referencia = rs[6]))
        json_producao= {}
        json_producao = json.dumps(lista)
        return json_producao

    def apt_inserirApt(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (self.fil_in,self.ordem_in,self.usuario,ref_cursor)
            cur.callproc('apt_intprod.apt_inserir_apt',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            for ret in c_rs:
                lista.append(dict(apt_in_sequencia=int(ret[7])))
            aponta= {}
            aponta = json.dumps(lista)
            return aponta
    def itens_ordem(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (self.fil_in,self.ordem_in,ref_cursor)
            cur.callproc('apt_intprod.apt_retornaitens',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(pro_in_codigo = int(rs[2]),
                              pro_st_descricao = rs[3],
                              uni_st_unidade = rs[4],
                              rfc_in_codigo = int(rs[5])))
            json_itens= {}
            json_itens = json.dumps(lista)
            return json_itens

    def itn_referencias(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (self.fil_in,self.pro_in,ref_cursor)
            cur.callproc('apt_intprod.apt_retornacaracteristica',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(rat_in_codigo = int(rs[0]),
                                  rat_st_opcoes = rs[1],
                                  itn_desc = rs[2],
                                  rat_desc = rs[3],
                                  rat_ch_tipo = rs[4],
                                  ref_rat_value = rs[5],
                                  rfc_in_codigo = int(rs[6])))
            json_referencia= {}
            json_referencia = json.dumps(lista)
            return json_referencia

    def itn_atributos(self):
        dbname = 'Producao.db'
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            sparams = (self.fil_in,self.pro_in,ref_cursor)
            cur.callproc('apt_intprod.apt_retornaatributo',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(pai_rat_in_codigo = int(rs[0]),
                                  rat_in_codigo = int(rs[1]),
                                  rat_st_descricao = rs[2],
                                  rat_value = rs[3],
                                  rat_ch_tipo = rs[4]))
            json_atributo= {}
            json_atributo = json.dumps(lista)
            return json_atributo

    def apt_inserirlote(self, pparams):
        if (self.equip_logado == 'S'):
            v_listlote = []
            v_listlote.append(pparams)
            con = getOracleConnection()
            cur = con.cursor()
            ref_cursor = con.cursor()
            for v_obj in v_listlote:
                v_apt = v_obj[0]
                v_quantidade = float(v_obj[1])
                v_qtdeconv = float(v_obj[2])
                v_item = int(v_obj[3])
                v_obs = v_obj[4]
                v_doc_origem = v_obj[5]
                v_referencia = v_obj[6]
                v_usu_in_codigo = v_obj[7]
                v_destino = v_obj[8]
            sparams = (self.fil_in,self.ordem_in,v_apt,v_quantidade,v_qtdeconv,v_item ,v_obs,v_doc_origem,v_referencia,v_usu_in_codigo,v_destino,ref_cursor)
            cur.callproc('apt_intprod.cli_p_lotes_ordem',(sparams))
            c_rs = ref_cursor.fetchall()
            cur.close
            con.close
            '''v_listlote = []
            c_etiqueta = gera_etiqueta()
            for rs in c_rs:
                v_listlote.append(rs[0])
                v_listlote.append(rs[1])
                v_listlote.append(rs[2])
                v_listlote.append(rs[3])
                v_listlote.append(rs[4])
                v_listlote.append(rs[5])
                v_listlote.append(rs[6])
                v_listlote.append(rs[7])
                v_listlote.append(rs[8])
                v_listlote.append(rs[9])
                v_listlote.append(rs[10])
                v_listlote.append(rs[11])
                v_listlote.append(rs[12])
                v_listlote.append(rs[13])
                v_listlote.append(rs[14])
                v_listlote.append(self.maquina)
                v_listlote.append(rs[15])
                c_etiqueta.etiqueta_pre(v_listlote)'''

    def lis_ocor(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select a.ati_tab_in_codigo,
                              a.ati_pad_in_codigo,
                              a.ati_in_codigo,
                              a.ati_st_nome
                         from mgman.pro_atividade a
                        where a.ati_ch_produtiva = 'I'
                              and a.ati_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in, 204, sysdate)
                              order by a.ati_in_codigo''')
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.fil_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(ati_tab_in_codigo = int(rs[0]),
                              ati_pad_in_codigo = int(rs[1]),
                              ati_in_codigo = int(rs[2]),
                              ati_st_nome = rs[3]))
            json_motivos = {}
            json_motivos = json.dumps(lista)
            return json_motivos

    def seq_ocorrencia(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select nvl(max(apo.ati_in_sequencia),0)+1 as ati_in_sequencia
                     from intprod.apt_ocorrencia apo''')
            cur.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
            for rs in c_rs:
                sequencia = int(rs[0])
            return sequencia

    def listar_ocor(self):
        if (self.equip_logado == 'S'):
            con = getOracleConnection()
            cur = con.cursor()
            selectSQL = ('''select o.ati_in_sequencia,
                              a.ati_st_nome,
                              to_char(o.ati_dt_inclusao,'DD/MM/YYYY HH24:MI:ss') ati_dt_inclusao,                              
                              o.ati_in_ordem,
                              o.ati_usu_inclusao,
                              o.ati_in_tempo,
                              o.ati_in_codigo
                         from mgman.pro_atividade a,
                              intprod.apt_ocorrencia o
                        where a.ati_tab_in_codigo = o.ati_tab_in_codigo
                          and a.ati_pad_in_codigo = o.ati_pad_in_codigo
                          and a.ati_in_codigo = o.ati_in_codigo
                          and a.ati_ch_produtiva = 'I'
                          and o.ati_in_ordem = :ord_in
                          and a.ati_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in, 204, sysdate)
                          order by o.ati_in_sequencia''')
            cur.prepare(selectSQL)
            cur.execute(None, {'fil_in': self.fil_in,'ord_in':self.ordem_in})
            c_rs = cur.fetchall()
            cur.close
            con.close
            lista = []
            for rs in c_rs:
                lista.append(dict(ati_in_sequencia = int([0],
                              ati_st_nome = rs[1],
                              ati_dt_inclusao = rs[2],
                              ati_in_ordem = int(rs[3]),
                              ati_usu_inclusao = rs[4]),
                              ati_in_tempo = int(rs[5]),
                              ati_in_codigo = int(rs[6])))
            json_ocorrencias = {}
            json_ocorrencias = json.dumps(lista)
            return json_ocorrencias

    def Ins_Ocor(self, pparams):
        if (self.equip_logado == 'S'):
            v_lista = []
            v_lista.append(pparams)
            for v_obj in v_lista:
                ocorrencia = v_obj[0]
                tempo = v_obj[1]
            c_ocorrencia = json.loads(self.lis_ocor())
            sequencia = self.seq_ocorrencia()
            con = getOracleConnection()
            cur = con.cursor()
            row_now = timezone.now()
            str_now = row_now.strftime('%Y/%m/%d %H:%M:%S')
            insertTableSQL = ('''insert into intprod.apt_ocorrencia
                            (ATI_IN_SEQUENCIA,ATI_TAB_IN_CODIGO,ATI_PAD_IN_CODIGO,ATI_IN_CODIGO,ATI_DT_INCLUSAO,ATI_USU_INCLUSAO,ATI_IN_ORDEM,ATI_IN_TEMPO)
                            values
                            (:ati_in_sequencia,:ati_tab_in_codigo,:ati_pad_in_codigo,:ati_in_codigo,to_date(:ati_dt_inclusao),:ati_usu_inclusao,:ati_in_ordem,:ati_in_tempo)''')
            for v_ocor in c_ocorrencia:
                if (v_ocor['ati_in_codigo']==ocorrencia):
                    ati_tab = int(v_ocor['ati_tab_in_codigo'])
                    ati_pad = int(v_ocor['ati_pad_in_codigo'])
            cur.prepare(insertTableSQL)
            cur.execute(None, {'ati_in_sequencia': sequencia,'ati_tab_in_codigo':ati_tab, 'ati_pad_in_codigo':ati_pad,
                               'ati_in_codigo':ocorrencia,'ati_dt_inclusao':str_now,
                               'ati_usu_inclusao':self.usuario,'ati_in_ordem':self.ordem_in,'ati_in_tempo':tempo})
            c_rs = cur.commit()
            cur.close
            con.close
