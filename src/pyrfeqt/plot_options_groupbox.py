# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the plot options groupbox class."""
from functools import partial
from typing import List, Optional

from PySide6 import QtCore, QtWidgets


class QSpinBox(QtWidgets.QSpinBox):
    def sizeHint(self):
        baseSizeHint = super().sizeHint()
        windows11 = QtCore.QOperatingSystemVersion(
            QtCore.QOperatingSystemVersion.Windows,
            QtCore.QOperatingSystemVersion.Windows11)
        if QtCore.QOperatingSystemVersion.current() >= windows11:
            return super().sizeHint() + QtCore.QSize(40, 0)
        else:
            return baseSizeHint


class SpinBoxStack(QtWidgets.QWidget):

    valueChanged = QtCore.Signal(int, int, int)

    def __init__(
        self,
        minimum: int,
        maximum: int,
        rows: int = 3,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        layout = QtWidgets.QGridLayout()
        self.spins = []
        for row in range(rows):
            spinRow = []
            for col in range(2):
                spin = QSpinBox()
                spin.setKeyboardTracking(False)
                spin.setRange(minimum, maximum)
                spin.setValue(minimum if col == 0 else maximum)
                spin.valueChanged.connect(
                    partial(self.onValueChanged, row=row, col=col))
                layout.addWidget(spin, row, col)

                spinRow.append(spin)
            self.spins.append(spinRow)

        self.setLayout(layout)

    @QtCore.Slot(int)
    def onValueChanged(self, value: int, row: int, col: int):
        otherCol = (col + 1) % 2
        otherValue = self.spins[row][otherCol].value()
        if (col - otherCol) * (value - otherValue) < 0:
            self.spins[row][col].setValue(otherValue)
            self.spins[row][otherCol].setValue(value)

        self.valueChanged.emit(row, *sorted((value, otherValue)))


class MultiModeBox(QtWidgets.QWidget):

    valueChanged = QtCore.Signal(str)

    def __init__(
        self,
        name: str,
        options: List[str],
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel(self.tr(name)))
        self.radios = [QtWidgets.QRadioButton(self.tr(opt)) for opt in options]
        self.radios[0].setChecked(True)
        for radio, opt in zip(self.radios, options):
            radio.toggled.connect(partial(self.onToggled, option=opt))
            layout.addWidget(radio)
        layout.addStretch()
        self.setLayout(layout)

    @QtCore.Slot(bool, str)
    def onToggled(self, checked: bool, option: str):
        if checked:
            self.valueChanged.emit(option)


class PlotOptionsGroupBox(QtWidgets.QGroupBox):

    rangeChanged = QtCore.Signal(int, int, int)
    signalModeChanged = QtCore.Signal(str)
    spectrModeChanged = QtCore.Signal(str)

    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(PlotOptionsGroupBox, self).__init__(title=title, parent=parent)

        layout = QtWidgets.QFormLayout()

        self.axisRanges = SpinBoxStack(0, 720, parent=self)
        self.axisRanges.valueChanged.connect(self.rangeChanged)

        self.signalAggregationMode = MultiModeBox(
            'Signals', ['none', 'mean', 'sum', 'max'], self)
        self.signalAggregationMode.valueChanged.connect(self.signalModeChanged)

        self.spectrAggregationMode = MultiModeBox(
            'Spectrograms', ['mean', 'sum', 'max'], self)
        self.spectrAggregationMode.valueChanged.connect(self.spectrModeChanged)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.signalAggregationMode)
        hbox.addWidget(self.spectrAggregationMode)

        layout.addRow('Axis ranges', self.axisRanges)
        layout.addRow('Aggregation mode', hbox)

        self.setLayout(layout)

    @QtCore.Slot(int, int, int)
    def updateRange(self, row: int, minimum: int, maximum: int):
        self.axisRanges.blockSignals(True)
        self.axisRanges.spins[row][0].setValue(minimum)
        self.axisRanges.spins[row][1].setValue(maximum)
        self.axisRanges.blockSignals(False)
