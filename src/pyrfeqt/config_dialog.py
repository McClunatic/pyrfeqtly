# SPDX-FileCopyrightText: 2024-present Brian McClune <bpmcclune@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Defines the configuration dialog class."""

from typing import Optional

from PySide6 import QtCore, QtWidgets

from .data_sources_groupbox import DataSourcesGroupBox
from .plot_options_groupbox import PlotOptionsGroupBox


class DataOptionsGroupBox(QtWidgets.QGroupBox):
    def __init__(
        self,
        title: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Constructor."""
        super(DataOptionsGroupBox, self).__init__(title=title, parent=parent)

        layout = QtWidgets.QFormLayout()

        self.binWidthBox = QtWidgets.QDoubleSpinBox()
        self.binWidthBox.setKeyboardTracking(False)
        self.binWidthBox.setRange(1e-6, 1e6)
        self.sampleSizeBox = QtWidgets.QSpinBox()
        self.sampleSizeBox.setKeyboardTracking(False)
        self.sampleSizeBox.setRange(2 ** 0, 2 ** 16)
        self.historySizeBox = QtWidgets.QSpinBox()
        self.historySizeBox.setKeyboardTracking(False)
        self.historySizeBox.setRange(2 ** 0, 2 ** 16)

        layout.addRow('sample bin width', self.binWidthBox)
        layout.addRow('sample size', self.sampleSizeBox)
        layout.addRow('max history size', self.historySizeBox)

        self.setLayout(layout)

    def applySettings(self, group: str = 'default'):
        settings = QtCore.QSettings()
        binWidth = settings.value(f'{group}/data/binWidth', type=float)
        sampleSize = settings.value(f'{group}/data/sampleSize', type=int)
        historySize = settings.value(f'{group}/data/historySize', type=int)

        self.binWidthBox.setValue(binWidth)
        self.sampleSizeBox.setValue(sampleSize)
        self.historySizeBox.setValue(historySize)

    def writeSettings(self, group: str):
        settings = QtCore.QSettings()
        settings.beginGroup(f'{group}/data')
        settings.setValue('binWidth', self.binWidthBox.value())
        settings.setValue('historySize', self.historySizeBox.value())
        settings.setValue('sampleSize', self.sampleSizeBox.value())
        settings.endGroup()

    def setReadOnly(self, ro: bool):
        self.binWidthBox.setReadOnly(ro)
        self.sampleSizeBox.setReadOnly(ro)
        self.historySizeBox.setReadOnly(ro)


class ConfigDialog(QtWidgets.QDialog):

    def __init__(
        self,
        title: str,
        group: str,
        mode: str,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr(title))
        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QGridLayout()

        self.group = group
        self.mode = mode
        self.plotOptions = []

        # Build the first row
        settings = QtCore.QSettings()
        settings.beginGroup(group)
        for idx, pos in enumerate(('left', 'center', 'right')):
            xRange = settings.value(
                f'plotOptions/{pos}/xRange', type=list)
            windowSize = settings.value(
                f'plotOptions/{pos}/windowSize', type=int)
            opts = PlotOptionsGroupBox(
                title=self.tr(f'Plot options ({pos})'),
                pos=pos,
                xRange=[int(lim) for lim in xRange],
                windowSize=windowSize)
            formLayout.addWidget(opts, 0, idx)
            self.plotOptions.append(opts)

        settings.endGroup()

        # Build the second row
        self.dataOptionsBox = DataOptionsGroupBox('Data options')
        formLayout.addWidget(self.dataOptionsBox, 1, 0)
        self.dataSourcesBox = DataSourcesGroupBox(
            'Data sources', horizontal=True)
        formLayout.addWidget(self.dataSourcesBox, 1, 1, 1, 2)

        # Build the button box
        buttonLayout = QtWidgets.QHBoxLayout()
        self.selectComboBox = None
        if mode in ('load', 'save', 'delete'):
            label = QtWidgets.QLabel('Current configuration:')
            self.selectComboBox = QtWidgets.QComboBox()
            self.selectComboBox.setEditable(mode == 'save')
            self.selectComboBox.addItems(settings.childGroups())
            self.selectComboBox.setCurrentText('default')
            label.setBuddy(self.selectComboBox)
            buttonLayout.addWidget(label)
            buttonLayout.addWidget(self.selectComboBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonLayout.addWidget(self.buttonBox, stretch=1)

        # Connect signals and slots
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        if self.selectComboBox and mode in ('load', 'delete'):
            self.selectComboBox.currentTextChanged.connect(
                self.onCurrentTextChanged)
        for opts in self.plotOptions:
            self.dataSourcesBox.sourceInserted.connect(opts.insertSource)
            self.dataSourcesBox.sourceRemoved.connect(opts.removeSource)

        # Apply editability settings
        if mode != 'edit':
            self.dataOptionsBox.setReadOnly(True)
            self.dataSourcesBox.setReadOnly(True)
            for opts in self.plotOptions:
                opts.setReadOnly(True)

        layout.addLayout(formLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def applySettings(self, group: Optional[str] = None):
        group = group if group is not None else self.group
        for opts in self.plotOptions:
            opts.applySettings(group)
        self.dataOptionsBox.applySettings(group)
        self.dataSourcesBox.applySettings(group)

    def writeSettings(self, group: Optional[str] = None):
        group = group if group is not None else self.group
        group = group if group is not None else self.group
        for opts in self.plotOptions:
            opts.writeSettings(group)
        self.dataOptionsBox.writeSettings(group)
        self.dataSourcesBox.writeSettings(group)

    @QtCore.Slot(str)
    def onCurrentTextChanged(self, text: str):
        self.group = text
        self.applySettings(text)

    def currentText(self):
        if self.selectComboBox:
            return self.selectComboBox.currentText()
        return self.group

    def accept(self):
        if self.mode in ('edit', 'load'):
            super().accept()
            return
        elif self.mode == 'save':
            self.acceptSave()
        else:
            self.acceptDelete()

    def acceptSave(self):
        settings = QtCore.QSettings()
        name = self.selectComboBox.currentText()
        if name in settings.childGroups():
            text = f'Configuration {name!r} already exists! Overwrite it?'
            ans = QtWidgets.QMessageBox.question(self, 'Confirm Save', text)
            if ans == QtWidgets.QMessageBox.StandardButton.Yes:
                super().accept()
        else:
            super().accept()

    def acceptDelete(self):
        name = self.selectComboBox.currentText()
        text = f'Configuration {name!r} will be deleted! Continue?'
        ans = QtWidgets.QMessageBox.question(self, 'Confirm Delete', text)
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            super().accept()

    def reject(self):
        text = 'Are you sure you want to cancel?'
        ans = QtWidgets.QMessageBox.question(self, 'Confirm Cancel', text)
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            super().reject()
