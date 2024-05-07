# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import sys
from PySide6 import QtWidgets
from pyrfeqt import MainWindow

app = QtWidgets.QApplication([])

widget = MainWindow()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())
