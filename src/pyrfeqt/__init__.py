# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import random
from typing import Optional, Union
from PySide6 import QtCore, QtWidgets


class FileProxyModel(QtCore.QSortFilterProxyModel):
    """See:

    https://stackoverflow.com/questions/53430989/pyside-qfilesystemmodel-display-show-root-item
    """
    def __init__(
        self,
        index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        self._rootIndex = index
        super(FileProxyModel, self).__init__(parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        sourceIndex = self.sourceModel().index(sourceRow, 0, sourceParent)
        if self._rootIndex.parent() == sourceParent and \
                self._rootIndex != sourceIndex:
            return False
        return super(FileProxyModel, self).filterAcceptsRow(
            sourceRow, sourceParent)


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        current_dir = QtCore.QDir.currentPath()
        parent_dir = os.path.dirname(current_dir)

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(parent_dir)
        self.splitter = QtWidgets.QSplitter()
        self.tree = QtWidgets.QTreeView(self.splitter)
        self.list = QtWidgets.QListView(self.splitter)
        self.proxy = FileProxyModel(
            QtCore.QPersistentModelIndex(
                self.model.index(current_dir)))
        self.proxy.setSourceModel(self.model)
        self.tree.setModel(self.proxy)
        self.tree.setRootIndex(
            self.proxy.mapFromSource(self.model.index(parent_dir)))
        self.list.setModel(self.proxy)
        self.list.setRootIndex(
            self.proxy.mapFromSource(self.model.index(parent_dir)))

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.splitter)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))
