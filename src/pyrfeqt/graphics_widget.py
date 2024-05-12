# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the graph layout widget."""

from functools import partial
from typing import Tuple

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.arange(720.)
        y = np.sin(t * np.pi / 180.)
        for idx, plot in enumerate(self.signal_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.setXRange(t.min(), t.max() + 1.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='signal', idx=idx))
        self.signal_curves = [plot.plot(t, y) for plot in self.signal_plots]

        self.nextRow()
        self.spectr_plots = [self.addPlot() for _ in range(3)]
        self.spectr_images = []
        for idx, plot in enumerate(self.spectr_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='spectr', idx=idx))
            m = np.empty((300, 720))
            for dt in range(300):
                m[dt, :] = np.sin((t + dt) * np.pi / 180.)
            self.spectr_images.append(pg.ImageItem(m.T, colorMap='viridis'))
            plot.addItem(self.spectr_images[-1])

    @QtCore.Slot(int, int, int)
    def updateRange(self, plot: int, minimum: int, maximum: int):
        signal_plot = self.signal_plots[plot]
        signal_plot.blockSignals(True)
        signal_plot.setXRange(minimum, maximum)
        signal_plot.blockSignals(False)

        spectr_plot = self.spectr_plots[plot]
        spectr_plot.blockSignals(True)
        spectr_plot.setXRange(minimum, maximum)
        spectr_plot.blockSignals(False)

    @QtCore.Slot(object, object)
    def onXRangeChanged(
        self,
        view: pg.ViewBox,
        xRange: Tuple[float, float],
        mode: str,
        idx: int,
    ):
        plot = (self.spectr_plots[idx] if mode == 'signal'
                else self.signal_plots[idx])
        plot.blockSignals(True)
        plot.setXRange(*xRange)
        plot.blockSignals(False)
        self.rangeChanged.emit(idx, int(xRange[0]), int(xRange[1]))
