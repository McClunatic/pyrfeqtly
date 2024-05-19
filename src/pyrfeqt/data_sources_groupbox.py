# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the data sources groupbox class."""

import pathlib
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class DataSourcesGroupBox(QtWidgets.QGroupBox):

    sourceChanged = QtCore.Signal(str, QtCore.Qt.CheckState, bool)

    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(DataSourcesGroupBox, self).__init__(title=title, parent=parent)

        self.listModel = QtGui.QStandardItemModel()
        self.listModel.itemChanged.connect(self.onItemChanged)
        self.listModel.rowsAboutToBeRemoved.connect(
            self.onRowsAboutToBeRemoved)
        self.treeModel = QtWidgets.QFileSystemModel()

        self.listView = QtWidgets.QListView()
        self.listView.setSizeAdjustPolicy(
            QtWidgets.QListView.SizeAdjustPolicy.AdjustToContents)
        self.listView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listView.setModel(self.listModel)

        self.listView.selectionModel().selectionChanged.connect(
            self.updateTreeView)

        self.buttonWidget = QtWidgets.QWidget()
        self.newButton = QtWidgets.QPushButton(self.tr("Add source"))
        self.newButton.clicked.connect(self.addSource)
        self.removeButton = QtWidgets.QPushButton(self.tr("Remove source(s)"))
        self.removeButton.clicked.connect(self.removeSources)
        self.removeButton.setEnabled(False)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.newButton)
        buttonLayout.addWidget(self.removeButton)
        self.buttonWidget.setLayout(buttonLayout)

        self.treeView = QtWidgets.QTreeView()
        self.treeView.setModel(self.treeModel)
        policy = self.treeView.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.treeView.setSizePolicy(policy)
        self.treeView.hide()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.listView)
        layout.addWidget(self.buttonWidget)
        layout.addWidget(self.treeView, stretch=1)
        self.setLayout(layout)

    @QtCore.Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def updateTreeView(self, selected, deselected):
        if self.listView.selectionModel().hasSelection():
            indexes = self.listView.selectionModel().selectedIndexes()
            rootPath = self.listModel.data(indexes[0])
            self.treeModel.setRootPath(rootPath)
            self.treeView.setRootIndex(self.treeModel.index(rootPath))

            self.removeButton.setEnabled(True)
            self.treeView.show()
        else:
            self.removeButton.setEnabled(False)
            self.treeView.hide()

    @QtCore.Slot()
    def addSource(self):
        source = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("Select data source directory"),
            str(pathlib.Path.cwd()),
            QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if source != '' and not self.listModel.findItems(source):
            item = QtGui.QStandardItem(source)
            item.setCheckable(True)
            self.listModel.appendRow(item)
            # Check the item to trigger onItemChanged after appending
            item.setCheckState(QtCore.Qt.CheckState.Checked)

    @QtCore.Slot()
    def removeSources(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        for index in indexes[::-1]:
            # Uncheck the item to trigger onItemChanged before removing
            self.listModel.itemFromIndex(index).setCheckState(
                QtCore.Qt.CheckState.Unchecked)
            self.listModel.removeRow(index.row())

    @QtCore.Slot(QtGui.QStandardItem)
    def onItemChanged(self, item):
        # text, checkState, removed=False
        self.sourceChanged.emit(item.text(), item.checkState(), False)

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def onRowsAboutToBeRemoved(self, index, first, last):
        items = [self.listModel.item(row, 0) for row in range(first, last + 1)]
        for item in items:
            # text, checkState, removed=False
            self.sourceChanged.emit(item.text(), item.checkState(), True)
