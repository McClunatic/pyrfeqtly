# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the graph layout widget."""

import pathlib
import warnings
from functools import partial
from typing import Tuple

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore

warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*ImageItem', lineno=501)
warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*graphics_widget', lineno=104)


class NumpyContainer:

    DEFAULT_DATA = np.empty((1, 1000, 720))
    DEFAULT_DATA[:] = np.nan

    def __init__(self, atol: float = 1e-2):
        self.atol = atol
        self.decimals = int(1 - np.log10(atol))

        #: List[str]
        self.paths = []

        #: np.ndarray of float64 of rounded mtimes
        self.mtimes = np.zeros((1000,))

        #: np.ndarray of float64
        self.data = np.empty((0, 1000, 720))
        self.data[:] = np.nan

    def remove(self, path: str):
        if path not in self.paths:
            return

        pix = self.paths.index(path)
        self.paths.pop(pix)
        self.data = np.delete(self.data, pix, axis=0)
        # if self.data.shape[0] > 1:
        #     self.data = np.delete(self.data, pix, axis=0)
        # # Special case: no data sources, nan data and 0 mtimes
        # else:
        #     self.mtimes[:] = 0.
        #     self.data[:] = np.nan

    def update(self, path: str):
        # Get path index
        pix = self.paths.index(path) if path in self.paths else len(self.paths)

        # Add path to paths list if not in it
        if pix == len(self.paths):
            self.paths.append(path)
            self.data = np.concatenate([self.data, self.DEFAULT_DATA], axis=0)

        # Loop over data and add new entries
        for entry in pathlib.Path(path).glob('*.npy'):
            mtime = np.round(entry.stat().st_mtime, decimals=self.decimals)

            # Get times index
            atix = np.where(
                np.isclose(self.mtimes, mtime, atol=self.atol, rtol=0.))[0]
            if atix.size > 1:
                raise ValueError('Tolerance not right for dataset')
            tix = atix.item() if atix.size == 1 else self.mtimes.size - 1

            # Case 1: data is already written for (pix, tix, :); continue
            if atix.size == 1 and not np.all(np.isnan(self.data[pix, tix])):
                continue
            # Case special: data is not accessible; continue
            try:
                with open(entry, 'rb') as npy_file:
                    new_data = np.load(npy_file)
            except EOFError:
                continue

            # Case 2a: need a new mtime and to roll mtimes & data, then insert
            # Case 2b: just need to insert
            if atix.size == 0:
                if np.any(mtime < self.mtimes):
                    raise ValueError('Unsorted mtime encountered')

                self.mtimes = np.roll(self.mtimes, -1)
                self.mtimes[-1] = mtime
                self.data = np.roll(self.data, -1, axis=1)

            self.data[pix, tix, :] = new_data

    def latest(self, mode: str, window: int):
        window_data = self.data[:, -window:, :]
        if np.all(np.isnan(window_data)):
            return None

        if mode not in ('mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')
        aggregator = getattr(np, f'nan{mode}')
        return aggregator(window_data, axis=0)


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.data = NumpyContainer()

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.arange(720.)
        y = self.data.DEFAULT_DATA[0, -1, :]
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
            m = self.data.DEFAULT_DATA[0, -300:, :]
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
            self.data.update(path=watchDir)
            self.watcher.addPath(watchDir)
        else:
            self.data.remove(path=watchDir)
            self.watcher.removePath(watchDir)
        self.updateGraphs()

    @QtCore.Slot(str)
    def updateData(self, watchDir):
        self.data.update(path=watchDir)
        self.updateGraphs()

    def updateGraphs(self):
        curveData = self.data.latest(mode='mean', window=1)
        if curveData is not None:
            for curve in self.signal_curves:
                curve.setData(curveData.flatten())
        imageData = self.data.latest(mode='mean', window=300)
        if imageData is not None:
            for image in self.spectr_images:
                image.setImage(imageData)
