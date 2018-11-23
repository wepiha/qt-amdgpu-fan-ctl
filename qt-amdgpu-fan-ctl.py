# -*- coding: utf-8 -*-

import sys, os
import json
import numpy as np
import math

from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
import mainwindow

CONFIG_FILE = "config.json"

CONFIG_PATH_VAR = "path"
CONFIG_CARD_VAR = "card"
CONFIG_POINT_VAR = "points"
CONFIG_INDEX_VAR = "${index}"
CONFIG_INTERVAL_VAR = "interval"
CONFIG_LOGGING_VAR = "logging"

HWMON_TEMP1_INPUT = "temp1_input"
HWMON_TEMP1_CRIT = "temp1_crit"
HWMON_PWM_INPUT = "pwm1"
HWMON_PWM_MAX = "pwm1_max"
HWMON_PWM_ENABLE = "pwm1_enable"

HWMON_STATUS_MAN = "MANUAL"
HWMON_STATUS_SYS = "AUTO"

VIEW_LIMITER = 110
VIEW_MIN = -1

# requires tweaking to store fan profile based on card index
DEFAULTCONFIG = {
    CONFIG_PATH_VAR : "/sys/class/drm/card" + CONFIG_INDEX_VAR + "/device/hwmon/hwmon0/",
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

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.myConfig = self.configLoad()

        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.spinBoxInterval.valueChanged.connect(self.setInterval)
        self.ui.pushButtonAdd.clicked.connect(self.addPoint)
        self.ui.pushButtonRemove.clicked.connect(self.removePoint)
        self.ui.pushButtonEnable.clicked.connect(self.setCtlOwner)
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

        lineCurrTemp = pg.InfiniteLine(pos=0, pen=pen, name="currTemp")
        lineLabelCurrTemp = pg.InfLineLabel(lineCurrTemp, text="Temp\n", position=0.8)
        
        lineCurrFan = pg.InfiniteLine(pos=0, angle=0, pen=pen, name="currFan")
        lineLabelCurrFan = pg.InfLineLabel(lineCurrFan, text="Fan Speed", position=0.1)

        textLabelXY = pg.TextItem()

        lineLabelCurrTemp.setAngle(90)
        lineLabelCurrFan.setAngle(0)

        scatterItem = pg.ScatterPlotItem(name='tMax', pen=pg.mkPen('r'))
        scatterItem.setData([self.getGPUTempCrit()], [100], symbol='t')

        gv.addItem(graph)
        gv.addItem(lineCurrTemp)
        gv.addItem(lineCurrFan)
        gv.addItem(textLabelXY)
        #gv.addItem(scatterItem)

    def initTimer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerTick)
        self.timer.start()
        self.setInterval(self.myConfig[CONFIG_INTERVAL_VAR])

    def setPerms(self, path):
        os.system('python3 ' + os.getcwd() + '/common/setperms.py ' + path)

    def closeEvent(self, *args, **kwargs):
        if (self.getHwmonStatus() == HWMON_STATUS_MAN):
            self.setCtlOwner(False)

    def setCtlOwner(self, value):
        path = self.myConfig[CONFIG_PATH_VAR] + HWMON_PWM_ENABLE
        
        self.setPerms(path)
        try:
            with open(path, "w") as file:
                file.write("1" if (value) else "2")
        except:
            print("Failed to setCtlOwner!")
        finally:
            print("setCtlOwner: " + self.getHwmonStatus() )
    def setCtlValue(self, value):
        path = self.myConfig[CONFIG_PATH_VAR] + HWMON_PWM_INPUT

        global lastCtlValue
        
        if (self.ui.pushButtonEnable.isChecked() != True) or (lastCtlValue == value):
            return
        
        lastCtlValue = value

        try:
            self.setPerms(path)
            with open(path, "w") as file:
                file.write(str(value))
        except:
            print("Failed to setCtlValue!")
        finally:
            print("setCtlValue: " + str(value) )

    def setInterval(self, value):
        self.myConfig[CONFIG_INTERVAL_VAR] = str(value)
        self.timer.setInterval(int(value))

        if ( self.ui.spinBoxInterval.value != value ):
            self.ui.spinBoxInterval.setValue(int(value))

    def getHwmonInt(self, path):
        try:
            file = open(self.myConfig[CONFIG_PATH_VAR] + path, "r")
            value = int(file.read())
        except:
            value = 0
        #print("getHwmonInt: %s%s (%d)" % (self.myConfig[CONFIG_PATH_VAR], path, value))
        return value
    def getHwmonStatus(self):
        fanStatus = self.getHwmonInt(HWMON_PWM_ENABLE)
        return HWMON_STATUS_MAN if fanStatus != 2 else HWMON_STATUS_SYS
    def getGPUTemp(self):
        tIn = self.getHwmonInt(HWMON_TEMP1_INPUT)
        return int(tIn / 1000)
    def getGPUTempCrit(self):
        tCrit = self.getHwmonInt(HWMON_TEMP1_CRIT)
        return int(tCrit / 1000)
    def getGPUPWMMax(self):
        return self.getHwmonInt(HWMON_PWM_MAX)
    def getGPUFanPercent(self):
        fIn = self.getHwmonInt(HWMON_PWM_INPUT)
        fMax = self.getGPUPWMMax()
        fRet = int((fIn / fMax) * 100)
        #print( "Get fan speed: %d%% (%d)" % (fRet, fIn))
        return fRet

    def getFanSpeedFromPlot(self):
        
        temp = self.getGPUTemp()
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
        pts = self.getGraphItem(0).pos

        for i in range(0, len(pts) - 1):
            x1 = pts[i][0]
            x2 = pts[i+1][0]
            y1 = pts[i][1]
            y2 = pts[i+1][1]

            if (( temp >= x1 ) and ( temp < x2)):
                sFan = (((temp - x1) / (x2 - x1)) * (y2 - y1)) + y1 
                output = int((sFan / 100) * self.getGPUPWMMax())
                break

        return output

    def setFanSpeedAdjustments(self):
        output = self.getFanSpeedFromPlot()
        self.setCtlValue(str(output))
        
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
        # always return something
        return self.ui.graphicsView.plotItem.items[0]
        
    def getGraphFlatList(self):
        shape = self.getGraphItem(None).pos.shape
        return self.getGraphItem(None).pos.reshape(shape).tolist()
        
    def timerTick(self):
        self.myConfig[CONFIG_POINT_VAR] = self.getGraphFlatList()

        gpuTemp = self.getGPUTemp()
        #fanSpeed = (self.getFanSpeedFromPlot() / 255) * 100 
        fanSpeed = self.getGPUFanPercent() # TODO: plot this on graph as data point, replacing this line with commented code above
        ctlStatus = self.getHwmonStatus()
        critTemp = self.getGPUTempCrit()

        color = "green"
        styleSheet = "QLabel { color: white; background-color: %s; }"
        
        if (ctlStatus == HWMON_STATUS_MAN):
            self.setFanSpeedAdjustments()
            color = "#ff5d00"

        r = 255
        g = 255
        n = int((gpuTemp / critTemp) * 255)

        if (gpuTemp <= ( critTemp / 2 )):
            r = 0
            g = 255 - n
        else:
            r = n
            g = 0

        hexstr = "#%s00" % ('{:02x}{:02x}'.format(r,g))

        self.ui.labelCurrentTemp.setText(str(gpuTemp))
        self.ui.labelCurrentTemp.setStyleSheet(styleSheet % hexstr)

        self.ui.labelCurrentFan.setText(str(fanSpeed))
        self.ui.labelFanProfileStatus.setText("  %s  " % ctlStatus)
        self.ui.labelFanProfileStatus.setStyleSheet("QLabel { color: white; background-color: %s; }" % color)

        # move InfiniteLines
        self.getGraphItem('currTemp').setValue(gpuTemp)
        self.getGraphItem('currFan').setValue(fanSpeed)
        
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
