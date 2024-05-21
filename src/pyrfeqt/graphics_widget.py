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

from .data_container import DataContainer

warnings.filterwarnings(
    'ignore', category=RuntimeWarning, module=r'.*ImageItem', lineno=501)


class GraphicsWidget(pg.GraphicsLayoutWidget):

    xRangeChanged = QtCore.Signal(int, int)

    def __init__(self, data: DataContainer, title=None, parent=None):
        super().__init__(parent=parent, title=title)

        self.data = data
        self.data.updated.connect(self.updatePlots)

        # TODO: make sure these get set on app init somehow
        self.signalMode = 'none'
        self.spectrMode = 'mean'
        self.sourceSelection = {}
        self.window = 300

        self.signalPlot = self.addPlot()
        self.signalPlot.addLegend(offset=(-1, -1))
        self.signalPlot.getViewBox().setDefaultPadding(0.)
        self.signalPlot.sigXRangeChanged.connect(
            partial(self.onXRangeChanged, mode='signal'))

        self.nextRow()
        self.spectrPlot = self.addPlot()
        viewBox = self.spectrPlot.getViewBox()
        viewBox.setDefaultPadding(0.)
        viewBox.invertY()
        self.spectrPlot.sigXRangeChanged.connect(
            partial(self.onXRangeChanged, mode='spectr'))

        self.nextRow()
        self.colorBar = pg.ColorBarItem(colorMap='plasma', orientation='h')
        self.colorBar.setVisible(False)
        self.addItem(self.colorBar)

    @QtCore.Slot(object, object)
    def onXRangeChanged(
        self,
        view: pg.ViewBox,
        xRange: Tuple[float, float],
        mode: str,
    ):
        plot = self.spectrPlot if mode == 'signal' else self.signalPlot
        plot.blockSignals(True)
        plot.setXRange(*xRange)
        plot.blockSignals(False)
        self.xRangeChanged.emit(int(xRange[0]), int(xRange[1]))

    @QtCore.Slot(int, int)
    def updateXRange(self, minimum: int, maximum: int):
        self.signalPlot.blockSignals(True)
        self.signalPlot.setXRange(minimum, maximum)
        self.signalPlot.blockSignals(False)

        self.spectrPlot.blockSignals(True)
        self.spectrPlot.setXRange(minimum, maximum)
        self.spectrPlot.blockSignals(False)

    @QtCore.Slot(str, str)
    def updateAggregationModes(self, signalMode: str, spectrMode: str):
        self.signalMode = signalMode
        self.spectrMode = spectrMode
        self.updatePlots()

    @QtCore.Slot(str, QtCore.Qt.CheckState)
    def updateSourceSelection(self, source: str, state: QtCore.Qt.CheckState):
        self.sourceSelection[source] = state == QtCore.Qt.CheckState.Checked

    def updateCurves(self, curveData, selection):
        tab_colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange
            '#2ca02c',  # green
            '#d62728',  # red
            '#9467bd',  # purple
            '#8c564b',  # brown
            '#e377c2',  # pink
            '#7f7f7f',  # gray
            '#bcbd22',  # olive
            '#17becf',  # cyan
        ]
        numSources = curveData.shape[0]
        numCurves = len(self.signalPlot.curves)
        # Add curve data for all sources
        for pix in range(numSources):
            pixData = curveData[pix]
            color = tab_colors[pix % len(tab_colors)]
            name = pathlib.Path(selection[pix]).name
            if pix < numCurves:
                curve = self.signalPlot.curves[pix]
                curve.setData(pixData.flatten(), pen=color)
                # Update legend for item
                self.signalPlot.legend.removeItem(curve)
                self.signalPlot.legend.addItem(curve, name=name)
            else:
                curve = pg.PlotDataItem(
                    pixData.flatten(), pen=color, name=name)
                self.signalPlot.addItem(curve)
        # Remove curve from viewbox for any extra curves
        for pix in range(numSources, numCurves):
            self.signalPlot.removeItem(self.signalPlot.curves[pix])

    def updateImages(self, imageData):
        if imageData.size == 0:
            self.spectrPlot.removeItem(self.spectrPlot.items[0])
            self.colorBar.setVisible(False)
        elif self.spectrPlot.items:
            self.spectrPlot.items[0].setImage(np.flipud(imageData))
            self.colorBar.setImageItem(self.spectrPlot.items[0])
            self.colorBar.setVisible(True)
        else:
            image = pg.ImageItem(np.flipud(imageData), axisOrder='row-major')
            self.spectrPlot.addItem(image)
            self.colorBar.setImageItem(image)
            self.colorBar.setVisible(True)

    @QtCore.Slot()
    def updatePlots(self):
        selection = [src for src in self.sourceSelection
                     if self.sourceSelection[src]]
        curveData = self.data.latest(
            selection=selection, mode=self.signalMode, window=1)
        self.updateCurves(curveData, selection)

        imageData = self.data.latest(
            selection=selection, mode=self.spectrMode, window=self.window)
        self.updateImages(imageData)
