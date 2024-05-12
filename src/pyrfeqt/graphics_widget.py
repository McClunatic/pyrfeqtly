# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the graph layout widget."""

from functools import partial
from typing import Tuple

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore


class DataSource:
    def __init__(self, name: str):
        """Constructor."""
        self.name = name
        self.data = {}

    def latest(self):
        return self.data[max(self.data.keys())]

    def latestWindow(self, window: int = 300):
        keys = sorted(self.data.keys())[-window:]
        rows = [self.data[key] for key in keys]
        if len(rows) < window:
            filler = np.empty((window - len(rows)), 720)
            filler[:] = np.nan
            rows.insert(0, filler)
        return np.vstack(rows)


class DataContainer:
    def __init__(self):
        """Constructor."""
        self.sources = []

    def latest(self, mode: str):
        data = [source.latest() for source in self.sources]
        if len(data) == 1:
            return data[0]

        if mode == 'sum':
            return np.sum(data, axis=0)
        elif mode == 'mean':
            return np.sum(data, axis=0)
        else:
            return np.max(data, axis=0)

    def latestWindow(self, mode: str, window: int = 300):
        data = [source.latestWindow(window) for source in self.sources]
        if len(data) == 1:
            return data[0]

        if mode == 'sum':
            return np.sum(data, axis=0)
        elif mode == 'mean':
            return np.sum(data, axis=0)
        else:
            return np.max(data, axis=0)

    def removeSource(self, name: str):
        matches = [src for src in self.sources if src.name == name]
        if matches:
            self.sources.remove(matches[0])


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.arange(720.)
        y = np.empty(t.size)
        y[:] = np.nan
        for idx, plot in enumerate(self.signal_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.setXRange(t.min(), t.max() + 1.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='signal', idx=idx))
        self.signal_curves = []
        for plot in self.signal_plots:
            curve = plot.plot(t, y)
            self.signal_curves.append(curve)

        self.nextRow()
        self.spectr_plots = [self.addPlot() for _ in range(3)]
        self.spectr_images = []
        for idx, plot in enumerate(self.spectr_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='spectr', idx=idx))
            m = np.empty((300, 720))
            m[:] = np.nan
            image = pg.ImageItem(m.T, colorMap='viridis')
            plot.addItem(image)
            self.spectr_images.append(image)

        self.watcher = QtCore.QFileSystemWatcher()

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

    @QtCore.Slot(str, QtCore.Qt.CheckState)
    def updateWatcher(self, dir, checkState):
        print(f'{dir=}, {checkState=}')
        if checkState == QtCore.Qt.CheckState.Checked:
            # collect the data since it's new
            # add to the watcher
            pass
        else:
            # drop the data source
            # delete from the watcher
            pass
