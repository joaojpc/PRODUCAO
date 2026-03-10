# -*- coding: utf-8 -*-
import json
import socket
import threading
import sys
import jarray
import time
import math

sys.path.append("/opt/pi4j/lib/pi4j-core.jar")
sys.path.append("/opt/pi4j/lib/pi4j-device.jar")
sys.path.append("/opt/pi4j/lib/pi4j-gpio-extension.jar")
sys.path.append("/opt/pi4j/lib/pi4j-encoder-read.jar")
sys.path.append("/home/pi/projetos/producao/lib/mysql-connector-java-5.1.46.jar")
sys.path.append("/home/pi/projetos/producao/lib/ojdbc6.jar")
sys.path.append("/opt/jython2.7.0/javalib/sqlite-jdbc-3.23.1.jar")

#sudo export CLASSPATH=/home/pi/projetos/producao/lib/ojdbc6.jar:$CLASSPATH


import com.pi4j.io.i2c.I2CBus as I2CBus
import com.pi4j.io.i2c.I2CDevice as I2CDevice
import com.pi4j.io.i2c.I2CFactory as I2CFactory
import java.io.IOException
import com.pi4j.io.gpio.GpioController as GpioController
import com.pi4j.io.gpio.GpioFactory as GpioFactory
import com.pi4j.io.gpio.GpioPinDigitalOutput as GpioPinDigitalOutput
import com.pi4j.io.gpio.PinState as PinState
import com.pi4j.io.gpio.RaspiPin as RaspiPin
import com.pi4j.io.gpio.PinPullResistance as PinPullResistance
import com.raspoid.examples.RotaryTesting as ler
import com.raspoid.examples.RotaryEncoder as ler2

from java.lang import Class
from java.sql  import DriverManager, SQLException
from datetime import datetime, date
from oracle.jdbc import OracleTypes
from oracle.jdbc.pool import OracleDataSource

DATABASE    = "/home/pi/tomcat/apache-tomcat-8.5.32/webapps/producao/WEB-INF/lib-python/producao.db"
JDBC_URL    = "jdbc:sqlite:%s"  % DATABASE
JDBC_DRIVER = "org.sqlite.JDBC"


consumo_acum  = []
ADS1x15_CONFIG_MODE_SINGLE   = 0x0100
ADS1x15_POINTER_CONVERSION   = 0x00
ADS1x15_CONFIG_MUX_OFFSET    = 12
ADS1x15_POINTER_CONFIG       = 0x01
ADS1x15_CONFIG_OS_SINGLE       = 0x8000
ADS1x15_DEFAULT_ADDRESS        = 0x48
ADS1x15_CONFIG_GAIN = {
    2/3: 0x0000,
    1:   0x0200,
    2:   0x0400,
    4:   0x0600,
    8:   0x0800,
    16:  0x0A00
}
ADS1x15_CONFIG_COMP_QUE_DISABLE = 0x0003
ADS1115_CONFIG_DR = {
    8:    0x0000,
    16:   0x0020,
    32:   0x0040,
    64:   0x0060,
    128:  0x0080,
    250:  0x00A0,
    475:  0x00C0,
    860:  0x00E0
}

class ADS1x15(object):

    def __init__(self, address=ADS1x15_DEFAULT_ADDRESS, **kwargs):
        self.bus = I2CFactory.getInstance(I2CBus.BUS_1)
        self._device = self.bus.getDevice(address)

    def _read(self, mux, gain, data_rate, mode):
        """Perform an ADC read with the provided mux, gain, data_rate, and mode
        values.  Returns the signed integer result of the read.
        """
        config = ADS1x15_CONFIG_OS_SINGLE  # Go out of power-down mode for conversion.
        # Specify mux value.
        config |= (mux & 0x07) << ADS1x15_CONFIG_MUX_OFFSET
        # Validate the passed in gain and then set it in the config.
        if gain not in ADS1x15_CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        config |= ADS1x15_CONFIG_GAIN[gain]
        # Set the mode (continuous or single shot).
        config |= mode
        # Get the default data rate if none is specified (default differs between
        # ADS1015 and ADS1115).
        if data_rate is None:
            data_rate = self._data_rate_default()
        # Set the data rate (this is controlled by the subclass as it differs
        # between ADS1015 and ADS1115).
        config |= self._data_rate_config(data_rate)
        config |= ADS1x15_CONFIG_COMP_QUE_DISABLE  # Disble comparator mode.
        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes.
        bytes = ''.join(chr(x) for x in [(config >> 8) & 0xFF, config & 0xFF])
        self._device.write(ADS1x15_POINTER_CONFIG, bytes, 0, 2)
        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/data_rate+0.0001)
        # Retrieve the result.
        length = 2
        result = jarray.zeros(length, 'b')
        self._device.read(ADS1x15_POINTER_CONVERSION, result, 0, 2)
        return self._conversion_value(result[1], result[0])

    def _data_rate_default(self):
        # Default from datasheet page 16, config register DR bit default.
        return 128
    def _data_rate_config(self, data_rate):
        if data_rate not in ADS1115_CONFIG_DR:
            raise ValueError('Data rate must be one of: 8, 16, 32, 64, 128, 250, 475, 860')
        return ADS1115_CONFIG_DR[data_rate]

    def _conversion_value(self, low, high):
        # Convert to 16-bit signed value.
        value = ((high & 0xFF) << 8) | (low & 0xFF)
        # Check for sign bit and turn into a negative value if set.
        if value & 0x8000 != 0:
            value -= 1 << 16
        return value
    def _conversion_value2(self, low, high):
        # Convert to 16-bit signed value.
        pga = 1024
        returnVal = 0
        val = ((low & 0xFF) << 8) | (high & 0xFF)
        if (val > 0x7FFF):
            ReturnVal = float((val - 0xFFFF) * pga / 32767)
        else:
            returnVal = float(val * pga / 32768)
        return returnVal

    def read_adc(self, channel, gain=1, data_rate=None):
        """Read a single ADC channel and return the ADC value as a signed integer
        result.  Channel must be a value within 0-3.
        """
        assert 0 <= channel <= 3, 'Channel must be a value within 0-3!'
        # Perform a single shot read and set the mux value to the channel plus
        # the highest bit (bit 3) set.
        return self._read(channel + 0x04, gain, data_rate, ADS1x15_CONFIG_MODE_SINGLE)


    #// consumo de energia

class minhaThread (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
         print "Iniciando  thread ID %d" % (self.threadID)
        #print "Finalizando " + self.threadID
    def processo(nome, contador):
        while contador:
            print "Thread %s fazendo o processo %d" % (nome, contador)
            contador -= 1
################################################################################
def getSqliteConnection(jdbc_url, driverName):
    """
        Given the name of a JDBC driver class and the url to be used
        to connect to a database, attempt to obtain a connection to
        the database.
    """
    try:
        Class.forName(driverName).newInstance()
    except Exception, msg:
        print msg
        #sys.exit(-1)
    try:
        dbConn = DriverManager.getConnection(jdbc_url)
    except SQLException, msg:
        print msg
        #sys.exit(-1)
    return dbConn

def getEnderIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ender_ip = (s.getsockname()[0])
    s.close()
    return ender_ip

def getOraclepoolConn():
    cs = "jdbc:oracle:thin:@192.168.0.8:1521:megag"
    ods = OracleDataSource()
    ods.setURL(cs)
    ods.setUser("intprod")
    ods.setPassword("supprod")
    try:
        conn = ods.getConnection()
    except Exception, mgs:
        print(mgs)
    return conn

class medicoes:
    def __init__(self):
        self.ender_ip = getEnderIP()
        self.ini_filial = 0
        self.usuario_in = ''
        self.ordem_in = 0
        self.volta = 0
        self.acumulador = 0
        self.consumo_kwh = 0
        self.media_consumo = 0
        self.consumo_final = 0
        self.valor_final = 0
        self.ult_produtividade = 0
        self.cont_integra = 0
        self.Tensao = 220
        self.controle_apontamento = True
        self.finaliza_dia = False
        
    def equipaLogado(self):
        logado = False
        conn = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
        selectSQL = ('''select apc.*
                     from apt_controle apc
                    where apc.ctl_st_ipaddress = ?
                      and apc.ctl_dt_logout is null''')
        stmt = conn.prepareStatement(selectSQL)
        stmt.setString(1, self.ender_ip)
        rs = stmt.executeQuery()
        stmt.close
        conn.close
        while rs.next():
            logado = True
        return logado
    
    def lis_controle(self):
        con = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
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
                           and c.ctl_st_ipaddress = ?''')
        cur = con.prepareStatement(selectSQL)
        cur.setString(1, self.ender_ip)
        rs = cur.executeQuery()
        cur.close
        con.close
        while rs.next():
            self.ini_filial = rs.getInt(4)
            self.usuario_in =rs.getString(6)
            self.ordem_in = rs.getInt(7)
        return True
    
    def valor_encoder(self):
        pinA = RaspiPin.GPIO_04
        pinB = RaspiPin.GPIO_05
        iniciar = True
        init = ler2(pinA,pinB,iniciar)
        while self.controle_apontamento:
            retorno = init.getValue()
            self.volta = self.volta + retorno
            #print(self.volta)
                
    def busca_seq(self):
        conn = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
        selectSQL = ('''select CASE WHEN CTL_IN_SEQUENCIA IS NULL THEN 1 ELSE 
                                      max(CTL_IN_SEQUENCIA)+1 END as CTL_IN_SEQUENCIA
                            from apt_reg_medidores''')
        curr = conn.prepareStatement(selectSQL)
        rs = curr.executeQuery()
        curr.close
        conn.close
        while rs.next():
            sequencia = rs.getInt(1)
        return sequencia    
    def permite_gravar(self):
        valido = False
        row_now = datetime.now()
        str_hora = int(row_now.strftime('%H'))
        str_min = int(row_now.strftime('%M'))
        str_wekday = int(row_now.strftime('%w'))        
        list_day = [0,6]        
        if str_wekday not in list_day:            
            if str_hora > 6 and str_hora <= 18:
                self.finaliza_dia = False
                if str_hora < 18:
                    valido = True
                if str_hora == 18 and str_min <=1:
                    valido = True
                    self.finaliza_dia = True
                if str_hora == 18 and str_min > 1:
                    self.consumo_final=0
                    self.volta=0
                    self.ult_produtividade =0
                    self.finaliza_dia = True
            else:
                self.consumo_final=0
                self.volta=0
                self.ult_produtividade=0
                self.finaliza_dia = False
        return valido
                    
    def grava_registros(self):
        #t3 = threading.Thread(name='testeLeitura', target=self.never_stop)
        t2 = threading.Thread(name='produtividade', target=self.valor_encoder)        
        #t4 = threading.Thread(name='consumo_energia', target=self.consumo)
        #t3.start()        
        #time.sleep(40)
        #t4.start()
        t2.start()        
        while self.controle_apontamento:
            time.sleep(60)
            self.cont_integra += 1
            valor_convertindo = 0
            if self.permite_gravar():
                self.logado = self.equipaLogado()
                c_dados = self.lis_controle()
                del consumo_acum[:]
                sequencia =self.busca_seq()
                valor_convertindo=float((self.volta*0.3047)-self.ult_produtividade)
                self.ult_produtividade= float(self.volta*0.3047)
                #valor_convertindo = float(self.volta*0.3047) 
                con = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
                str_now = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
                insertTableSQL = ('''insert into apt_reg_medidores
                            (CTL_IN_SEQUENCIA,CTL_ST_USUARIO,ORD_IN_CODIGO,FIL_IN_CODIGO,CTL_DT_REGISTRO,CTL_ST_IPADDRESS,CTL_IN_CONSENERGIA,CTL_IN_PRODUTIVIDADE,
                            CTL_CH_STATUSIMP)
                            values
                            (?,?,?,?,?,?,?,?,?)''')
                cur = con.prepareStatement(insertTableSQL)
                cur.setInt(1, sequencia)
                cur.setString(2, self.usuario_in)
                cur.setInt(3, self.ordem_in)
                cur.setInt(4, self.ini_filial)
                cur.setString(5, str_now)
                cur.setString(6, self.ender_ip)
                cur.setFloat(7, self.consumo_final)
                cur.setFloat(8, valor_convertindo)
                cur.setString(9, 'N')
                cur.executeUpdate()
                cur.close
                con.close
            if self.cont_integra == 60 or self.finaliza_dia:
                if self.permite_gravar() or self.finaliza_dia:
                    self.cont_integra=0
                    self.integrar_registros()
                        
    def reg_aberto_sqlite(self):
        con = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
        selectSQL = ('''select t.CTL_IN_SEQUENCIA,
                               t.CTL_ST_USUARIO,
                               t.ORD_IN_CODIGO,
                               t.FIL_IN_CODIGO,
                               t.CTL_DT_REGISTRO,
                               t.CTL_ST_IPADDRESS,
                               t.CTL_IN_CONSENERGIA,
                               t.CTL_IN_PRODUTIVIDADE
                                 from apt_reg_medidores t
                                where t.ctl_st_ipaddress = ?
                                  and t.ctl_ch_statusimp = ? ''')
        cur = con.prepareStatement(selectSQL)
        cur.setString(1, self.ender_ip)
        cur.setString(2, 'N')        
        rs = cur.executeQuery()
        cur.close
        con.close
        lista = []
        while rs.next():
            lista.append(dict(ctl_in_sequencia = rs.getInt(1),
                              ctl_in_usuario= rs.getString(2),
                              ord_in_codigo= rs.getInt(3),
                              eqp_in_filial = rs.getInt(4),
                              ctl_dt_registro = rs.getString(5),
                              eqp_st_ipaddress = rs.getString(6),
                              ctl_in_consenergia = rs.getString(7),                                
                              ctl_in_produtividade = rs.getString(8)))
        json_registros ={}
        json_registros = json.dumps(lista)
        return json_registros


    def controla_itegracao(self):
        while self.controle_apontamento:
            time.sleep(3600)
            if self.permite_gravar():
                self.integrar_registros()                
            
    def integrar_registros(self):                
        v_reg = json.loads(self.reg_aberto_sqlite())
        con = getOraclepoolConn()
        insertTableSQL = ('''insert into intprod.apt_reg_medidores
                            (CTL_IN_SEQUENCIA,CTL_IN_USUARIO,ORD_IN_CODIGO,FIL_IN_CODIGO,CTL_DT_REGISTRO,CTL_MAQ_IP,CTL_IN_CONSENERGIA,CTL_IN_PRODUTIVIDADE)
                            values
                            (?,?,?,?,to_date(?,'yyyy/mm/dd hh24:mi:ss'),?,?,?)''')
        cur = con.prepareStatement(insertTableSQL)
        con2 = getSqliteConnection(JDBC_URL, JDBC_DRIVER)
        ExecSQL =('''update apt_reg_medidores
                          set ctl_ch_statusimp = 'S'
                        where CTL_IN_SEQUENCIA = ?
                          and ctl_ch_statusimp  = ?''')
        cur2 = con2.prepareStatement(ExecSQL)
        for itn in v_reg:
            sequencia =self.busca_seq_integracao()        
            var_id = itn['ctl_in_sequencia']
            var_usu = itn['ctl_in_usuario']
            var_fil = itn['eqp_in_filial']
            var_ord = itn['ord_in_codigo']
            var_dtr = itn['ctl_dt_registro']
            var_ip = itn['eqp_st_ipaddress']
            var_prod = round(float(itn['ctl_in_produtividade']),2)
            var_cons = round(float(itn['ctl_in_consenergia']),2)            
            cur.setInt(1, sequencia)
            cur.setString(2, var_usu)
            cur.setInt(3, var_ord)            
            cur.setInt(4, var_fil)            
            cur.setString(5, var_dtr)            
            cur.setString(6, var_ip)            
            cur.setFloat(7, var_cons)            
            cur.setFloat(8, var_prod)
            cur.executeUpdate()
            cur2.setInt(1, var_id)
            cur2.setString(2, 'N')                        
            cur2.executeUpdate()
        cur2.close
        con2.close
        cur.close
        con.close

    def busca_seq_integracao(self):
        conn = getOraclepoolConn()
        selectSQL = ('''select intprod.reg_medidores_sq.nextval as sequencia from dual''')
        curr = conn.prepareStatement(selectSQL)
        rs = curr.executeQuery()
        curr.close
        conn.close
        while rs.next():
            sequencia = rs.getInt(1)
        return sequencia            
                    
    def consumo(self):
        acumulador = 0
        consumo_kwh = 0
        media_consumo = 0
        media_geral = 0        
        Tensao = 380
        memoria_kwh = []
        adc = ADS1x15()
        GAIN = 4
        while self.controle_apontamento:
            for i in range(50):
                valor = adc.read_adc(0, gain=GAIN)
                acumulador += math.fabs(valor)
                time.sleep(0.1)
                if acumulador > 0 and i > 0:
                    valor_acumulado = (acumulador / i)
                    if valor_acumulado < 2100:
                        valor_final = valor_acumulado * 0.00499
                        
                    elif valor_acumulado > 2100 and valor_acumulado < 4050:
                        valor_final = valor_acumulado * 0.00519
                        
                    elif valor_acumulado > 4050 and valor_acumulado < 5000:
                        valor_final = valor_acumulado * 0.00634
                        
                    elif valor_acumulado > 5500:
                        valor_final = valor_acumulado * 0.00732
            if i == 49:                
                consumo_kwh = valor_final * Tensao / 1000
                memoria_kwh.append(consumo_kwh)                
                acumulador = 0
                valor_final = 0
                
            if len(memoria_kwh) == 5:
                for n in memoria_kwh:
                    media_consumo += n / len(memoria_kwh)                
                memoria_kwh[:7] = []
                consumo_acum.append(media_consumo)                
                media_consumo = 0
                media_geral = 0
                for cm in consumo_acum:                    
                    media_geral += cm / len(consumo_acum)
                self.consumo_final = media_geral
if __name__ == '__main__':
    init = medicoes()
    init.grava_registros()    
