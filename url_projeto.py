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
def geturlapp(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https//'+url_remoto+'/app/'+funcao
    return url_principal
def geturlapi(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https://'+url_remoto+'/api/'+funcao
    return url_principal
def geturlprod(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https://'+url_remoto+'/prod/'+funcao
    return url_principal
def geturlest(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https://'+url_remoto+'/est/'+funcao
    return url_principal
def geturlinv(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https://'+url_remoto+'/inv/'+funcao
    return url_principal
def geturlrcb(funcao):
    url_remoto = settings.URL_SQLITE
    url_principal = 'https://'+url_remoto+'/rcb/'+funcao
    return url_principal