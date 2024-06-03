# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the data sources groupbox class."""

import pathlib
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class DataSourcesGroupBox(QtWidgets.QGroupBox):

    pathsChanged = QtCore.Signal(object)
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

        self.dirValue = QtWidgets.QLabel()
        self.dirValue.setFrameStyle(
            QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Plain)
        self.dirLabel = QtWidgets.QLabel(self.tr("Directory"))
        self.dirLabel.setBuddy(self.dirValue)

        self.listView = QtWidgets.QListView()
        self.listView.setSizeAdjustPolicy(
            QtWidgets.QListView.SizeAdjustPolicy.AdjustToContents)
        self.listView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listView.setModel(self.listModel)
        self.listLabel = QtWidgets.QLabel(self.tr("Source substrings"))
        self.listLabel.setBuddy(self.listView)

        self.listView.selectionModel().selectionChanged.connect(
            self.updateTreeView)

        self.buttonWidget = QtWidgets.QWidget()
        self.dirButton = QtWidgets.QPushButton(self.tr("Set directory"))
        self.dirButton.clicked.connect(self.setDirectory)
        self.newButton = QtWidgets.QPushButton(self.tr("Add source"))
        self.newButton.clicked.connect(self.addSource)
        self.removeButton = QtWidgets.QPushButton(self.tr("Remove source(s)"))
        self.removeButton.clicked.connect(self.removeSources)
        self.removeButton.setEnabled(False)
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.dirButton)
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
        listLayout.addWidget(self.dirLabel)
        listLayout.addWidget(self.dirValue)
        listLayout.addWidget(self.listLabel)
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
    def setDirectory(self):
        source = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("Select data source directory"),
            str(pathlib.Path.cwd()),
            QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if source != '':
            directories = self.watcher.directories()
            if directories:
                self.watcher.removePaths(directories)
            self.watcher.addPath(source)
            self.dirValue.setText(source)
            self.pathsChanged.emit([source])

    @QtCore.Slot()
    def addSource(self):
        ans, accepted = QtWidgets.QInputDialog.getText(
            self,
            self.tr("Select data source directory"),
            self.tr("Source substring:"))
        if ans != '' and accepted:
            item = QtGui.QStandardItem(ans)
            self.listModel.appendRow(item)

    @QtCore.Slot()
    def removeSources(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        for index in indexes[::-1]:
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
        # Update watcher
        directories = self.watcher.directories()
        if directories:
            self.watcher.removePaths(directories)
        paths = settings.value(f'{group}/dataSources/paths', type=list)
        if paths:
            self.watcher.addPaths(paths)

        srcs = settings.value(f'{group}/dataSources/sources', type=list)
        # Loop over model sources in reverse order: if not in srcs, remove
        for row in range(self.listModel.rowCount() - 1, -1, -1):
            index = self.listModel.index(row, 0)
            item = self.listModel.itemFromIndex(index)
            if item.text() not in srcs:
                self.listModel.removeRow(row)
        # Loop over srcs: if not in model sources, add
        for source in srcs:
            if not self.listModel.findItems(source):
                item = QtGui.QStandardItem(source)
                self.listModel.appendRow(item)
        self.blockSignals(False)

    def writeSettings(self, group: str):
        settings = QtCore.QSettings()
        directories = self.watcher.directories()
        settings.setValue(f'{group}/dataSources/paths', directories)
        srcs = []
        for row in range(self.listModel.rowCount()):
            index = self.listModel.index(row, 0)
            item = self.listModel.itemFromIndex(index)
            srcs.append(item.text())
        settings.setValue(f'{group}/dataSources/sources', srcs)

    def setReadOnly(self, ro: bool):
        if ro:
            self.listView.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            self.dirButton.setEnabled(False)
            self.newButton.setEnabled(False)
            self.removeButton.setEnabled(False)
        else:
            self.listView.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.dirButton.setEnabled(True)
            self.newButton.setEnabled(True)
            self.removeButton.setEnabled(
                self.listView.selectionModel().hasSelection())

    def paths(self):
        return self.watcher.directories()

    def sources(self):
        srcs = []
        for row in range(self.listModel.rowCount()):
            index = self.listModel.index(row, 0)
            item = self.listModel.itemFromIndex(index)
            srcs.append(item.text())
        return srcs
