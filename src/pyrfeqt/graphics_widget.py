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
    'ignore', category=RuntimeWarning, module=r'.*graphics_widget', lineno=107)


class NumpyContainer:
    def __init__(
        self,
        bin_width: float = 1e-1,
        history_size: int = 1000,
        sample_size: int = 720,
    ):
        self.bin_width = bin_width
        self.history_size = history_size

        #: List[str]
        self.paths = []

        #: np.ndarray of float64 of (rounded, actual) mtimes
        self.mtimes = np.zeros((2, 1))

        #: set of float64 of rounded mtimes
        self.set_mtimes = set(self.mtimes[0])

        #: np.ndarray of float64
        self.data = np.empty((0, 1, sample_size))
        self.data[:] = np.nan

    def remove_nan_samples(self):
        # Find tix mask for deletion
        delete_mask = np.all(np.isnan(self.data, axis=(0, 2)))

        # Remove those mtimes from the set
        self.set_mtimes.difference_update(self.mtimes[0, delete_mask])

        # Delete the mtimes and data
        self.mtimes = self.mtimes[: ~delete_mask]
        self.data = self.data[:, ~delete_mask, :]

    def remove(self, path: str):
        if path not in self.paths:
            return

        pix = self.paths.index(path)
        self.paths.pop(pix)
        self.data = np.delete(self.data, pix, axis=0)
        self.remove_nan_samples()

    def update(self, path: str):
        # Get path index
        pix = self.paths.index(path) if path in self.paths else len(self.paths)

        # Add path to paths list if not in it
        if pix == len(self.paths):
            self.paths.append(path)
            self.data = np.pad(
                self.data, ((0, 1), (0, 0), (0, 0)), constant_values=np.nan)

        # Loop over data and add new entries
        for entry in pathlib.Path(path).glob('*.npy'):
            mtime = entry.stat().st_mtime
            mtime_bin = np.floor(np.true_divide(mtime, self.bin_width))

            #   1b: not yet written for pix
            # Case 2: it's not in there and size < history_size
            # Case 3: it's not in there and size == history_size
            # Case 1: it's in there
            if mtime_bin in self.set_mtimes:
                tmask = mtime_bin == self.mtimes[0]
            #   1a: already written the data for pix
                if np.any(~np.isnan(self.data[pix, tmask])):
                    continue
            #   1b: it's not already written; use tmask later

            # Case 2: data is not accessible; continue
            try:
                with open(entry, 'rb') as npy_file:
                    new_data = np.load(npy_file)
            except EOFError:
                continue

            # Case 3: it's not in there and size == history_size; roll and
            #         overwrite data at time axis ends
            if self.mtimes.shape[1] == self.history_size:
                tmask = self.mtimes.shape[1] - 1
                self.set_mtimes.remove(self.mtimes[0, 0])
                self.mtimes = np.roll(self.mtimes, -1, axis=1)
                self.mtimes[:] = [mtime_bin, mtime]
                self.data = np.roll(self.data, -1, axis=1)
            # Case 4: it's not in there and size < history_size; append
            #         new data to end of time axes
            else:
                tmask = self.mtimes.shape[1]
                self.mtimes = np.concatenate(
                    self.mtimes,
                    [[mtime_bin], [mtime]],
                    axis=1)
                self.data = np.pad(
                    self.data,
                    ((0, 0), (0, 1), (0, 0)),
                    constant_values=np.nan)

            self.set_mtimes.add(mtime_bin)
            self.data[pix, tmask, :] = new_data

    def latest(self, mode: str, window: int):
        window_data = self.data[:, -window:, :]
        window_mtimes = self.mtimes[1, -window:]
        if np.all(np.isnan(window_data)):
            return None

        if window == 1 and mode not in ('none', 'mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')
        elif window > 1 and mode not in ('mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')
        try:
            aggregator = getattr(np, f'nan{mode}')
            return aggregator(window_data, axis=0)
        except AttributeError:
            return window_data, window_mtimes


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.data = NumpyContainer()

        self.signalMode = 'none'
        self.spectrMode = 'mean'

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.arange(720.)
        y = t * np.nan
        for idx, plot in enumerate(self.signal_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.setXRange(t.min(), t.max() + 1.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='signal', idx=idx))
        self.signal_curves = []
        for plot in self.signal_plots:
            curve = plot.plot(t, y)
            self.signal_curves.append([curve])

        self.nextRow()
        self.spectr_plots = [self.addPlot() for _ in range(3)]
        self.spectr_images = []
        m = np.empty((300, 720))
        m[:] = np.nan
        for idx, plot in enumerate(self.spectr_plots):
            plot.getViewBox().setDefaultPadding(0.)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='spectr', idx=idx))
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

    @QtCore.Slot(str)
    def updateSignalMode(self, mode):
        self.signalMode = mode

    @QtCore.Slot(str)
    def updateSpectrMode(self, mode):
        self.spectrMode = mode

    def updateCurves(self, curves, plot, curveData):
        numSources = curveData.shape[0]
        numCurves = len(curves)
        # Add curve data for all sources
        for pix in range(numSources):
            pixData = curveData[pix]
            if pix < numCurves:
                curves[pix].setData(pixData.flatten())
            else:
                curve = pg.PlotDataItem(pixData.flatten())
                curves.append(curve)
                plot.addItem(curve)
        # Remove curve from viewbox for any extra curves
        for pix in range(numSources, numCurves):
            curve = curves[pix]
            plot.removeItem(curve)

    def updateGraphs(self):
        curveData = self.data.latest(mode=self.signalMode, window=1)
        if curveData is not None:
            for curves, plot in zip(self.signal_curves, self.signal_plots):
                self.updateCurves(curves, plot, curveData)

        imageData = self.data.latest(mode=self.spectrMode, window=300)
        if imageData is not None:
            for image in self.spectr_images:
                image.setImage(imageData)
