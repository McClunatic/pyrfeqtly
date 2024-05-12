# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT

import time

import numpy as np
import pyqtgraph as pg


class GraphicsLayoutWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None, title=None):
        super().__init__(parent=parent, title=title)

        self.signal_plots = [self.addPlot() for _ in range(3)]
        t = np.linspace(0., 4 * np.pi, 720)
        y = np.sin(t + np.pi * time.time() / 30.)
        self.signal_curves = [plot.plot(t, y) for plot in self.signal_plots]

        self.nextRow()
        self.spectr_plots = [self.addPlot() for _ in range(3)]
        self.spectr_images = []
        for plot in self.spectr_plots:
            m = np.empty((300, 720))
            for dt in range(300):
                m[dt, :] = np.sin(t + np.pi * (time.time() + 0.1 * dt) / 30.)
            self.spectr_images.append(pg.ImageItem(m, colorMap='viridis'))
            plot.addItem(self.spectr_images[-1])
