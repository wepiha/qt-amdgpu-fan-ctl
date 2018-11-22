## qt-amdgpu-fan-ctl
Python script which enables a GUI controllable fan-curve for the AMDGPU driver under GNU/Linux

### License
GNU GPLv3

### Requirements
- Python3
- numpy
- pyqtgraph

You must have SUDO abilities, and NOPASSWD:ALL for sudoers
> $USER ALL=(ALL) NOPASSWD:ALL

### Basic functionality:
- Set GPU fan curve using GUI
- Near-unlimited control points
- Save fan curve state
- Monitor GPU temperature
- Monitor GPU fan speed

### Screenshot:
![Image showing GUI with gpu fan curve plot and various controls](media/qt-amdgpu-fan-ctl.gif "Main GUI")

### TODO:
- Handle multiple GPU fan profiles
- System information panel / window
- Better reflect SYSTEM / MANUAL status

## Known Issues:
- Fan speed shown on graph differs from hardware (will not fix)