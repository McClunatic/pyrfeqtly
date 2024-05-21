# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""The pyrfeqt package."""

from PySide6 import QtCore, QtWidgets
from .main_window import MainWindow

__all__ = ['MainWindow']

QtWidgets.QApplication.setApplicationName('pyrfeqt')
QtWidgets.QApplication.setOrganizationName('Brian')
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)

# float: default bin width used to bin samples together in time
BIN_WIDTH = 1e0

#: int: default number of samples to retain in memory as history
HISTORY_SIZE = 1000

#: int: default number of samples to display in spectrogram plots
WINDOW_SIZE = 300

#: int: default array size of a single source data sample
SAMPLE_SIZE = 720
