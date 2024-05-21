# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the main window class."""

from PySide6 import QtCore, QtGui, QtWidgets

from .data_container import DataContainer
from .data_sources_groupbox import DataSourcesGroupBox
from .plot_options_groupbox import PlotOptionsGroupBox
from .graphics_widget import GraphicsWidget

# float: default bin width used to bin samples together in time
BIN_WIDTH = 1e0

#: int: default number of samples to retain in memory as history
HISTORY_SIZE = 1000

#: int: default number of samples to display in spectrogram plots
WINDOW_SIZE = 300

#: int: default array size of a single source data sample
SAMPLE_SIZE = 720

QtWidgets.QApplication.setApplicationName('pyrfeqt')
QtWidgets.QApplication.setOrganizationName('Brian')
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)


class MainWindow(QtWidgets.QMainWindow):

    dataUpdated = QtCore.Signal()

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setCentralWidget(QtWidgets.QWidget())
        self.writeDefaultSettings()

        # Create the data container object
        settings = QtCore.QSettings()
        self.data = DataContainer(
            bin_width=settings.value('default/data/bin_width', type=float),
            sample_size=settings.value('default/data/sample_size', type=int),
            history_size=settings.value('default/data/history_size', type=int))

        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))

        self.newAct = self.openAct = self.saveAct = None
        self.editAct = self.prefAct = None
        self.aboutAct = None

        self.plotOptionsBox = QtWidgets.QStackedWidget()
        self.dataSourcesBox = DataSourcesGroupBox('Data sources', self)

        self._createFileActions()
        self._createEditActions()
        self._createHelpActions()

        self._buildLayout()
        self._connectSignalsAndSlots()

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
        for watchDir in self.dataSourcesWidget().watcher.directories():
            self.data.update(path=watchDir)
            self.dataUpdated.emit()

    def writeDefaultSettings(self):
        settings = QtCore.QSettings()
        groups = settings.childGroups()
        if 'default' in groups:
            return

        settings.beginGroup('default')
        settings.beginGroup('plotOptions')
        for pos in ('left', 'center', 'right'):
            settings.beginGroup(pos)
            settings.setValue('xRange', [0, SAMPLE_SIZE])
            settings.setValue('aggregationModes', ['none', 'mean'])
            settings.beginWriteArray('sourceSelection')
            settings.endArray()
            settings.endGroup()
        settings.endGroup()
        settings.beginGroup('dataSources')
        settings.setValue('paths', [])
        settings.endGroup()
        settings.beginGroup('data')
        settings.setValue('bin_width', BIN_WIDTH)
        settings.setValue('sample_size', SAMPLE_SIZE)
        settings.setValue('history_size', HISTORY_SIZE)
        settings.endGroup()
        settings.beginGroup('graphics')
        for title in ('left', 'center', 'right'):
            settings.beginGroup(title)
            settings.setValue('window_size', WINDOW_SIZE)
            settings.endGroup()
        settings.endGroup()
        settings.endGroup()

    @QtCore.Slot(str)
    def updateData(self, watchDir: str):
        self.data.update(path=watchDir)
        self.dataUpdated.emit()

    def _createFileActions(self):
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

    def _createEditActions(self):
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

    def _createHelpActions(self):
        self.aboutAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.HelpAbout),
            self.tr('&About'),
            self)
        self.aboutAct.setStatusTip(self.tr('Show about'))
        # TODO: connect self.aboutAct to function

        self.helpMenu.addAction(self.aboutAct)

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
            opts = PlotOptionsGroupBox(
                title=self.tr('Plot options'),
                pos=pos,
                xRange=[int(lim) for lim in xRange])
            self.plotOptionsBox.addWidget(opts)

        sideLayout = QtWidgets.QVBoxLayout()
        sideLayout.addLayout(plotButtonLayout)
        sideLayout.addWidget(self.plotOptionsBox)
        sideLayout.addWidget(self.dataSourcesBox, stretch=1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(sideLayout)
        for title in ('left', 'center', 'right'):
            window_size = settings.value(
                f'default/graphics/{title}/window_size', type=int),
            widget = GraphicsWidget(
                data=self.data,
                window_size=window_size,
                title=title,
                parent=self)
            layout.addWidget(widget, stretch=1)

        self.centralWidget().setLayout(layout)

    def _connectSignalsAndSlots(self):
        self.dataUpdated.connect(self.data.updated)
        self.dataSourcesBox.sourceDataChanged.connect(self.updateData)
        for idx in range(3):
            opts = self.plotOptionsBox.widget(idx)
            gfxs = self.centralWidget().layout().itemAt(idx + 1).widget()

            self.dataSourcesBox.sourceInserted.connect(opts.insertSource)
            self.dataSourcesBox.sourceRemoved.connect(opts.removeSource)
            opts.aggregationModesChanged.connect(gfxs.updateAggregationModes)
            opts.sourceSelectionChanged.connect(gfxs.updateSourceSelection)
            opts.xRangeChanged.connect(gfxs.updateXRange)
            gfxs.xRangeChanged.connect(opts.updateXRange)
