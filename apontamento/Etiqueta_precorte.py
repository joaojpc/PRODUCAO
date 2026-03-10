# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import  socket
import os
import json

class gera_etiqueta:
    def __init__(self,pparams):
        r_params = json.loads(pparams)
        #print(r_params)
        self.v_descr1 = None
        self.v_descr2 = None
        self.v_un = None
        self.v_codbar = None
        self.v_umidade = None
        self.v_qtde = None
        self.v_destino = None
        self.v_lote = None
        self.v_data = None
        self.v_grupo = None
        self.v_comprimento = None
        self.v_largura = None
        self.v_seqlote = None
        self.v_madeira = None
        self.v_maquina = None
        self.v_espessura =None
        self.v_impressora =None
        self.v_TPO = None
        self.v_loteordem = None
        self.v_item = None
        self.v_pallet = None
        self.v_origem = None
        self.v_qtde_conv = None
        self.v_classificacao = None
        self.v_filial = None
        self.volume = None
        self.pilha = None
        self.fornecedor = None
        for v_lis in r_params:
            #print(v_lis)
            self.v_ordem = self.trata_None(str(v_lis['ordem']))
            self.v_descr1 =self.trata_None(v_lis['descr1'])
            self.v_descr2 = self.trata_None(v_lis['descr2'])
            try:
                self.v_un = self.trata_None(v_lis['un'])
            except:
                pass
            self.v_codbar = self.trata_None(str(v_lis['codbar']))
            try:
                self.v_umidade = self.trata_None(str(v_lis['umidade']))
            except:
                pass
            self.v_qtde = self.trata_None(str(v_lis['qtde']))
            try:
                self.v_destino = self.trata_None(v_lis['destino'])
            except:
                pass
            self.v_lote = self.trata_None(str(v_lis['lote']))
            self.v_data = self.trata_None(str(v_lis['data']))
            try:
                self.v_grupo = self.trata_None(v_lis['grupo'])
            except:
                pass
            self.v_comprimento = self.trata_None(str(v_lis['comprimento']))
            try:
                self.v_largura = self.trata_None(str(v_lis['largura']))
            except:
                pass
            self.v_seqlote = self.trata_None(str(v_lis['seqlote']))
            try:
                self.v_madeira = self.trata_None(v_lis['madeira']).upper()
            except:
                pass
            try:
                self.v_maquina = self.trata_None(v_lis['maquina'])
            except:
                pass
            try:
                self.v_espessura =self.trata_None(str(v_lis['espessura']))
            except:
                pass
            try:
                self.v_TPO = self.trata_None(v_lis['tipoordem'])
            except:
                self.v_TPO = ''                
            self.v_impressora =self.trata_None(str(v_lis['impressora']))
            try:
                self.v_pallet = self.trata_None(v_lis['pallet'])
            except:
                pass
            self.v_loteordem = self.trata_None(v_lis['loteordem'])
            self.v_item = self.trata_None(str(v_lis['item']))
            try:
                self.v_origem = self.trata_None(v_lis['origem'])
                if len(self.v_origem) == 22:
                    self.v_origem = self.v_origem[11:-6]
            except:
                pass
            try:
                self.volume = self.trata_None(v_lis['volume'])
            except:
                pass
            try:
                self.v_qtde_conv = self.trata_None(str(v_lis['qtde_conv']))                
            except:
                pass
            try:
                self.v_classificacao = self.trata_None(v_lis['classificacao'])
            except:
                pass
            try:
                self.v_filial = self.trata_None(v_lis['filial'])
            except:
                pass
            try:
                self.pilha = self.trata_None(v_lis['pilha'])
            except:
                pass
            try:
                self.fornecedor = self.trata_None(v_lis['fornecedor'])
            except:
                pass
        if self.v_filial == 312:
            if self.v_impressora == '192.168.60.100':
                pass
            elif self.v_impressora == '192.168.60.101':
                pass
            else:
                self.v_impressora = '192.168.60.100'
        if (self.v_TPO == 'OP001') and (self.v_filial == 3):
            self.etiqueta_tabicado()        
        elif (self.v_TPO == 'OP003') and (self.v_filial == 3):
            self.etiqueta_pre()
        elif (self.v_TPO == 'OP002') and (self.v_filial == 3):
            self.etiqueta_estufa()
        elif (self.v_filial == 312) and (self.v_TPO ==''):        
            self.etiqueta_zk_avr()
        elif (self.v_filial == 312) and (self.v_TPO =='INV'):
            self.etiqueta_zk_lv_inv()
        elif (self.v_filial == 312) and (self.v_TPO =='INVT'):
            self.etiqueta_zk_tr_inv()
        elif (self.v_filial == 312):
            self.etiqueta_zk_lv()        
        else:
            self.etiqueta_pre()
    def replaceString(self,vtexto):
        self.v_testo1 = vtexto
        self.v_testo2 = self.v_testo1.replace('á','\A0')
        self.v_testo1 = self.v_testo2.replace('à','\85')
        self.v_testo2 = self.v_testo1.replace('â','\83')
        self.v_testo1 = self.v_testo2.replace('ã','\C6')
        self.v_testo2 = self.v_testo1.replace('Á','\B5')
        self.v_testo1 = self.v_testo2.replace('À','\B7')
        self.v_testo2 = self.v_testo1.replace('Â','\B6')
        self.v_testo1 = self.v_testo2.replace('Ã','\C7')
        self.v_testo2 = self.v_testo1.replace('é','\82')
        self.v_testo1 = self.v_testo2.replace('è','\8A')
        self.v_testo2 = self.v_testo1.replace('ê','\88')
        self.v_testo1 = self.v_testo2.replace('É','\90')
        self.v_testo2 = self.v_testo1.replace('È','\D4')
        self.v_testo1 = self.v_testo2.replace('Ê','\D2')
        self.v_testo2 = self.v_testo1.replace('í','\A1')
        self.v_testo1 = self.v_testo2.replace('ì','\8D')
        self.v_testo2 = self.v_testo1.replace('î','\8C')
        self.v_testo1 = self.v_testo2.replace('Í','\D6')
        self.v_testo2 = self.v_testo1.replace('Î','\D7')
        self.v_testo1 = self.v_testo2.replace('ó','\A2')
        self.v_testo2 = self.v_testo1.replace('ò','\95')
        self.v_testo1 = self.v_testo2.replace('ô','\93')
        self.v_testo2 = self.v_testo1.replace('õ','\E4')
        self.v_testo1 = self.v_testo2.replace('Ó','\E3')
        self.v_testo2 = self.v_testo1.replace('Ô','\E2')
        self.v_testo1 = self.v_testo2.replace('Õ','\E5')
        self.v_testo2 = self.v_testo1.replace('ú','\A3')
        self.v_testo1 = self.v_testo2.replace('ù','\97')
        self.v_testo2 = self.v_testo1.replace('û','\96')
        self.v_testo1 = self.v_testo2.replace('Ú','\E9')
        self.v_testo2 = self.v_testo1.replace('Ù','\EB')
        self.v_testo1 = self.v_testo2.replace('Û','\EA')
        self.v_testo2 = self.v_testo1.replace('ñ','\A4')
        self.v_testo1 = self.v_testo2.replace('Ñ','\A5')
        self.v_testo2 = self.v_testo1.replace('ç','\87')
        self.v_testo1 = self.v_testo2.replace('Ç','\80')
        #.upper()--converter toda a string em maiuscula)
        retorno = self.v_testo1
        return retorno
    def trata_None(self, param):
        if not (param is None):
            retorno = param
        else:
            retorno =''
        return retorno
    # Etiqueta do pré corte;
    def etiqueta_pre(self):
        label5 = '^XA'+'\n'
        label5 += '^CI28'+'\n'
        label5 += '^~SD20'+'\n'
        label5 += '^PW799'+'\n'
        label5 += '^LL0799'+'\n'
        label5 += '^LS0'+'\n'
        label5 += '^LT-10'+'\n'
        label5 += '^FO5,32^GFA,03456,03456,00036,:Z64:'+'\n'
        label5 += 'eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50'+'\n'
        label5 += '^FO6,6^GB782,0,4^FS'+'\n'
        label5 += '^FO6,6^GB0,782,4^FS'+'\n'
        label5 += '^FO6,788^GB782,0,4^FS'+'\n'
        label5 += '^FO786,6^GB0,782,4^FS'+'\n'
        label5 += '^FO6,140^GB782,0,4^FS'+'\n'
        label5 += '^FO6,570^GB782,0,4^FS'+'\n'
        label5 += '^FO410,500^GB370,60,4^FS'+'\n'
        label5 += '^FT318,98^A0N,62,72^FH\^FD'+self.v_grupo+'^FS'+'\n'
        label5 += '^FT15,205^A0N,48,48^FH\^FDOP: '+self.v_ordem+'^FS'+'\n'
        label5 += '^FT400,205^A0N,48,48^FH\^FDData: '+self.v_data+'^FS'+'\n'
        label5 += '^FT15,265^A0N,48,48^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        label5 += '^FT15,305^A0N,48,48^FH\^FD'+self.v_descr2+'^FS'+'\n'
        if self.v_destino !='':
            label5 += '^FT15,365^A0N,36,36^FH\^FDDestino: '+self.v_destino+'^FS'+'\n'
        label5 += '^FT15,425^A0N,36,36^FH\^FDEspecie: '+self.v_madeira+'^FS'+'\n'
        label5 += '^FT15,485^A0N,36,36^FH\^FDLarg: '+self.v_largura+' mm'+'^FS'+'\n'
        label5 += '^FT300,485^A0N,36,36^FH\^FDEsp: '+self.v_espessura+' mm'+'^FS'+'\n'
        label5 += '^FT585,485^A0N,36,36^FH\^FDUmid: '+self.v_umidade+'%'+'^FS'+'\n'
        label5 += '^FT15,545^A0N,36,36^FH\^FDMaquina: '+self.v_maquina+'^FS'+'\n'
        label5 += '^FT420,545^A0N,48,48^FH\^FDQTDE: '+self.v_qtde_conv+' '+self.v_un+'^FS'+'\n'
        label5 += '^FT50,627^A0N,60,60^FH\^FDLote^FS'+'\n'
        label5 += '^FT180,627^A0N,65,65^FH\^FD'+self.v_seqlote+'^FS'+'\n'
        label5 += '^FT440,780^A0N,18,22^FH\^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^BY2,1,120'+'\n'
        label5 += '^FO210,640^BCN,N,N,N^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^XZ'+'\n'
        v_print =  label5
        #Imprimir Etiqueta;
        #f = open("print_etiqueta.txt", "a")
        #f.write(v_print)
        #f.close()
        #Imprimir Etiqueta Fim;
        #v_print =  'b'+'"'+v_impressao+'"'
        #v_print = "^XA^A0N,50,50^FO50,50^FDProgramação Delphi^FS^XZ"
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            #TCP_IP = '192.168.101.225'
            #TCP_PORT = 9100
            #BUFFER_SIZE = 1024
            #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.connect((TCP_IP, TCP_PORT))
            #host = "192.168.1.212"
            host = self.v_impressora
            port = 9100
            zpl = """
                ^XA
                ^FO150,40^BY3
                ^BCN,110,Y,N,N
                ^FD123456^FS
                ^XZ 
            """
            try:
                mysocket.connect((host, port))
                #connecting to host
                mysocket.send(bytes(v_print, "utf-8"))
                #mysocket.send(v_print)
                #print(v_print)
                #mysocket.send('b'+v_print)
                #using bytes
                mysocket.close()
                # #closing connection except: print("Error with the connection")
            except:
                mysocket.close()
            #s.send(bytes(v_print))
            #print('Etiqueta 134')
            #s.close()
        except:
            mysocket.close()
    # Etiqueta Estufa;
    def etiqueta_estufa(self):
        label5 = '^XA'+'\n'
        label5 += '^CI28'+'\n'
        label5 += '^~SD20'+'\n'
        label5 += '^PW799'+'\n'
        label5 += '^LL0799'+'\n'
        label5 += '^LS0'+'\n'
        label5 += '^LT-10'+'\n'
        label5 += '^FO5,32^GFA,03456,03456,00036,:Z64:'+'\n'
        label5 += 'eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50'+'\n'
        label5 += '^FO6,6^GB782,0,4^FS'+'\n'
        label5 += '^FO6,6^GB0,782,4^FS'+'\n'
        label5 += '^FO6,788^GB782,0,4^FS'+'\n'
        label5 += '^FO786,6^GB0,782,4^FS'+'\n'
        label5 += '^FO6,140^GB782,0,4^FS'+'\n'
        label5 += '^FO6,570^GB782,0,4^FS'+'\n'
        label5 += '^FO410,500^GB370,60,4^FS'+'\n'
        label5 += '^FT450,60^A0N,48,48^FH\^FDMADEIRA^FS'+'\n'
        label5 += '^FT450,110^A0N,48,48^FH\^FD'+self.v_madeira+'^FS'+'\n'
        #label5 += '^FT318,98^A0N,62,72^FH\^FD'+self.v_grupo+'^FS'+'\n'
        label5 += '^FT15,205^A0N,48,48^FH\^FDOP: '+self.v_ordem+'^FS'+'\n'
        label5 += '^FT400,205^A0N,48,48^FH\^FDData: '+self.v_data+'^FS'+'\n'
        label5 += '^FT15,265^A0N,48,48^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        label5 += '^FT15,305^A0N,48,48^FH\^FD'+self.v_descr2+'^FS'+'\n'
        label5 += '^FT15,365^A0N,36,36^FH\^FDOrigem: '+self.v_origem+'^FS'+'\n'
        #label5 += '^FT15,425^A0N,36,36^FH\^FDEspecie: '+self.v_madeira+'^FS'+'\n'
        label5 += '^FT15,485^A0N,36,36^FH\^FDLarg: '+self.v_largura+' mm'+'^FS'+'\n'
        label5 += '^FT300,485^A0N,36,36^FH\^FDEsp: '+self.v_espessura+' mm'+'^FS'+'\n'
        label5 += '^FT585,485^A0N,36,36^FH\^FDUmid: '+self.v_umidade+'%'+'^FS'+'\n'
        label5 += '^FT15,545^A0N,36,36^FH\^FDPallet: '+self.v_pallet+'^FS'+'\n'
        label5 += '^FT420,545^A0N,48,48^FH\^FDQTDE: '+self.v_qtde_conv+' '+self.v_un+'^FS'+'\n'
        label5 += '^FT50,627^A0N,60,60^FH\^FDLote^FS'+'\n'
        label5 += '^FT180,627^A0N,65,65^FH\^FD'+self.v_seqlote+'    '+self.v_loteordem+'^FS'+'\n'
        label5 += '^FT440,780^A0N,18,22^FH\^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^BY2,1,120'+'\n'
        label5 += '^FO210,640^BCN,N,N,N^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^XZ'+'\n'
        v_print =  label5
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()

    def etiqueta_zk_lv(self):
        etiqueta = '^XA'+'\n'
        etiqueta += '^CI28'+'\n'
        etiqueta += '^MMT'+'\n'
        etiqueta += '^PW799'+'\n'
        etiqueta += '^LL0679'+'\n'
        etiqueta += '^LS0'+'\n'
        etiqueta += '^FT759,564^A0I,34,33^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        etiqueta += '^FT759,518^A0I,34,33^FH\^FD'+self.v_descr2+'^FS'+'\n'
        etiqueta += '^FO40,19^GB732,644,8^FS'+'\n'
        etiqueta += '^FT282,209^A0I,34,33^FH\^FD'+self.v_ordem+'^FS'+'\n'
        etiqueta += '^FT514,209^A0I,34,33^FH\^FD'+self.v_data+'^FS'+'\n'
        etiqueta += '^FT759,311^A0I,34,33^FH\^FD'+self.v_classificacao+'^FS'+'\n'
        etiqueta += '^BY3,3,119^FT653,59^BCI,,Y,N'+'\n'
        etiqueta += '^FD>;'+self.v_codbar+'^FS'+'\n'
        etiqueta += '^FT514,414^A0I,34,33^FH\^FD'+self.v_qtde+'^FS'+'\n'
        etiqueta += '^FT281,414^A0I,34,33^FH\^FD'+self.v_qtde_conv+'^FS'+'\n'
        etiqueta += '^FT759,209^A0I,34,33^FH\^FD'+self.v_origem+'^FS'+'\n'
        etiqueta += '^FT514,311^A0I,34,33^FH\^FD'+self.v_comprimento+'^FS'+'\n'
        etiqueta += '^FT759,414^A0I,34,33^FH\^FD'+self.v_seqlote+'^FS'+'\n'
        etiqueta += '^FT281,311^A0I,34,33^FH\^FD'+self.v_largura+'^FS'+'\n'
        etiqueta += '^FT759,614^A0I,34,33^FH\^FDItem^FS'+'\n'
        etiqueta += '^FT759,463^A0I,34,33^FH\^FDLote:^FS'+'\n'
        etiqueta += '^FT513,463^A0I,34,33^FH\^FDQtde Peças: ^FS'+'\n'
        etiqueta += '^FT280,463^A0I,34,33^FH\^FDM3 :^FS'+'\n'
        etiqueta += '^FT759,360^A0I,34,33^FH\^FDClassificação^FS'+'\n'
        etiqueta += '^FT514,360^A0I,34,33^FH\^FDComprimento^FS'+'\n'
        etiqueta += '^FT281,360^A0I,34,33^FH\^FDLargura^FS'+'\n'
        etiqueta += '^FT759,255^A0I,34,33^FH\^FDOrigem^FS'+'\n'
        etiqueta += '^FT514,255^A0I,34,33^FH\^FDData^FS'+'\n'
        etiqueta += '^FT282,255^A0I,34,33^FH\^FDOrdem^FS'+'\n'
        etiqueta += '^FO290,194^GB0,308,8^FS'+'\n'
        etiqueta += '^FO524,194^GB0,312,8^FS'+'\n'
        etiqueta += '^FO46,292^GB718,0,8^FS'+'\n'
        etiqueta += '^FO49,189^GB718,0,8^FS'+'\n'
        etiqueta += '^FO48,395^GB719,0,8^FS'+'\n'
        etiqueta += '^FO51,497^GB718,0,8^FS'+'\n'
        etiqueta += '^PQ1,0,1,Y^XZ'
        v_print =  etiqueta
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()
    def etiqueta_zk_lv_inv(self):
        etiqueta = '^XA'+'\n'
        etiqueta += '^CI28'+'\n'
        etiqueta += '^MMT'+'\n'
        etiqueta += '^PW799'+'\n'
        etiqueta += '^LL0679'+'\n'
        etiqueta += '^LS0'+'\n'
        etiqueta += '^FT759,564^A0I,34,33^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        etiqueta += '^FT759,518^A0I,34,33^FH\^FD'+self.v_descr2+'^FS'+'\n'
        etiqueta += '^FO40,19^GB732,644,8^FS'+'\n'
        etiqueta += '^FT282,209^A0I,34,33^FH\^FD'+self.v_ordem+'^FS'+'\n'
        etiqueta += '^FT759,311^A0I,34,33^FH\^FD'+self.v_classificacao+'^FS'+'\n'
        etiqueta += '^BY3,3,119^FT653,59^BCI,,Y,N'+'\n'
        etiqueta += '^FD>;'+self.v_codbar+'^FS'+'\n'
        etiqueta += '^FT514,414^A0I,34,33^FH\^FD'+self.v_qtde+'^FS'+'\n'
        etiqueta += '^FT281,414^A0I,34,33^FH\^FD'+self.v_qtde_conv+'^FS'+'\n'
        etiqueta += '^FT759,209^A0I,34,33^FH\^FD'+self.v_origem+'^FS'+'\n'
        etiqueta += '^FT514,311^A0I,34,33^FH\^FD'+self.v_comprimento+'^FS'+'\n'
        etiqueta += '^FT759,414^A0I,34,33^FH\^FD'+self.v_seqlote+'^FS'+'\n'
        etiqueta += '^FT281,311^A0I,34,33^FH\^FD'+self.v_largura+'^FS'+'\n'
        etiqueta += '^FT759,614^A0I,34,33^FH\^FDItem^FS'+'\n'
        etiqueta += '^FT759,463^A0I,34,33^FH\^FDLote:^FS'+'\n'
        etiqueta += '^FT513,463^A0I,34,33^FH\^FDQtde Peças: ^FS'+'\n'
        etiqueta += '^FT280,463^A0I,34,33^FH\^FDM3 :^FS'+'\n'
        etiqueta += '^FT759,360^A0I,34,33^FH\^FDClassificação^FS'+'\n'
        etiqueta += '^FT514,360^A0I,34,33^FH\^FDComprimento^FS'+'\n'
        etiqueta += '^FT281,360^A0I,34,33^FH\^FDLargura^FS'+'\n'
        etiqueta += '^FT759,255^A0I,34,33^FH\^FDOrigem^FS'+'\n'
        etiqueta += '^FT282,255^A0I,34,33^FH\^FDDocumento^FS'+'\n'
        etiqueta += '^FO290,194^GB0,308,8^FS'+'\n'
        etiqueta += '^FO524,296^GB0,210,8^FS'+'\n'
        etiqueta += '^FO46,292^GB718,0,8^FS'+'\n'
        etiqueta += '^FO49,189^GB718,0,8^FS'+'\n'
        etiqueta += '^FO48,395^GB719,0,8^FS'+'\n'
        etiqueta += '^FO51,497^GB718,0,8^FS'+'\n'
        etiqueta += '^PQ1,0,1,Y^XZ'
        v_print =  etiqueta
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()

    def etiqueta_zk_avr(self):
        etiqueta = '^XA'+'\n'
        etiqueta += '^CI28'+'\n'
        etiqueta += '^MMT'+'\n'
        etiqueta += '^PW799'+'\n'
        etiqueta += '^LL0679'+'\n'
        etiqueta += '^LS0'+'\n'
        etiqueta += '^FT234,598^A0I,51,50^FH\^FD'+self.pilha+'^FS'+'\n'
        etiqueta += '^FT759,564^A0I,34,33^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        etiqueta += '^FT759,518^A0I,34,33^FH\^FD'+self.v_descr2+'^FS'+'\n'
        etiqueta += '^FO40,19^GB732,644,8^FS'+'\n'
        etiqueta += '^FT282,209^A0I,34,33^FH\^FD'+self.v_ordem+'^FS'+'\n'
        etiqueta += '^FT514,209^A0I,34,33^FH\^FD'+self.v_data+'^FS'+'\n'
        etiqueta += '^FT759,311^A0I,34,33^FH\^FD'+self.v_classificacao+'^FS'+'\n'
        etiqueta += '^BY3,3,119^FT653,59^BCI,,Y,N'+'\n'
        etiqueta += '^FD>;'+self.v_codbar+'^FS'+'\n'
        etiqueta += '^FT514,414^A0I,34,33^FH\^FD'+self.v_qtde+'^FS'+'\n'
        etiqueta += '^FT281,414^A0I,34,33^FH\^FD'+self.v_qtde_conv+'^FS'+'\n'
        etiqueta += '^FT759,209^A0I,34,33^FH\^FD'+self.v_origem+'^FS'+'\n'
        etiqueta += '^FT514,311^A0I,34,33^FH\^FD'+self.v_comprimento+'^FS'+'\n'
        etiqueta += '^FT759,414^A0I,34,33^FH\^FD'+self.v_seqlote+'^FS'+'\n'
        etiqueta += '^FT281,311^A0I,34,33^FH\^FD'+self.volume+'^FS'+'\n'
        etiqueta += '^FT377,598^A0I,51,50^FH\^FDPilha:^FS'+'\n'
        etiqueta += '^FT759,614^A0I,34,33^FH\^FDItem^FS'+'\n'
        etiqueta += '^FT759,463^A0I,34,33^FH\^FDLote:^FS'+'\n'
        etiqueta += '^FT513,463^A0I,34,33^FH\^FDQtde Peças: ^FS'+'\n'
        etiqueta += '^FT280,463^A0I,34,33^FH\^FDM3 :^FS'+'\n'
        etiqueta += '^FT759,360^A0I,34,33^FH\^FDClassificação^FS'+'\n'
        etiqueta += '^FT514,360^A0I,34,33^FH\^FDComprimento^FS'+'\n'
        etiqueta += '^FT281,360^A0I,34,33^FH\^FDVolume^FS'+'\n'
        etiqueta += '^FT759,255^A0I,34,33^FH\^FDOrigem^FS'+'\n'
        etiqueta += '^FT514,255^A0I,34,33^FH\^FDData^FS'+'\n'
        etiqueta += '^FT282,255^A0I,34,33^FH\^FDDocumento^FS'+'\n'
        etiqueta += '^FO290,194^GB0,308,8^FS'+'\n'
        etiqueta += '^FO524,194^GB0,312,8^FS'+'\n'
        etiqueta += '^FO46,292^GB718,0,8^FS'+'\n'
        etiqueta += '^FO49,189^GB718,0,8^FS'+'\n'
        etiqueta += '^FO48,395^GB719,0,8^FS'+'\n'
        etiqueta += '^FO51,497^GB718,0,8^FS'+'\n'
        etiqueta += '^PQ1,0,1,Y^XZ'
        v_print =  etiqueta
        #print(v_print)
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()

    def etiqueta_zk_tr_inv(self):
        etiqueta = '^XA'+'\n'
        etiqueta += '^CI28'+'\n'
        etiqueta += '^~SD20'+'\n'
        etiqueta += '^MMT'+'\n'
        etiqueta += '^PW799'+'\n'
        etiqueta += '^LL0679'+'\n'
        etiqueta += '^LS0'+'\n'
        etiqueta += '^FT234,598^A0I,51,50^FH\^FD'+self.pilha+'^FS'+'\n'
        etiqueta += '^FT759,564^A0I,34,33^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        etiqueta += '^FT759,518^A0I,34,33^FH\^FD'+self.v_descr2+'^FS'+'\n'
        etiqueta += '^FO40,19^GB732,644,8^FS'+'\n'
        etiqueta += '^FT282,209^A0I,34,33^FH\^FD'+self.v_ordem+'^FS'+'\n'
        #etiqueta += '^FT514,209^A0I,34,33^FH\^FD'+self.v_data+'^FS'+'\n'
        etiqueta += '^FT759,311^A0I,34,33^FH\^FD'+self.v_classificacao+'^FS'+'\n'
        etiqueta += '^BY3,3,119^FT653,59^BCI,,Y,N'+'\n'
        etiqueta += '^FD>;'+self.v_codbar+'^FS'+'\n'
        etiqueta += '^FT514,414^A0I,34,33^FH\^FD'+self.v_qtde+'^FS'+'\n'
        etiqueta += '^FT281,414^A0I,34,33^FH\^FD'+self.v_qtde_conv+'^FS'+'\n'
        etiqueta += '^FT759,209^A0I,34,33^FH\^FD'+self.v_origem+'^FS'+'\n'
        etiqueta += '^FT514,311^A0I,34,33^FH\^FD'+self.v_comprimento+'^FS'+'\n'
        etiqueta += '^FT759,414^A0I,34,33^FH\^FD'+self.v_seqlote+'^FS'+'\n'
        etiqueta += '^FT281,311^A0I,34,33^FH\^FD'+self.volume+'^FS'+'\n'
        etiqueta += '^FT377,598^A0I,51,50^FH\^FDPilha:^FS'+'\n'
        etiqueta += '^FT759,614^A0I,34,33^FH\^FDItem^FS'+'\n'
        etiqueta += '^FT759,463^A0I,34,33^FH\^FDLote:^FS'+'\n'
        etiqueta += '^FT513,463^A0I,34,33^FH\^FDQtde Peças: ^FS'+'\n'
        etiqueta += '^FT280,463^A0I,34,33^FH\^FDM3 :^FS'+'\n'
        etiqueta += '^FT759,360^A0I,34,33^FH\^FDClassificação^FS'+'\n'
        etiqueta += '^FT514,360^A0I,34,33^FH\^FDComprimento^FS'+'\n'
        etiqueta += '^FT281,360^A0I,34,33^FH\^FDVolume^FS'+'\n'
        etiqueta += '^FT759,255^A0I,34,33^FH\^FDOrigem^FS'+'\n'
        #etiqueta += '^FT514,255^A0I,34,33^FH\^FDData^FS'+'\n'
        etiqueta += '^FT282,255^A0I,34,33^FH\^FDDocumento^FS'+'\n'
        etiqueta += '^FO290,194^GB0,308,8^FS'+'\n'
        etiqueta += '^FO524,296^GB0,210,8^FS'+'\n'
        etiqueta += '^FO46,292^GB718,0,8^FS'+'\n'
        etiqueta += '^FO49,189^GB718,0,8^FS'+'\n'
        etiqueta += '^FO48,395^GB719,0,8^FS'+'\n'
        etiqueta += '^FO51,497^GB718,0,8^FS'+'\n'
        etiqueta += '^PQ1,0,1,Y^XZ'
        v_print =  etiqueta
        #print(v_print)
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()
    def etiqueta_tabicado(self):
        #self.v_impressora = '192.168.0.250'
        label5 = '^XA'+'\n'
        label5 += '^CI28'+'\n'
        label5 += '^~SD20'+'\n'
        label5 += '^PW799'+'\n'
        label5 += '^LL0799'+'\n'
        label5 += '^LS0'+'\n'
        label5 += '^LT-10'+'\n'
        label5 += '^FO35,12^GFA,03456,03456,00036,:Z64:'+'\n'
        label5 += 'eJztlcGL20YUxsfS7moZaraFBl1W2UUnM6dA0viUrs0WQg+BnNIcYnDYQ69KrGgMDbuKwWBEC73kUOjCoNMwf4UNLfQScGAXZJD+l743shNZIju9puQdPPLo6adP33wjEfKlPrMak6GxR1rS1NLKW7mRoyxl5EROZOZQMyf3itjIYcrU04p+4UMjJ1XCxCkWRWbkTJTJ6Ba3udEg8NlkEKxXUfwXTmzgnNsXvGfkSJNBWs/85h6r5DA8Zp/osSM75AHp4nH3Bg77NMeK4acNeS6WxMMJr9mzi1LpzXo050Fkv7rolVJOmj1OD346pc8MrqDIoYQI0iEkRgARmrMq18vbfTf3Lr3pfBCvMvDsenq9WOa7udYjynVnlhJM0YlQQkkLMpWoWEiqKGTLfh7p/HQdHnDuOs9hCB3IlMP7QehyN0DdwJEfORBuBTtuzWEqgXO7b0BPhnpWy2eFN10Uyxx23KK4LEDPoLjM8DGAI5Aj4DLgpDgkwJnE+gg4tzE/Q7DG6Qevu0fO2Ysg+N51TscuTITnLvrTQU6MnLjkiFiCVxNB1xNw7inmJ0Y9cHsP9OQkOyTtxVJPDIrpfM0hHzlCEeCwDUchJ2hFNm6vLt6+i/70gvs2Pw20Hs5Rz3GDAwP4XOU8Xb8PN3rmg2V22C4aemSVQ3FINxydn3ugJ9zoOXGd4UEwvn/08DQ4QsMinR9a5/g4WFucdk3P3wvQg3/0xDMP9eC6VzhJisumdU0++Oz0I2ejJ+LuT2ejIIy6rvbnRci7DuZH6KhpDuRH6fww9EfFCv2Bk633ubfRMygwOMsC87MEj/Bgiu9KqViVo/NMNxxain11PnpNyvyc8AM+5MPR2IX1ci56F+FBZAd6f6UfOMxKBYultMBnK8UDSfAk3Lv2/coqO70sqqVXS1Z2+npDc71elQoqO33drurf0yan+T1t6ml+l5scEtrBds+4oQcSHZP/dXWMHXvkzh6Od/fXEy3yVa2FQamEzlg666R+J02pShKx3fPNat7/7devsx+vrm69eXtrurOTrX7/qyZm5jNJ9yWT+8cplqWoqHHuPX45GrrfBqPwh+/O+N2fH+69fHKnFqxjOfE7CZF+LI7hpThhVrKf1jjeo1XR/uPwn/517r2/Kq4f7ayyP9/G28/lM+UTKn0fniuWaceazWbWds+X+izqX2I2xjs=:FF50'+'\n'
        #linha superior
        label5 += '^FO26,6^GB742,0,4^FS'+'\n'
        #linha esquerda
        label5 += '^FO26,6^GB0,762,4^FS'+'\n'
        #linha inferior
        label5 += '^FO26,768^GB742,0,4^FS'+'\n'
        #linha direita
        label5 += '^FO766,6^GB0,762,4^FS'+'\n'
        #segunda linha superior
        label5 += '^FO26,140^GB742,0,4^FS'+'\n'
        #terceira linha superior
        label5 += '^FO26,540^GB742,0,4^FS'+'\n'
        #borda da quantidade
        label5 += '^FO380,470^GB380,60,4^FS'+'\n'
        label5 += '^FT450,60^A0N,48,48^FH\^FDMADEIRA^FS'+'\n'
        label5 += '^FT450,110^A0N,48,48^FH\^FD'+self.v_madeira+'^FS'+'\n'
        #label5 += '^FT318,98^A0N,62,72^FH\^FD'+self.v_grupo+'^FS'+'\n'
        label5 += '^FT35,185^A0N,48,48^FH\^FDOP: '+self.v_ordem+'^FS'+'\n'
        label5 += '^FT420,185^A0N,48,48^FH\^FDData: '+self.v_data+'^FS'+'\n'
        label5 += '^FT35,245^A0N,48,48^FH\^FD'+self.v_item+' - '+self.v_descr1+'^FS'+'\n'
        label5 += '^FT35,285^A0N,48,48^FH\^FD'+self.v_descr2+'^FS'+'\n'
        label5 += '^FT35,345^A0N,36,36^FH\^FDNF: '+self.v_origem+' Fornecedor: '+self.fornecedor+'^FS'+'\n'        
        #label5 += '^FT15,425^A0N,36,36^FH\^FDEspecie: '+self.v_madeira+'^FS'+'\n'
        label5 += '^FT35,455^A0N,36,36^FH\^FDLarg: '+self.v_largura+' mm'+'^FS'+'\n'
        label5 += '^FT320,455^A0N,36,36^FH\^FDEsp: '+self.v_espessura+' mm'+'^FS'+'\n'
        #alterado por JPC em 18/06/2024 => Umidade oculto na linha abaixo 
        #label5 += '^FT585,465^A0N,36,36^FH\^FDUmid: '+self.v_umidade+'%'+'^FS'+'\n'
        label5 += '^FT35,515^A0N,36,36^FH\^FDPallet: '+self.v_pallet+'^FS'+'\n'
        label5 += '^FT420,515^A0N,48,48^FH\^FDQTDE: '+format(float(self.v_qtde), ".3f")+' '+self.v_un+'^FS'+'\n'
        label5 += '^FT50,597^A0N,60,60^FH\^FDLote^FS'+'\n'
        label5 += '^FT180,597^A0N,65,65^FH\^FD'+self.v_seqlote+'    '+self.v_loteordem+'^FS'+'\n'
        label5 += '^FT350,750^A0N,18,22^FH\^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^BY2,1,120'+'\n'
        label5 += '^FO170,610^BCN,N,N,N^FD'+self.v_codbar+'^FS'+'\n'
        label5 += '^XZ'+'\n'        
        v_print =  label5
        #print(v_print)
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()

    def printer_erro(self):
        mysocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        v_print = """
                ^XA
                ^FO150,40^BY3
                ^BCN,110,Y,N,N
                ^FD123456^FS
                ^XZ 
            """
        try:
            host = self.v_impressora
            port = 9100
            try:
                mysocket.connect((host, port))
                mysocket.send(bytes(v_print, "utf-8"))
                mysocket.close()
            except:
                mysocket.close()
        except:
            mysocket.close()
