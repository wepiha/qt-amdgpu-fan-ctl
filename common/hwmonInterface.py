import os
from enum import Enum
#
# Documentation for the amdgpu hwmon interfaces
# Source: https://www.kernel.org/doc/html/latest/gpu/amdgpu.html#hwmon-interfaces 
#

# The amdgpu driver exposes the following sensor interfaces:

#     GPU temperature (via the on-die sensor)
#     GPU voltage
#     Northbridge voltage (APUs only)
#     GPU power
#     GPU fan

# hwmon interfaces for GPU temperature:

#     temp1_input: the on die GPU temperature in millidegrees Celsius
#     temp1_crit: temperature critical max value in millidegrees Celsius
#     temp1_crit_hyst: temperature hysteresis for critical limit in millidegrees Celsius

# hwmon interfaces for GPU voltage:

#     in0_input: the voltage on the GPU in millivolts
#     in1_input: the voltage on the Northbridge in millivolts

# hwmon interfaces for GPU power:

#     power1_average: average power used by the GPU in microWatts
#     power1_cap_min: minimum cap supported in microWatts
#     power1_cap_max: maximum cap supported in microWatts
#     power1_cap: selected power cap in microWatts

# hwmon interfaces for GPU fan:

#     pwm1: pulse width modulation fan level (0-255)
#     pwm1_enable: pulse width modulation fan control method (0: no fan speed control, 1: manual fan speed control using pwm interface, 2: automatic fan speed control)
#     pwm1_min: pulse width modulation fan control minimum level (0)
#     pwm1_max: pulse width modulation fan control maximum level (255)
#     fan1_min: an minimum value Unit: revolution/min (RPM)
#     fan1_max: an maxmum value Unit: revolution/max (RPM)
#     fan1_input: fan speed in RPM
#     fan[1-*]_target: Desired fan speed Unit: revolution/min (RPM)
#     fan[1-*]_enable: Enable or disable the sensors.1: Enable 0: Disable


class PwmState(Enum):
    def __str__(self):
        return str(self.name)
    Disabled = 0
    Manual = 1
    Auto = 2

class PowerDPMFState(Enum):
    def __str__(self):
        return str(self.name)
    Auto = "auto"
    Low = "low"
    High = "high"
    Manual = "manual"
    profile_standard = "profile_standard"
    profile_min_sclk = "profile_min_sclk"
    profile_min_mclk = "profile_min_mclk"
    profile_peak = "profile_peak"

class HwMon0(Enum):
    def __str__(self):
        return str(self.value)
    
    pwm1 = "pwm1"
    pwm1_enable = "pwm1_enable"
    pwm1_min = "pwm1_min"
    pwm1_max = "pwm1_max"
    temp1_input = "temp1_input"
    temp1_crit = "temp1_crit"
    power1_cap = "power1_cap"
    power1_average = "power1_average"
    in0_input = "in0_input"

HWMON_KERNEL_PATH = "/sys/class/drm/card%s/device/hwmon/hwmon0/%s"
SETPERMS_PATH = 'python3 %s/common/setperms.py %s'

class HwMon:

    _card = 0

    def __init__(self, card = 0):
        self._card = card
        self.__setperms(HWMON_KERNEL_PATH % (self._card, HwMon0.pwm1))
    
    def __getvalue(self, path):
        try:
            file = open(HWMON_KERNEL_PATH % (self._card, path), "r")
            value = int(file.read())
        except Exception as e:
            raise e
            
        return value

    def __setperms(self, path):
        os.system('python3 %s/common/setperms.py %s' % (os.getcwd(), path) )

    def __setvalue(self, interface, value):
        path = HWMON_KERNEL_PATH % (self._card, interface)
        try:
            self.__setperms(path)

            with open(path, "w") as file:
                file.write(str(value))
        except Exception as e:
            print("__setvalue(%s, %s) failed: %s" % (interface.name, value, e))
        finally:
            print("__setvalue(%s, %s) success" % (interface.name, value) )
    

    @property
    def pwm1(self):
        return self.__getvalue(HwMon0.pwm1)
    @pwm1.setter
    def pwm1(self, value):
        if (not isinstance(value, int)):
            raise TypeError("value must be an integer")
        if ((value < 0) or (value > self.pwm1_max)):
            raise ArithmeticError("value is not within range")
        self.__setvalue(HwMon0.pwm1, value)


    @property
    def pwm1_enable(self):
        return self.__getvalue(HwMon0.pwm1_enable)

    @pwm1_enable.setter
    def pwm1_enable(self, pwmstate = PwmState.Auto):
        if not isinstance(pwmstate, PwmState):
            raise TypeError("pwmstate must be an instance of PwmState Enum")
        
        self.__setvalue(HwMon0.pwm1_enable, pwmstate.value)
    

    @property
    def temp1_input(self):
        return self.__getvalue(HwMon0.temp1_input) / 1000

    @property
    def temp1_crit(self):
        tCrit = self.__getvalue(HwMon0.temp1_crit)
        return int(tCrit / 1000)

    @property
    def pwm1_max(self):
        return 255
        #return self.__getvalue(Interface.pwm1_max)

    @property
    def power1_average(self):
        return self.__getvalue(HwMon0.power1_average) / 1000000