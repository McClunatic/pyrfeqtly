# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT

import pathlib
from typing import Optional
from PySide6 import QtCore, QtWidgets


class PlotOptionsGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(PlotOptionsGroupBox, self).__init__(title=title, parent=parent)

        self.maxi = 720
        self.ranges = [[0, self.maxi]] * 3
        self.multimodes = ['Multi-line', 'Sum', 'Average']
        self.sliders = []
        self.spinboxes = []
        self.radios = []

        # Create QSlider and QSpinBox widgets
        for idx, (mini, maxi) in enumerate(self.ranges):
            sliders = []
            spinboxes = []

            loBound = self.maxi * idx // 3
            upBound = self.maxi * (idx + 1) // 3
            for bound in (loBound, upBound):
                slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
                slider.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
                slider.setSingleStep(1)
                slider.setMinimum(mini)
                slider.setMaximum(maxi)
                slider.setValue(bound)

                spinbox = QtWidgets.QSpinBox()
                spinbox.setSingleStep(1)
                spinbox.setMinimum(mini)
                spinbox.setMaximum(maxi)
                spinbox.setValue(bound)

                slider.sliderMoved.connect(spinbox.setValue)
                spinbox.valueChanged.connect(slider.setValue)

                sliders.append(slider)
                spinboxes.append(spinbox)

            self.sliders.append(sliders)
            self.spinboxes.append(spinboxes)

        # Create multi-source radio button options
        radioWidget = QtWidgets.QWidget()
        radioLayout = QtWidgets.QHBoxLayout()
        for mode in self.multimodes:
            radio = QtWidgets.QRadioButton(self.tr(mode))
            self.radios.append(radio)

            radioLayout.addWidget(radio)

        self.radios[0].setChecked(True)
        radioWidget.setLayout(radioLayout)

        # Create layout
        layout = QtWidgets.QGridLayout()
        layout.setColumnMinimumWidth(3, 8)
        layout.setColumnMinimumWidth(1, 80)
        layout.setColumnMinimumWidth(4, 80)
        for row in range(3):
            layout.addWidget(self.sliders[row][0], row, 0)
            layout.addWidget(self.spinboxes[row][0], row, 1)
            layout.addWidget(self.sliders[row][1], row, 3)
            layout.addWidget(self.spinboxes[row][1], row, 4)

        layout.addWidget(radioWidget, 3, 0, 1, 5)
        self.setLayout(layout)


class DataSourcesGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(DataSourcesGroupBox, self).__init__(title=title, parent=parent)

        demo_paths = [
            str(pathlib.Path.cwd()),
            str(pathlib.Path.cwd().parent)
        ]
        self.listModel = QtCore.QStringListModel(demo_paths)
        self.treeModel = QtWidgets.QFileSystemModel()

        self.listView = QtWidgets.QListView()
        self.listView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listView.setModel(self.listModel)

        self.listView.selectionModel().selectionChanged.connect(
            self.updateTreeView)

        self.treeView = QtWidgets.QTreeView()
        self.treeView.setModel(self.treeModel)
        policy = self.treeView.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.treeView.setSizePolicy(policy)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.listView)
        layout.addWidget(self.treeView)
        self.setLayout(layout)

    @QtCore.Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def updateTreeView(self, selected, deselected):
        if self.listView.selectionModel().hasSelection():
            indexes = self.listView.selectionModel().selectedIndexes()
            rootPath = QtCore.QDir.fromNativeSeparators(
                self.listModel.data(indexes[0]))
            self.treeModel.setRootPath(rootPath)
            self.treeView.setRootIndex(self.treeModel.index(rootPath))
            self.treeView.show()
        else:
            self.treeView.hide()
