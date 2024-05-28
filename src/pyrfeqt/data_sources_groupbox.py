# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the data sources groupbox class."""

import pathlib
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class DataSourcesGroupBox(QtWidgets.QGroupBox):

    sourceInserted = QtCore.Signal(str)
    sourceRemoved = QtCore.Signal(str)
    sourceDataChanged = QtCore.Signal(str)

    def __init__(
        self,
        title: str,
        horizontal: bool = False,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(DataSourcesGroupBox, self).__init__(title=title, parent=parent)

        self.listModel = QtGui.QStandardItemModel()
        self.listModel.rowsInserted.connect(self.onRowsInserted)
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

        layout = (
            QtWidgets.QHBoxLayout() if horizontal else QtWidgets.QVBoxLayout())
        listLayout = QtWidgets.QVBoxLayout()
        listLayout.addWidget(self.listView)
        listLayout.addWidget(self.buttonWidget)
        layout.addLayout(listLayout)
        layout.addWidget(self.treeView, stretch=1)
        self.setLayout(layout)

        # Create data source watcher
        self.watcher = QtCore.QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.sourceDataChanged)

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
            self.watcher.addPath(source)
            self.listModel.appendRow(item)

    @QtCore.Slot()
    def removeSources(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        for index in indexes[::-1]:
            item = self.listModel.itemFromIndex(index)
            self.watcher.removePath(item.text())
            self.listModel.removeRow(index.row())

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def onRowsInserted(self, index, first, last):
        items = [self.listModel.item(row, 0) for row in range(first, last + 1)]
        for item in items:
            self.sourceInserted.emit(item.text())

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def onRowsAboutToBeRemoved(self, index, first, last):
        items = [self.listModel.item(row, 0) for row in range(first, last + 1)]
        for item in items:
            self.sourceRemoved.emit(item.text())

    def applySettings(self, group: str = 'default'):
        self.blockSignals(True)
        settings = QtCore.QSettings()
        paths = settings.value(f'{group}/dataSources/paths', type=list)
        # Loop over sources in reverse order: if not in paths, remove
        for row in range(self.listModel.rowCount() - 1, -1, -1):
            index = self.listModel.index(row, 0)
            item = self.listModel.itemFromIndex(index)
            if item.text() not in paths:
                self.watcher.removePath(item.text())
                self.listModel.removeRow(row)
        # Loop over paths: if not in sources, add
        for source in paths:
            if not self.listModel.findItems(source):
                item = QtGui.QStandardItem(source)
                self.watcher.addPath(source)
                self.listModel.appendRow(item)
        self.blockSignals(False)

    def writeSettings(self, group: str):
        settings = QtCore.QSettings()
        paths = []
        for row in range(self.listModel.rowCount()):
            index = self.listModel.index(row, 0)
            item = self.listModel.itemFromIndex(index)
            paths.append(item.text())
        settings.setValue(f'{group}/dataSources/paths', paths)

    def setReadOnly(self, ro: bool):
        if ro:
            self.listView.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            self.newButton.setEnabled(False)
            self.removeButton.setEnabled(False)
        else:
            self.listView.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.newButton.setEnabled(True)
            self.removeButton.setEnabled(
                self.listView.selectionModel().hasSelection())
