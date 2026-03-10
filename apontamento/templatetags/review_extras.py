# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import template
import datetime
from django.template.context import Context
#from django.utils import simplejson as json
import socket
import json
import sqlite3
DATABASE    = "/home/admin/prod/producao.db"

register = template.Library()

def getSqliteConnection(dbname):
    try:
        dbConn = conn = sqlite3.connect(dbname)
    except sqlite3.OperationalError:
        print ("Erro ao criar conexão com sqlite...")
    return dbConn

@register.simple_tag
def tag_equipaLogado():
    logado = False
    v_params = []
    ender_ip = socket.gethostbyname(socket.gethostname())    
    dbname = DATABASE
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    v_params.append(ender_ip)
    selectSQL = ('''select apc.*
                     from apt_controle apc
                    where apc.CTL_ST_IPADDRESS = ?
                      and apc.CTL_DT_LOGOUT is null''')
    cur.execute(selectSQL,v_params)
    eqpto_logado = cur.fetchall()
    cur.close
    con.close
    for v_logado in eqpto_logado:
        logado = True    
    return logado
