# -*- coding: utf-8 -*-

import pyqtgraph as pg

from enum import Enum
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from common.graphs import InitPlotWidget, ScrollingGraph, graph_add_data
from common.hwmonInterface import sysfs_device_hwmon_monitors_amdgpu, HwMon
from common.theme import set_dark_rounded_css

import logging

LOG = logging.getLogger(__name__)

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

        for attr in sysfs_device_hwmon_monitors_amdgpu:
            self._add_monitor_widget(attr.value)
        
        self.setFixedHeight(628)

    def _init_layout(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout(self.centralwidget)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)

        self.centralwidget.setLayout(layout)

        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.centralwidget)
        scroll.setFrameShape(QtWidgets.QFrame.StyledPanel)
        scroll.setFrameShadow(QtWidgets.QFrame.Plain)
        scroll.setContentsMargins(0, 0, 0, 0)

        vLayout = QtWidgets.QVBoxLayout(self)
        vLayout.addWidget(scroll)
        vLayout.setSpacing(0)
        vLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vLayout)

    def _add_monitor_widget(self, attr):
        frame = QtWidgets.QFrame(self.centralwidget)
        frame.setObjectName(f"{attr['attribute']}_frame")
        frame.setContentsMargins(0, 0, 0, 0)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setObjectName(f"{attr['attribute']}_gridLayout")
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)

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

        InitPlotWidget(graphicsView)
        ScrollingGraph(graphicsView, getattr(self.hwmon, attr['attribute']), attr['maximum'])
        set_dark_rounded_css(graphicsView)

        self.centralwidget.layout().addWidget(frame)

    def _get_monitor_widget(self, base_name, ext):

        for i in range(1, self.centralwidget.layout().count()):
            frame = self.centralwidget.layout().itemAt(i).widget()

            if (frame.objectName() == f'{base_name}_frame'):
                for child in frame.children():
                    if (not hasattr(child, 'objectName')):
                        continue

                    if (child.objectName() == f'{base_name}_{ext}'):
                        return child

        raise LookupError(f'No child found matching {base_name}_{ext}...')
        
    def append_monitor_data(self, monitor: sysfs_device_hwmon_monitors_amdgpu):
        
        base_attr = monitor['attribute']
        base_value = getattr(self.hwmon, base_attr)

        # update each widget with their respective values
        for key in ['value', 'min', 'max']:
            widget = self._get_monitor_widget(base_attr, key)

            if ((type(widget) == PlotWidget) or (widget == None)):
                continue

            sub_attr = '' if (key == 'value') else f'_{key}'
            
            # find the value for associated label
            value = getattr(self.hwmon, f'{base_attr}{sub_attr}')

            # update the label text
            widget.setText(f"{key.title()}: {value} {monitor['unit']}")

        # acquire graph for monitor, and update with the new value
        graph = self._get_monitor_widget(base_attr, 'plotWidget')
        graph_add_data(graph, base_value)

    def refresh_monitors(self):

        self.hwmon.update_ext_attributes()

        for attr in sysfs_device_hwmon_monitors_amdgpu:
            if hasattr(self.hwmon, attr.value['attribute']):
                self.append_monitor_data(attr.value)
