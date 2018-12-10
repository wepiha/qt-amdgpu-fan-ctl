# -*- coding: utf-8 -*-

import sys, os
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

import json
import pyqtgraph as pg
import ui.mainwindow as mainwindow
 
from PyQt5 import QtCore, QtGui, QtWidgets

from common import hwmonInterface
from common.fancurvegraph  import FanCurveGraph
from common.config import (Config, CONFIG_INTERVAL_VAR, CONFIG_POINT_VAR)

VIEW_LIMITER = 110
VIEW_MIN = -3

QLABEL_STYLE_SHEET = "QLabel { color: white; background-color: %s; }"

hwmon = hwmonInterface.HwMon()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.myConfig = Config()
        self.timerUI = QtCore.QTimer()
        self.timerCtl = QtCore.QTimer() 

        self.lastFanValue = -1

        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.spinBoxInterval.valueChanged.connect(self.spinBoxIntervalChanged)
        self.ui.pushButtonEnable.clicked.connect(self.buttonEnableClicked)
        self.ui.pushButtonSave.clicked.connect(self.buttonSaveClicked)
        self.ui.pushButtonClose.clicked.connect(self.close)
        self.ui.comboBoxPerfProfile.currentTextChanged.connect(self.comboBoxPerfProfileChanged)
        self.timerUI.timeout.connect(self.timerUpdateTick)
        self.timerCtl.timeout.connect(self.timerCtlTick)
        self.timerUI.start()
        self.timerCtl.start(250)

        self.spinBoxIntervalChanged(self.myConfig.getValue(CONFIG_INTERVAL_VAR))

        pg.setConfigOptions(antialias=True)
        gv = self.ui.graphicsView

        gv.setLabels(left=('Fan Speed', '%'), bottom=("Temperature", '°C'))
        gv.setMenuEnabled(False)
        gv.setAspectLocked(True)
        gv.showGrid(x=True, y=True, alpha=0.1)
        gv.getAxis('bottom').setTickSpacing(10, 1)
        gv.getAxis('left').setTickSpacing(10, 5)
        gv.hideButtons()
        gv.setLimits(
            xMin = VIEW_MIN,
            yMin = VIEW_MIN,
            xMax = VIEW_LIMITER + VIEW_MIN,
            yMax = VIEW_LIMITER + VIEW_MIN,
            minXRange = VIEW_LIMITER,
            maxXRange = VIEW_LIMITER,
            minYRange = VIEW_LIMITER,
            maxYRange = VIEW_LIMITER
        )

        graph = FanCurveGraph(gv, data=self.myConfig.getValue(CONFIG_POINT_VAR), name='graph', staticPos=[hwmon.temp1_crit / 1000, 100])
        pen = pg.mkPen('w', width=0.2, style=QtCore.Qt.DashLine)

        lineCurrTemp = pg.InfiniteLine(pos=0, pen=pen, name="currTemp", angle=270)
        lineCurrFan = pg.InfiniteLine(pos=0, pen=pen, name="currFan", angle=0)

        pg.InfLineLabel(lineCurrTemp, text="Temp", position=0.7, rotateAxis=(2,0))
        pg.InfLineLabel(lineCurrFan, text="Fan", position=0.15, rotateAxis=(0,0))

        textLabelXY = pg.TextItem()

        scatterItem = pg.ScatterPlotItem(pen=pg.mkPen('r'))
        scatterItem._name = 'tMax'
        scatterItem.setData([int(hwmon.temp1_crit / 1000)], [100], symbol='d')

        targetTemp = pg.ScatterPlotItem(pen=pg.mkPen('#0000FF'))
        targetTemp._name = 'fTarget'
        targetTemp.setData([-10], [-10], symbol='d')

        legendItem = pg.LegendItem()
        legendItem.addItem(scatterItem, name='GPU tMax')
        legendItem.addItem(targetTemp, name='Fan PWM')
        legendItem.setPos(0, 100)

        gv.addItem(graph)
        gv.addItem(lineCurrTemp)
        gv.addItem(lineCurrFan)
        gv.addItem(textLabelXY)
        gv.addItem(targetTemp)
        gv.addItem(scatterItem)

        gv.addItem(legendItem)

        self.ui.pushButtonAdd.clicked.connect(graph.addPoint)
        self.ui.pushButtonRemove.clicked.connect(graph.removePoint)

        for level in hwmonInterface.accepted_power_dpm_force_performance_level:
            self.ui.comboBoxPerfProfile.addItem(level.name.title())

        self.lastUpdate = hwmon.temp1_input
        self.hysteresis = self.lastUpdate / 1000
  
    def closeEvent(self, *args, **kwargs):
        if (hwmonInterface.accepted_pwm1_enable(hwmon.pwm1_enable) == hwmonInterface.accepted_pwm1_enable.Manual):
            hwmon.pwm1_enable = hwmonInterface.accepted_pwm1_enable.Auto

    def buttonEnableClicked(self, value):
        hwmon.pwm1_enable = hwmonInterface.accepted_pwm1_enable.Manual if value else hwmonInterface.accepted_pwm1_enable.Auto
    def buttonSaveClicked(self):
        self.myConfig.save()

    def spinBoxIntervalChanged(self, value):
        self.myConfig.setValue(CONFIG_INTERVAL_VAR, value)
        self.timerUI.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))
    
    def comboBoxPerfProfileChanged(self, value):
        for level in hwmonInterface.accepted_power_dpm_force_performance_level:
            if (str(value.lower()) == str(level)):
                hwmon.power_dpm_force_performance_level = level

    def getSceneItem(self, name):
        for item in self.ui.graphicsView.plotItem.items:
            if (hasattr(item, '_name')) and (item._name == name):
                return item
        
        raise LookupError("The item '%s' was not found" % name)
    
    def timerUpdateTick(self):
        self.myConfig.setValue(CONFIG_POINT_VAR, self.getSceneItem('graph').pos.tolist())

        pwm1_max = hwmon.pwm1_max
        #temp1_input = hwmon.temp1_input / 1000
        temp1_input = self.hysteresis
        temp1_crit = hwmon.temp1_crit / 1000
        pwm1_enable = hwmon.pwm1_enable

        targetSpeed = int((self.getSceneItem('graph').getIntersection(x=temp1_input) / 100) * pwm1_max)
        fanSpeed = int((hwmon.pwm1 / pwm1_max) * 100)
        
        r = int((temp1_input / temp1_crit) * 255)
        g = 255 - r
        
        if (hwmonInterface.accepted_pwm1_enable(pwm1_enable) == hwmonInterface.accepted_pwm1_enable.Manual):
            if (self.lastFanValue != targetSpeed):
                hwmon.pwm1 = targetSpeed
                self.lastFanValue = targetSpeed
            color = "#ff5d00"
            button = "Disable"
            y = [(targetSpeed / 255) * 100]
        else:
            color = "#0000ff"
            button = "Enable"
            y = [fanSpeed]
        
        self.getSceneItem('fTarget').setPen(color)
        self.getSceneItem('fTarget').setData(temp1_input, y)

        self.getSceneItem('currTemp').setValue(temp1_input)
        self.getSceneItem('currFan').setValue(fanSpeed)

        self.ui.labelTemperature.setText("%s °C" % temp1_input)
        self.ui.labelTemperature.setStyleSheet(QLABEL_STYLE_SHEET % '#{:02x}{:02x}{:02x}'.format(r, g, 0))

        self.ui.labelFanSpeed.setText("%s RPM" % hwmon.fan1_input)

        self.ui.labelFanProfileStatus.setText("%s" % hwmonInterface.accepted_pwm1_enable(pwm1_enable))
        self.ui.labelFanProfileStatus.setStyleSheet(QLABEL_STYLE_SHEET % color)

        self.ui.pushButtonEnable.setText(button)
        self.ui.pushButtonEnable.setChecked(hwmonInterface.accepted_pwm1_enable(pwm1_enable) == hwmonInterface.accepted_pwm1_enable.Manual)

        self.ui.labelPower.setText("%.1f W" % (hwmon.power1_average / 1000000))
        self.ui.labelVoltage.setText("%d mV" % hwmon.in0_input)

        self.ui.labelMemClock.setText("%s MHz" % hwmon.pp_dpm_mclk_mhz)
        self.ui.labelCoreClock.setText("%s MHz" % hwmon.pp_dpm_sclk_mhz)

        self.ui.comboBoxPerfProfile.setCurrentText(hwmon.power_dpm_force_performance_level.title())

        self.ui.labelPowerProfile.setText(hwmon.pp_power_profile_mode_active.mode_name.title())

    def timerCtlTick(self):
        self.hysteresis = (hwmon.temp1_input + self.lastUpdate) / 2000
        self.lastUpdate = hwmon.temp1_input
        

app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
