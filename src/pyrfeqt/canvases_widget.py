# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the canvases widget class."""

import time
from typing import Optional

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6 import QtWidgets


class CanvasesWidget(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Constructor."""
        super(CanvasesWidget, self).__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout()

        signal_canvas = FigureCanvas(Figure(figsize=(15, 3)))
        # self.addToolBar(NavigationToolbar(signal_canvas, self))
        layout.addWidget(NavigationToolbar(signal_canvas, self))
        layout.addWidget(signal_canvas)

        spectro_canvas = FigureCanvas(Figure(figsize=(15, 3)))
        layout.addWidget(spectro_canvas)
        # bottom = QtCore.Qt.ToolBarArea.BottomToolBarArea
        # self.addToolBar(bottom, NavigationToolbar(spectro_canvas, self))
        layout.addWidget(NavigationToolbar(spectro_canvas, self))

        # Set up a Line2D.
        self.signal_axes = signal_canvas.figure.subplots(1, 3)
        t = np.linspace(0., 4 * np.pi, 720)
        y = np.sin(t + np.pi * time.time() / 30.)
        for ax in self.signal_axes:
            ax.plot(t, y)

        self.spectro_axes = spectro_canvas.figure.subplots(1, 3)
        self.matrices = []
        self.images = []
        for ax in self.spectro_axes:
            m = np.empty((300, 720))
            for dt in range(300):
                m[dt, :] = np.sin(t + np.pi * (time.time() + 0.1 * dt) / 30.)
            self.matrices.append(m)
            self.images.append(ax.imshow(m))

        signal_canvas.figure.tight_layout()
        spectro_canvas.figure.tight_layout()
        self.setLayout(layout)
