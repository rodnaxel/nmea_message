from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


compass_fields = ( 
    ('id', 'индефикатор', ['HCHDT']),
    ('interval', 'темп, мс', ['100', '500', '1000', '2000']),
    ('heading', 'курс, град.', (0.0, 359.9)),
    ('power', 'питание', ['T', 'N'])
)

sonar_fields = (
    ('id', 'индефикатор', ['SDDBT']),
    ('interval', 'темп, мс', ['100', '500', '1000', '2000']),
    ('depth', 'глубина, М', (0, 9999.9)),
    ('danger', 'Оп. глубина, М', (0, 99)),
    ('accuracy', 'Исправность', ('V', 'A'))
)

class OptionBox(QWidget):
    def __init__(self, fields, parent=None):
        super().__init__(parent)

        self.fields = fields

        self.create_widget() 

    def create_widget(self):
        self.layout = QGridLayout(self)

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

            self.layout.addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            self.layout.addWidget(w, row, 1)
            row += 1

    def get_param(self): 
        return {
            'id': self.findChild(QComboBox, "id").currentText(),
            'interval': self.findChild(QComboBox, "interval").currentText(),
            'heading': round(self.findChild(QDoubleSpinBox, "heading").value(), 1),
            'power': self.findChild(QComboBox, "power").currentText()
        }


def createMessageBox(self):
        """ Create message configuration"""
        wgt = QWidget()
        layout = QGridLayout(wgt)

        # Slots
        def _update_data():
            self.message_data = {
                'id': wgt.findChild(QComboBox, "id").currentText(),

                'interval': wgt.findChild(QComboBox, "interval").currentText(),
                'depth': round(wgt.findChild(QDoubleSpinBox, "depth").value(), 2),
                'danger': wgt.findChild(QSpinBox, "danger").value(),
                'accuracy': wgt.findChild(QComboBox, "accuracy").currentText()
            }

        row = 0
        for key, name, items in (
            ('id', 'индефикатор', ['SDDBT']),
            ('interval', 'темп, мс', ['100', '500', '1000', '2000']),
            ('depth', 'глубина, М', (0, 9999.9)),
            ('danger', 'Оп. глубина, М', (0, 99)),
            ('accuracy', 'Исправность', ('V', 'A'))
        ):

            if key in ('id', 'interval', 'accuracy'):
                w = QComboBox()
                w.setObjectName(key)
                w.setFixedWidth(60)
                w.addItems(items)
                w.currentTextChanged['QString'].connect(_update_data)
            else:
                if key in ['depth']:
                    w = QDoubleSpinBox()
                    w.setDecimals(1)
                    w.setSingleStep(0.1)
                else:
                    w = QSpinBox()
                    w.setSingleStep(1)
                w.setObjectName(key)
                w.setRange(*items)
                w.setFixedWidth(60)
                w.valueChanged.connect(_update_data)

            layout.addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            layout.addWidget(w, row, 1)
            row += 1

        _update_data()

        return wgt