# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import sys
import traceback
from PySide6 import QtWidgets
from pyrfeqt import MainWindow


def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = excepthook

app = QtWidgets.QApplication([])

widget = MainWindow()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())
