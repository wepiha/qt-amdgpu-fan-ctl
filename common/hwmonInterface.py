import os
from enum import Enum

class Status(Enum):
    def __str__(self):
        return str(self.value)
    Disabled = "DISABLED"
    Manual = "MANUAL"
    Auto = "AUTO"

class Interface(Enum):
    def __str__(self):
        return str(self.value)
        
    temp1_input = "temp1_input"
    temp1_crit = "temp1_crit"
    pwm1 = "pwm1"
    pwm1_max = "pwm1_max"
    pwm1_enable = "pwm1_enable"
    power1_cap = "power1_cap"

HWMON_KERNEL_PATH = "/sys/class/drm/card%s/device/hwmon/hwmon0/%s"
SETPERMS_PATH = 'python3 %s/common/setperms.py %s'

class HwMon:

    _card = 0

    def __init__(self, card = 0):
        self._card = card
        self.__setperms(Interface.pwm1)
    
    def __getvalue(self, path):
        try:
            file = open(HWMON_KERNEL_PATH % (self._card, path), "r")
            value = int(file.read())
        except Exception as e:
            raise e
            
        return value

    def __setperms(self, interface):
        if not isinstance(interface, Interface):
            raise TypeError("interface must be an instance of Interface Enum")
        
        path = HWMON_KERNEL_PATH % (self._card, interface)
        os.system('python3 %s/common/setperms.py %s' % (os.getcwd(), path) )

    def setvalue(self, interface, value):
        if not isinstance(interface, Interface):
            raise TypeError("interface must be an instance of Interface Enum")

        path = HWMON_KERNEL_PATH % (self._card, interface)
        try:
            self.__setperms(interface)

            with open(path, "w") as file:
                file.write(str(value))
        except Exception as e:
            print("__setvalue(%s, %s) failed: %s" % (interface.name, value, e))
        finally:
            print("__setvalue(%s, %s) success" % (interface.name, value) )
        
    
    def setpwm1_enable(self, automatic = True):
        self.setvalue(Interface.pwm1_enable, "2" if automatic else "1")

    def getHwmonPowerCap(self):
        pass
    
    def getGPUTemp(self):
        tIn = self.__getvalue(Interface.temp1_input)
        return int(tIn / 1000)

    def getGPUTempCrit(self):
        tCrit = self.__getvalue(Interface.temp1_crit)
        return int(tCrit / 1000)

    def getGPUPWMMax(self):
        return self.__getvalue(Interface.pwm1_max)

    def getGPUFanPercent(self):
        fIn = self.__getvalue(Interface.pwm1)
        fMax = self.getGPUPWMMax()
        fRet = int((fIn / fMax) * 100)
        
        return fRet

    def getStatus(self):
        val = self.__getvalue(Interface.pwm1_enable)

        if (val == 0):
            return Status.Disabled
        elif (val == 1):
            return Status.Manual
        else:
            return Status.Auto
