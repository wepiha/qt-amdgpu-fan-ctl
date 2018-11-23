# -*- coding: utf-8 -*-

import sys, os
import json
import numpy as np
import math

from PyQt5 import QtCore, QtGui, QtWidgets

from common import hwmonInterface as hw
from common.hwmonInterface import hwmon_hwmon0, PwmState

import pyqtgraph as pg
import mainwindow

CONFIG_FILE = "config.json"

CONFIG_PATH_VAR = "path"
CONFIG_CARD_VAR = "card"
CONFIG_POINT_VAR = "points"
CONFIG_INDEX_VAR = "${index}"
CONFIG_INTERVAL_VAR = "interval"
CONFIG_LOGGING_VAR = "logging"

VIEW_LIMITER = 110
VIEW_MIN = -3

QLABEL_STYLE_SHEET = "QLabel { color: white; background-color: %s; }"

# requires tweaking to store fan profile based on card index
DEFAULTCONFIG = {
    CONFIG_CARD_VAR : "0",
    CONFIG_POINT_VAR : (
        (0, 0),
        (39, 0),
        (40, 40),
        (65, 100)
    ),
    CONFIG_INTERVAL_VAR : "2500",
    CONFIG_LOGGING_VAR : False
}

lastCardIndex = 0
lastCtlValue = -1
hwmon = hw.HwMon()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.myConfig = self.configLoad()
        self.timer = QtCore.QTimer()

        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.spinBoxInterval.valueChanged.connect(self.spinBoxIntervalChanged)
        self.ui.pushButtonEnable.clicked.connect(self.buttonEnableClicked)
        self.ui.pushButtonSave.clicked.connect(self.buttonSaveClicked)
        self.ui.pushButtonClose.clicked.connect(self.close)
        self.timer.timeout.connect(self.timerTick)
        self.timer.start()
        self.spinBoxIntervalChanged(self.myConfig[CONFIG_INTERVAL_VAR])

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

        graph = Graph(gv, data=self.myConfig[CONFIG_POINT_VAR], name='graph')
        pen = pg.mkPen('w', width=0.2, style=QtCore.Qt.DashLine)

        lineCurrTemp = pg.InfiniteLine(pos=0, pen=pen, name="currTemp", angle=270)
        lineCurrFan = pg.InfiniteLine(pos=0, pen=pen, name="currFan", angle=0)
        
        pg.InfLineLabel(lineCurrTemp, text="Temperature", position=0.7, rotateAxis=(2,0))
        pg.InfLineLabel(lineCurrFan, text="Fan Speed", position=0.15, rotateAxis=(0,0))

        textLabelXY = pg.TextItem()

        scatterItem = pg.ScatterPlotItem(pen=pg.mkPen('r'))
        scatterItem._name = 'tMax'
        scatterItem.setData([hwmon.temp1_crit], [100], symbol='d')

        targetTemp = pg.ScatterPlotItem(pen=pg.mkPen('#0000FF'))
        targetTemp._name = 'fTarget'
        targetTemp.setData([-10], [-10], symbol='d')

        legendItem = pg.LegendItem()
        legendItem.addItem(scatterItem, name='GPU tMax')
        legendItem.addItem(targetTemp, name='Fan Target')
        legendItem.setPos(85, 30)

        gv.addItem(graph)
        gv.addItem(lineCurrTemp)
        gv.addItem(lineCurrFan)
        gv.addItem(textLabelXY)
        gv.addItem(targetTemp)
        gv.addItem(scatterItem)

        gv.addItem(legendItem)

        self.ui.pushButtonAdd.clicked.connect(graph.addPoint)
        self.ui.pushButtonRemove.clicked.connect(graph.removePoint)
  
    def closeEvent(self, *args, **kwargs):
        if (PwmState(hwmon.pwm1_enable) == PwmState.Manual):
            hwmon.pwm1_enable = PwmState.Auto

    def buttonEnableClicked(self, value):
        hwmon.pwm1_enable = PwmState.Manual if value else PwmState.Auto

    def spinBoxIntervalChanged(self, value):
        self.myConfig[CONFIG_INTERVAL_VAR] = str(value)
        self.timer.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))
    
    def getSceneItem(self, name):
        for item in self.ui.graphicsView.plotItem.items:
            if (hasattr(item, '_name')) and (item._name == name):
                return item
        
        raise LookupError("The item '%s' was not found" % name)
    
    def timerTick(self):
        self.myConfig[CONFIG_POINT_VAR] = self.getSceneItem('graph').pos.tolist()

        pwm1_max = hwmon.pwm1_max
        temp1_input = hwmon.temp1_input
        temp1_crit = hwmon.temp1_crit
        pwm1_enable = hwmon.pwm1_enable

        targetSpeed = int((self.getSceneItem('graph').getIntersection(x=temp1_input) / 100) * pwm1_max)
        fanSpeed = int((hwmon.pwm1 / pwm1_max) * 100)
        
        r = int((temp1_input / temp1_crit) * 255)
        g = 255 - r
        
        if (PwmState(pwm1_enable) == PwmState.Manual):
            hwmon.pwm1 = targetSpeed
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

        self.ui.labelFanProfileStatus.setText("%s" % PwmState(pwm1_enable))
        self.ui.labelFanProfileStatus.setStyleSheet(QLABEL_STYLE_SHEET % color)

        self.ui.pushButtonEnable.setText(button)
        self.ui.pushButtonEnable.setChecked(PwmState(pwm1_enable) == PwmState.Manual)

        self.ui.labelPower.setText("%.1f W" % hwmon.power1_average)
        self.ui.labelVoltage.setText("%d mV" % hwmon.in0_input)

        self.ui.labelMemClock.setText("%s MHz" % hwmon.pp_dpm_mclk_value)
        self.ui.labelCoreClock.setText("%s MHz" % hwmon.pp_dpm_sclk_value)

    def buttonSaveClicked(self):
        
        try:
            with open(CONFIG_FILE, "w") as write_file:
                json.dump(self.myConfig, write_file, sort_keys=True, indent=4)
            print("Saved %s: %s" % (CONFIG_FILE, self.myConfig))
        except:
            print("Failed to save config!")
    def configLoad(self):
        conf = DEFAULTCONFIG
        
        try:
            with open(CONFIG_FILE, "r") as read_file:
                conf = json.load(read_file)
        except:
            print("Could not open file, using default config")
        
        conf = dict(DEFAULTCONFIG, **conf)

        if conf.__contains__(CONFIG_PATH_VAR) and conf.__contains__(CONFIG_CARD_VAR):
            path = conf[CONFIG_PATH_VAR].replace(CONFIG_INDEX_VAR, conf[CONFIG_CARD_VAR])
            
            if not os.path.isdir(path):
                path = DEFAULTCONFIG[CONFIG_PATH_VAR].replace(CONFIG_INDEX_VAR, DEFAULTCONFIG[CONFIG_CARD_VAR])

            conf[CONFIG_PATH_VAR] = path

        if len(conf[CONFIG_POINT_VAR]) < 2:
            conf[CONFIG_POINT_VAR] = DEFAULTCONFIG[CONFIG_POINT_VAR]
        
        with open(CONFIG_FILE, "w") as write_file:
            json.dump(conf, write_file)
        
        conf[CONFIG_POINT_VAR] = sorted(conf[CONFIG_POINT_VAR], key=lambda tup: tup[1])

        print("Loaded %s: %s" % (CONFIG_FILE, conf))

        return conf
 
class Graph(pg.GraphItem):
    MIN_POINT_DISTANCE = 16

    def __init__(self, parent, data, name):
        self.dragPoint = None
        self.dragOffset = None
        self.plotWidget = parent
        self._name = name
        
        pg.GraphItem.__init__(self)
        self.setData(pos=np.stack(data))

    def setData(self, **kwds):
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['adj'] = np.column_stack((np.arange(0, npts-1), np.arange(1, npts)))
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
        self.updateGraph()
    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)

    def addPoint(self):
        # work out where the largest gap occurs and insert the new point in the middle
        inspos = -1
        length = 0
        output = [0, 0]

        for i in range(0, len(self.data['pos']) - 1):
            h = self.getPointDistance(i, i + 1)

            if (h > length):
                inspos = i
                length = h
                output = [ 
                    int(self.data['pos'][i][0] + ( ( self.data['pos'][i+1][0] - self.data['pos'][i][0] ) / 2 )), 
                    int(self.data['pos'][i][1] + ( ( self.data['pos'][i+1][1] - self.data['pos'][i][1] ) / 2 )) 
                ]
        
        if (length < self.MIN_POINT_DISTANCE):
            return

        flat = self.data['pos'].tolist()
        flat.insert(inspos + 1, output)

        self.setData(pos=np.stack(flat))
    def removePoint(self):
        if (len(self.data['pos']) == 2):
            # don't remove the last 2 points
            return

        delpos = 1
        length = 1000

        for i in range(1, len(self.data['pos']) - 1):
            h = self.getPointDistance(i, i + 1)
            #print("%d is %d " % (i, h))
            if (h < length):
                delpos = i
                length = h
        
        flat = self.data['pos'].tolist()
        #print("Removing %d (%d)" % (delpos, length))

        del flat[delpos]
        self.setData(pos=np.stack(flat))
    def getIntersection(self, x = None, y = None):
        if (x == None) and (y == None):
            raise SyntaxError("Must specify either x or y intersection value")
        
        pts = self.data['pos']

        for i in range(0, len(pts) - 1):
            x1 = pts[i][0]
            x2 = pts[i+1][0]
            y1 = pts[i][1]
            y2 = pts[i+1][1]

            if ((x != None) and ( x >= x1 ) and ( x < x2)):
                return (((x - x1) / (x2 - x1)) * (y2 - y1)) + y1
                    
            if ((y != None) and ( y >= y1 ) and ( y < y2)):
                return (((y - y1) / (y2 - y1)) * (x2 - x1)) + x1

        return 0

    def getPointDistance(self, p1, p2):
        return math.sqrt(
            math.pow( self.data['pos'][p2][0] - self.data['pos'][p1][0], 2 ) + 
            math.pow( self.data['pos'][p2][1] - self.data['pos'][p1][1], 2 )
        )

    def mouseDragEvent(self, event):
        textWidget = self.plotWidget.plotItem.items[3] #FIXME: If possible, refer without using fixed-value indicies
        textWidget.setText("")

        if event.button() != QtCore.Qt.LeftButton:
            event.ignore()
            return
        if event.isStart():
            pos = event.buttonDownPos()
            points = self.scatter.pointsAt(pos)

            if len(points) == 0:
                event.ignore()
                return
            self.dragPoint = points[0]
            index = points[0].data()[0]

            self.dragOffsetX = self.data['pos'][index][0] - pos[0]
            self.dragOffsetY = self.data['pos'][index][1] - pos[1]
        elif event.isFinish():
            self.dragPoint = None
            return
        else:
            if self.dragPoint is None:
                event.ignore()
                return

        index = self.dragPoint.data()[0]
        
        if (index == 0) or (index == len(self.data['pos']) - 1):
            #disallow moving the first or last points
            event.ignore()
            return

        p = self.data['pos'][index]

        p[0] = event.pos()[0] + self.dragOffsetX
        p[1] = event.pos()[1] + self.dragOffsetY

        minX = self.data['pos'][index - 1][0]
        minY = self.data['pos'][index - 1][1]
        maxX = self.data['pos'][index + 1][0]
        maxY = self.data['pos'][index + 1][1]

        if p[0] < minX: p[0] = minX
        if p[0] > maxX: p[0] = maxX
        if p[1] < minY: p[1] = minY
        if p[1] > maxY: p[1] = maxY

        textWidget.setPos(p[0] - 8, p[1] + 8 )
        textWidget.setText("(%d, %d)" % (p[0], p[1]))

        self.updateGraph()
        event.accept()

app = QtWidgets.QApplication(sys.argv)

my_mainWindow = MainWindow()
my_mainWindow.show()

sys.exit(app.exec_())
