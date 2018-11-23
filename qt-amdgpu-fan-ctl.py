# -*- coding: utf-8 -*-

import sys, os
import json
import numpy as np
import math

from PyQt5 import QtCore, QtGui, QtWidgets

from common import hwmonInterface as hw
from common.hwmonInterface import Interface, PwmState

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
VIEW_MIN = -1

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

        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.spinBoxInterval.valueChanged.connect(self.setInterval)
        self.ui.pushButtonEnable.clicked.connect(self.setEnabled)
        self.ui.pushButtonAdd.clicked.connect(self.addPoint)
        self.ui.pushButtonRemove.clicked.connect(self.removePoint)
        self.ui.pushButtonSave.clicked.connect(self.configSave)
        self.ui.pushButtonClose.clicked.connect(self.close)

        self.initPlotWidget()
        self.initTimer()
        
    def initPlotWidget(self):
        pg.setConfigOptions(antialias=True)
        gv = self.ui.graphicsView

        gv.setLabels(left=('Fan Speed', '%'), bottom=("Temperature", '°C'))
        gv.setMenuEnabled(False)
        gv.setAspectLocked(True)
        gv.showGrid(x=True, y=True, alpha=0.25)
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
        pen = pg.mkPen('w', width=0.2, style=QtCore.Qt.DashLine)

        graph = Graph(gv)
        graph.setData(pos=np.stack(self.myConfig[CONFIG_POINT_VAR]))
        graph._name = 'graph'

        lineCurrTemp = pg.InfiniteLine(pos=0, pen=pen, name="currTemp")
        lineLabelCurrTemp = pg.InfLineLabel(lineCurrTemp, text="Temp\n", position=0.8)
        
        lineCurrFan = pg.InfiniteLine(pos=0, angle=0, pen=pen, name="currFan")
        lineLabelCurrFan = pg.InfLineLabel(lineCurrFan, text="Fan Speed", position=0.1)

        textLabelXY = pg.TextItem()

        lineLabelCurrTemp.setAngle(90)
        lineLabelCurrFan.setAngle(0)

        scatterItem = pg.ScatterPlotItem(name='tMax', pen=pg.mkPen('r'))
        scatterItem._name = 'tMax'
        scatterItem.setData([hwmon.temp1_crit], [100], symbol='t')

        targetTemp = pg.ScatterPlotItem(name='fTarget', pen=pg.mkPen('#0000FF'))
        targetTemp._name = 'fTarget'
        targetTemp.setData([-10], [-10], symbol='t')

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

    def initTimer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerTick)
        self.timer.start()
        self.setInterval(self.myConfig[CONFIG_INTERVAL_VAR])

    def closeEvent(self, *args, **kwargs):
        if (PwmState(hwmon.pwm1_enable) == PwmState.Manual):
            hwmon.pwm1_enable = PwmState.Auto

    def setEnabled(self, value):
        hwmon.pwm1_enable = PwmState.Manual if value else PwmState.Auto

    def setInterval(self, value):
        self.myConfig[CONFIG_INTERVAL_VAR] = str(value)
        self.timer.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))
    
    def getFanSpeedFromPlot(self):
        
        temp = hwmon.temp1_input
        # given gpuTemp we use some trig to 
        # calculate output fan speed as a 
        # percentage of the maximum 255
        #          |
        #       .--|-.(x2,y2)
        #       |  |/
        # ---------+------------<-- output
        #       | /|
        #       |/ |
        #       .  |<-- gpuTemp
        #       ^    
        #      (x1,y1)
        #
        pts = self.getGraphItem('graph').pos

        for i in range(0, len(pts) - 1):
            x1 = pts[i][0]
            x2 = pts[i+1][0]
            y1 = pts[i][1]
            y2 = pts[i+1][1]

            if (( temp >= x1 ) and ( temp < x2)):
                sFan = (((temp - x1) / (x2 - x1)) * (y2 - y1)) + y1 
                output = int((sFan / 100) * hwmon.pwm1_max)
                break

        return output

    def getLineLength(self, p1, p2):
        #FIXME: needs bounds checks
        pts = self.getGraphItem(0).pos
        
        x1 = pts[p1][0]
        x2 = pts[p2][0]
        y1 = pts[p1][1]
        y2 = pts[p2][1]

        return math.sqrt( #pythagoras
            math.pow( x2 - x1, 2 ) + 
            math.pow( y2 - y1, 2 )
        )

    def addPoint(self):
        # work out where the largest gap occurs and insert the new point in the middle
        pts = self.getGraphItem(0).pos
        
        inspos = -1
        length = 0
        output = [0, 0]

        for i in range(0, len(pts) - 1):
            h = self.getLineLength(i, i + 1)

            if (h > length):
                inspos = i
                length = h
                output = [ 
                    int(pts[i][0] + ( ( pts[i+1][0] - pts[i][0] ) / 2 )), 
                    int(pts[i][1] + ( ( pts[i+1][1] - pts[i][1] ) / 2 )) 
                ]
        
        if (length < 20):
            return

        flat = pts.tolist()
        flat.insert(inspos + 1, output)

        self.setGraphData(flat)
    def removePoint(self):
        pts = self.getGraphItem(0).pos
        
        if (len(pts) == 2):
            return

        delpos = 1
        length = 1000

        for i in range(1, len(pts) - 1):
            h = self.getLineLength(i, i + 1)
            #print("%d is %d " % (i, h))
            if (h < length):
                delpos = i
                length = h
        
        flat = pts.tolist()
        #print("Removing %d (%d)" % (delpos, length))

        del flat[delpos]
        self.setGraphData(flat)

    def setGraphData(self, data):
        self.myConfig[CONFIG_POINT_VAR] = data
        self.getGraphItem(0).setData(pos=np.stack(data))
    def getGraphItem(self, name):
        for item in self.ui.graphicsView.plotItem.items:
            if (hasattr(item, '_name')) and (item._name == name):
                return item
        
        raise LookupError("The item '%s' was not found" % name)
        
    def getGraphFlatList(self):
        shape = self.getGraphItem('graph').pos.shape
        return self.getGraphItem('graph').pos.reshape(shape).tolist()
        
    def timerTick(self):
        self.myConfig[CONFIG_POINT_VAR] = self.getGraphFlatList()

        targetSpeed = self.getFanSpeedFromPlot()
        gpuTemp = hwmon.temp1_input
        fanSpeed = int((hwmon.pwm1 / hwmon.pwm1_max) * 100)
        critTemp = hwmon.temp1_crit
        state = hwmon.pwm1_enable
        
        r = 255
        g = 255
        b = 0
        n = int((gpuTemp / critTemp) * 255)

        if (gpuTemp <= ( critTemp / 2 )):
            r = 0
            g = 255 - n
        else:
            r = n
            g = 0
        
        if (PwmState(state) == PwmState.Manual):
            hwmon.pwm1 = targetSpeed
            color = "#ff5d00"
            button = "Disable"
            y = [(targetSpeed / 255) * 100]
        else:
            color = "#0000ff"
            button = "Enable"
            y = [fanSpeed]
        
        self.getGraphItem('fTarget').setPen(color)
        self.getGraphItem('fTarget').setData([gpuTemp], y)

        self.getGraphItem('currTemp').setValue(gpuTemp)
        self.getGraphItem('currFan').setValue(fanSpeed)

        self.ui.labelCurrentTemp.setText(str(gpuTemp))
        self.ui.labelCurrentTemp.setStyleSheet(QLABEL_STYLE_SHEET % '#{:02x}{:02x}{:02x}'.format(r, g, b))

        self.ui.labelCurrentFan.setText(str(fanSpeed))

        self.ui.labelFanProfileStatus.setText("  %s  " % PwmState(state))
        self.ui.labelFanProfileStatus.setStyleSheet(QLABEL_STYLE_SHEET % color)

        self.ui.pushButtonEnable.setText(button)
        self.ui.pushButtonEnable.setChecked(PwmState(state) == PwmState.Manual)

    def configSave(self):
        
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
    def __init__(self, parent):
        self.dragPoint = None
        self.dragOffset = None
        self.plotWidget = parent

        pg.GraphItem.__init__(self)
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
