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

HWMON_SYSFS_PATH = "/sys/class/drm/card%s/%s"

class accepted_pwm1_enable(Enum):
    def __str__(self):
        return str(self.name)
    Disabled = 0
    Manual = 1
    Auto = 2

class accepted_power_dpm_force_performance_level(Enum):
    def __str__(self):
        return str(self.name)
    auto = "auto"
    low = "low"
    high = "high"
    manual = "manual"
    profile_standard = "profile_standard"
    profile_min_sclk = "profile_min_sclk"
    profile_min_mclk = "profile_min_mclk"
    profile_peak = "profile_peak"

class accepted_power_dpm_state(Enum):
    def __str__(self):
        return str(self.name)
    battery = "battery"
    balanced = "balanced"
    performance = "performance"

class sysfs_device_hwmon_hwmon0(Enum):
    """
    Enums that are related to sysfs interfaces found in
    /sys/class/drm/cardN/device/hwmon/hwmon0/
    """
    def __str__(self):
        return str("device/hwmon/hwmon0/%s" % self.name)
    
    pwm1 = "pwm1"
    pwm1_enable = "pwm1_enable"
    pwm1_min = "pwm1_min"
    pwm1_max = "pwm1_max"
    temp1_input = "temp1_input"
    temp1_crit = "temp1_crit"
    fan1_input = "fan1_input"
    power1_cap = "power1_cap"
    power1_average = "power1_average"
    in0_input = "in0_input"

class sysfs_device(Enum):
    """
    Enums that are related to sysfs interfaces found in
    /sys/class/drm/cardN/device/
    """
    def __str__(self):
        return str("device/%s" % self.name)

    #current_link_width = "current_link_width"
    #current_link_speed = "current_link_speed"
    pp_dpm_mclk = "pp_dpm_mclk"
    pp_dpm_pcie = "pp_dpm_pcie"
    pp_dpm_sclk =  "pp_dpm_sclk"
    power_dpm_state = "power_dpm_state"
    pp_power_profile_mode = "pp_power_profile_mode"
    power_dpm_force_performance_level = "power_dpm_force_performance_level"

class power_dpm_force_performance_level_profile:
    def __init__(self, data):
        pass
class pp_power_profile:
    def __init__(self, data):
        if "*:" in data:
            data[2] = "True"
        else:
            data.insert(2, "False")

        self.__data = {
            "NUM" : data[0],
            "MODE_NAME" : data[1].replace(":", "").replace("_", " "),
            "ACTIVE" : data[2],
            "SCLK_UP_HYST" : data[3],
            "SCLK_DOWN_HYST" : data[4],
            "SCLK_ACTIVE_LEVEL" : data[5],
            "MCLK_UP_HYST" : data[6],
            "MCLK_DOWN_HYST" : data[7],
            "MCLK_ACTIVE_LEVEL" : data[0]
        }

    @property 
    def num(self):
        return self.__data["NUM"]
    @property
    def active(self):
        return self.__data["ACTIVE"]
    @property 
    def mode_name(self):
        return self.__data["MODE_NAME"]
    @property 
    def sclk_up_hyst(self):
        return self.__data["SCLK_UP_HYST"]
    @property 
    def sclk_down_hyst(self):
        return self.__data["SCLK_DOWN_HYST"]
    @property 
    def sclk_active_level(self):
        return self.__data["SCLK_ACTIVE_LEVEL"]
    @property 
    def mclk_up_hyst(self):
        return self.__data["MCLK_UP_HYST"]
    @property 
    def mclk_down_hyst(self):
        return self.__data["MCLK_DOWN_HYST"]
    @property 
    def mclk_active_level(self):
        return self.__data["MCLK_ACTIVE_LEVEL"]


class HwMon:
    def __init__(self, card = 0):
        self._card = card
    
    def __setperms(self, path):
        os.system('python3 %s/common/setperms.py %s' % (os.getcwd(), path) )

    def __getvalue(self, path):
        try:
            file = open(HWMON_SYSFS_PATH % (self._card, path), "r")
            value = file.read().strip()
        except Exception as e:
            raise e
            
        return value
    
    def __setvalue(self, interface, value):
        path = HWMON_SYSFS_PATH % (self._card, interface)
        try:
            self.__setperms(path)

            with open(path, "w") as file:
                file.write(str(value))
        except Exception as e:
            print("__setvalue(%s, %s) failed: %s" % (interface.name, value, e))
        else:
            print("__setvalue(%s, %s) success" % (interface.name, value) )

    @property
    def pwm1(self):
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.pwm1))
    @pwm1.setter
    def pwm1(self, value):
        """
        pulse width modulation fan level (0-255)
        """
        if (not isinstance(value, int)):
            raise TypeError("value must be an integer")
        if ((value < 0) or (value > self.pwm1_max)):
            raise ArithmeticError("value is not within range")
        self.__setvalue(sysfs_device_hwmon_hwmon0.pwm1, value)


    @property
    def pwm1_enable(self):
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.pwm1_enable))

    @pwm1_enable.setter
    def pwm1_enable(self, pwmstate = accepted_pwm1_enable.Auto):
        """
        pulse width modulation fan control method (0: no fan speed control, 1: manual fan speed control using pwm interface, 2: automatic fan speed control)
        """
        if not isinstance(pwmstate, accepted_pwm1_enable):
            raise TypeError("pwmstate must be an instance of accepted_pwm1_enable Enum")
        
        self.__setvalue(sysfs_device_hwmon_hwmon0.pwm1_enable, pwmstate.value)
    
    @property
    def pwm1_min(self):
        """
        pulse width modulation fan control minimum level (0)
        """
        return 0
        #return self.__getvalue(Interface.pwm1_min)

    @property
    def pwm1_max(self):
        """
        pulse width modulation fan control maximum level (255)
        """
        return 255
        #return self.__getvalue(Interface.pwm1_max)

    @property
    def temp1_input(self):
        """
        the on die GPU temperature in millidegrees Celsius
        """
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.temp1_input))

    @property
    def temp1_crit(self):
        """
        temperature critical max value in millidegrees Celsius
        """
        return int(int(self.__getvalue(sysfs_device_hwmon_hwmon0.temp1_crit)))

    @property
    def fan1_input(self):
        """
        fan speed in RPM
        """
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.fan1_input))

    @property
    def power1_average(self):
        """
        average power used by the GPU in microWatts
        """
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.power1_average))

    @property
    def in0_input(self):
        """
        the voltage on the GPU in millivolts
        """
        return int(self.__getvalue(sysfs_device_hwmon_hwmon0.in0_input))

    @property
    def pp_dpm_mclk(self):
        """
        available power levels within the power state and the clock information for those levels
        use pp_dpm_mclk_mhz to retrieve the current state in megahertz
        """
        return self.__getvalue(sysfs_device.pp_dpm_mclk)
    @pp_dpm_mclk.setter
    def pp_dpm_mclk(self, levels):
        """
        available power levels within the power state and the clock information for those levels 
        specify a list of integers that contain the levels to be enabled, you may use -1 to enable all levels
        """
        data = str(self.pp_dpm_mclk).splitlines()
        output = ''

        if (levels == -1):
            levels = range(len(data) - 1)
        else:
            if not isinstance(levels, list):
                raise TypeError("levels must be a list")
            if not all(isinstance(i, int) for i in levels):
                raise TypeError("levels must only contain a list of integers")

        for level in sorted(levels):
            if (not level in range(len(data) - 1)):
                raise ArithmeticError("level %d is out-of-range (range:0-%d)" % (level, len(levels)))
                
            print("enabling pp_dpm_mclk: %d (%s)" %(level, data[level]))

            output = "%s %d" % (output, level)
        self.__setvalue(sysfs_device.pp_dpm_mclk, output)

    @property
    def pp_dpm_mclk_mhz(self):
        """
        current power level state memory clock in megahertz 
        """
        for line in str(self.__getvalue(sysfs_device.pp_dpm_mclk)).splitlines():
            if "*" in line:
                return line[3:-5]

        return 0

    @property
    def pp_dpm_sclk(self):
        """
        available power levels within the power state and the clock information for those levels 
        """
        return self.__getvalue(sysfs_device.pp_dpm_sclk)
    @pp_dpm_sclk.setter
    def pp_dpm_sclk(self, levels):
        """
        available power levels within the power state and the clock information for those levels 
        specify a list of integers that contain the levels to be enabled, you may use -1 to enable all levels
        """
        data = str(self.pp_dpm_sclk).splitlines()
        output = ''

        if (levels == -1):
            levels = range(len(data) - 1)
        else:
            if not isinstance(levels, list):
                raise TypeError("levels must be a list")
            if not all(isinstance(i, int) for i in levels):
                raise TypeError("levels must only contain a list of integers")

        for level in sorted(levels):
            if (not level in range(len(data) - 1)):
                raise ArithmeticError("level %d is out-of-range (range:0-%d)" % (level, len(levels)))
                
            #print("enabling pp_dpm_sclk: %d (%s)" %(level, data[level]))
            output = "%s %d" % (output, level)
        #print("pp_dpm_sclk ")
        self.__setvalue(sysfs_device.pp_dpm_sclk, output)

    @property
    def pp_dpm_sclk_mhz(self):
        """
        current power level state core clock in megahertz 
        """
        for line in str(self.__getvalue(sysfs_device.pp_dpm_sclk)).splitlines():
            if "*" in line:
                return line[3:-5]

    @property
    def pp_power_profile_mode(self):
        """
        The amdgpu driver provides a sysfs API for adjusting the heuristics 
        related to switching between power levels in a power state. 
        use pp_power_profile_mode_index to return the current index
        """
        return self.__getvalue(sysfs_device.pp_power_profile_mode)
    @pp_power_profile_mode.setter
    def pp_power_profile_mode(self, value):
        values = self.pp_power_profile_list

        if not isinstance(value, int):
            raise TypeError("value must be an integer")
        if (not value in range(len(values) - 1)):
            raise ArithmeticError("value %d is out-of-range (range:0-%d)" % (value, len(values)))
        
        self.__setvalue(sysfs_device.pp_power_profile_mode, value)
    @property
    def pp_power_profile_list(self):
        """
        list of pp_power_profiles containing all data read from pp_power_profile_mode
        """
        result = []

        lines = str(self.pp_power_profile_mode).splitlines()
        del lines[0]

        for line in lines:
            result.append ( pp_power_profile(line.split()) )

        return result

    @property
    def pp_power_profile_mode_active(self):
        for profile in self.pp_power_profile_list:
            if (profile.active):
                return profile

    @property
    def power_dpm_force_performance_level(self):
        return self.__getvalue(sysfs_device.power_dpm_force_performance_level)
    @property
    def power_dpm_force_performance_level_list(self):
        """
        list of available power_dpm_force_performance_levels
        """
        result = []

        lines = str(self.power_dpm_force_performance_level).splitlines()
        del lines[0]

        for line in lines:
            result.append ( power_dpm_force_performance_level_profile(line.split()) )

        return result
    @power_dpm_force_performance_level.setter
    def power_dpm_force_performance_level(self, value):
        """
        control available power related parameters
        """
        if not isinstance(value, accepted_power_dpm_force_performance_level):
            raise TypeError("value must be an instance of accepted_power_dpm_force_performance_level")
        if (sysfs_device.power_dpm_force_performance_level.value != value.value):
            self.__setvalue(sysfs_device.power_dpm_force_performance_level, value.value)
        
    @property
    def power_dpm_state(self):
        return self.__getvalue(sysfs_device.power_dpm_state)
    @power_dpm_state.setter
    def power_dpm_state(self, value):
        """
        deprecated function added for older hardware
        """
        if not isinstance(value, accepted_power_dpm_state):
            raise TypeError("value must be an instance of accepted_power_dpm_state")
        if (sysfs_device.power_dpm_state.value != value.value):
            self.__setvalue(sysfs_device.power_dpm_state, value.value)
