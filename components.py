from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class OptionBox(QWidget):
    def __init__(self, fields, parent=None):
        super().__init__(parent)

        self.fields = fields
        self.setLayout(QGridLayout(self))

        self.create_widget()

    def create_widget(self):
        row = 0 
        for key, name, items in self.fields:
            if isinstance(items, (list, tuple)):
                if isinstance(items[0], str):
                    w = QComboBox()
                    w.setObjectName(key)
                    w.setFixedWidth(60)
                    w.addItems(items)
                elif isinstance(items[0], float):
                    w = QDoubleSpinBox()
                    w.setDecimals(1)
                    w.setSingleStep(0.1)
                    w.setRange(*items)  
                else:
                    w = QSpinBox()
                    w.setSingleStep(1)
                    w.setRange(*items)

                w.setObjectName(key)
                w.setFixedWidth(60)
            else:
                raise ValueError()

            self.layout().addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            self.layout().addWidget(w, row, 1)
            
            row += 1

        # Add emty space to widget
        self.layout().setRowStretch(self.layout().rowCount(), 2)

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
