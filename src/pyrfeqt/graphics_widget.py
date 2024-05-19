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
from scipy.interpolate import RegularGridInterpolator

warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*ImageItem', lineno=501)
warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*graphics_widget', lineno=107)


class NumpyContainer:
    def __init__(
        self,
        bin_width: float,
        history_size: int,
        sample_size: int,
    ):
        self.bin_width = bin_width
        self.history_size = history_size

        #: List[str]
        self.paths = []

        #: np.ndarray of float64 of (rounded, actual) mtimes
        self.mtimes = np.empty((2, 0), dtype=float)

        #: set of float64 of rounded mtimes
        self.set_mtimes = set()

        #: np.ndarray of float64
        self.data = np.empty((0, 0, sample_size), dtype=float)

    def remove_nan_samples(self):
        # Find tix mask for deletion
        delete_mask = np.all(np.isnan(self.data), axis=(0, 2))
        delete_idxs = delete_mask.nonzero()[0]

        # Remove those mtimes from the set
        self.set_mtimes.difference_update(self.mtimes[0, delete_mask])

        # Delete the mtimes and data
        self.mtimes = np.delete(self.mtimes, delete_idxs, axis=1)
        self.data = np.delete(self.data, delete_idxs, axis=1)

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
        entries = sorted(
            pathlib.Path(path).glob('*.npy'), key=lambda e: e.stat().st_mtime)
        for entry in entries[-self.history_size:]:
            # Case 1: data is not accessible; continue
            try:
                with open(entry, 'rb') as npy_file:
                    new_data = np.load(npy_file)
            except EOFError:
                continue

            mtime = entry.stat().st_mtime
            mtime_bin = np.floor(np.true_divide(mtime, self.bin_width))

            # Case 2: mtime is in there
            if mtime_bin in self.set_mtimes:
                tmask = mtime_bin == self.mtimes[0]
            #   2a: already written the data for pix
                if np.any(~np.isnan(self.data[pix, tmask])):
                    continue
            #   2b: it's not already written; use tmask later
            # Case 3: mtime is not in there and size == history_size
            elif self.mtimes.shape[1] == self.history_size:
                tmask = self.mtimes.shape[1] - 1
                self.set_mtimes.remove(self.mtimes[0, 0])
                self.mtimes = np.roll(self.mtimes, -1, axis=1)
                self.mtimes[:] = [mtime_bin, mtime]
                self.data = np.roll(self.data, -1, axis=1)
            # Case 4: mtime is not in there and size < history_size
            else:
                tmask = self.mtimes.shape[1]
                self.mtimes = np.concatenate(
                    (self.mtimes, [[mtime_bin], [mtime]]),
                    axis=1)
                self.data = np.pad(
                    self.data,
                    ((0, 0), (0, 1), (0, 0)),
                    constant_values=np.nan)

            self.set_mtimes.add(mtime_bin)
            self.data[pix, tmask, :] = new_data

    def latest(self, mode: str, window: int):
        if self.data.size == 0:
            return None

        # Sort the array
        argsort = np.argsort(self.mtimes[1])
        data = self.data[:, argsort]
        mtimes = self.mtimes[:, argsort]

        mtime_target = mtimes[1, -1] - self.bin_width * (window - 1)
        window_idx = np.argmin(np.abs(mtimes[1] - mtime_target))

        window_data = data[:, window_idx:]
        window_mtimes = mtimes[1, window_idx:]
        window_points = np.arange(window_data.shape[2])

        if np.all(np.isnan(window_data)):
            return None

        if window == 1 and mode not in ('none', 'mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')
        elif window > 1 and mode not in ('mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')

        def noop(arr, axis=None):
            return arr

        aggregator = getattr(np, f'nan{mode}', noop)
        window_values = aggregator(window_data, axis=0)
        # Return data as is when time dimension is removed
        if window == 1:
            return window_values
        # Interpolate data when time dimension is not (window > 1)
        interp = RegularGridInterpolator(
            (window_mtimes, window_points), window_values)
        window_frac = np.round(
            (mtimes[1, -1] - mtimes[1, window_idx]) /
            (mtimes[1, -1] - mtime_target),
            decimals=2)
        window_frac = min(1., window_frac)
        window_samples = np.linspace(
            mtimes[1, window_idx],
            mtimes[1, -1],
            int(np.floor(window * window_frac)))
        T, Y = np.meshgrid(window_samples, window_points, indexing='ij')
        return interp((T, Y))


class GraphicsWidget(pg.GraphicsLayoutWidget):

    rangeChanged = QtCore.Signal(int, int, int)

    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        bin_width = 1e0
        history_size = 1000
        sample_size = 720
        self.window = 300
        self.data = NumpyContainer(
            bin_width=bin_width,
            history_size=history_size,
            sample_size=sample_size)

        self.signalMode = 'none'
        self.spectrMode = 'mean'

        self.signal_plots = [self.addPlot() for _ in range(3)]
        for idx, plot in enumerate(self.signal_plots):
            plot.addLegend()
            viewBox = plot.getViewBox()
            viewBox.setDefaultPadding(0.)
            plot.setXRange(0, sample_size)
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='signal', idx=idx))

        self.nextRow()
        self.spectr_plots = [self.addPlot() for _ in range(3)]
        for idx, plot in enumerate(self.spectr_plots):
            viewBox = plot.getViewBox()
            viewBox.setDefaultPadding(0.)
            viewBox.invertY()
            plot.sigXRangeChanged.connect(
                partial(self.onXRangeChanged, mode='spectr', idx=idx))

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
        self.updateGraphs()

    @QtCore.Slot(str)
    def updateSpectrMode(self, mode):
        self.spectrMode = mode
        self.updateGraphs()

    def updateCurves(self, plot, curveData):
        tab_colors = [
            '#1f77b4',
            '#ff7f0e',
            '#2ca02c',
            '#d62728',
            '#9467bd',
            '#8c564b',
            '#e377c2',
            '#7f7f7f',
            '#bcbd22',
            '#17becf',
        ]
        numSources = curveData.shape[0]
        numCurves = len(plot.curves)
        # Add curve data for all sources
        for pix in range(numSources):
            pixData = curveData[pix]
            color = tab_colors[pix]
            name = pathlib.Path(self.data.paths[pix]).name
            if pix < numCurves:
                plot.curves[pix].setData(pixData.flatten(), pen=color)
            else:
                curve = pg.PlotDataItem(
                    pixData.flatten(), pen=color, name=name)
                plot.addItem(curve)
        # Remove curve from viewbox for any extra curves
        for pix in range(numSources, numCurves):
            plot.removeItem(curve)

    def updateImages(self, plot, imageData):
        if plot.items:
            plot.items[0].setImage(np.flipud(imageData))
        else:
            image = pg.ImageItem(
                np.flipud(imageData),
                colorMap='viridis', axisOrder='row-major')
            plot.addItem(image)

    def updateGraphs(self):
        curveData = self.data.latest(mode=self.signalMode, window=1)
        if curveData is not None and curveData.size > 0:
            for plot in self.signal_plots:
                self.updateCurves(plot, curveData)

        imageData = self.data.latest(mode=self.spectrMode, window=self.window)
        if imageData is not None and imageData.size > 0:
            for plot in self.spectr_plots:
                self.updateImages(plot, imageData)
