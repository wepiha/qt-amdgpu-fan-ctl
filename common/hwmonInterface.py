import os
import logging
from enum import Enum
#
# Documentation for the amdgpu hwmon interfaces
# Source: https://www.kernel.org/doc/html/latest/gpu/amdgpu.html#hwmon-interfaces 
#

LOG = logging.getLogger(__name__)

HWMON_SYSFS_DIR = "/sys/class/hwmon/"
SUPPORTED_SYSFS_NAMES = ['amdgpu']

class accepted_pwm1_enable(Enum):
    """
    Enum class for control state

    Disabled = 0
    Manual = 1
    Auto = 2
    """
    def __str__(self):
        return str(self.name)
    Disabled = 0
    Manual = 1
    Auto = 2

class accepted_power_dpm_force_performance_level(Enum):
    """Enum class for forced performance level

    auto = "auto"
    low = "low"
    high = "high"
    manual = "manual"
    profile_standard = "profile_standard"
    profile_min_sclk = "profile_min_sclk"
    profile_min_mclk = "profile_min_mclk"
    profile_peak = "profile_peak"
    """
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
    """
    Enum class for acceptable power dpm states


    battery = "battery"
    balanced = "balanced"
    performance = "performance"
    """
    def __str__(self):
        return str(self.name)
    battery = "battery"
    balanced = "balanced"
    performance = "performance"

class accepted_pp_dpm_sclk(dict):
    """
    create a dictionary of accepted pp_dpm_sclk speeds from the current power level state 
    """
    def __init__(self, values: str):
        index = 0
        for value in str(values).splitlines():
            self[index] = {
                'active': ('*' in value),
                'value': int(value[3:].replace('Mhz', '').replace('*', '').strip())
            }
            index += 1

class sysfs_device_hwmon(Enum):
    """
    Enum class of sysfs device capabilities
    """
    def __str__(self):
        return str(self.name)
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

class sysfs_device_hwmon_monitors_amdgpu(Enum):
    # FIXME: the maximum values should be acquired from hardware/other instead of fixed 
    temp1_input = {
        'attribute': 'temp1_input_degrees',
        'descriptor': 'Temperature',
        'maximum': 120,
        'unit': '°C'
    }
    fan1_input = {
        'attribute': 'fan1_input',
        'descriptor': 'Fan Speed',
        'maximum': 4000,
        'unit': 'RPM'
    }
    pp_dpm_mclk_mhz = { 
        'attribute': 'pp_dpm_mclk_mhz',
        'descriptor': 'Memory Clock',
        'maximum': 2500,
        'unit': 'MHz'
    }
    pp_dpm_sclk_mhz = { 
        'attribute': 'pp_dpm_sclk_mhz',
        'descriptor': 'Core Clock',
        'maximum': 2500,
        'unit': 'MHz'
    }
    power1_average = {
        'attribute': 'power1_average_watts',
        'descriptor': 'Power Average',
        'maximum': 500,
        'unit': 'W'
    }

class sysfs_device(Enum):
    """
    Enums that are related to sysfs interfaces found in
    /sys/class/drm/cardN/device/
    """
    def __str__(self):
        return f"device/{self.name}"

    current_link_width = "current_link_width"
    current_link_speed = "current_link_speed"
    pp_dpm_mclk = "pp_dpm_mclk"
    pp_dpm_pcie = "pp_dpm_pcie"
    pp_dpm_sclk =  "pp_dpm_sclk"
    power_dpm_state = "power_dpm_state"
    pp_power_profile_mode = "pp_power_profile_mode"
    power_dpm_force_performance_level = "power_dpm_force_performance_level"

class sysfs_device_power(Enum):
    """
    Enums that are related to sysfs interfaces found in
    /sys/class/drm/cardN/device/power/
    """
    def __str__(self):
        return f"device/power/{self.name}"

    runtime_usage = "runtime_usage"

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
    """
    The amdgpu driver exposes the following sensor interfaces:

        GPU temperature (via the on-die sensor)
        GPU voltage
        Northbridge voltage (APUs only)
        GPU power
        GPU fan

    hwmon interfaces for GPU temperature:

        temp1_input: the on die GPU temperature in millidegrees Celsius
        temp1_crit: temperature critical max value in millidegrees Celsius
        temp1_crit_hyst: temperature hysteresis for critical limit in millidegrees Celsius

    hwmon interfaces for GPU voltage:

        in0_input: the voltage on the GPU in millivolts
        in1_input: the voltage on the Northbridge in millivolts

    hwmon interfaces for GPU power:

        power1_average: average power used by the GPU in microWatts
        power1_cap_min: minimum cap supported in microWatts
        power1_cap_max: maximum cap supported in microWatts
        power1_cap: selected power cap in microWatts

    hwmon interfaces for GPU fan:

        pwm1: pulse width modulation fan level (0-255)
        pwm1_enable: pulse width modulation fan control method (0: no fan speed control, 1: manual fan speed control using pwm interface, 2: automatic fan speed control)
        pwm1_min: pulse width modulation fan control minimum level (0)
        pwm1_max: pulse width modulation fan control maximum level (255)
        fan1_min: an minimum value Unit: revolution/min (RPM)
        fan1_max: an maxmum value Unit: revolution/max (RPM)
        fan1_input: fan speed in RPM
        fan[1-*]_target: Desired fan speed Unit: revolution/min (RPM)
        fan[1-*]_enable: Enable or disable the sensors.1: Enable 0: Disable
    """
    def __init__(self, interface = 0):
        self.__interfaces = self.__getinterfaces()
        self.interface = interface

        self.update_ext_attributes()

    def __getinterfaces(self) -> tuple:
        valid_interfaces = {}

        # look at every device in the sysfs directory
        for sysfs_dev in os.scandir(HWMON_SYSFS_DIR):

            # we only want subdirectories, not files here
            if not sysfs_dev.is_dir():
                continue
            
            # check if the name exists, and ensure it matches a valid device node
            if os.path.isfile(f'{sysfs_dev.path}/name'):
                sysfs_name = open(f'{sysfs_dev.path}/name').read().strip()

                if (sysfs_name in SUPPORTED_SYSFS_NAMES):
                    valid_interfaces[len(valid_interfaces)] = { 
                        'name': sysfs_name, 
                        'path': sysfs_dev.path 
                    }
        
        return valid_interfaces

    def __setperms(self, path):
        os.system(f'python3 {os.getcwd()}/common/setperms.py {path}')

    def __getvalue(self, path):
        try:
            sysfs_file = f'{self.__interface["path"]}/{path}'
            if not os.path.isfile(sysfs_file):
                return "Unsupported"

            value = open(sysfs_file, "r").read().strip()
        except Exception as e:
            raise e
            
        return value
    
    def __setvalue(self, path: str, value: str) -> bool:
        sysfs_file = f'{self.__interface["path"]}/{path}'
        try:
            self.__setperms(sysfs_file)
            
            open(sysfs_file, "w").write(str(value))
        except Exception as e:
            LOG.info(f"__setvalue({path}, {value})::failed: {e}")
            return False
        else:
            LOG.info(f"__setvalue({path}, {value})::success")
            return True

    @property
    def interfaces(self) -> list:
        return self.__interfaces

    @property
    def interface(self):
        return self.__interface
    @interface.setter
    def interface(self, value):
        if value not in self.__interfaces:
            raise IndexError(f'{value} is out of range of 0-{len(self._interfaces)}')
        
        self.__interface = self.__interfaces[value]

    def update_ext_attributes(self):
        """
        adds or updates extended min and max attributes, for those 
        devices in `sysfm_device_hwmon_monitors`
        """
        for monitor in sysfs_device_hwmon_monitors_amdgpu:
            base_attr = monitor.value['attribute']
            new_value = int(getattr(self, base_attr))

            for ext_attr in ['min', 'max']:
                full_attr = f'{base_attr}_{ext_attr}'
                
                curr_value = int(getattr(self, full_attr, new_value))

                if ((ext_attr == 'min') and (new_value < curr_value)) or ((ext_attr == 'max') and (new_value > curr_value)):
                    curr_value = new_value

                setattr(self, full_attr, curr_value)
    
    @property
    def name(self):
        return str(self.__getvalue(sysfs_device_hwmon.name))

    @property
    def pwm1(self):
        return int(self.__getvalue(sysfs_device_hwmon.pwm1))
    @pwm1.setter
    def pwm1(self, value):
        """
        pulse width modulation fan level (0-255)
        """
        if (not isinstance(value, int)):
            raise TypeError("value must be an integer")
        if ((value < 0) or (value > self.pwm1_max)):
            raise ArithmeticError("value is not within range")
        self.__setvalue(sysfs_device_hwmon.pwm1, value)

    @property
    def pwm1_enable(self):
        return int(self.__getvalue(sysfs_device_hwmon.pwm1_enable))

    @pwm1_enable.setter
    def pwm1_enable(self, pwmstate = accepted_pwm1_enable.Auto):
        """
        pulse width modulation fan control method (0: no fan speed control, 1: manual fan speed control using pwm interface, 2: automatic fan speed control)
        """
        if not isinstance(pwmstate, accepted_pwm1_enable):
            raise TypeError("pwmstate must be an instance of accepted_pwm1_enable Enum")
        
        self.__setvalue(sysfs_device_hwmon.pwm1_enable, pwmstate.value)
    
    @property
    def pwm1_min(self):
        """
        pulse width modulation fan control minimum level (0)
        """
        #return 0
        return int(self.__getvalue(sysfs_device_hwmon.pwm1_min))

    @property
    def pwm1_max(self):
        """
        pulse width modulation fan control maximum level (255)
        """
        #return 255
        return int(self.__getvalue(sysfs_device_hwmon.pwm1_max))

    @property
    def temp1_input(self):
        """
        the on die GPU temperature in millidegrees Celsius
        """
        return int(self.__getvalue(sysfs_device_hwmon.temp1_input))

    @property
    def temp1_input_degrees(self):
        """
        the on die GPU temperature in degrees Celsius
        """
        return int(self.temp1_input / 1000)

    @property
    def temp1_crit(self):
        """
        temperature critical max value in millidegrees Celsius
        """
        return int(int(self.__getvalue(sysfs_device_hwmon.temp1_crit)))

    @property
    def temp1_crit_degrees(self):
        return int(self.temp1_crit / 1000)

    @property
    def fan1_input(self):
        """
        fan speed in RPM
        """
        return int(self.__getvalue(sysfs_device_hwmon.fan1_input))

    @property
    def power1_average(self):
        """
        average power used by the GPU in microWatts
        """
        return int(self.__getvalue(sysfs_device_hwmon.power1_average))

    @property
    def power1_average_watts(self):
        """
        average power used by the GPU in microWatts
        """
        return int(self.power1_average / 1000000)

    @property
    def in0_input(self):
        """
        the voltage on the GPU in millivolts
        """
        return int(self.__getvalue(sysfs_device_hwmon.in0_input))

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
                raise ArithmeticError(f"level {level} is out-of-range (range:0-{len(levels)})")
                
            LOG.info(f"enabling pp_dpm_mclk: {level} ({data[level]})")

        output = f"{output} {level}"
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
                raise ArithmeticError(f"level {level} is out-of-range (range:0-{len(levels)})")
                
            LOG.info(f"enabling pp_dpm_sclk: {level} ({data[level]})")

            output = f"{output} {level}"
            
        self.__setvalue(sysfs_device.pp_dpm_sclk, output)

    @property
    def pp_dpm_sclk_mhz(self):
        """
        current power level state core clock in megahertz 
        """
        for sclk in accepted_pp_dpm_sclk(self.__getvalue(sysfs_device.pp_dpm_sclk)).values():
            if sclk['active']:
                return sclk['value']

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
            raise ArithmeticError(f"value {value} is out-of-range (range:0-{len(values)})")
        
        self.__setvalue(sysfs_device.pp_power_profile_mode, value)
    @property
    def pp_power_profile_list(self):
        """
        list of pp_power_profiles containing all data read from pp_power_profile_mode
        """
        # FIXME: the result should be a new class that stores the values
        result = []

        lines = str(self.pp_power_profile_mode).splitlines()
        del lines[0]

        for line in lines:
            result.append ( pp_power_profile(line.split()) )

        return result

    @property
    def pp_power_profile_mode_active(self) -> pp_power_profile:
        """
        returns the active pp_power_profile_mode
        """
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

    @property
    def current_link_speed(self):
        return self.__getvalue(sysfs_device.current_link_speed)

    @property
    def runtime_usage(self):
        return self.__getvalue(sysfs_device_power.runtime_usage)