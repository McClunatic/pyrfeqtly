# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import random
from PySide6 import QtCore, QtWidgets, QtGui

from . import widgets
from . import graph_widgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))

        self.createFileActions()
        self.createEditActions()
        self.createHelpActions()

        # Create settings sliders
        self.sliderBox = widgets.PlotOptionsGroupBox('Plot options', self)

        # Create tree views
        self.sourcesBox = widgets.DataSourcesGroupBox('Data sources', self)

        # Create canvases widget
        # self.canvasWidget = widgets.CanvasesWidget(self)
        self.canvasWidget = graph_widgets.GraphicsLayoutWidget(self)

        # Create layout
        sideLayout = QtWidgets.QVBoxLayout()
        sideLayout.addWidget(self.sliderBox)
        sideLayout.addWidget(self.sourcesBox)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sideLayout)
        layout.addWidget(self.canvasWidget, stretch=1)
        self.widget.setLayout(layout)

    def createFileActions(self):
        self.newAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentNew),
            self.tr('&New'),
            self)
        self.newAct.setShortcut(QtGui.QKeySequence.StandardKey.New)
        self.newAct.setStatusTip(self.tr('Create a new file'))
        # TODO: connect self.newAct to function

        self.openAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentOpen),
            self.tr('&Open...'),
            self)
        self.openAct.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.openAct.setStatusTip(self.tr('Open an existing file'))
        # TODO: connect self.openAct to function

        self.saveAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentSave),
            self.tr('&Save'),
            self)
        self.saveAct.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.saveAct.setStatusTip(self.tr('Save the file to disk'))
        # TODO: connect self.saveAct to function

        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)

    def createEditActions(self):
        self.editAct = QtGui.QAction(
            self.tr('&Edit'), self)
        self.editAct.setStatusTip(self.tr('Edit current configuration'))
        # TODO: connect self.editAct to function

        self.prefAct = QtGui.QAction(
            self.tr('&Preferences...'), self)
        self.prefAct.setShortcut(QtGui.QKeySequence.StandardKey.Preferences)
        self.openAct.setStatusTip(self.tr('Edit preferences'))
        # TODO: connect self.prefAct to function

        self.editMenu.addAction(self.editAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.prefAct)

    def createHelpActions(self):
        self.aboutAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.HelpAbout),
            self.tr('&About'),
            self)
        self.newAct.setStatusTip(self.tr('Show about'))
        # TODO: connect self.aboutAct to function

        self.helpMenu.addAction(self.aboutAct)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))
