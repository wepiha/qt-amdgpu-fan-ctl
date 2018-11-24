## qt-amdgpu-fan-ctl
Python script which enables a GUI controllable fan-curve for the AMDGPU driver under GNU/Linux

### License
GNU GPLv3

### Requirements
- Qt5
- Python3
- pyqtgraph
- numpy


### System Control
To enable control (fan, performance levels, etc) the amdgpu sysfs interface requires ownership of the path,
it isn't necessary to have root permissions to have read access, it is only required for writing, therefore

You can either have run the script as root
> sudo python3 ./qt-amdgpu-fan-ctl.py

AND/OR

Allow SUDO with NOPASSWD:ALL for sudoers
> $USER ALL=(ALL) NOPASSWD:ALL


### Functionality:
- [x] Monitor GPU temperature, fan speed, performance levels, clock speeds etc!
- [x] Set and save GPU fan curve with near-unlimited control points
- [x] Monitor and set PowerPlay profile
- [ ] Handle multiple GPU fan profiles
- [ ] Overclocking Interface
- [ ] Configuration (log settings, SI units, enable/disable features like colorization, graph options)

### Screenshot:
![Image showing GUI with gpu fan curve plot and various controls](media/screenshot.png "Main GUI")

###### Screencap may differ from current build
