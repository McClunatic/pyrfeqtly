# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the data sources groupbox class."""

import pathlib
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class DataSourcesGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(DataSourcesGroupBox, self).__init__(title=title, parent=parent)

        self.listModel = QtGui.QStandardItemModel()
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
        if not self.listModel.findItems(source):
            item = QtGui.QStandardItem(source)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.listModel.appendRow(item)

    @QtCore.Slot()
    def removeSources(self):
        indexes = self.listView.selectionModel().selectedIndexes()
        for index in indexes[::-1]:
            self.listModel.removeRow(index.row())
