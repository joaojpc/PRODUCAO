# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.

# -*- coding: utf-8 -*-
# Create your tests here.
from java.sql import *
from oracle.jdbc import OracleTypes
import socket
import json
#import json
#from pandas import json


def getOracleConnection():
    jdbc_url = "jdbc:oracle:thin:@192.168.0.8:1521:megag"
    username = "intprod"
    password = "supprod"
    conn = DriverManager.getConnection(jdbc_url, username, password)
    return conn;

conn = getOracleConnection()
# prep = "{ call pck_sptest.procout(?) }"
prep = "{ call apt_intprod.apt_retornacaracteristica(?,?,?) }"
cs = conn.prepareCall(prep)
cs.setInt(1, 302)
cs.setInt(2, 230)
cs.registerOutParameter(3, OracleTypes.CURSOR)
cs.execute()
ret = cs.getObject(3)
#print (ret)
#while ret.next():
#    print(ret.getInt(1))
#    print(ret.getString(2))
#    print(ret.getString(3))
#    print(ret.getString(4))
#    print(ret.getString(5))
#    print(ret.getString(6))
#    print(ret.getInt(7))
#    print(ret.getInt(8))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ender_ip = (s.getsockname()[0])
s.close()

print('ender:'+ ender_ip)
selectSQL = ('''select apc.*
                     from intprod.apt_controle apc
                    where apc.ctl_maq_ip = ?
                      and apc.ctl_logout is null''')
stmt = conn.prepareStatement(selectSQL)
stmt.setString(1, ender_ip)
rs = stmt.executeQuery()
emp = {}
result = {}
lista = []
while rs.next():
    #print(rs.getString(5))
    emp.update({
        'ctl_in_codigo': rs.getInt(1),
        'ctl_in_usuario': rs.getString(2),
        'ord_in_codigo': rs.getInt(3),
        'ctl_login': rs.getDate(4),
        'ctl_maq_ip': rs.getString(5),
        'ctl_logout': rs.getDate(6),
        'ctl_in_consenergia': rs.getInt(7),
        'ctl_in_produtividade': rs.getInt(8),
    })
    #lista.append({'ctl_in_codigo': rs.getInt(1),
    #    'ctl_in_usuario': rs.getString(2),
    #    'ord_in_codigo': rs.getInt(3),
    #    'ctl_login': rs.getString(4),
    #    'ctl_maq_ip': rs.getString(5),
    #    'ctl_logout': rs.getString(6),
    #    'ctl_in_consenergia': rs.getInt(7),
    #    'ctl_in_produtividade': rs.getInt(8)})

    lista.append(dict(ctl_in_codigo = rs.getInt(1),
                              ctl_in_usuario = rs.getString(2),
                              ord_in_codigo = rs.getInt(3),
                              ctl_login = rs.getString(4),
                              ctl_maq_ip = rs.getString(5),
                              ctl_logout= rs.getString(6),
                              ctl_in_consenergia= rs.getInt(7),
                              ctl_in_produtividade = rs.getInt(8)))

    #result= json.dumps(lista)

#jsondata = '{"number": 1.573937639}'


dict_litens ={}
dict_litens= json.dumps(lista)

    #result.update(lista)
#print (result)
#print json.loads(dict_litens)

csaida = json.loads(dict_litens)
for v_saida in csaida:
    print(v_saida['ctl_in_codigo'])

#for v_ini in csaida:
#     if v_ini['ctl_maq_ip']:
#         print v_ini['ctl_maq_ip']


#print  emp

label2 ="""
^XA~TA000~JSN^LT0^MNW^MTD^PON^PMN^LH0,0^JMA^PR4,4~SD15^JUS^LRN^CI0^XZ 
^XA
^MMT
^PW799
^LL0799
^LS0
^FO0,32^GFA,03456,03456,00036,:Z64:
eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50
^FO3,792^GB791,0,4^FS
^FO793,5^GB0,790,5^FS
^FO2,4^GB0,789,5^FS
^FO3,3^GB791,0,4^FS
^FO508,156^GB0,78,4^FS
^FO164,516^GB0,79,4^FS
^FO435,515^GB0,280,4^FS
^FO282,437^GB0,79,4^FS
^FO281,6^GB0,354,4^FS
^FO8,594^GB428,0,4^FS
^FO9,516^GB783,0,4^FS
^FO9,435^GB783,0,4^FS
^FO8,355^GB783,0,4^FS
^FO9,233^GB782,0,4^FS
^FO8,153^GB783,0,4^FS
^FT292,269^A0N,28,28^FH\^FDDESCRI\80\C7O DO PRODUTO^FS
^FT130,631^A0N,28,28^FH\^FDESPESSURA^FS
^FT238,551^A0N,28,28^FH\^FDPALLET^FS
^FT17,551^A0N,28,28^FH\^FDLARGURA^FS
^FT295,471^A0N,28,28^FH\^FDCOMPRADOR^FS
^FT15,470^A0N,28,28^FH\^FDNR FORNECEDOR^FS
^FT12,390^A0N,28,28^FH\^FDOBSERVA\80\E5ES^FS
^FT37,266^A0N,24,24^FH\^FDCOD PRODUTO^FS
^FT524,186^A0N,24,24^FH\^FDDATA PRODU\80\C7O^FS
^FT11,185^A0N,24,24^FH\^FDM3^FS
^FT523,227^A0N,34,33^FH\^FD23/02/2018^FS
^FT343,228^A0N,34,33^FH\^FD42552^FS
^FT148,730^A0N,79,79^FH\^FD25^FS
^FT171,590^A0N,34,33^FH\^FD3,0 x 1,3 m^FS
^FT48,589^A0N,34,33^FH\^FD100^FS
^FT289,510^A0N,34,33^FH\^FDJo\C6o Paulo Castro^FS
^FT86,509^A0N,34,33^FH\^FD46450^FS
^FT12,420^A0N,24,24^FH\^FDlote 10235/10236 Verissimo/Ivanildo^FS
^FT288,306^A0N,34,33^FH\^FDGUAIUVIRA TABICADA^FS
^FT288,348^A0N,34,33^FH\^FD25X100 MM^FS
^FT80,315^A0N,34,33^FH\^FD7114^FS
^FT14,227^A0N,34,33^FH\^FD1,700^FS
^FT491,584^A0N,60,60^FH\^FD026974^FS
^FT354,186^A0N,24,24^FH\^FDNR OP^FS
^FT318,119^A0N,48,86^FH\^FDGUAIUVIRA^FS
^FT446,46^A0N,32,31^FH\^FDMADEIRA^FS
^BY1,3,96^FT500,718^B2N,,Y,N
^FD2018082310203040508090^FS
^PQ1,0,1,Y^XZ
"""
label="""
^XA~TA000~JSN^LT0^MNW^MTD^PON^PMN^LH0,0^JMA^PR4,4~SD15^JUS^LRN^CI0^XZ
^XA
^MMT
^PW799
^LL0799
^LS0
^FO0,32^GFA,03456,03456,00036,:Z64:
eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50
^FO3,792^GB791,0,4^FS
^FO793,5^GB0,790,5^FS
^FO2,4^GB0,789,5^FS
^FO3,3^GB791,0,4^FS
^FO508,156^GB0,78,4^FS
^FO164,516^GB0,79,4^FS
^FO435,515^GB0,280,4^FS
^FO282,437^GB0,79,4^FS
^FO281,6^GB0,354,4^FS
^FO8,594^GB428,0,4^FS
^FO9,516^GB783,0,4^FS
^FO9,435^GB783,0,4^FS
^FO8,355^GB783,0,4^FS
^FO9,233^GB782,0,4^FS
^FO8,153^GB783,0,4^FS
^FT292,269^A0N,28,28^FH\^FDDESCRI\80\C7O DO PRODUTO^FS
^FT130,631^A0N,28,28^FH\^FDESPESSURA^FS
^FT238,551^A0N,28,28^FH\^FDPALLET^FS
^FT17,551^A0N,28,28^FH\^FDLARGURA^FS
^FT295,471^A0N,28,28^FH\^FDCOMPRADOR^FS
^FT15,470^A0N,28,28^FH\^FDNR FORNECEDOR^FS
^FT12,390^A0N,28,28^FH\^FDOBSERVA\80\E5ES^FS
^FT37,266^A0N,24,24^FH\^FDCOD PRODUTO^FS
^FT524,186^A0N,24,24^FH\^FDDATA PRODU\80\C7O^FS
^FT11,185^A0N,24,24^FH\^FDM3^FS
^FT523,227^A0N,34,33^FH\^FD23/02/2018^FS
^FT343,228^A0N,34,33^FH\^FD42552^FS
^FT148,730^A0N,79,79^FH\^FD25^FS
^FT171,590^A0N,34,33^FH\^FD3,0 x 1,3 m^FS
^FT48,589^A0N,34,33^FH\^FD100^FS
^FT289,510^A0N,34,33^FH\^FDJo\C6o Paulo Castro^FS
^FT86,509^A0N,34,33^FH\^FD46450^FS
^FT12,420^A0N,24,24^FH\^FDlote 10235/10236 Verissimo/Ivanildo^FS
^FT288,306^A0N,34,33^FH\^FDGUAIUVIRA TABICADA^FS
^FT288,348^A0N,34,33^FH\^FD25X100 MM^FS
^FT80,315^A0N,34,33^FH\^FD7114^FS
^FT14,227^A0N,34,33^FH\^FD1,700^FS
^FT491,584^A0N,60,60^FH\^FD026974^FS
^FT354,186^A0N,24,24^FH\^FDNR OP^FS
^FT318,119^A0N,48,86^FH\^FDGUAIUVIRA^FS
^FT446,46^A0N,32,31^FH\^FDMADEIRA^FS
^BY1,2,96^FT458,721^B3N,N,,Y,N
^FD2018082310203040508090^FS
^PQ1,0,1,Y^XZ
"""

label3 = """
^XA~TA000~JSN^LT0^MNA^MTD^PON^PMN^LH0,0^JMA^PR4,4~SD15^JUS^LRN^CI0^XZ
^XA
^PW799
^LL0799
^LS0
^FO0,32^GFA,03456,03456,00036,:Z64:
eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50
^FO3,792^GB791,0,4^FS
^FO793,5^GB0,790,5^FS
^FO2,4^GB0,789,5^FS
^FO3,3^GB791,0,4^FS
^FO508,156^GB0,78,4^FS
^FO164,516^GB0,79,4^FS
^FO435,515^GB0,280,4^FS
^FO282,437^GB0,79,4^FS
^FO281,6^GB0,354,4^FS
^FO8,594^GB428,0,4^FS
^FO9,516^GB783,0,4^FS
^FO9,435^GB783,0,4^FS
^FO8,355^GB783,0,4^FS
^FO9,233^GB782,0,4^FS
^FO8,153^GB783,0,4^FS
^FT292,269^A0N,28,28^FH\^FDDESCRI\80\C7O DO PRODUTO^FS
^FT130,631^A0N,28,28^FH\^FDESPESSURA^FS
^FT238,551^A0N,28,28^FH\^FDPALLET^FS
^FT17,551^A0N,28,28^FH\^FDLARGURA^FS
^FT295,471^A0N,28,28^FH\^FDCOMPRADOR^FS
^FT15,470^A0N,28,28^FH\^FDNR FORNECEDOR^FS
^FT12,390^A0N,28,28^FH\^FDOBSERVA\80\E5ES^FS
^FT37,266^A0N,24,24^FH\^FDCOD PRODUTO^FS
^FT524,186^A0N,24,24^FH\^FDDATA PRODU\80\C7O^FS
^FT11,185^A0N,24,24^FH\^FDM3^FS
^FT523,227^A0N,34,33^FH\^FD23/02/2018^FS
^FT343,228^A0N,34,33^FH\^FD42552^FS
^FT148,730^A0N,79,79^FH\^FD25^FS
^FT171,590^A0N,34,33^FH\^FD3,0 x 1,3 m^FS
^FT48,589^A0N,34,33^FH\^FD100^FS
^FT289,510^A0N,34,33^FH\^FDJo\C6o Paulo Castro^FS
^FT86,509^A0N,34,33^FH\^FD18410^FS
^FT12,420^A0N,24,24^FH\^FDlote 10235/10236 Verissimo/Ivanildo^FS
^FT288,306^A0N,34,33^FH\^FDGUAIUVIRA TABICADA^FS
^FT288,348^A0N,34,33^FH\^FD25X100 MM^FS
^FT80,315^A0N,34,33^FH\^FD7114^FS
^FT14,227^A0N,34,33^FH\^FD1,700^FS
^FT491,584^A0N,60,60^FH\^FD048559^FS
^FT354,186^A0N,24,24^FH\^FDNR OP^FS
^FT318,119^A0N,48,86^FH\^FDGUAIUVIRA^FS
^FT446,46^A0N,32,31^FH\^FDMADEIRA^FS
^BY1,2,96^FT458,721^B3N,N,,Y,N
^FO460,610^BY2
^BCN,100,Y,N,N
^FD2018111200018410048559^FS
^PQ1,0,1,Y^XZ
"""
label4 = """
^XA
^PW799
^LL0799
^LS0
^FO0,32^GFA,03456,03456,00036,:Z64:
eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50
^FO3,792^GB791,0,4^FS
^FO793,5^GB0,790,5^FS
^FO2,4^GB0,789,5^FS
^FO3,3^GB791,0,4^FS
^FO508,156^GB0,78,4^FS
^FO150,516^GB0,79,4^FS
^FO306,515^GB0,280,4^FS
^FO282,437^GB0,79,4^FS
^FO282,6^GB0,354,4^FS
^FO8,594^GB300,0,4^FS
^FO9,516^GB783,0,4^FS
^FO9,435^GB783,0,4^FS
^FO8,355^GB783,0,4^FS
^FO9,233^GB782,0,4^FS
^FO8,153^GB783,0,4^FS
^FT292,269^A0N,28,28^FH\^FDDESCRI\80\C7O DO PRODUTO^FS
^FT100,631^A0N,28,28^FH\^FDESPESSURA^FS
^FT178,551^A0N,28,28^FH\^FDPALLET^FS
^FT17,551^A0N,28,28^FH\^FDLARGURA^FS
^FT295,471^A0N,28,28^FH\^FDCOMPRADOR^FS
^FT15,470^A0N,28,28^FH\^FDNR FORNECEDOR^FS
^FT12,390^A0N,28,28^FH\^FDOBSERVA\80\E5ES^FS
^FT37,266^A0N,24,24^FH\^FDCOD PRODUTO^FS
^FT524,186^A0N,24,24^FH\^FDDATA PRODU\80\C7O^FS
^FT11,185^A0N,24,24^FH\^FDM3^FS
^FT523,227^A0N,34,33^FH\^FD23/02/2018^FS
^FT343,228^A0N,34,33^FH\^FD42552^FS
^FT138,730^A0N,79,79^FH\^FD25^FS
^FT165,590^A0N,34,33^FH\^FD3,0 x 1,3 m^FS
^FT50,589^A0N,34,33^FH\^FD100^FS
^FT289,510^A0N,34,33^FH\^FDJo\C6o Paulo Castro^FS
^FT86,509^A0N,34,33^FH\^FD46450^FS
^FT12,420^A0N,24,24^FH\^FDlote 10235/10236 Verissimo/Ivanildo^FS
^FT288,306^A0N,34,33^FH\^FDGUAIUVIRA TABICADA^FS
^FT288,348^A0N,34,33^FH\^FD25X100 MM^FS
^FT80,315^A0N,34,33^FH\^FD7114^FS
^FT14,227^A0N,34,33^FH\^FD1,700^FS
^FT491,584^A0N,60,60^FH\^FD026974^FS
^FT354,186^A0N,24,24^FH\^FDNR OP^FS
^FT318,119^A0N,48,86^FH\^FDGUAIUVIRA^FS
^FT446,46^A0N,32,31^FH\^FDMADEIRA^FS
^FO318,620^BY2
^BCN,100,Y,N,N
^FD26974^FS
^PQ1,0,1,Y^XZ
"""

v_un = 'M3'
v_data = '23/02/2018'
v_ordem = '42552'
v_espessura ='25'
v_codbar = '2018122100018540049793'
v_largura = '100'
v_pallet = '3,0 x 1,3 m'
v_comprador = 'João Paulo Castro'
v_documento = '46450'
v_obs = 'lote 10235/10236 Verissimo/Ivanildo'
v_descricao = 'GUAIUVIRA TABICADA'
v_descricao2 = '25X100 MM'
v_item = '7114'
v_seqlote = '026974'
v_madeira = 'GUAIUVIRA'


label5 = '^XA'+'\n'
label5 +='^PW799'+'\n'
label5 +='^LL0799'+'\n'
label5 +='^LS0'+'\n'
label5 +='^FO0,32^GFA,03456,03456,00036,:Z64:'+'\n'
label5 +='eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50'+'\n'
label5 +='^FO3,792^GB791,0,4^FS'+'\n'
label5 +='^FO793,5^GB0,790,5^FS'+'\n'
label5 +='^FO2,4^GB0,789,5^FS'+'\n'
label5 +='^FO3,3^GB791,0,4^FS'+'\n'
label5 +='^FO508,156^GB0,78,4^FS'+'\n'
label5 +='^FO150,516^GB0,79,4^FS'+'\n'
label5 +='^FO306,515^GB0,280,4^FS'+'\n'
label5 +='^FO282,437^GB0,79,4^FS'+'\n'
label5 +='^FO282,6^GB0,354,4^FS'+'\n'
label5 +='^FO8,594^GB300,0,4^FS'+'\n'
label5 +='^FO9,516^GB783,0,4^FS'+'\n'
label5 +='^FO9,435^GB783,0,4^FS'+'\n'
label5 +='^FO8,355^GB783,0,4^FS'+'\n'
label5 +='^FO9,233^GB782,0,4^FS'+'\n'
label5 +='^FO8,153^GB783,0,4^FS'+'\n'
label5 +='^FT292,269^A0N,28,28^FH\^FDDESCRI\80\C7O DO PRODUTO^FS'+'\n'
label5 +='^FT100,631^A0N,28,28^FH\^FDESPESSURA^FS'+'\n'
label5 +='^FT178,551^A0N,28,28^FH\^FDPALLET^FS'+'\n'
label5 +='^FT17,551^A0N,28,28^FH\^FDLARGURA^FS'+'\n'
label5 +='^FT295,471^A0N,28,28^FH\^FDCOMPRADOR^FS'+'\n'
label5 +='^FT15,470^A0N,28,28^FH\^FDNR FORNECEDOR^FS'+'\n'
label5 +='^FT12,390^A0N,28,28^FH\^FDOBSERVA\80\E5ES^FS'+'\n'
label5 +='^FT37,266^A0N,24,24^FH\^FDCOD PRODUTO^FS'+'\n'
label5 +='^FT524,186^A0N,24,24^FH\^FDDATA PRODU\80\C7O^FS'+'\n'
label5 +='^FT11,185^A0N,24,24^FH\^FD'+v_un+'^FS'+'\n'
label5 +='^FT523,227^A0N,34,33^FH\^FD'+v_data+'^FS'+'\n'
label5 +='^FT343,228^A0N,34,33^FH\^FD'+v_ordem+'^FS'+'\n'
label5 +='^FT138,730^A0N,79,79^FH\^FD'+v_espessura+'^FS'+'\n'
label5 +='^FT165,590^A0N,34,33^FH\^FD'+v_pallet+'^FS'+'\n'
label5 +='^FT50,589^A0N,34,33^FH\^FD'+v_largura+'^FS'+'\n'
label5 +='^FT289,510^A0N,34,33^FH\^FD'+v_comprador+'^FS'+'\n'
label5 +='^FT86,509^A0N,34,33^FH\^FD'+v_documento+'^FS'+'\n'
label5 +='^FT12,420^A0N,24,24^FH\^FD'+v_obs+'^FS'+'\n'
label5 +='^FT288,306^A0N,34,33^FH\^FD'+v_descricao+'^FS'+'\n'
label5 +='^FT288,348^A0N,34,33^FH\^FD'+v_descricao2+'^FS'+'\n'
label5 +='^FT80,315^A0N,34,33^FH\^FD'+v_item+'^FS'+'\n'
label5 +='^FT14,227^A0N,34,33^FH\^FD1,700^FS'+'\n'
label5 +='^FT491,584^A0N,60,60^FH\^FD'+v_seqlote+'^FS'+'\n'
label5 +='^FT354,186^A0N,24,24^FH\^FDNR OP^FS'+'\n'
label5 +='^FT318,119^A0N,48,86^FH\^FD'+v_madeira+'^FS'+'\n'
label5 +='^FT446,46^A0N,32,31^FH\^FDMADEIRA^FS'+'\n'
label5 +='^FO460,770^FD'+v_codbar+'^FS'+'\n'
label5 +='^BY1,1,150'+'\n'
label5 +='^FO450,610^BCN,N,N,N^FD'+v_codbar+'^FS'+'\n'
label5 +='^XZ'

print (label5)
TCP_IP = '192.168.0.239'
TCP_PORT = 9100
BUFFER_SIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
#s.send(bytes(label5))
s.close()
