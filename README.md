## qt-amdgpu-fan-ctl
Python script which enables a GUI controllable fan-curve for the AMDGPU driver under GNU/Linux

### License
GNU GPLv3

### Requirements
- Qt5
- Python3
- pyqtgraph
- numpy

You can either have run the script as root
> sudo python3 ./qt-amdgpu-fan-ctl.py

AND/OR

Allow SUDO with NOPASSWD:ALL for sudoers
> $USER ALL=(ALL) NOPASSWD:ALL

### Basic functionality:
- [x] Set GPU fan curve using GUI
- [x] Near-unlimited control points
- [x] Save fan curve state
- [ ] Handle multiple GPU fan profiles
- [x] Monitor GPU temperature
- [x] Monitor GPU fan speed
- [x] Monitor GPU power
- [ ] Monitor a lot more
- [ ] Configuration (log settings, SI units, enable/disable features like colorization, graph options)

### Screenshot:
![Image showing GUI with gpu fan curve plot and various controls](media/screenshot.png "Main GUI")

Screencap is from and older build, and will change rapidly now the kernel interface can be added to easily
