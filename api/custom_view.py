# -*- coding: utf-8 -*-
from django.utils import timezone
import cx_Oracle as cxo
import json
import socket

def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip

def getOracleConnection():
    username = 'idp'
    password = 'megamega'
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

class Baixas:
    def __init__(self):
        self.status = 'A'
        self.org_in = None
        self.fil_in = None
        self.acao_in = None
        self.usuario_in = None
        c_usu = self.apt_usuarios()
        for v_usu in c_usu:
            self.org_in = v_usu[0]
            self.fil_in = v_usu[1]
            self.usuario_in = v_usu[3]
    def bxa_usuario(self):
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        con = getOracleConnection()
        cur = con.cursor()
        cur.prepare('''select opd.org_in_codigo,
                                   opd.fil_in_codigo,
                                   opd.col_st_chapeira,
                                   opd.col_st_nome
                              from idp.apt_cadastro_colaboradores opd
                             where opd.col_st_chapeira = :usu_in 
                             order by opd.col_in_sequencia''')
        cur.execute(None, {'usu_in': self.usuario_in})
        c_users = cur.fetchall()
        cur.close
        con.close
        lista = []
        for v_rs in c_users:
            lista.append(dict(org_in_codigo = int(v_rs[0]),
                              fil_in_codigo = int(v_rs[1]),
                              col_st_chapeira = v_rs[2],
                              col_st_nome = v_rs[3]))
        usuarios ={}
        usuarios = json.dumps(lista)
        return usuarios
    def apt_usuarios(self):
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        con = getOracleConnection()
        cur = con.cursor()
        cur.execute('''select usu.org_in_codigo,
			                  usu.fil_in_codigo,
			                  usu.usu_in_codigo,
		                      usu.usu_st_usuario,
		                      usu.usu_st_senha,
                              usu.usu_st_email,
                              usu.usu_st_nome,
                              usu.usu_st_status
			             from int_cadusuarios usu''')
        usu_logado = cur.fetchall()
        return usu_logado

    def listar_baixas(self):
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        con = getOracleConnection()
        cur = con.cursor()
        cur.prepare('''select bxa.pro_in_codigo,
                              pro.pro_st_descricao,
                              bxa.pro_re_qtdlote,
                              bxa.pro_st_lote,
                              idp.adm_pck_util.f_formatacaract(bxa.pro_st_referencia) as mvs_st_referencia_desc                               
                         from idp.apt_pro_baixaestoque bxa,
                              idp.est_produtos pro
                        where pro.pro_tab_in_codigo = bxa.pro_tab_in_codigo
                          and pro.pro_pad_in_codigo = bxa.pro_pad_in_codigo
                          and pro.pro_in_codigo = bxa.pro_in_codigo
                          and bxa.mov_st_status = :status                         
                          and bxa.pro_pad_in_codigo = mgglo.pck_mega.achapadraodatabela(:fil_in,100,sysdate)''')
        cur.execute(None, {'fil_in': self.fil_in,'status': self.status})
        c_baixas = cur.fetchall()
        cur.close
        con.close
        lista = []
        for rs in c_baixas:
            lista.append(dict(pro_in_codigo = int(rs[0]),
                              pro_st_descricao = rs[1],
                              pro_re_qtdlote = float(rs[2]),
                              pro_st_lote = rs[3],
                              mvs_st_referencia_desc = rs[4]))
        json_baixas= {}
        json_baixas = json.dumps(lista)
        return json_baixas

    def apt_gerarBaixa(self):
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.acao_in,self.acao_in)
        cur.callproc('apt_intprod.p_Gera_BaixaEstoque',(sparams))
        c_cursor = ref_cursor.fetchall()
        cur.close
        con.close
        for v_ret in c_cursor:
            result = v_ret[0]
        return result

    def apt_inserirBaixa(self, pparams):
        v_listlote = []
        v_listlote.append(pparams)
        for v_obj in v_listlote:
            v_mvs_st_loteforne = v_obj[0]
            v_apt_re_quantidade = float(v_obj[1])
            v_pro_in_codigo = int(v_obj[2])
        v_fmt_st_codigo = '0'
        v_col_st_cracha = self.usuario_in
        con = getOracleConnection()
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (ref_cursor,self.org_in,self.fil_in,v_mvs_st_loteforne,v_apt_re_quantidade,v_col_st_cracha,v_fmt_st_codigo,v_pro_in_codigo)
        cur.callproc('apt_intprod.p_Insere_BaixaEstoque',(sparams))
        c_cursor = ref_cursor.fetchall()
        cur.close
        con.close
        for v_ret in c_cursor:
            result = v_ret[0]
        return result

    def itens_baixa(self):
        #con = cxo.connect('intprod/supprod@192.168.0.8:1521/megag')
        con = getOracleConnection()
        cur = con.cursor()
        ref_cursor = con.cursor()
        sparams = (self.fil_in,self.org_in,ref_cursor)
        cur.callproc('apt_intprod.apt_RetornaItensDisp',(sparams))
        c_cursor = ref_cursor.fetchall()
        cur.close
        con.close
        lista = []
        for v_ret in c_cursor:
            lista.append(dict(pro_in_codigo = int(v_ret[0]),
                              pro_st_descricao = v_ret[1],
                              mvs_re_quantidade = float(v_ret[2]),
                              mvs_st_loteforne = v_ret[3],
                              mvs_st_referenciadesc = v_ret[4],
                              mvs_st_referencia = v_ret[5]))
        json_baixas= {}
        json_baixas = json.dumps(lista)
        return json_baixas
class Login_inicial:
    def __init__(self,p_ordem,p_usuario):
        self.ender_ip = getEnderIP()
        self.ordem_in = p_ordem
        self.usuario_in = p_usuario
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select *
                         from idp.apt_equipamentos eqp
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

    def ordem(self):
        con = getOracleConnection()
        cur = con.cursor()
        selectSQL = ('''select op.org_in_codigo,
                              op.fil_in_codigo,                                     
                              op.ord_in_codigo,
                              op.ord_st_situacao        
                         from idp.pro_ordens op
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
                              ord_st_situacao = rs[4]))
        ordens= {}
        ordens = json.dumps(lista)
        return ordens
