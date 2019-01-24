# -*- coding: utf-8 -*-

import numpy as np
import math
import pyqtgraph as pg
from pyqtgraph import PlotWidget, PlotItem
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette

import logging

LOG = logging.getLogger(__name__)


def graph_from_widget(parent):
    return get_plotwidget_item(parent, 'graph')

def graph_add_data(parent, data):
    graph = graph_from_widget(parent)
    graph_from_widget(parent).append_data(data)

def get_plotwidget_item(parent, name = 'graph') -> PlotItem:
    """ Helper function to acquire items added to the `PlotWidget` """
    for item in parent.plotItem.items:
        if (hasattr(item, '_name')) and (item._name == name):
            return item
    
    raise LookupError("The item '%s' was not found" % name)


def InitPlotWidget(plotwidget, **kwds):
    
    kwds_default = {
        'menuEnabled': False,
        'aspectLocked': True,
        'hideButtons': True,

        'labels': {
            'bottom': [],
            'left': []
        },

        'showGrid': {
            'x': True,
            'y': True,
            'alpha': 0.5
        },

        'tickSpacing' : {
            'bottom': False,
            'left': False
        },

        'background' : None
    }

    data = dict(kwds_default, **kwds)

    plotwidget.setMenuEnabled(data['menuEnabled'])
    plotwidget.setLabels(**data['labels'])
    plotwidget.setAspectLocked(data['aspectLocked'])
    plotwidget.showGrid(**data['showGrid'])
    plotwidget.setBackground(data['background'])

    if (data['tickSpacing']['bottom'] is not False):
        plotwidget.getAxis('bottom').setTickSpacing(data['tickSpacing']['bottom'][0], data['tickSpacing']['bottom'][1])
    
    if (data['tickSpacing']['left'] is not False):
        plotwidget.getAxis('left').setTickSpacing(data['tickSpacing']['left'][0], data['tickSpacing']['left'][1])

    if 'hideButtons' in data:
        plotwidget.hideButtons()
    
    if 'limits' in data:
        if len(data['limits']) == 2:
            plotwidget.setLimits(
                xMin = data['limits'][0],
                yMin = data['limits'][0],
                xMax = data['limits'][1] + data['limits'][0],
                yMax = data['limits'][1] + data['limits'][0],
                minXRange = data['limits'][1],
                maxXRange = data['limits'][1],
                minYRange = data['limits'][1],
                maxYRange = data['limits'][1]
            )

class EditableGraph(pg.GraphItem):
    MIN_POINT_DISTANCE = 16

    def __init__(self, parent: PlotWidget, data: list, staticPos=None):
        super().__init__()

        self.plotWidget = parent

        # adds _name attribute similar tto those in plotItem.items
        self._name = 'graph'
        self.staticPos = staticPos

        self.dragPoint = None
        self.dragOffset = None
        
        self.setData(pos=np.stack(data))

        # adds pg.GraphItem to the parent PlotItems
        parent.addItem(pg.TextItem())
        parent.addItem(self)

    def setData(self, **kwds):
        self.data = kwds
        if 'pos' in self.data:

            pos = self.data['pos'].tolist()

            if (pos[0] != [0, 0]):
                pos.insert(0, [0, 0])

            if (self.staticPos is not None) and (pos[len(pos) - 1] != self.staticPos):
                pos.append(self.staticPos)
                self.setData(pos=np.stack(pos))
                return

            npts = self.data['pos'].shape[0]
            self.data['adj'] = np.column_stack((np.arange(0, npts-1), np.arange(1, npts)))
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)

            # force array values to be integers 
            self.data['pos'] = self.data['pos'].astype(int)

            self.updateGraph()
    def updateGraph(self):
        super().setData(**self.data)

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

        index = 1
        min_len = self.getPointDistance(0, len(self.data['pos']) -1)

        for i in range(1, len(self.data['pos']) - 1):
            closest = self.getPointDistance(i-1, i+1)
            
            if (closest < min_len):
                index = i
                min_len = closest
        
        LOG.info(f"removePoint() index={index}, length={min_len}")

        flat = self.data['pos'].tolist()
        del flat[index]
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

    def getCoordWidget(self):
        coordWidget = None

        for item in self.plotWidget.plotItem.items:
            if (isinstance(item, pg.graphicsItems.TextItem.TextItem)):
                coordWidget = item
                break

        return coordWidget

    def setCoordText(self, text = ""):
        coordWidget = self.getCoordWidget()

        if (coordWidget is None):
            return

        coordWidget.setText(text)

    def setCoordValues(self, x, y):
        coordWidget = self.getCoordWidget()

        if (coordWidget is None):
            return

        coordWidget.setPos(x, y)

    def mouseDragEvent(self, event):
        
        self.setCoordText()

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

        ps = self.plotWidget.getViewBox().viewPixelSize()

        self.setCoordValues(p[0] - (ps[0] * 24), p[1] + (ps[1] * 24) )
        self.setCoordText("(%d, %d)" % (p[0], p[1]))
        
        self.updateGraph()
        event.accept()

class ScrollingGraph(pg.GraphItem):
    def __init__(self, parent: PlotWidget, data: list, maxY: int):
        super().__init__()

        self.plot = pg.PlotDataItem()
        self.plot._name = 'graph'

        parent.showAxis('bottom', False)
        parent.setLimits(
                yMin = -3,
                #xMax = 60,
                yMax = maxY - 3,
                maxXRange = 60,
                minYRange = maxY,
                maxYRange = maxY
            )

        highlight = parent.palette().color(QPalette.Highlight)

        self.plot.setPen(pg.mkPen(highlight, width = 2))
        self.plot.setBrush(highlight.darker())
        self.plot.setFillLevel(-1.0)
        self.plot.setData(np.zeros(60))# + int(data))

        self.plot.append_data = self.append_data

        parent.getViewBox().setMouseEnabled(False)
        # prevent mouse wheel event
        parent.getViewBox().wheelEvent = lambda event: None
        parent.getViewBox().hoverEvent = self.mouse_hover
        parent.addItem(self.plot)

    def mouse_hover(self, event):
        if event.exit:
            return

    def append_data(self, y):
        self.plot.yData[:-1] = self.plot.yData[1:]
        self.plot.yData[-1] = int(y)

        self.plot.setData(self.plot.yData)