# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the plot options groupbox class."""

from typing import List, Optional

from PySide6 import QtCore, QtWidgets


class QSpinBox(QtWidgets.QSpinBox):
    def sizeHint(self):
        return super().sizeHint() + QtCore.QSize(40, 0)


class SpinBoxStack(QtWidgets.QWidget):
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
                spin.setRange(minimum, maximum)
                spin.setValue(maximum)
                # spin.adjustSize()
                layout.addWidget(spin, row, col)

                spinRow.append(spin)
            self.spins.append(spinRow)

        self.setLayout(layout)


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
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(PlotOptionsGroupBox, self).__init__(title=title, parent=parent)

        layout = QtWidgets.QFormLayout()

        self.axisRanges = SpinBoxStack(0, 720, parent=self)
        self.aggregationMode = MultiModeBox(
            ['none (multi-line)', 'sum', 'average'], self)

        layout.addRow('Axis ranges', self.axisRanges)
        layout.addRow('Aggregation mode', self.aggregationMode)

        self.setLayout(layout)
