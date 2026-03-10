# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import socket
import json
import sqlite3
import datetime
from django.utils import timezone
from producao import settings
import requests
import sys
import getmac
# reload(sys)
# sys.setdefaultencoding('utf-8')
DATABASE    = "/home/suporte/prod/producao.db"
################################################################################
'''def sqlite3.connect(dbname):
    """
        Given the name of a JDBC driver class and the url to be used
        to connect to a database, attempt to obtain a connection to
        the database.
    """
    try:
        dbConn = conn = sqlite3.connect(dbname)
    except sqlite3.OperationalError:
        print "Erro ao criar conexão com sqlite..."
    return dbConn
'''
def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip
def geturlapp(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/app/'+funcao
    #print (url_principal)
    return url_principal

def geturlapi(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/api/'+funcao
    #print (url_principal)
    return url_principal

def geturlprod(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'http://'+url_remoto+'/prod/'+funcao
    #print (url_principal)
    return url_principal

def formatar_ordem(pOrdem):
        v_ordem = pOrdem
        v_ordem_oper = None
        v_ordem_ordem = None
        v_ord_filial = None
        #print('ordem',v_ordem)
        if len(v_ordem) == 14:
            v_ordem_oper = v_ordem[-4:-1]
            v_ordem_ordem = v_ordem[5:-4]
            v_ord_filial = v_ordem[0:3]
        elif len(v_ordem) == 13:
            v_ordem_oper =v_ordem[-4:-1]
            v_ordem_ordem =v_ordem[4:-4]
            v_ord_filial =v_ordem[0:2]
        elif len(v_ordem) == 12:
            v_ordem_oper =v_ordem[-4:-1]
            v_ordem_ordem =v_ordem[3:-4]
            v_ord_filial =v_ordem[0:1]
        else:
            v_ordem_ordem =v_ordem[3:-4]

        l_retorno = []
        l_retorno.append(dict(ordem = int(v_ordem_ordem),
                              filial = int(v_ord_filial),
                            operacao = int(v_ordem_oper)))
        v_retorno ={}
        v_retorno = json.dumps(l_retorno)
        return  v_retorno
    
class User_logado_sqlite:
    def __init__(self,p_usuario,p_ordem):
        self.ord_filial = None
        self.ordem_in = None
        self.ord_operacao = None
        self.ender_ip = getEnderIP()
        #getEnderIP()
        self.dbname = DATABASE
        self.usuario_in = p_usuario
        v_ordem = p_ordem
        r_ordem = json.loads(formatar_ordem(v_ordem))
        for v_ord in r_ordem:
            self.ordem_in = v_ord['ordem']
            self.ord_filial = v_ord['filial']
            self.ord_operacao = v_ord['operacao']
        v_preparar = Listar_opcoes_sqlite()
        equipamento = json.loads(v_preparar.lis_controle_sqlite())
        for v_equip in equipamento:
            self.ini_filial = v_equip['eqp_in_filial']
            self.usuario_in =v_equip['ctl_in_usuario']
            self.seq_controle = v_equip['ctl_in_codigo']
class Listar_opcoes_sqlite:
    def __init__(self):
        self.ender_ip = getEnderIP()
        self.dbname = DATABASE
        self.equipamento_cad = 'S'
        c_dados = json.loads(self.lis_controle_sqlite())
        for v_ini in c_dados:
            self.ini_filial = v_ini['eqp_in_filial']
            self.ini_ordem = v_ini['ord_in_codigo']
            self.ini_usuario = v_ini['ctl_in_usuario']
            self.equipamento_cad = 'S'
    def equipaLogado_sqlite(self):
        logado = False
        v_params = []
        conn = sqlite3.connect(self.dbname)
        v_params.append(self.ender_ip)    
        selectSQL = ('''select apc.*
                     from apt_controle apc
                    where apc.ctl_st_ipaddress = ?
                      and apc.ctl_dt_logout is null''')
        stmt = conn.execute(selectSQL,v_params)
        #stmt.setString(1, self.ender_ip)
        c_rs = stmt.fetchall()
        stmt.close
        conn.close
        for rs in c_rs:
            logado = True
        return logado
    def lis_controle_sqlite(self):
        con = sqlite3.connect(self.dbname)
        v_params = []
        v_params.append(self.ender_ip)
        #print (self.ender_ip)
        selectSQL = ('''select t.eqp_in_codigo,
                                      t.eqp_st_name,
                                      t.eqp_st_ipaddress,
                                      t.eqp_in_filial,
                                      t.maq_in_codigo,
                                      c.ctl_st_usuario,
                                      c.ord_in_codigo,
                                      c.ctl_dt_login,
                                      c.ctl_in_codigo
                                 from apt_equipamentos t,
                                      apt_controle c
                                where c.ctl_st_ipaddress = t.eqp_st_ipaddress
                                  and c.ctl_st_ipaddress = ?
                                  and c.ctl_dt_logout is null''')        
        cur = con.execute(selectSQL,v_params)
        #cur.setString(1, self.ender_ip)
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(eqp_in_codigo = rs[0],
                              eqp_st_name = rs[1],
                              eqp_st_ipaddress = rs[2],
                              eqp_in_filial = rs[3],
                              maq_in_codigo = rs[4],
                              ctl_in_usuario= rs[5],
                              ord_in_codigo= rs[6],
                              ctl_login = rs[7],
                              ctl_in_codigo = rs[8]))
        json_litens ={}
        json_litens = json.dumps(lista)
        return json_litens
    def lis_resumo_sqlite(self):
        con = sqlite3.connect(self.dbname)
        v_params = []
        v_params.append(self.ender_ip)
        selectSQL = ('''select t.ctl_st_ipaddress,
                               t.fil_in_codigo,
                               c.ctl_st_usuario,
                               c.ord_in_codigo,
                               c.ctl_dt_login,
                               sum(t.ctl_in_produtividade) as ctl_in_produtividade,
                               sum(t.ctl_in_consenergia) as ctl_in_consenergia,
                               max(t.ctl_dt_registro) as ctl_dt_registro
                              from apt_reg_medidores t,
                                   apt_controle c
                             where c.ctl_st_ipaddress = t.ctl_st_ipaddress
                               and c.ctl_st_ipaddress = ?
			       and t.fil_in_codigo > 0
			       and c.ctl_dt_logout is null
			       and strftime('%Y-%m-%d',replace(t.ctl_dt_registro,'/','-')) = strftime('%Y-%m-%d',date('now'))
                          group by t.fil_in_codigo,
				   t.ctl_st_ipaddress,
				   c.ctl_st_usuario,
				   c.ctl_dt_login,
			           c.ord_in_codigo''')
        selectSQL2 = ('''select t.ctl_in_sequencia,
                                      t.ctl_in_produtividade,
                                      t.ctl_in_consenergia,
                                      t.ctl_st_ipaddress,
                                      t.fil_in_codigo,
                                      t.ctl_dt_registro,
                                      c.ctl_st_usuario,
                                      c.ord_in_codigo,
                                      c.ctl_dt_login,
                                      c.ctl_in_codigo
                                 from apt_reg_medidores t,
                                      apt_controle c
                                where c.ctl_st_ipaddress = t.ctl_st_ipaddress
                                  and c.ctl_st_ipaddress = ?
                                  and c.ctl_dt_logout is null
                                  and t.ctl_in_sequencia =
                                      (select max( a.ctl_in_sequencia)
                                         from apt_reg_medidores a
                                        where a.ctl_st_ipaddress = ?)''')
        cur = con.execute(selectSQL,v_params)
        #cur.setString(1, self.ender_ip)
        c_rs = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_rs:
            lista.append(dict(ctl_in_produtividade = rs.getString(6),
                              ctl_in_consenergia = rs.getString(7),
                              eqp_st_ipaddress = rs.getString(1),
                              eqp_in_filial = rs.getInt(2),
                              ctl_dt_registro = rs.getString(8),
                              ctl_in_usuario= rs.getString(3),
                              ord_in_codigo= rs.getInt(4),
                              ctl_login = rs.getString(5)))
        json_litens ={}
        json_litens = json.dumps(lista)
        return json_litens    

class Login_inicial_sqlite:
    def __init__(self,p_ordem,p_usuario,ip):
        self.ord_filial = None
        self.ordem_in = None
        self.ord_operacao = None
        self.equipamento_cad = 'N'
        self.ender_ip = ip
        #getEnderIP()
        self.dbname = DATABASE
        self.usuario_in = p_usuario
        self.ordem_st_extenso = p_ordem
        r_ordem = json.loads(formatar_ordem(self.ordem_st_extenso))
        for v_ord in r_ordem:
            self.ordem_in = v_ord['ordem']
            self.ord_filial = v_ord['filial']
            self.ord_operacao = v_ord['operacao']

    def apt_usuario_sqlite(self):
        v_params = []
        usuarios = {}
        lista = []
        if self.equipamento_cad == 'N':
            con = sqlite3.connect(self.dbname)
            v_params.append(self.usuario_in)
            selectSQL = ('''select opd.opd_in_codigo,
                              opd.opd_st_cracha,
                              opd.opd_st_nome
                         from Apt_Pro_CadOperador opd
                         where opd.opd_st_cracha = ?
                       order by opd_in_codigo''')
            cur = con.execute(selectSQL,v_params)
            #cur.setString(1, self.usuario_in)
            c_rs = cur.fetchall()
            cur.close
            con.close
            if c_rs is None:
                print ('Vazio')
            for rs in c_rs:
                lista.append(dict(opd_in_codigo = rs[0],
                              opd_st_alternativo = rs[1],
                              opd_st_descricao = rs[2]))
        else:
            lista.append(dict(opd_in_codigo = None,
                              opd_st_alternativo = None,
                              opd_st_descricao = None))
        usuarios = json.dumps(lista)
        return usuarios

    def equipamento_cadastrado(self):
        v_params = []
        con = sqlite3.connect(self.dbname)
        v_params.append(self.ender_ip)
        selectSQL = ('''select *
                         from apt_equipamentos eqp
                        where eqp.eqp_st_ipaddress = ?''')
        cur = con.execute(selectSQL,v_params)
        #cur.setString(1, self.ender_ip)
        c_rs = cur.fetchall()
        cur.close
        con.close
        v_equipamento_cad = 'N'
        for rs in c_rs:
            v_equipamento_cad = 'S'
        return v_equipamento_cad

    def seq_initapt_sqlite(self):
        sequencia = 1
        con = sqlite3.connect(self.dbname)
        selectSQL =('''select CASE WHEN apc.ctl_in_codigo IS NULL THEN 1 ELSE
                                      max(apc.ctl_in_codigo)+1 END as ctl_in_codigo
                            from apt_controle apc''')
        cur = con.execute(selectSQL)
        c_rs = cur.fetchall()
        cur.close
        con.close
        for rs in c_rs:
            if not rs[0] is None:
                sequencia = rs[0]
            else:
                sequencia = 1
        return sequencia
    
    def userLogado_sqlite(self):
        logado = False
        if self.usuario_in:
            con = sqlite3.connect(self.dbname)
            v_lista = []
            v_lista.append(self.usuario_in)
            v_lista.append(self.ordem_st_extenso)
            selectSQL = ('''select apc.*
                              from apt_controle apc
                             where apc.ctl_st_usuario = ?
                               and apc.ord_st_extenso = ?
                               and apc.ctl_dt_logout is null''')
            cur = con.execute(selectSQL,v_lista)
            c_rs = cur.fetchall()
            #print(c_rs)
            cur.close
            con.close
            lista = []
            if c_rs:
                for rs in c_rs:
                    lista.append(dict(ctl_in_codigo = int(rs[0]),
                                      logado = True))
            else:
                lista.append(dict(ctl_in_codigo = None,
                                  logado = False))
            usuarios = json.dumps(lista)
        return usuarios
    def descontar_sqlite(self):
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        #row_now = timezone.now()
        #str_now = row_now.strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        str_now = now.strftime('%Y-%m-%d %H:%M:%S')
        v_lista = []
        v_lista.append(str_now)
        v_lista.append(self.usuario_in)
        v_lista.append(self.ordem_st_extenso)
        #print(v_lista)
        #v_lista.append(self.seq_controle)
        #print (self.usuario_in, self.seq_controle,str_now)
        ExecSQL =('''update apt_controle
                          set ctl_dt_logout = ?
                        where ctl_st_usuario = ?
                          and ord_st_extenso = ?''')
        cur.execute(ExecSQL,v_lista)
        con.commit()
        #cur.setString(1, str_now)
        #cur.setString(2, self.usuario_in)
        #cur.setInt(3, self.seq_controle)
        #cur.executeUpdate()
        cur.close
        con.close
        return True
    def conectar_sqlite(self):
        v_params = []
        v_iniciar = []
        v_conect = {}
        maquina = None
        maquina_id = ''
        ordem_id = ''
        now = datetime.datetime.now()
        str_now = now.strftime('%Y-%m-%d %H:%M:%S')
        sequencia = self.seq_initapt_sqlite()
        v_params.append(sequencia)
        v_params.append(self.usuario_in)
        v_params.append(self.ordem_in)
        v_params.append(str_now)
        v_params.append(self.ender_ip)
        v_params.append(self.ordem_st_extenso)
        funcao = 'ordens/'
        app_url = geturlapp(funcao)
        payload = {'ord_in_codigo': self.ordem_in,'fil_in_codigo': self.ord_filial}
        try:
            cur_ord = requests.get(app_url, params=payload).json()
            if not (cur_ord):
                v_listOrd = []
                v_listOrd.append(None)
                v_listOrd.append(self.ord_filial)
                v_listOrd.append(self.ordem_in)
                ini = IntOrdens()
                ini.buscaOrdens(v_listOrd)
            cur_ord = requests.get(app_url, params=payload).json()
            for rs_ord in cur_ord:
                ordem_id = rs_ord['ORD_ST_ID']
        except:
            pass
        funcao = 'equipamento/'
        app_url = geturlprod(funcao)
        payload = {'cliente': v_params[4]}
        try:
            cr_printer = requests.get(app_url, params=payload).json()
            for rs_printer in cr_printer:
                maquina = rs_printer['MAQ_IN_CODIGO']
        except:
            pass
        if maquina is not None:
            funcao = 'maquina/'
            app_url = geturlprod(funcao)
            payload = {'cmaq_seq': maquina}
            try:
                cr_maquina = requests.get(app_url, params=payload).json()
                if cr_maquina:
                    for rs_maquina in cr_maquina:
                        maquina_id = rs_maquina['CMAQ_ST_ID']
            except:
                pass        
        funcao = 'controleApt/'
        uri = geturlprod(funcao)
        dados = data = {"CTL_IN_CODIGO": sequencia,
                        "CTL_ST_USUARIO": self.usuario_in,
                        "ORD_IN_CODIGO": self.ordem_in,
                        "CTL_DT_LOGIN": str_now,
                        "CTL_ST_IPADDRESS": self.ender_ip,
                        "ORD_ST_EXTENSO": self.ordem_st_extenso,
                        "CTL_ST_STATUS": 'A',
                        "FIL_IN_CODIGO": self.ord_filial,
                        "ORD_ST_ID":ordem_id,
                        "CMAQ_ST_ID":maquina_id}
        try:
            response = requests.post(uri, data=dados)
            v_iniciar.append(dict(ctl_in_codigo = sequencia,
                                   logado = True))
        except:
            v_iniciar.append(dict(ctl_in_codigo = None,
                                   logado = False))
        v_conect = json.dumps(v_iniciar)
        return v_conect
        '''con = sqlite3.connect(self.dbname)
        insertTableSQL = ('''
        '''insert into apt_controle
                            (CTL_IN_CODIGO,CTL_ST_USUARIO,ORD_IN_CODIGO,CTL_DT_LOGIN,CTL_ST_IPADDRESS,ORD_ST_EXTENSO)
                            values
                            (?,?,?,?,?,?)'''
        ''')
        con.execute(insertTableSQL,v_params)
        con.commit()
        con.close'''
class IntAPI_sqlite:
    def __init__(self, pParams):
        self.funcao = None
        self.uri = None        
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        self.dbname = DATABASE
    def listar_producao_sqlite(self):
        self.funcao = 'apontamentos/'
        self.uri = geturlapp(self.funcao)
        #print(self.uri)
        self.ordem_in = pParams[0]
        self.fil_in = pParams[1]
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_producao= {}
        json_producao = json.dumps(vRes_json)
        return json_producao

    def itens_ordem_sqlite(self):
        json_Itens= {}
        self.funcao = 'ordens/'
        self.uri = geturlapp(self.funcao)        
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        c_appitens = requests.get(self.uri, params=payload).json()
        if c_appitens:
            for r_appitens in c_appitens:
                d_tens = r_appitens['PRO_ST_ITENS']
                json_Itens = json.dumps(d_tens)
        #print(json_Itens)
        return json_Itens
    def listar_ocorrencias_sqlite(self):
        self.funcao = 'atividade/'
        self.uri = geturlapp(self.funcao)
        payload = {'ordem': self.ordem_in,'filial': self.fil_in}
        vresponse = requests.get(self.uri, params=payload)
        vRes_json = json.loads(vresponse.content)
        json_ocorrencias= {}
        json_ocorrencias = json.dumps(vRes_json)
        return json_ocorrencias
    
    def seq_movdem_sqlite(self):
        v_seqdem = 0
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apd.mov_in_sequencia IS NULL THEN 1 ELSE
                                      max(apd.mov_in_sequencia)+1 END as mov_in_sequencia
                            from Apt_Pro_Demandas apd''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_seqdem = 1
                else:
                    v_seqdem = int(rs[0])
        return v_seqdem

    def seq_movprod_sqlite(self):
        v_sequencia = 0
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apd.apt_in_sequencia IS NULL THEN 1 ELSE
                                      max(apd.apt_in_sequencia)+1 END as apt_in_sequencia
                            from apt_apontaordem apd''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_sequencia = 1
                else:
                    v_sequencia = int(rs[0])
        return v_sequencia

    def seq_ocor_sqlite(self):
        try:
            con = sqlite3.connect(self.dbname)
            selectSQL =('''select CASE WHEN apo.ati_in_sequencia IS NULL THEN 1 ELSE
                                      max(apo.ati_in_sequencia)+1 END as ati_in_sequencia
                            from Apt_Ocorrencia apo''')
            cur = con.execute(selectSQL)
            c_rs = cur.fetchall()
            cur.close
            con.close
        except:
            c_rs = [(0,)]
        v_seqOcorrencia = 0
        if c_rs:
            for rs in c_rs:
                if rs[0] is None:
                    v_seqOcorrencia = 1
                else:
                    v_seqOcorrencia = int(rs[0])
        return v_seqOcorrencia
