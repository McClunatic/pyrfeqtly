# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the plot options groupbox class."""
from functools import partial
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets


class QSpinBox(QtWidgets.QSpinBox):
    def sizeHint(self):
        baseSizeHint = super().sizeHint()
        if QtCore.QOperatingSystemVersion.current() >= \
                QtCore.QOperatingSystemVersion.Windows11:
            return super().sizeHint() + QtCore.QSize(40, 0)
        else:
            return baseSizeHint


class SpinBoxPair(QtWidgets.QWidget):

    valueChanged = QtCore.Signal(int, int)

    def __init__(
        self,
        minimum: int,
        maximum: int,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        layout = QtWidgets.QHBoxLayout()
        self.lbound = QSpinBox()
        self.lbound.setKeyboardTracking(False)
        self.lbound.setRange(minimum, maximum)
        self.lbound.setValue(minimum)
        self.lbound.valueChanged.connect(
            partial(self.onValueChanged, left=True))
        layout.addWidget(self.lbound)
        self.rbound = QSpinBox()
        self.rbound.setKeyboardTracking(False)
        self.rbound.setRange(minimum, maximum)
        self.rbound.setValue(minimum)
        self.rbound.valueChanged.connect(
            partial(self.onValueChanged, left=False))
        layout.addWidget(self.rbound)

        self.setLayout(layout)

    @QtCore.Slot(int)
    def onValueChanged(self, value: int, left: bool):
        bound = self.lbound if left else self.rbound
        otherBound = self.rbound if left else self.lbound
        otherValue = otherBound.value()
        if (-1 if left else 1) * (value - otherValue) < 0:
            bound.setValue(otherValue)
            otherBound.setValue(value)

        self.valueChanged.emit(*sorted((value, otherValue)))

    @QtCore.Slot(int, int)
    def updateRange(self, lbound: int, rbound: int):
        self.blockSignals(True)
        self.lbound.setValue(lbound)
        self.rbound.setValue(rbound)
        self.blockSignals(False)


class ComboBoxPair(QtWidgets.QWidget):

    valueChanged = QtCore.Signal(str, str)

    def __init__(
        self,
        signalOptions: List[str],
        spectrOptions: List[str],
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        layout = QtWidgets.QGridLayout()
        self.signal = QtWidgets.QComboBox()
        self.signal.addItems(signalOptions)
        self.signal.currentTextChanged.connect(self.onCurrentTextChanged)
        layout.addWidget(QtWidgets.QLabel(self.tr('Signal')), 0, 0)
        layout.addWidget(self.signal, 1, 0)
        self.spectr = QtWidgets.QComboBox()
        self.spectr.addItems(spectrOptions)
        self.spectr.currentTextChanged.connect(self.onCurrentTextChanged)
        layout.addWidget(QtWidgets.QLabel(self.tr('Spectrogram')), 0, 1)
        layout.addWidget(self.spectr, 1, 1)

        self.setLayout(layout)

    @QtCore.Slot(int)
    def onCurrentTextChanged(self, value: str):
        self.valueChanged.emit(
            self.signal.currentText(), self.spectr.currentText())

    @QtCore.Slot(str, str)
    def updateCurrentText(self, signal: str, spectr: str):
        self.signal.setCurrentText(signal)
        self.spectr.setCurrentText(spectr)


class SelectedSourcesGroupBox(QtWidgets.QWidget):

    sourceChanged = QtCore.Signal(str, QtCore.Qt.CheckState)

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        self.listModel = QtGui.QStandardItemModel()
        self.listModel.itemChanged.connect(self.onItemChanged)

        self.listView = QtWidgets.QListView()
        self.listView.setSizeAdjustPolicy(
            QtWidgets.QListView.SizeAdjustPolicy.AdjustToContents)
        self.listView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.listView.setModel(self.listModel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.listView)
        self.setLayout(layout)

    @QtCore.Slot(str)
    def insertSource(self, source: str):
        item = QtGui.QStandardItem(source)
        item.setCheckable(True)
        self.listModel.appendRow(item)
        # Check the item to trigger onItemChanged after appending
        item.setCheckState(QtCore.Qt.CheckState.Checked)

    @QtCore.Slot(str)
    def removeSource(self, source: str):
        items = self.listModel.findItems(source)
        for item in items:
            # Uncheck the item to trigger onItemChanged before removing
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            index = self.listModel.indexFromItem(item)
            self.listModel.removeRow(index.row())

    @QtCore.Slot(QtGui.QStandardItem)
    def onItemChanged(self, item):
        self.sourceChanged.emit(item.text(), item.checkState())


class PlotOptionsGroupBox(QtWidgets.QGroupBox):

    xRangeChanged = QtCore.Signal(int, int)
    aggregationModesChanged = QtCore.Signal(str, str)
    sourceSelectionChanged = QtCore.Signal(str, QtCore.Qt.CheckState)

    updateXRange = QtCore.Signal(int, int)
    insertSource = QtCore.Signal(str)
    removeSource = QtCore.Signal(str)

    def __init__(
        self,
        title: str,
        pos: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(PlotOptionsGroupBox, self).__init__(title=title, parent=parent)
        self.pos = pos

        layout = QtWidgets.QFormLayout()

        self.xAxisRange = SpinBoxPair(0, 720, parent=self)
        self.xAxisRange.valueChanged.connect(self.xRangeChanged)
        self.updateXRange.connect(self.xAxisRange.updateRange)

        self.aggregationModes = ComboBoxPair(
            signalOptions=['none', 'mean', 'sum', 'max'],
            spectrOptions=['none', 'mean', 'sum', 'max'],
            parent=self)
        self.aggregationModes.valueChanged.connect(
            self.aggregationModesChanged)

        self.dataSources = SelectedSourcesGroupBox(parent=self)
        self.dataSources.sourceChanged.connect(self.sourceSelectionChanged)
        self.insertSource.connect(self.dataSources.insertSource)
        self.removeSource.connect(self.dataSources.removeSource)

        layout.addRow('x-axis range', self.xAxisRange)
        layout.addRow('aggregation modes', self.aggregationModes)
        layout.addRow('data sources', self.dataSources)

        self.setLayout(layout)

    def applySettings(self, group: str = 'default'):
        settings = QtCore.QSettings()
        xRange = settings.value(
            f'{group}/plotOptions/{self.pos}/xRange', type=list)
        self.xAxisRange.blockSignals(True)
        self.xAxisRange.updateRange(*xRange)
        self.xAxisRange.blockSignals(False)

        aggregationModes = settings.value(
            f'{group}/plotOptions/{self.pos}/aggregationModes', type=list)
        self.aggregationModes.blockSignals(True)
        self.aggregationModes.updateCurrentText(*aggregationModes)
        self.aggregationModes.blockSignals(False)

        size = settings.beginReadArray(
            f'{group}/plotOptions/{self.pos}/sourceSelection')
        paths = []
        sourceSelection = []
        for idx in range(size):
            settings.setArrayIndex(idx)
            paths.append(
                settings.value(f'{group}/plotOptions/{self.pos}/path'))
            sourceSelection.append((
                settings.value(f'{group}/plotOptions/{self.pos}/path'),
                settings.value(f'{group}/plotOptions/{self.pos}/checked')))
        settings.endArray()

        self.dataSources.blockSignals(True)
        # Loop over sources in reverse order: if not in paths, remove
        for row in range(self.dataSources.listModel.rowCount() - 1, -1, -1):
            item = self.dataSources.listModel.index(row, 0)
            if item.text() not in paths:
                self.dataSources.listModel.removeRow(row)
        # Loop over paths: if not in sources, add
        for (source, checked) in sourceSelection:
            checkState = (QtCore.Qt.CheckState.Checked if checked
                          else QtCore.Qt.CheckState.Unchecked)
            if not self.dataSources.listModel.findItems(source):
                item = QtGui.QStandardItem(source)
                item.setCheckable(True)
                self.listModel.appendRow(item)
                item.setCheckState(checkState)
        self.dataSources.blockSignals(False)
