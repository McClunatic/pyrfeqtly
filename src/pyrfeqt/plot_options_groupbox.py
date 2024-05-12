# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the plot options groupbox class."""
from functools import partial
from typing import List, Optional

from PySide6 import QtCore, QtWidgets


class QSpinBox(QtWidgets.QSpinBox):
    def sizeHint(self):
        return super().sizeHint() + QtCore.QSize(40, 0)


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
    def __init__(
        self,
        options: List[str],
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super().__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout()
        self.radios = [QtWidgets.QRadioButton(self.tr(opt)) for opt in options]
        self.radios[0].setChecked(True)
        for radio in self.radios:
            layout.addWidget(radio)
        self.setLayout(layout)


class PlotOptionsGroupBox(QtWidgets.QGroupBox):

    rangeChanged = QtCore.Signal(int, int, int)

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

        self.aggregationMode = MultiModeBox(
            ['none (multi-line)', 'sum', 'average'], self)

        layout.addRow('Axis ranges', self.axisRanges)
        layout.addRow('Aggregation mode', self.aggregationMode)

        self.setLayout(layout)

    @QtCore.Slot(int, int, int)
    def updateRange(self, row: int, minimum: int, maximum: int):
        self.axisRanges.blockSignals(True)
        self.axisRanges.spins[row][0].setValue(minimum)
        self.axisRanges.spins[row][1].setValue(maximum)
        self.axisRanges.blockSignals(False)
