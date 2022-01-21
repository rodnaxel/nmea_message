# -*- coding: utf-8 -*-

import json
from math import comb
import os.path
import sys
from collections import ChainMap

import logging

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import app_rc
from components import OptionBox

import model

__title__ = "Генератор сообщений NMEA-0183"
__version__ = "0.1.0"
__author__ = "Александр Смирнов"    


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        #logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
        logging.StreamHandler()
    ])
logger = logging.getLogger()


class Ui(QMainWindow):

    deviceTypeChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.timer_id = 0
        self.isBlink = False
        self.status = {}

        self.createUI()

        #self.settings = dict(ChainMap(self.portbox_data, self.message_data))
        self.settings = dict(ChainMap(self.portbox_data, self.compassBox.get_param()))

        self.transmitter = model.Transmitter()


        # Connect signal/slots

        self.deviceTypeChanged.connect(self._changeStackIndex)

    def _changeStackIndex(self):
        index = self.stack.currentIndex() + 1
        if index > self.stack.count() - 1:
            index = 0
        print(index, self.stack.count())
        self.stack.setCurrentIndex(index)

    def _center(self):
        """ This method aligned main window related center screen """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def createUI(self):
        self.setWindowTitle("{0} (версия {1})".format(__title__, __version__))
        self.setWindowIcon(QIcon(":/rc/logo.png"))
        self.setMaximumSize(800, 500)
        
        centralWgt = QWidget(self)
        self.setCentralWidget(centralWgt)

        # Create widgets
        self.control = self.createButtons()
        self.deviceType = self.createDeviceType()
        self.portbox = self.createPortbox()

        message_group = QGroupBox("Настройка сообщения", self)
        self.stack = QStackedLayout()

        self.sonarBox = self.createMessageBox()
        self.stack.addWidget(self.sonarBox)

        self.compassBox = OptionBox(fields=( 
            ('id', 'индефикатор', ['HCHDT']),
            ('interval', 'темп, мс', ['100', '500', '1000', '2000']),
            ('heading', 'курс, град.', (0.0, 359.9)),
            ('power', 'питание', ['T', 'N'])
        ))
        self.stack.addWidget(self.compassBox)
    

        term_wgt = self.createTerminal()

        self.createStatusbar()

        # Layouts
        centralLayout = QVBoxLayout(centralWgt)
        centralLayout.addWidget(self.control)
        centralLayout.addWidget(self.deviceType)
        settingsLayout = QHBoxLayout()
        settingsLayout.addWidget(self.portbox)

        message_layout = QHBoxLayout(message_group)
        #message_layout.addWidget(self.messagebox)
        message_layout.addLayout(self.stack)

        settingsLayout.addWidget(message_group)
        centralLayout.addLayout(settingsLayout)
        centralLayout.addWidget(term_wgt)

        self._center()

        self.show()

    def createTerminal(self):
        term_wgt = QWidget()

        self.terminal = terminal_output = QTextEdit()
        terminal_output.setReadOnly(True)

        def _clear():
            self.terminal.clear()

        btn_clear = QPushButton('Очистить')
        btn_clear.setFixedWidth(60)

        btn_clear.clicked.connect(_clear)

        term_layout = QVBoxLayout(term_wgt)
        term_layout.addWidget(self.terminal)
        term_layout.addWidget(btn_clear)

        return term_wgt

    def createButtons(self):
        wgt = QWidget()
        layout = QHBoxLayout(wgt)

        self.buttons = {}
        for (name, key, enabled, action, icon) in (
                ('старт', 'start', True, self._on_start, ':/rc/red-start.png'),
                ('стоп', 'stop',  False, self._on_stop, ':/rc/red-stop.png'),
                ('выход', 'exit', True, self._on_quit, ':/rc/red-quit.png')
        ):
            button = QPushButton(name.capitalize())
            button.setEnabled(enabled)
            button.setFixedSize(80, 25)
            
            if icon: 
                button.setIcon(QIcon(icon))
            
            button.setStyleSheet("text-align: left")
            
            if action:
                button.clicked.connect(action)

            layout.addWidget(button)
            layout.setSpacing(1)

            self.buttons[key] = button
        return wgt

    def createDeviceType(self):
        wgt = QWidget()
        layout = QHBoxLayout(wgt) 

        combo = QComboBox()
        combo.setObjectName("deviceType")
        combo.setFixedWidth(120)
        combo.addItems(("Репитер КФ1", "Репитер НЭЛ"))
        
        layout.addWidget(QLabel("Тип устройства: "))
        layout.addWidget(combo)

        combo.currentTextChanged['QString'].connect(self.deviceTypeChanged)
        
        return wgt

    def createPortbox(self):
        """ Port configuration"""
        wgt = QGroupBox('Настройки порта', self)
        layout = QGridLayout(wgt)

        # Slots
        def _update_data():
            self.portbox_data = {"port": wgt.findChild(QComboBox, "port").currentText(),
                                 "baudrate": int(wgt.findChild(QComboBox, "baudrate").currentText()),
                                 "interval": int(wgt.findChild(QComboBox, "interval").currentText())
                                 }

        def _on_find_ports():
            port = wgt.findChild(QComboBox, "port")
            port.clear()
            port.addItems(model.serial_ports())
            if not port.isEnabled():
                port.setEnabled(True)

        row = 0
        for key, name, items in (
            ('port', 'Порт', available_ports),
            ('baudrate', 'скорость', ['4800', '9600', '19200', '38400', '57600', '115200']),
            ('bytesize', 'биты данных', ['5', '6', '7', '8']),
            ('parity', 'четность', ['N']),
            ('stopbits', 'стоп', ['1', '1.5', '2']),
            ('interval', 'темп, мс', ['100', '500', '1000', '2000'])
        ):
            combo = QComboBox()
            combo.setObjectName(key)
            combo.setFixedWidth(60)

            if items:
                combo.addItems(items)
            else:
                combo.setDisabled(True)

            combo.currentTextChanged['QString'].connect(_update_data)

            layout.addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            layout.addWidget(combo, row, 1)
            row += 1

        # Button re-find available port
        btnRescan = QPushButton("Обновить")
        btnRescan.setFixedWidth(60)
        layout.addWidget(btnRescan, 0, 2)

        # Connect signal/slot
        btnRescan.clicked.connect(_on_find_ports)

        _update_data()

        return wgt

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

    def createStatusbar(self):
        '''
        for (key, text) in (
                ['tx', 'сообщений'],
        ):
            wgt = QLabel(' {}: {}'.format(text, 0))
            wgt.setFixedWidth(90)
            stretch = 2 if key == 'er' else 0
            self.statusBar().addPermanentWidget(wgt, stretch)
            self.status[key] = wgt
        '''
        pix = QLabel()
        self.statusBar().addPermanentWidget(pix)
        self.status['pixmap'] = pix
        self.updatePixmap('noconnect')

    def _on_start(self):
        self._lock(True)

        stg = self.read_settings()[0]
        self.transmitter.configure(stg)

        interval_ms = int(self.message_data['interval'])
        self.timer_id = self.startTimer(interval_ms, timerType=QtCore.Qt.PreciseTimer)

    def _on_stop(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
            self.timer_id = 0
        self._lock(False)
        self.updatePixmap('idle')

    def _on_quit(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
        QtCore.QCoreApplication.exit(0)

    def closeEvent(self, event):
        self._on_quit()

    def timerEvent(self, event):
        data = self.read_settings()[1]

        message = model.SonarMessage(self.read_settings()[1])
        msg_bytes = message.to_bytes()
        self.transmitter.send(msg_bytes)

        msg_ascii = message.to_ascii()
        self.terminal.append(msg_ascii)

        self.blinkPixmap()

    def _lock(self, is_lock):
        self.portbox.setDisabled(is_lock)
        self.buttons['start'].setDisabled(is_lock)
        self.buttons['stop'].setEnabled(is_lock)

    def read_settings(self):
        return self.portbox_data, self.message_data

    def blinkPixmap(self):
        if self.isBlink:
            self.updatePixmap('tx')
            self.isBlink = False
        else:
            self.updatePixmap('rx')
            self.isBlink = True

    def updatePixmap(self, state=None):
        if not state:
            state = "noconnect"
        pixmaps = {
            'noconnect': {'ico': ":/rc/network-offline.png", 'description': 'нет подключения'},
            'idle': {'ico': ":/rc/network-idle.png", 'description': 'ожидание'},
            'rx': {'ico': ":/rc/network-receive.png", 'description': 'прием'},
            'tx': {'ico': ":/rc/network-transmit.png", 'description': 'передача'},
            'error': {'ico': ":/rc/network-error.png", 'description': 'ошибка'}
        }
        self.status['pixmap'].setPixmap(QPixmap(pixmaps[state]['ico']))
        self.status['pixmap'].setToolTip(pixmaps[state]['description'])

    def updateStatus(self, key, value):
        self.status[key].setText(' {}: {}'.format('отп', value))


class UserialMainWindow(Ui):
    pass


if __name__ == '__main__':
    available_ports = model.serial_ports()

    app = QApplication(sys.argv)

    # Add icon in the taskbar (only windows))
    if sys.platform == 'win32':
        import ctypes
        myappid = u'navi-dals.kf1-m.udegausswer.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    ex = UserialMainWindow()


    sys.exit(app.exec_())
