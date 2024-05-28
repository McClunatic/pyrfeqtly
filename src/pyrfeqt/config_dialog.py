# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the configurtion dialog class."""

from typing import Optional

from PySide6 import QtCore, QtWidgets

from .data_sources_groupbox import DataSourcesGroupBox
from .plot_options_groupbox import PlotOptionsGroupBox


class DataOptionsGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(PlotOptionsGroupBox, self).__init__(title=title, parent=parent)

        layout = QtWidgets.QFormLayout()

        self.binWidthBox = QtWidgets.QDoubleSpinBox()
        self.binWidthBox.setKeyboardTracking(False)
        self.binWidthBox.setMinimum(0.001)
        self.sampleSizeBox = QtWidgets.QSpinBox()
        self.sampleSizeBox.setKeyboardTracking(False)
        self.sampleSizeBox.setMinimum(2)
        self.historySizeBox = QtWidgets.QSpinBox()
        self.historySizeBox.setKeyboardTracking(False)
        self.historySizeBox.setMinimum(2)

        layout.addRow('sample bin width', self.binWidthBox)
        layout.addRow('sample size', self.sampleSizeBox)
        layout.addRow('max history size', self.historySizeBox)

        self.setLayout(layout)

    def applySettings(self, group: str = 'default'):
        settings = QtCore.QSettings()
        binWidth = settings.value(f'{group}/data/binWidth', type=float)
        sampleSize = settings.value(f'{group}/data/sampleSize', type=int)
        historySize = settings.value(f'{group}/data/historySize', type=int)

        self.binWidthBox.setValue(binWidth)
        self.sampleSizeBox.setValue(sampleSize)
        self.historySizeBox.setValue(historySize)

    def writeSettings(self, group: str):
        settings = QtCore.QSettings()
        settings.beginGroup(f'{group}/data')
        settings.setValue('binWidth', self.binWidthBox.value())
        settings.setValue('historySize', self.historySizeBox.value())
        settings.setValue('sampleSize', self.sampleSizeBox.value())
        settings.endGroup()


class ConfigDialog(QtWidgets.QDialog):

    def __init__(
        self,
        title: str,
        group: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr(title))
        layout = QtWidgets.QGridLayout()

        self.group = group
        self.plotOptions = []

        # Build the first row
        settings = QtCore.QSettings()
        settings.beginGroup(group)
        for idx, pos in enumerate(('left', 'center', 'right')):
            xRange = settings.value(
                f'plotOptions/{pos}/xRange', type=list)
            windowSize = settings.value(
                f'plotOptions/{pos}/windowSize', type=int)
            opts = PlotOptionsGroupBox(
                title=self.tr(f'Plot options ({pos})'),
                pos=pos,
                xRange=[int(lim) for lim in xRange],
                windowSize=windowSize)
            layout.addWidget(opts, 0, idx)
            self.plotOptions.append(opts)

        settings.endGroup()

        # Build the second row
        self.dataOptionsBox = DataOptionsGroupBox('Data options')
        layout.addWidget(self.dataOptionsBox, 1, 0)
        self.dataSourcesBox = DataSourcesGroupBox(
            'Data sources', horizontal=True)
        layout.addWidget(self.dataSourcesBox, 1, 1, 1, 2)

        # Connect signals and slots
        for opts in self.plotOptions:
            self.dataSourcesBox.sourceInserted.connect(opts.insertSource)
            self.dataSourcesBox.sourceRemoved.connect(opts.removeSource)

        self.setLayout(layout)

    def applySettings(self, group: Optional[str] = None):
        group = group if group is not None else self.group
        for opts in self.plotOptions:
            opts.applySettings(group)
        self.dataOptionsBox.applySettings(group)
        self.dataSourcesBox.applySettings(group)

    def writeSettings(self, group: Optional[str] = None):
        group = group if group is not None else self.group
        group = group if group is not None else self.group
        for opts in self.plotOptions:
            opts.writeSettings(group)
        self.dataOptionsBox.writeSettings(group)
        self.dataSourcesBox.writeSettings(group)
