# -*- coding: utf-8 -*-

import sys, os
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

import pyqtgraph as pg
import ui.mainwindow as mainwindow
from ui.monitorwindow import MonitorWindow

from PyQt5 import QtCore, QtWidgets

from common.hwmonInterface import HwMon, accepted_pwm1_enable, accepted_power_dpm_force_performance_level
from common.graphs  import InitPlotWidget, EditableGraph, get_plotwidget_item, graph_from_widget
from common.config import Config, CONFIG_INTERVAL_VAR, CONFIG_POINT_VAR
from common.theme import *

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

LOG = logging.getLogger(__name__)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self._init_locals()
        self._init_graphview()
        self._init_timers()
        self._init_pyqtsignals()
        self._init_drivervalues()
        self._init_styles()
        self._init_monitor_ui()

        # start working now
        self._timer_update_tick()

    def _init_locals(self):
        """ Initializes `local` variables """
        pg.setConfigOptions(antialias=True)

        self.hwmon = HwMon()
        self.config = Config()
        
        self.lastFanValue = -1

    def _init_timers(self):
        """ Initializes timers and starts them """
        self.timerUI = QtCore.QTimer()
        self.timerUI.timeout.connect(self._timer_update_tick)
        self.timerUI.start()

        self.timerMonitor = QtCore.QTimer() 
        self.timerMonitor.timeout.connect(self._timer_monitor_tick)
        self.timerMonitor.start(1000)

    def _init_pyqtsignals(self):
        """ Connects pyqt5 signals to various slots """
        self.ui.spinBoxInterval.valueChanged.connect(self._spin_interval_changed)
        self.ui.pushButtonEnable.clicked.connect(self._button_enable_toggled)
        self.ui.pushButtonSave.clicked.connect(self._button_save_clicked)
        self.ui.comboBoxCardIndex.currentIndexChanged.connect(self._combo_card_index_changed)
        self.ui.comboBoxPerfProfile.currentTextChanged.connect(self._combo_perf_profile_changed)
        self.ui.pushButtonMonitor.clicked.connect(self._button_monitor_toggled)

        self._spin_interval_changed(self.config.getValue(CONFIG_INTERVAL_VAR))

        self.ui.pushButtonAdd.clicked.connect(get_plotwidget_item(self.ui.graphicsView).addPoint)
        self.ui.pushButtonRemove.clicked.connect(get_plotwidget_item(self.ui.graphicsView).removePoint)

        self.closeEvent = self._mainwindow_closeevent

    def _init_graphview(self):
        """ Initializes the graph widgets """
        self._init_graph()
        self._init_graph_lines()
        self._init_graph_legend()

    def _init_graph(self):
        """ 
        Initializes the `PlotWidget`:

        - Adds a `EditableGraph` which allows for point manipulation
        - Adds xy labels for Fan Speed and Temperature
        - Sets and locks the viewport, disables the right-click menu
        - Shows the Grid, and sets the Tick Spacing
        """
        InitPlotWidget(
            self.ui.graphicsView, 
            labels={'left': ('Fan Speed', '%'), 'bottom': ("Temperature", '°C')},
            showGrid={'x': True, 'y': True, 'alpha': 0.1},
            tickSpacing={'left': (10, 5), 'bottom': (10, 1)},
            limits=(-3, 110)
        )
        
        # FIXME the labels appear too close to the boundary and require additional padding 

        EditableGraph(
            self.ui.graphicsView,
            data=self.config.getValue(CONFIG_POINT_VAR),
            staticPos=[self.hwmon.temp1_crit / 1000, 100]
        )
       
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
        
        tempMax = pg.ScatterPlotItem(pen=pg.mkPen('#ff0000'), width=2)
        tempMax._name = 'tMax'
        tempMax.setData([int(self.hwmon.temp1_crit / 1000)], [100], symbol='d')

        fanTarget = pg.ScatterPlotItem(pen=pg.mkPen('#0000ff'), width=2)
        fanTarget._name = 'targetFan'
        fanTarget.setData([-10], [-10], symbol='d')

        legendItem.addItem(tempMax, name='GPU tMax')
        legendItem.addItem(fanTarget, name='Fan PWM')
        legendItem.setPos(0, 100)

        self.ui.graphicsView.addItem(tempMax)
        self.ui.graphicsView.addItem(fanTarget)
        self.ui.graphicsView.addItem(legendItem)

    def _init_styles(self):
        """ Sets the UI styles for plot and display widgets"""
        set_dark_rounded_css(self.ui.frame)

    def _init_drivervalues(self):
        """ Adds various data pieces to the `mainwindow` widgets """
        for level in accepted_power_dpm_force_performance_level:
            self.ui.comboBoxPerfProfile.addItem(level.name.title())

    def _monitor_closed(self, evt):
        """ Handle close event for monitor window """
        # restore monitor window checked state
        self.ui.pushButtonMonitor.setChecked(False)

    def _init_monitor_ui(self):
        self.monwindow = MonitorWindow(self.hwmon)
        self.monwindow.closeEvent = self._monitor_closed

    def _button_monitor_toggled(self, value):
        if (value):
            self.monwindow.move(self.pos().x() + self.frameGeometry().width(), self.pos().y())
            self.monwindow.show()
            self.activateWindow()
        else:
            self.monwindow.hide()

    def _button_enable_toggled(self, value):
        """ Changes the control state """
        self.hwmon.pwm1_enable = accepted_pwm1_enable.Manual if value else accepted_pwm1_enable.Auto

    def _button_save_clicked(self):
        """ Saves and applies the fan curve """
        data = get_plotwidget_item(self.ui.graphicsView).pos.tolist()

        self.config.setValue(CONFIG_POINT_VAR, data)
        self.config.save()

    def _spin_interval_changed(self, value):
        """ Set the `mainwindow` timer timeout """
        self.config.setValue(CONFIG_INTERVAL_VAR, value)
        self.timerUI.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))
    
    def _combo_card_index_changed(self, value):
        if (value == -1):
            return
        self.hwmon.interface = value

    def _combo_perf_profile_changed(self, value):
        """ Set the `power_dpm_force_performance_level` when the user changes the value """
        for level in accepted_power_dpm_force_performance_level:
            if (str(value.lower()) == str(level)):
                self.hwmon.power_dpm_force_performance_level = level
                
    def _timer_update_tick(self):
        """ Event occurs on timertick from the Update Interval on the `mainwindow` """
        self._get_hwmon_values()
        self._refresh_main_ui()
        self._set_hwmon_values()

    def _get_hwmon_values(self):
        """ Retrieves values from `hwmon` interface and stores them in global variables """
        # acquire hardware values
        self.pwm1_max = self.hwmon.pwm1_max
        self.temp1_input = self.hwmon.temp1_input_degrees
        
        self.temp1_crit = self.hwmon.temp1_crit_degrees
        self.pwm1_enable = self.hwmon.pwm1_enable
        
        intesect = graph_from_widget(self.ui.graphicsView).getIntersection(x=self.temp1_input)

        self.targetSpeed = int((intesect / 100) * self.pwm1_max)
        self.fanSpeed = int((self.hwmon.pwm1 / self.pwm1_max) * 100)

    def is_hwmon_ctrl_state_manual(self):
        """ checks if the manual state is set in hardware """
        # compare the local value against it's corresponding enum
        return ( self.pwm1_enable == accepted_pwm1_enable.Manual.value )

    def _set_hwmon_values(self):
        """ Sends values to the `hwmon` interface """
        if ( self.is_hwmon_ctrl_state_manual() ):
            if ( self.lastFanValue != self.targetSpeed ):
                self.hwmon.pwm1 = self.targetSpeed
                self.lastFanValue = self.targetSpeed
        else:
            if ( self.ui.pushButtonEnable.isChecked() ):
                # restore the state we set last
                self.hwmon.pwm1_enable = accepted_pwm1_enable.Manual

    def _refresh_main_ui(self):
        """ Refresh the user interface with data aquired from the `hwmon` interface """
        # calculate red (higher or hotter) vs green (cooler or normal) balance

        base_temp = 0
        delta = (self.temp1_input - base_temp) / (self.temp1_crit - base_temp) % 1

        r = int(255 * delta)
        g = 255 - r

        LOG.debug(f'tdiff={self.temp1_input - base_temp}, delta={delta}, r={r}, g={g} b=255')

        if ( self.is_hwmon_ctrl_state_manual() ):
            color = BG_COLOR_MANUAL
            button = "Disable"
            target_indicator_y = [(self.targetSpeed / 255) * 100]
        else:
            color = BG_COLOR_AUTO
            button = "Enable"
            target_indicator_y = [self.fanSpeed]

        get_plotwidget_item(self.ui.graphicsView, 'targetFan').setPen(color)
        get_plotwidget_item(self.ui.graphicsView, 'targetFan').setData(self.temp1_input, target_indicator_y)

        get_plotwidget_item(self.ui.graphicsView, 'currTemp').setValue(self.temp1_input)
        get_plotwidget_item(self.ui.graphicsView, 'currFan').setValue(self.fanSpeed)

        self.ui.pushButtonEnable.setText(button)
        self.ui.pushButtonEnable.setChecked(self.is_hwmon_ctrl_state_manual())

        self.ui.labelTemperature.setText("%s °C" % self.temp1_input)
        self.ui.labelTemperature.setStyleSheet(UI_QLABEL_BG_CSS % '#{:02x}{:02x}{:02x}'.format(r, g, 0))

        self.ui.labelFanSpeed.setText("%s RPM" % self.hwmon.fan1_input)

        self.ui.labelFanProfileStatus.setText("%s" % accepted_pwm1_enable(self.pwm1_enable))
        self.ui.labelFanProfileStatus.setStyleSheet(UI_QLABEL_BG_CSS % color)

        self.ui.labelPower.setText("%.1f W" % (self.hwmon.power1_average_watts))
        self.ui.labelVoltage.setText("%d mV" % self.hwmon.in0_input)

        self.ui.labelMemClock.setText("%s MHz" % self.hwmon.pp_dpm_mclk_mhz)
        self.ui.labelCoreClock.setText("%s MHz" % self.hwmon.pp_dpm_sclk_mhz)

        self.ui.comboBoxPerfProfile.setCurrentText(self.hwmon.power_dpm_force_performance_level.title())
        self.ui.labelPowerProfile.setText(self.hwmon.pp_power_profile_mode_active.mode_name.title())
    

        if (len(self.hwmon.interfaces) != self.ui.comboBoxCardIndex.count()):
            self.ui.comboBoxCardIndex.clear()
            for i in range(len(self.hwmon.interfaces)):
                self.ui.comboBoxCardIndex.addItem(f'{str(i)} - {self.hwmon.interfaces[i]["name"]}')

        self.ui.labelCurrentLinkSpeed.setText(self.hwmon.current_link_speed.title())

    def _timer_monitor_tick(self):
        self.monwindow.refresh_monitors()
        
    def _mainwindow_closeevent(self, *args, **kwargs):
        """ Handles `mainwindow` closeEvent"""
        # mainwindow is closing, reset the pwm1_enable to Auto if we have Manually set the value
        if (accepted_pwm1_enable(self.hwmon.pwm1_enable) == accepted_pwm1_enable.Manual):
            self.hwmon.pwm1_enable = accepted_pwm1_enable.Auto

def main():
        
    app = QtWidgets.QApplication(sys.argv)

    my_mainWindow = MainWindow()
    my_mainWindow.show()

    app.exec()

if __name__ == '__main__':
    main()
