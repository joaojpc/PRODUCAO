import requests

dados = {u'ATI_IN_ORDEM': 50602, u'ATI_IN_CODIGO': 103, u'ATI_DT_INCLUSAO': '2019-12-16 15:49:08', u'ATI_IN_TEMPO': 4, u'ATI_IN_SEQUENCIA': 110, u'ATI_USU_INCLUSAO': u'0000041873'}

print(dados)

response = requests.post('http://192.168.0.250/producao/ocorrencias/',dados)

