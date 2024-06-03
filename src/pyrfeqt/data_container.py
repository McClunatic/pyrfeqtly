# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the container class for source data."""
import pathlib
import warnings
from typing import List, Optional

import numpy as np
from PySide6 import QtCore
from scipy.interpolate import RegularGridInterpolator


class DataContainer(QtCore.QObject):

    updated = QtCore.Signal()

    def __init__(
        self,
        binWidth: float,
        historySize: int,
        sampleSize: int,
        parent: QtCore.QObject = None,
    ):
        super().__init__(parent=parent)

        self.binWidth = binWidth
        self.historySize = historySize
        self.sampleSize = sampleSize

        #: List[str]
        self.paths = []

        #: List[str]
        self.sources = []

        #: np.ndarray of float64 of (rounded, actual) mtimes
        self.mtimes = np.empty((2, 0), dtype=float)

        #: set of float64 of rounded mtimes
        self.mtimesSet = set()

        #: np.ndarray of float64
        self.data = np.empty((0, 0, self.sampleSize), dtype=float)

    def applySettings(self, group: str = 'default'):
        settings = QtCore.QSettings()
        paths = settings.value(f'{group}/dataSources/paths', type=list)
        sources = settings.value(f'{group}/dataSources/sources', type=list)
        binWidth = settings.value(f'{group}/data/binWidth', type=float)
        historySize = settings.value(f'{group}/data/historySize', type=int)
        sampleSize = settings.value(f'{group}/data/sampleSize', type=int)

        forceReset = (
            self.paths != paths or
            self.sources != sources or
            self.binWidth != binWidth or
            self.sampleSize != sampleSize)

        self.binWidth = binWidth
        self.historySize = historySize
        self.sampleSize = sampleSize

        self.updateAll(paths, sources, sampleSize, forceReset=forceReset)

    def writeSettings(self, group: str):
        settings = QtCore.QSettings()
        settings.setValue(f'{group}/data/binWidth', self.binWidth)
        settings.setValue(f'{group}/data/historySize', self.historySize)
        settings.setValue(f'{group}/data/sampleSize', self.sampleSize)

    def removeNanSamples(self):
        # Find tix mask for deletion
        delete_mask = np.all(np.isnan(self.data), axis=(0, 2))
        delete_idxs = delete_mask.nonzero()[0]

        # Remove those mtimes from the set
        self.mtimesSet.difference_update(self.mtimes[0, delete_mask])

        # Delete the mtimes and data
        self.mtimes = np.delete(self.mtimes, delete_idxs, axis=1)
        self.data = np.delete(self.data, delete_idxs, axis=1)

    def remove(self, source: str):
        if source not in self.sources:
            return

        pix = self.sources.index(source)
        self.sources.pop(pix)
        self.data = np.delete(self.data, pix, axis=0)
        self.removeNanSamples()

    def updateAll(
        self,
        paths: List[str],
        sources: Optional[List[str]] = None,
        sampleSize: Optional[int] = None,
        forceReset: bool = False,
    ):
        sources = sources if sources is not None else self.sources
        sampleSize = sampleSize if sampleSize is not None else self.sampleSize

        if paths != self.paths or forceReset:
            self.paths[:] = paths
            self.sources = []
            self.mtimes = np.empty((2, 0), dtype=float)
            self.mtimesSet = set()
            self.data = np.empty((0, 0, sampleSize), dtype=float)

        for source in sources:
            self.update(source)

    def update(self, source: str):
        # Get source index
        pix = self.sources.index(source) if source in self.sources \
            else len(self.sources)

        # Add source to sources list if not in it
        if pix == len(self.sources):
            self.sources.append(source)
            self.data = np.pad(
                self.data, ((0, 1), (0, 0), (0, 0)), constant_values=np.nan)

        # If no base path, return
        if not self.paths:
            return

        # Loop over data and add new entries
        path = self.paths[0]
        entries = sorted(
            pathlib.Path(path).glob(f'{source}'),
            key=lambda e: e.stat().st_mtime)
        for entry in entries[-self.historySize:]:
            mtime = entry.stat().st_mtime
            mtime_bin = np.floor(np.true_divide(mtime, self.binWidth))

            # Case 1: mtime in there, data is already written the data for pix
            if mtime_bin in self.mtimesSet:
                tmask = mtime_bin == self.mtimes[0]
            #   1a: already written the data for pix
                if np.any(~np.isnan(self.data[pix, tmask])):
                    continue

            # Case 2: data is not accessible; continue
            try:
                with open(entry, 'rb') as npy_file:
                    new_data = np.load(npy_file)
            except EOFError:
                continue

            # Case 3: mtime in there, data not already written; use tmask later
            if mtime_bin in self.mtimesSet:
                pass
            # Case 4: mtime is not in there and size == historySize
            elif self.mtimes.shape[1] == self.historySize:
                tmask = self.mtimes.shape[1] - 1
                self.mtimesSet.remove(self.mtimes[0, 0])
                self.mtimes = np.roll(self.mtimes, -1, axis=1)
                self.mtimes[:, -1] = [mtime_bin, mtime]
                self.data = np.roll(self.data, -1, axis=1)
            # Case 5: mtime is not in there and size < historySize
            else:
                tmask = self.mtimes.shape[1]
                self.mtimes = np.concatenate(
                    (self.mtimes, [[mtime_bin], [mtime]]),
                    axis=1)
                self.data = np.pad(
                    self.data,
                    ((0, 0), (0, 1), (0, 0)),
                    constant_values=np.nan)

            self.mtimesSet.add(mtime_bin)
            self.data[pix, tmask, :] = new_data

        self.updated.emit()

    def latest(self, selection: List[str], mode: str, window: int):
        if self.data.size == 0:
            return np.empty((0, 0))

        select_data = self.data[[src in selection for src in self.sources]]
        if select_data.size == 0:
            return np.empty((0, 0))

        # Sort the array
        argsort = np.argsort(self.mtimes[1])
        data = select_data[:, argsort]
        mtimes = self.mtimes[:, argsort]

        mtime_target = mtimes[1, -1] - self.binWidth * (window - 1)
        window_idx = np.argmin(np.abs(mtimes[1] - mtime_target))

        window_data = data[:, window_idx:]
        window_mtimes = mtimes[1, window_idx:]
        window_points = np.arange(window_data.shape[2])

        if np.all(np.isnan(window_data)):
            return np.empty((0, 0))

        if window == 1 and mode not in ('none', 'mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')
        elif window > 1 and mode not in ('mean', 'sum', 'max'):
            raise ValueError(f'Unexpected aggregate mode: {mode}')

        def noop(arr, axis=None):
            return arr

        aggregator = getattr(np, f'nan{mode}', noop)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=RuntimeWarning)
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
