import sys
import jarray
import time


sys.path.append("/opt/pi4j/lib/pi4j-core.jar")
sys.path.append("/opt/pi4j/lib/pi4j-device.jar")
sys.path.append("/opt/pi4j/lib/pi4j-gpio-extension.jar")

import com.pi4j.io.i2c.I2CBus as I2CBus
import com.pi4j.io.i2c.I2CDevice as I2CDevice
import com.pi4j.io.i2c.I2CFactory as I2CFactory
import java.io.IOException 

ADS1x15_CONFIG_MODE_SINGLE   = 0x0100
ADS1x15_POINTER_CONVERSION   = 0x00
ADS1x15_CONFIG_MUX_OFFSET    = 12
ADS1x15_POINTER_CONFIG       = 0x01
ADS1x15_CONFIG_GAIN = {
    2/3: 0x0000,
    1:   0x0200,
    2:   0x0400,
    4:   0x0600,
    8:   0x0800,
    16:  0x0A00
}
ADS1x15_CONFIG_COMP_QUE_DISABLE = 0x0003

# Create I2C bus

bus = I2CFactory.getInstance(I2CBus.BUS_1);
# Get I2C device, ADS1115 I2C address is 0x48(72)
device = bus.getDevice(0x48);

# byte[] config = {(byte)0x84, (byte)0x83};
config = ''.join(chr(x) for x in [0x84, 0x83])
print(config[0])

# Select configuration register
# AINP = AIN0 and AINN = AIN1, +/- 2.048V, Continuous conversion mode, 128 SPS
device.write(0x01, config, 0, 1)
# Thread.sleep(500);
#Read 2 bytes of data
#raw_adc msb, raw_adc lsb
length = 2
data = jarray.zeros(length, 'b')
#data = bytearray[]
device.read(0x00, data, 0, 1)
print ('teste:'+ str(data[0]))
# Convert the data
raw_adc = ((data[0] & 0xFF) * 256) + (data[1] & 0xFF)

if (raw_adc > 32767):
    raw_adc -= 65535
#Output data to screen
print("Digital Value of Analog Input : %d %n", raw_adc)
