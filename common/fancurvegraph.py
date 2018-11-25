
# -*- coding: utf-8 -*-

import pyqtgraph as pg
import numpy as np
import math

from PyQt5 import QtCore, QtGui, QtWidgets

class FanCurveGraph(pg.GraphItem):
    MIN_POINT_DISTANCE = 16

    def __init__(self, parent, data, name, staticPos=None):
        self.dragPoint = None
        self.dragOffset = None
        self.plotWidget = parent
        self._name = name
        
        self.staticPos = staticPos

        pg.GraphItem.__init__(self)
        self.setData(pos=np.stack(data))

    def setData(self, **kwds):
        self.data = kwds
        if 'pos' in self.data:

            pos = self.data['pos'].tolist()

            if (pos[0] != [0, 0]):
                pos.insert(0, [0, 0])

            if (self.staticPos) and (pos[len(pos) - 1] != self.staticPos):
                pos.append(self.staticPos)
                self.setData(pos=np.stack(pos))
                return

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