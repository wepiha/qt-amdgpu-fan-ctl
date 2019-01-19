# -*- coding: utf-8 -*-

import pyqtgraph as pg

from enum import Enum
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from common.graphs import InitPlotWidget, ScrollingGraph, get_plotwidget_item
from common.hwmonInterface import sysfm_device_hwmon_monitors, HwMon

class MonitorWindow(QtWidgets.QDialog):
    def __init__(self, hwmon: HwMon):

        super(MonitorWindow, self).__init__()
        
        self.setWindowTitle('Monitoring')
        self.resize(462, 405)
        self.setWindowFlag(QtCore.Qt.SubWindow)
        self.setContentsMargins(0, 0, 0, 0)

        self.hwmon = hwmon
        self.objects = {}

        self._init_layout()

        for attr in sysfm_device_hwmon_monitors:
            self._add_monitor_widget(attr.value)

    def _init_layout(self):
        self.widget = QtWidgets.QWidget()
        self.widget.setContentsMargins(0, 0, 0, 0)

        layout = QtGui.QVBoxLayout(self)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)

        self.widget.setLayout(layout)

        scroll = QtGui.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.widget)

        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(scroll)
        self.setLayout(vLayout)

    def _add_monitor_widget(self, attr):
        frame = QtGui.QFrame(self.widget)
        frame.setObjectName(f"{attr['attribute']}_frame")
        frame.setContentsMargins(6, 6, 6, 6)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setObjectName(f"{attr['attribute']}_gridLayout")
        gridLayout.setContentsMargins(6, 6, 6, 6)

        labelDeviceName = QtWidgets.QLabel(frame)
        labelDeviceName.setObjectName(f"{attr['attribute']}_descriptor")
        labelDeviceName.setText( attr['descriptor'] )#name.split('_', 1)[0] )

        labelDeviceValue = QtWidgets.QLabel(frame)
        labelDeviceValue.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        labelDeviceValue.setObjectName(f"{attr['attribute']}_value")
        labelDeviceValue.setText( 'labelDeviceValue' )

        graphicsView = PlotWidget(frame)
        graphicsView.setObjectName(f"{attr['attribute']}_plotWidget")

        labelDeviceMin = QtWidgets.QLabel(frame)
        labelDeviceMin.setObjectName(f"{attr['attribute']}_min")
        labelDeviceMin.setText( 'labelDeviceMin' )

        labelDeviceMax = QtWidgets.QLabel(frame)
        labelDeviceMax.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        labelDeviceMax.setObjectName(f"{attr['attribute']}_max")
        labelDeviceMax.setText( 'labelDeviceMax' )

        gridLayout.addWidget(labelDeviceName, 0, 0, 1, 1)
        gridLayout.addWidget(labelDeviceValue, 0, 1, 1, 1)
        gridLayout.addWidget(graphicsView, 1, 0, 1, 2)
        gridLayout.addWidget(labelDeviceMin, 2, 0, 1, 1)
        gridLayout.addWidget(labelDeviceMax, 2, 1, 1, 1)

        ScrollingGraph(graphicsView, getattr(self.hwmon, attr['attribute']))

        self.widget.layout().addWidget(frame)

    def _get_frame_widget(self, name):

        for i in range(1, self.widget.layout().count()):
            frame = self.widget.layout().itemAt(i).widget()

            if (frame.objectName() == f'{name}_frame'):
                return frame

        raise LookupError(f'No frame found matching {name}...')

    def _get_monitor_widget(self, base_name, ext):

        for child in self._get_frame_widget(base_name).children():
            if (not hasattr(child, 'objectName')):
                continue

            if (child.objectName() == f'{base_name}_{ext}'):
                return child

        raise LookupError(f'No child found matching {name}...')
    def append_monitor_data(self, monitor: sysfm_device_hwmon_monitors):
        
        objects = {}
        base_attr = monitor['attribute']
        base_value = getattr(self.hwmon, base_attr)

        # get the qobject frame items, temporarily store as tuple items
        for key in ['value', 'min', 'max']:
            objects[key] = self._get_monitor_widget(base_attr, key)

        # update each qobject item with their respective values
        for key in objects.keys():
            if ((type(objects[key]) == PlotWidget) or (objects[key] == None)):
                continue

            sub_attr = '' if (key == 'value') else f'_{key}'
            
            # find the value for associated label
            value = getattr(self.hwmon, f'{base_attr}{sub_attr}')

            # update the label text
            objects[key].setText(f"{key.title()}: {value} {monitor['unit']}")

        # acquire graph for monitor, and update with the new value
        graph = self._get_monitor_widget(base_attr, 'plotWidget')
        get_plotwidget_item(graph, 'graph').update(base_value)