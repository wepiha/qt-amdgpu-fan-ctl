# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/wepiha/Documents/amdgpuproautofans/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(651, 638)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.labelGPUforCurrentProfileLabel = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelGPUforCurrentProfileLabel.sizePolicy().hasHeightForWidth())
        self.labelGPUforCurrentProfileLabel.setSizePolicy(sizePolicy)
        self.labelGPUforCurrentProfileLabel.setObjectName("labelGPUforCurrentProfileLabel")
        self.horizontalLayout_3.addWidget(self.labelGPUforCurrentProfileLabel)
        self.comboBoxCardIndex = QtWidgets.QComboBox(self.centralwidget)
        self.comboBoxCardIndex.setObjectName("comboBoxCardIndex")
        self.comboBoxCardIndex.addItem("")
        self.horizontalLayout_3.addWidget(self.comboBoxCardIndex)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelFanProfileLabel = QtWidgets.QLabel(self.centralwidget)
        self.labelFanProfileLabel.setObjectName("labelFanProfileLabel")
        self.horizontalLayout.addWidget(self.labelFanProfileLabel)
        self.labelFanProfileStatus = QtWidgets.QLabel(self.centralwidget)
        self.labelFanProfileStatus.setObjectName("labelFanProfileStatus")
        self.horizontalLayout.addWidget(self.labelFanProfileStatus)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.labelCurrentFan = QtWidgets.QLabel(self.centralwidget)
        self.labelCurrentFan.setObjectName("labelCurrentFan")
        self.horizontalLayout.addWidget(self.labelCurrentFan)
        self.labelFanRPMLabel = QtWidgets.QLabel(self.centralwidget)
        self.labelFanRPMLabel.setObjectName("labelFanRPMLabel")
        self.horizontalLayout.addWidget(self.labelFanRPMLabel)
        self.labelTemperatureLabel = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelTemperatureLabel.sizePolicy().hasHeightForWidth())
        self.labelTemperatureLabel.setSizePolicy(sizePolicy)
        self.labelTemperatureLabel.setObjectName("labelTemperatureLabel")
        self.horizontalLayout.addWidget(self.labelTemperatureLabel)
        self.labelCurrentTemp = QtWidgets.QLabel(self.centralwidget)
        self.labelCurrentTemp.setObjectName("labelCurrentTemp")
        self.horizontalLayout.addWidget(self.labelCurrentTemp)
        self.labelDegreesCLabel = QtWidgets.QLabel(self.centralwidget)
        self.labelDegreesCLabel.setObjectName("labelDegreesCLabel")
        self.horizontalLayout.addWidget(self.labelDegreesCLabel)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.graphicsView = PlotWidget(self.centralwidget)
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout_2.addWidget(self.graphicsView, 2, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.labelUpdateEveryLabel = QtWidgets.QLabel(self.centralwidget)
        self.labelUpdateEveryLabel.setObjectName("labelUpdateEveryLabel")
        self.horizontalLayout_2.addWidget(self.labelUpdateEveryLabel)
        self.spinBoxInterval = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBoxInterval.setMinimum(50)
        self.spinBoxInterval.setMaximum(5000)
        self.spinBoxInterval.setSingleStep(500)
        self.spinBoxInterval.setProperty("value", 2500)
        self.spinBoxInterval.setObjectName("spinBoxInterval")
        self.horizontalLayout_2.addWidget(self.spinBoxInterval)
        self.labelSLabel = QtWidgets.QLabel(self.centralwidget)
        self.labelSLabel.setObjectName("labelSLabel")
        self.horizontalLayout_2.addWidget(self.labelSLabel)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.pushButtonAdd = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonAdd.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButtonAdd.sizePolicy().hasHeightForWidth())
        self.pushButtonAdd.setSizePolicy(sizePolicy)
        self.pushButtonAdd.setObjectName("pushButtonAdd")
        self.horizontalLayout_2.addWidget(self.pushButtonAdd)
        self.pushButtonRemove = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonRemove.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButtonRemove.sizePolicy().hasHeightForWidth())
        self.pushButtonRemove.setSizePolicy(sizePolicy)
        self.pushButtonRemove.setObjectName("pushButtonRemove")
        self.horizontalLayout_2.addWidget(self.pushButtonRemove)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.pushButtonEnable = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonEnable.setCheckable(True)
        self.pushButtonEnable.setChecked(False)
        self.pushButtonEnable.setObjectName("pushButtonEnable")
        self.gridLayout.addWidget(self.pushButtonEnable, 0, 0, 1, 1)
        self.pushButtonSave = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonSave.setObjectName("pushButtonSave")
        self.gridLayout.addWidget(self.pushButtonSave, 0, 1, 1, 1)
        self.pushButtonClose = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonClose.setObjectName("pushButtonClose")
        self.gridLayout.addWidget(self.pushButtonClose, 0, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 4, 0, 1, 1)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setEnabled(False)
        self.plainTextEdit.setMaximumSize(QtCore.QSize(16777215, 80))
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayout_2.addWidget(self.plainTextEdit, 5, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "AMDGPUPRO Auto Fan"))
        self.labelGPUforCurrentProfileLabel.setText(_translate("MainWindow", "GPU for Current Profile:"))
        self.comboBoxCardIndex.setItemText(0, _translate("MainWindow", "0"))
        self.labelFanProfileLabel.setText(_translate("MainWindow", "Fan Profile:"))
        self.labelFanProfileStatus.setText(_translate("MainWindow", "SYSTEM"))
        self.labelCurrentFan.setText(_translate("MainWindow", "..."))
        self.labelFanRPMLabel.setText(_translate("MainWindow", "%"))
        self.labelTemperatureLabel.setText(_translate("MainWindow", "Temperature: "))
        self.labelCurrentTemp.setText(_translate("MainWindow", "..."))
        self.labelDegreesCLabel.setText(_translate("MainWindow", "°C"))
        self.labelUpdateEveryLabel.setText(_translate("MainWindow", "Update Every:"))
        self.labelSLabel.setText(_translate("MainWindow", "ms"))
        self.pushButtonAdd.setText(_translate("MainWindow", "+"))
        self.pushButtonRemove.setText(_translate("MainWindow", "-"))
        self.pushButtonEnable.setText(_translate("MainWindow", "Enable"))
        self.pushButtonSave.setText(_translate("MainWindow", "Save"))
        self.pushButtonClose.setText(_translate("MainWindow", "Close"))
        self.plainTextEdit.setPlainText(_translate("MainWindow", "WARNING: THIS SOFTWARE DOES NOT INCLUDE A WARRANTY OF ANY KIND. ENABLE MANUAL FAN CONTROL AT YOUR OWN RISK. YOU HAVE BEEN WARNED! Also note that many devices will limit the lowest possible fan speed and may not allow for control below that threshold."))

from pyqtgraph import PlotWidget
