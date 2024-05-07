# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import random
from typing import Optional, Union
from PySide6 import QtCore, QtWidgets, QtGui

from . import widgets


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


class MyWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))

        self.createFileActions()
        self.createEditActions()
        self.createHelpActions()

        # Create settings sliders
        self.sliderBox = widgets.PlotSettingsGroupBox('Plot options', self)

        # Create tree views
        self.list = ['One', 'Two', 'Three']
        self.listBox = QtWidgets.QGroupBox()
        self.listModel = QtCore.QStringListModel()
        self.listModel.setStringList(self.list)
        self.listView = QtWidgets.QListView()
        self.listView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listView.setModel(self.listModel)
        self.listLayout = QtWidgets.QHBoxLayout()
        self.listLayout.addWidget(self.listView)
        self.listBox.setLayout(self.listLayout)

        self.createHelloWidgets()
        self.createDirWidgets()
        self.buildLayout()

    def createFileActions(self):
        self.newAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentNew),
            self.tr('&New'),
            self)
        self.newAct.setShortcut(QtGui.QKeySequence.StandardKey.New)
        self.newAct.setStatusTip(self.tr('Create a new file'))
        # TODO: connect self.newAct to function

        self.openAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentOpen),
            self.tr('&Open...'),
            self)
        self.openAct.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.openAct.setStatusTip(self.tr('Open an existing file'))
        # TODO: connect self.openAct to function

        self.saveAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentSave),
            self.tr('&Save'),
            self)
        self.saveAct.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.saveAct.setStatusTip(self.tr('Save the file to disk'))
        # TODO: connect self.saveAct to function

        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)

    def createEditActions(self):
        self.editAct = QtGui.QAction(
            self.tr('&Edit'), self)
        self.editAct.setStatusTip(self.tr('Edit current configuration'))
        # TODO: connect self.editAct to function

        self.prefAct = QtGui.QAction(
            self.tr('&Preferences...'), self)
        self.prefAct.setShortcut(QtGui.QKeySequence.StandardKey.Preferences)
        self.openAct.setStatusTip(self.tr('Edit preferences'))
        # TODO: connect self.prefAct to function

        self.editMenu.addAction(self.editAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.prefAct)

    def createHelpActions(self):
        self.aboutAct = QtGui.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.HelpAbout),
            self.tr('&About'),
            self)
        self.newAct.setStatusTip(self.tr('Show about'))
        # TODO: connect self.aboutAct to function

        self.helpMenu.addAction(self.aboutAct)

    def createHelloWidgets(self):
        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]
        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        self.button.clicked.connect(self.magic)

    def createDirWidgets(self):
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

    def buildLayout(self):
        sideLayout = QtWidgets.QVBoxLayout()
        sideLayout.addWidget(self.sliderBox)
        sideLayout.addWidget(self.listBox)

        bigLayout = QtWidgets.QVBoxLayout()
        bigLayout.addWidget(self.splitter)
        bigLayout.addWidget(self.text)
        bigLayout.addWidget(self.button)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(sideLayout)
        self.layout.addLayout(bigLayout, stretch=1)
        self.widget.setLayout(self.layout)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))
