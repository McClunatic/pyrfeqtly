# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the main window class."""

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

        # Create the data container object
        # TODO: make sure these get set on app init somehow
        self.data = DataContainer(
            bin_width=1e0,
            history_size=100,
            sample_size=720)

        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))
        self.createFileActions()
        self.createEditActions()
        self.createHelpActions()

        self.sideLayout = QtWidgets.QVBoxLayout()
        self.plotOptionsBox = QtWidgets.QStackedWidget()
        self.dataSourcesBox = DataSourcesGroupBox('Data sources', self)
        self.createSideLayout()
        self.createMainLayout()
        self.connectSignalsAndSlots()

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

    def createSideLayout(self):
        # Create tabbed set of plot options widgets
        plotButtonLayout = QtWidgets.QHBoxLayout()
        plotButtonGroup = QtWidgets.QButtonGroup(self)
        plotButtonGroup.idClicked.connect(
            self.plotOptionsBox.setCurrentIndex)

        for idx, label in enumerate(('left', 'center', 'right')):
            button = QtWidgets.QPushButton(self.tr(label))
            button.setCheckable(True)
            button.setChecked(idx == 0)
            plotButtonGroup.addButton(button, id=idx)
            plotButtonLayout.addWidget(button)
            opts = PlotOptionsGroupBox(self.tr('Plot options'))
            self.plotOptionsBox.addWidget(opts)

        self.sideLayout.addLayout(plotButtonLayout)
        self.sideLayout.addWidget(self.plotOptionsBox)
        self.sideLayout.addWidget(self.dataSourcesBox, stretch=1)

    def createMainLayout(self):
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.sideLayout)
        for title in ('left', 'center', 'right'):
            widget = GraphicsWidget(data=self.data, title=title, parent=self)
            layout.addWidget(widget, stretch=1)

        self.widget.setLayout(layout)

    def connectSignalsAndSlots(self):
        self.dataUpdated.connect(self.data.updated)
        self.dataSourcesBox.sourceDataChanged.connect(self.updateData)
        for idx in range(3):
            opts = self.plotOptionsBox.widget(idx)
            gfxs = self.widget.layout().itemAt(idx + 1).widget()

            self.dataSourcesBox.sourceInserted.connect(opts.insertSource)
            self.dataSourcesBox.sourceRemoved.connect(opts.removeSource)
            opts.aggregationModesChanged.connect(gfxs.updateAggregationModes)
            opts.sourceSelectionChanged.connect(gfxs.updateSourceSelection)
            opts.xRangeChanged.connect(gfxs.updateXRange)
            gfxs.xRangeChanged.connect(opts.updateXRange)

    @QtCore.Slot(str)
    def updateData(self, watchDir: str):
        self.data.update(path=watchDir)
        self.dataUpdated.emit()
