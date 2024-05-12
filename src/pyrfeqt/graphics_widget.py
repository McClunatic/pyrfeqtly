# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the graph layout widget."""

import datetime
import pathlib
import warnings
from functools import partial
from typing import Tuple

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore

warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*ImageItem', lineno=501)

NAN_LATEST = np.empty((300, 720))
NAN_LATEST[:] = np.nan


class DataSource:
    def __init__(self, name: str):
        """Constructor."""
        self.name = name
        self.data = {}
        self.latest_mtime = datetime.datetime.fromtimestamp(0.)
        self.update()

    def update(self):
        mtime = max_mtime = cutoff = self.latest_mtime
        for path in pathlib.Path(self.name).glob('*.npy'):
            mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            if mtime <= cutoff:
                continue
            max_mtime = max(max_mtime, mtime)
            try:
                with open(path, 'rb') as npy_file:
                    self.data[mtime] = np.load(npy_file)
            except EOFError:
                continue
        self.latest_mtime = mtime

    def latest(self):
        if not self.data:
            return NAN_LATEST[-1]
        return self.data[max(self.data.keys())]

    def latestWindow(self, window: int = 300):
        if not self.data:
            return NAN_LATEST
        keys = sorted(self.data.keys())[-window:]
        rows = [self.data[key] for key in keys]
        if len(rows) < window:
            filler = np.empty((window - len(rows), 720))
            filler[:] = np.nan
            rows.insert(0, filler)
        return np.vstack(rows)


class DataContainer:
    def __init__(self):
        """Constructor."""
        self.sources = []

    def latest(self, mode: str):
        data = [source.latest() for source in self.sources]
        if len(data) == 0:
            return None
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
        if len(data) == 0:
            return None
        if len(data) == 1:
            return data[0]

        if mode == 'sum':
            return np.sum(data, axis=0)
        elif mode == 'mean':
            return np.sum(data, axis=0)
        else:
            return np.max(data, axis=0)

    def addSource(self, source: DataSource):
        self.sources.append(source)

    def removeSource(self, name: str):
        matches = [src for src in self.sources if src.name == name]
        if matches:
            self.sources.remove(matches[0])

    def updateSource(self, name: str):
        matches = [src for src in self.sources if src.name == name]
        if matches:
            matches[0].update()


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.data = DataContainer()

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.arange(720.)
        y = NAN_LATEST[-1]
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
            m = NAN_LATEST
            image = pg.ImageItem(m, colorMap='viridis', axisOrder='row-major')
            plot.addItem(image)
            self.spectr_images.append(image)

        self.watcher = QtCore.QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.updateData)

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
    def updateWatcher(self, watchDir, checkState):
        if checkState == QtCore.Qt.CheckState.Checked:
            dataSource = DataSource(name=watchDir)
            self.data.addSource(dataSource)
            self.watcher.addPath(watchDir)
        else:
            self.data.removeSource(name=watchDir)
            self.watcher.removePath(watchDir)
        self.updateGraphs()

    @QtCore.Slot(str)
    def updateData(self, watchDir):
        self.data.updateSource(watchDir)
        self.updateGraphs()

    def updateGraphs(self):
        curveData = self.data.latest('')
        if curveData is not None:
            for curve in self.signal_curves:
                curve.setData(curveData)
        imageData = self.data.latestWindow('')
        if imageData is not None:
            for image in self.spectr_images:
                image.setImage(imageData)
