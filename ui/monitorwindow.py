# -*- coding: utf-8 -*-

import pyqtgraph as pg

from enum import Enum
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from common.graphs import InitPlotWidget, ScrollingGraph
from common.hwmonInterface import sysfm_device_hwmon_monitors, HwMon

class MonitorWindow(QtWidgets.QDialog):
    def __init__(self, hwmon: HwMon):

        super(MonitorWindow, self).__init__()
        
        self.setWindowTitle("Monitoring")
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
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.widget)

        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(scroll)
        self.setLayout(vLayout)

    def _add_monitor_widget(self, attr):
        frame = QtGui.QFrame(self.widget)
        frame.setObjectName(f"frame_{attr['attribute']}")
        frame.setContentsMargins(0, 0, 0, 0)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setObjectName(f"gridLayout_{attr['attribute']}")
        gridLayout.setContentsMargins(0, 0, 0, 0)

        labelDeviceName = QtWidgets.QLabel(frame)
        labelDeviceName.setObjectName(f"descriptor_{attr['attribute']}")
        labelDeviceName.setText( attr['descriptor'] )#name.split("_", 1)[0] )

        labelDeviceValue = QtWidgets.QLabel(frame)
        labelDeviceValue.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        labelDeviceValue.setObjectName(f"value_{attr['attribute']}")
        labelDeviceValue.setText( 'labelDeviceValue' )

        graphicsView = PlotWidget(frame)
        graphicsView.setObjectName(f"graphicsView_{attr['attribute']}")

        labelDeviceMin = QtWidgets.QLabel(frame)
        labelDeviceMin.setObjectName(f"min_{attr['attribute']}")
        labelDeviceMin.setText( 'labelDeviceMin' )

        labelDeviceMax = QtWidgets.QLabel(frame)
        labelDeviceMax.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        labelDeviceMax.setObjectName(f"max_{attr['attribute']}")
        labelDeviceMax.setText( 'labelDeviceMax' )


        
        gridLayout.addWidget(labelDeviceName, 0, 0, 1, 1)
        gridLayout.addWidget(labelDeviceValue, 0, 1, 1, 1)
        gridLayout.addWidget(graphicsView, 1, 0, 1, 2)
        gridLayout.addWidget(labelDeviceMin, 2, 0, 1, 1)
        gridLayout.addWidget(labelDeviceMax, 2, 1, 1, 1)

        ScrollingGraph(graphicsView)

        self.widget.layout().addWidget(frame)

    def _get_frame_obj(self, name):
        for i in range(1, self.widget.layout().count()):
            frame = self.widget.layout().itemAt(i).widget()

            if (frame.objectName() == f"frame_{name}"):
                break

        return frame
    def _get_monitor_obj(self, name, obj):

        frame = self._get_frame_obj(name)
        
        for child in frame.children():
            if ((type(child) == PlotWidget) or (not hasattr(child, 'objectName'))):
                continue

            if (child.objectName() == f"{obj}_{name}"):
                return child

        raise LookupError("No child found matching {obj}...")
    def append_monitor_data(self, monitor: sysfm_device_hwmon_monitors):
        
        objects = {}
        base_attr = monitor['attribute']

        # get the qobject frame items, temporarily store as tuple items
        for key in ['value', 'min', 'max']:
            objects[key] = self._get_monitor_obj(base_attr, key)

        # update each qobject item with their respective values
        for key in objects.keys():
            sub_attr = ''

            if key != 'value': 
                sub_attr = f'_{key}'
            
            value = getattr(self.hwmon, f"{base_attr}{sub_attr}")
            objects[key].setText(f"{key.title()}: {value} {monitor['unit']}")



