# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the main window class."""

import uuid
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from .data_container import DataContainer
from .data_sources_groupbox import DataSourcesGroupBox
from .plot_options_groupbox import PlotOptionsGroupBox
from .graphics_widget import GraphicsWidget
from .config_dialog import ConfigDialog

# float: default bin width used to bin samples together in time
BIN_WIDTH = 1e0

#: int: default number of samples to retain in memory as history
HISTORY_SIZE = 31

#: int: default number of samples to display in spectrogram plots
WINDOW_SIZE = 30

#: int: default array size of a single source data sample
SAMPLE_SIZE = 720

QtWidgets.QApplication.setApplicationName('pyrfeqt')
QtWidgets.QApplication.setOrganizationName('Brian')
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setCentralWidget(QtWidgets.QWidget())
        self.createDefaultSettings()

        # Create the data container object
        settings = QtCore.QSettings()
        self.data = DataContainer(
            binWidth=settings.value('default/data/binWidth', type=float),
            sampleSize=settings.value('default/data/sampleSize', type=int),
            historySize=settings.value('default/data/historySize', type=int))

        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))

        self.newAct = self.openAct = self.saveAct = None
        self.editAct = self.prefAct = None
        self.aboutAct = None

        self.plotOptionsBox = QtWidgets.QStackedWidget()
        self.dataSourcesBox = DataSourcesGroupBox('Data sources')

        self._createFileActions()
        self._createEditActions()
        self._createHelpActions()

        self._buildLayout()
        self._connectSignalsAndSlots()
        self.applySettings()

    def plotOptionsWidget(self, index: int):
        return self.plotOptionsBox.widget(index)

    def dataSourcesWidget(self):
        return self.dataSourcesBox

    def graphicsWidget(self, index: int):
        return self.centralWidget().layout().itemAt(index + 1).widget()

    def applySettings(self, group: str = 'default'):
        self.data.applySettings(group)
        self.dataSourcesWidget().applySettings(group)
        for idx in range(3):
            self.plotOptionsWidget(idx).applySettings(group)
        for idx in range(3):
            self.graphicsWidget(idx).applySettings(group)

    def writeSettings(self, group: str):
        self.data.writeSettings(group)
        self.dataSourcesWidget().writeSettings(group)
        for idx in range(3):
            self.plotOptionsWidget(idx).writeSettings(group)

    def createDefaultSettings(self):
        settings = QtCore.QSettings()
        groups = settings.childGroups()
        if 'default' in groups:
            return

        settings.beginGroup('default')
        settings.beginGroup('plotOptions')
        for pos in ('left', 'center', 'right'):
            settings.beginGroup(pos)
            settings.setValue('xRange', [0, SAMPLE_SIZE])
            settings.setValue('windowSize', WINDOW_SIZE)
            settings.setValue('aggregationModes', ['none', 'mean'])
            settings.beginWriteArray('sourceSelection')
            settings.endArray()
            settings.endGroup()
        settings.endGroup()
        settings.beginGroup('dataSources')
        settings.setValue('paths', [])
        settings.setValue('sources', [])
        settings.endGroup()
        settings.beginGroup('data')
        settings.setValue('binWidth', BIN_WIDTH)
        settings.setValue('sampleSize', SAMPLE_SIZE)
        settings.setValue('historySize', HISTORY_SIZE)
        settings.endGroup()
        settings.endGroup()

    @QtCore.Slot(str)
    def insertData(self, source: str):
        self.data.update(source=source)

    @QtCore.Slot(str)
    def removeData(self, source: str):
        self.data.remove(source=source)

    @QtCore.Slot(str)
    def updateData(self, paths: str | List[str]):
        if isinstance(paths, str):
            paths = [paths]
        self.data.updateAll(paths=paths)

    def _createFileActions(self):
        self.newAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentNew),
            self.tr('&New'),
            self)
        self.newAct.setShortcut(QtGui.QKeySequence.StandardKey.New)
        self.newAct.setStatusTip(self.tr('Start new configuration'))
        self.newAct.triggered.connect(self.newConfig)

        self.openAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentOpen),
            self.tr('&Load...'),
            self)
        self.openAct.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.openAct.setStatusTip(self.tr('Load an existing configuration'))
        self.openAct.triggered.connect(self.loadConfig)

        self.saveAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentSave),
            self.tr('&Save...'),
            self)
        self.saveAct.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.saveAct.setStatusTip(self.tr('Save current configuration'))
        self.saveAct.triggered.connect(self.saveConfig)

        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)

    def _createEditActions(self):
        self.editAct = QtGui.QAction(
            self.tr('&Edit...'), self)
        self.editAct.setStatusTip(self.tr('Edit current configuration...'))
        self.editAct.triggered.connect(self.editConfig)

        self.delAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.EditDelete),
            self.tr('&Delete saved...'),
            self)
        self.delAct.setStatusTip(self.tr('Delete a saved configuration...'))
        self.delAct.triggered.connect(self.deleteConfig)

        self.prefAct = QtGui.QAction(
            self.tr('&Preferences...'), self)
        self.prefAct.setShortcut(QtGui.QKeySequence.StandardKey.Preferences)
        self.prefAct.setStatusTip(self.tr('Edit preferences'))
        self.prefAct.triggered.connect(self.showPreferences)

        self.editMenu.addAction(self.editAct)
        self.editMenu.addAction(self.delAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.prefAct)

    def _createHelpActions(self):
        self.aboutAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.HelpAbout),
            self.tr('&About'),
            self)
        self.aboutAct.setStatusTip(self.tr('Show about'))
        self.aboutAct.triggered.connect(self.showAbout)

        self.aboutQtAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.HelpAbout),
            self.tr('About &Qt'),
            self)
        self.aboutQtAct.setStatusTip(self.tr('Show about Qt'))
        self.aboutQtAct.triggered.connect(self.showAboutQt)

        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def _buildLayout(self):
        settings = QtCore.QSettings()
        plotButtonLayout = QtWidgets.QHBoxLayout()
        plotButtonGroup = QtWidgets.QButtonGroup(self)
        plotButtonGroup.idClicked.connect(
            self.plotOptionsBox.setCurrentIndex)

        for idx, pos in enumerate(('left', 'center', 'right')):
            button = QtWidgets.QPushButton(self.tr(pos))
            button.setCheckable(True)
            button.setChecked(idx == 0)
            plotButtonGroup.addButton(button, id=idx)
            plotButtonLayout.addWidget(button)
            xRange = settings.value(
                f'default/plotOptions/{pos}/xRange', type=list)
            windowSize = settings.value(
                f'default/plotOptions/{pos}/windowSize', type=int)
            opts = PlotOptionsGroupBox(
                title=self.tr('Plot options'),
                pos=pos,
                xRange=[int(lim) for lim in xRange],
                windowSize=windowSize)
            self.plotOptionsBox.addWidget(opts)

        sideLayout = QtWidgets.QVBoxLayout()
        sideLayout.addLayout(plotButtonLayout)
        sideLayout.addWidget(self.plotOptionsBox)
        sideLayout.addWidget(self.dataSourcesBox, stretch=1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sideLayout)
        for title in ('left', 'center', 'right'):
            windowSize = settings.value(
                f'default/plotOptions/{title}/windowSize', type=int)
            widget = GraphicsWidget(
                data=self.data,
                windowSize=windowSize,
                title=title,
                parent=self)
            layout.addWidget(widget, stretch=1)

        self.centralWidget().setLayout(layout)

    def _connectSignalsAndSlots(self):
        self.dataSourcesBox.pathsChanged.connect(self.updateData)
        self.dataSourcesBox.sourceInserted.connect(self.insertData)
        self.dataSourcesBox.sourceRemoved.connect(self.removeData)
        self.dataSourcesBox.sourceDataChanged.connect(self.updateData)
        for idx in range(3):
            opts = self.plotOptionsBox.widget(idx)
            gfxs = self.centralWidget().layout().itemAt(idx + 1).widget()

            self.dataSourcesBox.sourceInserted.connect(opts.insertSource)
            self.dataSourcesBox.sourceRemoved.connect(opts.removeSource)
            opts.aggregationModesChanged.connect(gfxs.updateAggregationModes)
            opts.sourceSelectionChanged.connect(gfxs.updateSourceSelection)
            opts.windowSizeChanged.connect(gfxs.updateWindowSize)
            opts.xRangeChanged.connect(gfxs.updateXRange)
            gfxs.xRangeChanged.connect(opts.updateXRange)

    def editConfig(self):
        settings = QtCore.QSettings()
        # Create a dummy group
        dummyGroup = uuid.uuid4().hex
        while dummyGroup in settings.childGroups():
            dummyGroup = uuid.uuid4().hex
        # Write settings to the dummy group
        self.writeSettings(group=dummyGroup)
        # Apply settings to configuration dialog
        dialog = ConfigDialog(
            'Edit configuration',
            group=dummyGroup,
            mode='edit')
        dialog.applySettings()
        # If accepted: serialize and deserialize settings to apply
        if dialog.exec():
            dialog.writeSettings()
            self.applySettings(group=dummyGroup)
        # Always remove the dummy group
        settings.remove(dummyGroup)

    def newConfig(self):
        ans = QtWidgets.QMessageBox.question(
            self,
            'Confirm New',
            'This will return all options to default settings. Continue?')
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            self.applySettings(group='default')

    def loadConfig(self):
        dialog = ConfigDialog(
            'Edit configuration',
            group='default',
            mode='load')
        dialog.applySettings()
        if dialog.exec():
            group = dialog.currentText()
            self.applySettings(group=group)

    def deleteConfig(self):
        settings = QtCore.QSettings()
        dialog = ConfigDialog(
            'Delete configuration',
            group='default',
            mode='delete')
        dialog.applySettings()
        if dialog.exec():
            group = dialog.currentText()
            settings.remove(group)

    def saveConfig(self):
        settings = QtCore.QSettings()
        # Create a dummy group
        dummyGroup = uuid.uuid4().hex
        while dummyGroup in settings.childGroups():
            dummyGroup = uuid.uuid4().hex
        # Write settings to the dummy group
        self.writeSettings(group=dummyGroup)
        # Apply settings to configuration dialog
        dialog = ConfigDialog(
            'Save configuration',
            group=dummyGroup,
            mode='save')
        dialog.applySettings()
        # If accepted: serialize and deserialize settings to apply
        if dialog.exec():
            group = dialog.currentText()
            self.writeSettings(group=group)
        # Always remove the dummy group
        settings.remove(dummyGroup)

    def showPreferences(self):
        QtWidgets.QMessageBox.information(
            self,
            'Preferences',
            'There are currently no preferences options!')

    def showAbout(self):
        QtWidgets.QMessageBox.about(
            self,
            'About',
            'Pyrfeqt is for rendering file-based data with Qt.')

    def showAboutQt(self):
        QtWidgets.QMessageBox.aboutQt(self, 'About Qt')
