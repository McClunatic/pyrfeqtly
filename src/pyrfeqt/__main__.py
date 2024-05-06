# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import sys
from PySide6 import QtWidgets
from pyrfeqt import MyWidget

app = QtWidgets.QApplication([])

widget = MyWidget()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())
