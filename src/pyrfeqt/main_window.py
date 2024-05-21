# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the main window class."""

import random

from PySide6 import QtCore, QtGui, QtWidgets

from .data_container import DataContainer
from .data_sources_groupbox import DataSourcesGroupBox
from .plot_options_groupbox import PlotOptionsGroupBox
from .graphics_widget import GraphicsWidget


class MainWindow(QtWidgets.QMainWindow):

    dataUpdated = QtCore.Signal()

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

        # Create tabbed set of plot options widgets
        plotButtonLayout = QtWidgets.QHBoxLayout()
        plotButtonGroup = QtWidgets.QButtonGroup(self)
        plotOptionsWidget = QtWidgets.QStackedWidget()
        self.plotOptionsBoxes = []
        for idx, label in enumerate(('left', 'center', 'right')):
            button = QtWidgets.QPushButton(self.tr(label))
            button.setCheckable(True)
            button.setChecked(idx == 0)
            plotButtonGroup.addButton(button, id=idx)
            plotButtonLayout.addWidget(button)

            opts = PlotOptionsGroupBox(self.tr('Plot options'))
            plotOptionsWidget.addWidget(opts)
            self.plotOptionsBoxes.append(opts)

        plotButtonGroup.idClicked.connect(plotOptionsWidget.setCurrentIndex)

        # Create data sources widget
        self.sourcesBox = DataSourcesGroupBox('Data sources', self)

        # Create the data container object
        # TODO: make sure these get set on app init somehow
        self.data = DataContainer(
            bin_width=1e0,
            history_size=100,
            sample_size=720)

        # Create graphics widgets
        self.graphicsWidgets = [
            GraphicsWidget(data=self.data, title=title, parent=self)
            for title in ('left', 'center', 'right')]

        # Create layout
        sideLayout = QtWidgets.QVBoxLayout()
        sideLayout.addLayout(plotButtonLayout)
        sideLayout.addWidget(plotOptionsWidget)
        sideLayout.addWidget(self.sourcesBox, stretch=1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sideLayout)
        for graphicsWidget in self.graphicsWidgets:
            layout.addWidget(graphicsWidget, stretch=1)
        self.widget.setLayout(layout)

        # Connect signals and slots
        self.sourcesBox.sourceDataChanged.connect(self.updateData)
        for opts, gfxs in zip(self.plotOptionsBoxes, self.graphicsWidgets):
            self.sourcesBox.sourceInserted.connect(opts.insertSource)
            self.sourcesBox.sourceRemoved.connect(opts.removeSource)
            opts.aggregationModesChanged.connect(gfxs.updateAggregationModes)
            opts.sourceSelectionChanged.connect(gfxs.updateSourceSelection)
            opts.xRangeChanged.connect(gfxs.updateXRange)
            gfxs.xRangeChanged.connect(opts.updateXRange)
            self.dataUpdated.connect(self.data.updated)

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

    @QtCore.Slot(str)
    def updateData(self, watchDir: str):
        self.data.update(path=watchDir)
        self.dataUpdated.emit()
