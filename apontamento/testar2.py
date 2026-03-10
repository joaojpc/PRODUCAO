# -*- coding: utf-8 -*-

import time
import math
import Adafruit_ADS1x15
import java.io.IOException
import java.text.DecimalFormat
import sys

sys.path.append("/opt/pi4j/lib/pi4j-core.jar")
sys.path.append("/opt/pi4j/lib/pi4j-device.jar")
sys.path.append("/opt/pi4j/lib/pi4j-gpio-extension.jar")

import com.pi4j.gpio.extension.ads.ADS1115GpioProvider as adsgp
import com.pi4j.gpio.extension.ads.ADS1115Pin as ADS1115Pin
import com.pi4j.gpio.extension.ads.ADS1x15GpioProvider.ProgrammableGainAmplifierValue as ProgrammableGainAmplifierValue
import com.pi4j.io.gpio.GpioController as GpioController
import com.pi4j.io.gpio.GpioFactory as gpf
import com.pi4j.io.gpio.GpioPinAnalogInput as GpioPinAnalogInput
import com.pi4j.io.gpio.event.GpioPinAnalogValueChangeEvent as GpioPinAnalogValueChangeEvent
import com.pi4j.io.gpio.event.GpioPinListenerAnalog as GpioPinListenerAnalog
import com.pi4j.io.i2c.I2CBus as I2CBus
import com.pi4j.io.i2c.I2CFactory.UnsupportedBusNumberException as UnsupportedBusNumberException

import com.pi4j.io.i2c.I2CDevice as I2CDevice
import com.pi4j.io.i2c.I2CFactory as I2CFactory



ADS1115_ADDRESS = 0x48
IODIRA_REGISTER = 0x00 
    
GPIOA_REGISTER = 0x12

key = ''.join(chr(x) for x in [0x00, 0xFF])
    

print("ADS1115 Example")
i2c = I2CFactory.getInstance(I2CBus.BUS_1)
device = i2c.getDevice(ADS1115_ADDRESS)        
acumulador = 0
valor_final = 0
device.write(IODIRA_REGISTER, key[0])      
while True:
    print(device.read(GPIOA_REGISTER))    
    for i in range(50):
        print(valor_final)
        #valor = adc.read_adc(0, gain=GAIN)
	valor = device.read(GPIOA_REGISTER)
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
    print(valor_final)      