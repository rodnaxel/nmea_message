from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget


class OptionBox(QWidget):
    def __init__(self, fields: (list, tuple), parent=None):
        super().__init__(parent)

        self._fields = fields
        self._create_widget()

    def _create_widget(self):
        self.setLayout(QGridLayout(self))

        row = 0 
        for key, name, items in self._fields:
            try:
                if isinstance(items[0], str):
                    w = self._create_combobox(items)
                elif isinstance(items[0], float):
                    w = self._create_double_spinbox(items)
                else:
                    w = self._create_spin_box(items)
            except TypeError as e:
                pass

            w.setObjectName(key)
            w.setFixedWidth(60)

            self.layout().addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            self.layout().addWidget(w, row, 1)
            
            row += 1

        # Add empty space to widget
        self.layout().setRowStretch(self.layout().rowCount(), 2)

    def _create_spin_box(self, items):
        w = QSpinBox()
        w.setSingleStep(1)
        w.setRange(*items)
        return w

    def _create_double_spinbox(self, items):
        w = QDoubleSpinBox()
        w.setDecimals(1)
        w.setSingleStep(0.1)
        w.setRange(*items)
        return w

    def _create_combobox(self, items):
        w = QComboBox()
        w.addItems(items)
        return w

    def update_params(self):
        self.params = {} 
        for child in self.children():
            if hasattr(child, "currentText"):
                self.params[child.objectName()] = child.currentText()
            elif hasattr(child, "value"):
                self.params[child.objectName()] = child.value()

    def get_param(self):
        self.update_params()
        return self.params


class Terminal(QWidget):
    def __init__(self, parent: QWidget | None ) -> None:
        super().__init__(parent)
        self._createUi()

    def append(self, value: str):
        print(f"append {value}")

    def clear(self):
        print(f"on clear")

    def _createUi(self):
        self.listview = QListView()
        self.listview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listview.setSelectionMode(QAbstractItemView.NoSelection)
        self.listview.setFocusPolicy(QtCore.Qt.NoFocus)

        btn = QPushButton('Очистить')
        btn.setFixedWidth(60)
        btn.clicked.connect(self.clear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.listview)
        layout.addWidget(btn)

    