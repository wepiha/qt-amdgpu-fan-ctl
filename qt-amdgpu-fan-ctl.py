# -*- coding: utf-8 -*-

import sys, os
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

import json
import pyqtgraph as pg
import ui.mainwindow as mainwindow
 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette

from common import hwmonInterface
from common.fancurvegraph  import FanCurveGraph
from common.config import (Config, CONFIG_INTERVAL_VAR, CONFIG_POINT_VAR)

VIEW_LIMITER = 110
VIEW_MIN = -3

UI_QLABEL_BG_CSS = "QLabel { color: white; background-color: %s; }"
UI_DARK_ROUND_CSS = "background-color: %s; border-style: solid; border-color: %s; border-width: 2px; border-radius: 3px;"

GRAPHITEM_NAME = 'graph'


hwmon = hwmonInterface.HwMon()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.myConfig = Config()

        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self._init_defaultvalues()

        self._init_graphview()
        self._init_timers()
        self._init_pyqtsignals()
        self._init_drivervalues()
        self._init_styles()

    def _init_timers(self):
        """ Initializes timers and starts them """
        self.timerUI = QtCore.QTimer()
        self.timerUI.timeout.connect(self._timer_update_tick)
        self.timerUI.start()

        self.timerCtl = QtCore.QTimer() 
        self.timerCtl.timeout.connect(self.timer_ctrl_tick)
        self.timerCtl.start(250)

    def _init_pyqtsignals(self):
        """ Connects pyqt5 signals to various slots """
        self.ui.spinBoxInterval.valueChanged.connect(self._spin_interval_changed)
        self.ui.pushButtonEnable.clicked.connect(self._button_enable_clicked)
        self.ui.pushButtonSave.clicked.connect(self._button_save_clicked)
        self.ui.pushButtonClose.clicked.connect(self.close)
        self.ui.comboBoxPerfProfile.currentTextChanged.connect(self._combo_perf_profile_changed)

        self._spin_interval_changed(self.myConfig.getValue(CONFIG_INTERVAL_VAR))

        self.ui.pushButtonAdd.clicked.connect(self._get_plotwidget_item(GRAPHITEM_NAME).addPoint)
        self.ui.pushButtonRemove.clicked.connect(self._get_plotwidget_item(GRAPHITEM_NAME).removePoint)

    def _init_graphview(self):
        """ 
        Initializes the graph widgets
        """
        self._init_graph()
        self._init_graph_lines()
        self._init_graph_legend()
        self._init_graph_coords()

    def _init_graph(self):
        """ 
        Initializes the `PlotWidget` (base class: `graphicsView`):
        - Adds xy labels for Fan Speed and Temperature
        - Sets and locks the viewport, disables the right-click menu
        - Shows the Grid, and sets the Tick Spacing
        - Adds a `FanCurveGraph` which allows for point manipulation (base class: `pyqtgraph.GraphItem`)
        """
        self.ui.graphicsView.setLabels(left=('Fan Speed', '%'), bottom=("Temperature", '°C'))
        self.ui.graphicsView.setMenuEnabled(False)
        self.ui.graphicsView.setAspectLocked(True)
        self.ui.graphicsView.hideButtons()
        self.ui.graphicsView.showGrid(x=True, y=True, alpha=0.1)
        self.ui.graphicsView.getAxis('bottom').setTickSpacing(10, 1)
        self.ui.graphicsView.getAxis('left').setTickSpacing(10, 5)
        self.ui.graphicsView.setLimits(
            xMin = VIEW_MIN,
            yMin = VIEW_MIN,
            xMax = VIEW_LIMITER + VIEW_MIN,
            yMax = VIEW_LIMITER + VIEW_MIN,
            minXRange = VIEW_LIMITER,
            maxXRange = VIEW_LIMITER,
            minYRange = VIEW_LIMITER,
            maxYRange = VIEW_LIMITER
        )

        graph = FanCurveGraph(self.ui.graphicsView, data=self.myConfig.getValue(CONFIG_POINT_VAR), name=GRAPHITEM_NAME, staticPos=[hwmon.temp1_crit / 1000, 100])

        self.ui.graphicsView.addItem(graph)
       
    def _init_graph_lines(self):
        """ 
        Adds `InfiniteLine` for x and y axis to display the current Fan Speed and Temperature 
        """
        pen = pg.mkPen('w', width=0.2, style=QtCore.Qt.DashLine)

        lineCurrTemp = pg.InfiniteLine(pos=0, pen=pen, name='currTemp', angle=270)
        lineCurrFan = pg.InfiniteLine(pos=0, pen=pen, name='currFan', angle=0)

        pg.InfLineLabel(lineCurrTemp, text="Temp {value}°C'", position=0.9, rotateAxis=(-1,0))
        pg.InfLineLabel(lineCurrFan, text="Fan {value}%", position=0.2, rotateAxis=(0,0))

        self.ui.graphicsView.addItem(lineCurrTemp)
        self.ui.graphicsView.addItem(lineCurrFan)

    def _init_graph_legend(self):
        """ Adds a `LegendItem` which has a `ScatterPlotItem` for both the Max Temperature and Fan Targets """
        legendItem = pg.LegendItem()
        
        tempMax = pg.ScatterPlotItem(pen=pg.mkPen('#ff0000'))
        tempMax._name = 'tMax'
        tempMax.setData([int(hwmon.temp1_crit / 1000)], [100], symbol='d')

        fanTarget = pg.ScatterPlotItem(pen=pg.mkPen('#0000ff'))
        fanTarget._name = 'fTarget'
        fanTarget.setData([-10], [-10], symbol='d')

        legendItem.addItem(tempMax, name='GPU tMax')
        legendItem.addItem(fanTarget, name='Fan PWM')
        legendItem.setPos(0, 100)

        self.ui.graphicsView.addItem(tempMax)
        self.ui.graphicsView.addItem(fanTarget)
        self.ui.graphicsView.addItem(legendItem)

    def _init_graph_coords(self):
        """ Adds a co-ordinate display to the `PlotWidget` when the user drags a point """
        dragCoordText = pg.TextItem()
        self.ui.graphicsView.addItem(dragCoordText)

    def _init_styles(self):
        """ Sets the UI styles for plot and display widgets"""
        darkbg = self.ui.centralwidget.palette().color(QPalette.Dark).name()

        self.ui.graphicsView.setBackground(darkbg)
        self.ui.graphicsView.setStyleSheet( UI_DARK_ROUND_CSS % ( darkbg, darkbg ) )
        self.ui.widget.setStyleSheet( UI_DARK_ROUND_CSS % ( darkbg, darkbg) )

    def _init_defaultvalues(self):
        """ Initializes `global` defaults """
        pg.setConfigOptions(antialias=True)

        self.lastUpdate = hwmon.temp1_input
        self.lastEnabled = False
        self.lastFanValue = -1
        self.hysteresis = self.lastUpdate / 1000

    def _init_drivervalues(self):
        """ Adds various data pieces to the `mainwindow` widgets """
        for level in hwmonInterface.accepted_power_dpm_force_performance_level:
            self.ui.comboBoxPerfProfile.addItem(level.name.title())

    def _mainwindow_close_event(self, *args, **kwargs):
        """ Handles `mainwindow` is close event"""
        # mainwindow is closing, reset the pwm1_enable to Auto if we have Manually set the value
        if (hwmonInterface.accepted_pwm1_enable(hwmon.pwm1_enable) == hwmonInterface.accepted_pwm1_enable.Manual):
            hwmon.pwm1_enable = hwmonInterface.accepted_pwm1_enable.Auto

    def _button_enable_clicked(self, value):
        """ Changes the control state """
        self.lastEnabled = value
        hwmon.pwm1_enable = hwmonInterface.accepted_pwm1_enable.Manual if value else hwmonInterface.accepted_pwm1_enable.Auto

    def _button_save_clicked(self):
        """ Saves and applies the fan curve """
        self.myConfig.setValue(CONFIG_POINT_VAR, self._get_plotwidget_item(GRAPHITEM_NAME).pos.tolist())
        self.myConfig.save()

    def _spin_interval_changed(self, value):
        """ Set the `mainwindow` timer timeout """
        self.myConfig.setValue(CONFIG_INTERVAL_VAR, value)
        self.timerUI.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))
    
    def _combo_perf_profile_changed(self, value):
        """ Set the `power_dpm_force_performance_level` when the user changes the value """
        for level in hwmonInterface.accepted_power_dpm_force_performance_level:
            if (str(value.lower()) == str(level)):
                hwmon.power_dpm_force_performance_level = level

    def _get_plotwidget_item(self, name):
        """ Helper function to acquire items added to the `PlotWidget` """
        for item in self.ui.graphicsView.plotItem.items:
            if (hasattr(item, '_name')) and (item._name == name):
                return item
        
        raise LookupError("The item '%s' was not found" % name)
    
    def _timer_update_tick(self):
        """ Event occurs on timertick from the Update Interval on the `mainwindow` """
        self._get_hwmon_values()
        self._refresh_ui()
        self._set_hwmon_values()

    def _get_hwmon_values(self):
        """ Retrieves values from `hwmon` interface and stores them in global variables """
        # acquire hardware values
        self.pwm1_max = hwmon.pwm1_max
        self.temp1_input = hwmon.temp1_input / 1000
        #temp1_input = self.hysteresis
        self.temp1_crit = hwmon.temp1_crit / 1000
        self.pwm1_enable = hwmon.pwm1_enable
        
        # calculate speed using trig
        self.targetSpeed = int((self._get_plotwidget_item(GRAPHITEM_NAME).getIntersection(x=self.temp1_input) / 100) * self.pwm1_max)
        self.fanSpeed = int((hwmon.pwm1 / self.pwm1_max) * 100)

    def is_manual_state_enabled(self):
        """ checks if the manual state is actually enabled in hardware """
        # compare the local value against it's corresponding enum
        return ( hwmonInterface.accepted_pwm1_enable(self.pwm1_enable) == hwmonInterface.accepted_pwm1_enable.Manual )

    def _set_hwmon_values(self):
        """ Sends values to the `hwmon` interface """
        if ( self.is_manual_state_enabled() ):
            if ( self.lastFanValue != self.targetSpeed ):
                hwmon.pwm1 = self.targetSpeed
                self.lastFanValue = self.targetSpeed
        else:
            if ( self.lastEnabled ):
                # restore the state we set last
                hwmon.pwm1_enable = hwmonInterface.accepted_pwm1_enable.Manual

    def _refresh_ui(self):
        """ Refresh the user interface with data aquired from the `hwmon` interface """
        # calculate red (higher or hotter) vs green (cooler or normal) balance 
        r = int((self.temp1_input / self.temp1_crit) * 255)
        g = 255 - r
        
        if ( self.is_manual_state_enabled() ):
            color = "#ff5d00"
            button = "Disable"
            y = [(self.targetSpeed / 255) * 100]
        else:
            color = "#0000ff"
            button = "Enable"
            y = [self.fanSpeed]

        self._get_plotwidget_item('fTarget').setPen(color)
        self._get_plotwidget_item('fTarget').setData(self.temp1_input, y)

        self._get_plotwidget_item('currTemp').setValue(self.temp1_input)
        self._get_plotwidget_item('currFan').setValue(self.fanSpeed)

        self.ui.labelTemperature.setText("%s °C" % self.temp1_input)
        self.ui.labelTemperature.setStyleSheet(UI_QLABEL_BG_CSS % '#{:02x}{:02x}{:02x}'.format(r, g, 0))

        self.ui.labelFanSpeed.setText("%s RPM" % hwmon.fan1_input)

        self.ui.labelFanProfileStatus.setText("%s" % hwmonInterface.accepted_pwm1_enable(self.pwm1_enable))
        self.ui.labelFanProfileStatus.setStyleSheet(UI_QLABEL_BG_CSS % color)

        self.ui.pushButtonEnable.setText(button)
        self.ui.pushButtonEnable.setChecked(self.is_manual_state_enabled())

        self.ui.labelPower.setText("%.1f W" % (hwmon.power1_average / 1000000))
        self.ui.labelVoltage.setText("%d mV" % hwmon.in0_input)

        self.ui.labelMemClock.setText("%s MHz" % hwmon.pp_dpm_mclk_mhz)
        self.ui.labelCoreClock.setText("%s MHz" % hwmon.pp_dpm_sclk_mhz)

        self.ui.comboBoxPerfProfile.setCurrentText(hwmon.power_dpm_force_performance_level.title())

        self.ui.labelPowerProfile.setText(hwmon.pp_power_profile_mode_active.mode_name.title())

    def timer_ctrl_tick(self):
        self.hysteresis = (hwmon.temp1_input + self.lastUpdate) / 2000
        self.lastUpdate = hwmon.temp1_input
        

app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
