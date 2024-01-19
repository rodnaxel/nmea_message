# -*- coding: utf-8 -*-

import logging
import os.path
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ui.components import OptionBox, Option
from ui import app_rc

import ioserial
from protocols import CompassMessage, SonarMessage, HMRDorient
from message_desc import messages

__title__ = "NMEA-0183"
__version__ = "1.0.0"
__author__ = "Александр Смирнов"

ROOT = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        # logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
        logging.StreamHandler()
    ])
logger = logging.getLogger()

pixmaps = {
    'noconnect': {'ico': ":/rc/network-offline.png", 'description': 'нет подключения'},
    'idle': {'ico': ":/rc/network-idle.png", 'description': 'ожидание'},
    'rx': {'ico': ":/rc/network-receive.png", 'description': 'прием'},
    'tx': {'ico': ":/rc/network-transmit.png", 'description': 'передача'},
    'error': {'ico': ":/rc/network-error.png", 'description': 'ошибка'}
}


class Ui(QMainWindow):

    def __init__(self):
        super().__init__()

        self.timer_id = 0
        self.isBlink = False
        self.status = {}

        # select type message
        self.message_names = ["compass", "sonar", "sensor"]
        self.mode = 0

        self.transceiver = ioserial.SerialPort()

        self.createUI()

        # Connect signals/slots
        self.deviceType.currentIndexChanged['int'].connect(self.on_change_device)

    def createUI(self):
        self.setWindowTitle("{0} (версия {1})".format(__title__, __version__))
        self.setWindowIcon(QIcon(":/rc/logo.png"))
        self.setMaximumSize(800, 500)

        centralWgt = QWidget(self)
        self.setCentralWidget(centralWgt)

        # Create widgets
        self.deviceType = Option(
            parent=None, 
            title="Тип устройства",
            items=(messages[name]["desc"] for name in self.message_names)
        )

        self.transmitDirection = Option(
            parent=None,
            title="Режим работы",
            items=("Передача", "Прием")
        )
        self.portbox = self.createPortbox()
        self.control = self.createButtons()

        # Widget params of message
        message_group = QGroupBox("Параметры сообщения:", self)
        self.stack = QStackedLayout()
        for key in self.message_names:
            box = OptionBox(fields=messages[key]["fields"])
            self.stack.addWidget(box)
        self.stack.setCurrentIndex(0)

        le = QLineEdit()

        terminal = self.createTerminal()      

        self.createStatusbar()
        
        # Layouts
        centralLayout = QVBoxLayout(centralWgt)
        centralLayout.addWidget(self.deviceType)
        centralLayout.addWidget(self.transmitDirection)
        settingsLayout = QHBoxLayout()
        settingsLayout.addWidget(self.portbox)

        message_layout = QHBoxLayout(message_group)
        message_layout.addLayout(self.stack)
        message_layout.setContentsMargins(0, 0, 0, 0)

        settingsLayout.addWidget(message_group)
        centralLayout.addLayout(settingsLayout)
        centralLayout.addWidget(le)
        centralLayout.addWidget(terminal)
        centralLayout.addWidget(self.control)

        self._center()

        self.show()

    def createTerminal(self):   
        self.terminal = QListView(parent=None)
        self.terminal.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.terminal.setSelectionMode(QAbstractItemView.NoSelection)
        self.terminal.setFocusPolicy(QtCore.Qt.NoFocus)

        model = QtCore.QStringListModel()
        self.terminal.setModel(model)
        
        def _on_clear():
            model.setStringList(tuple())
            
        def _on_append(item: str):
            new_item = item
            model.insertRow(model.rowCount())
            index = model.index(model.rowCount()-1, 0)
            model.setData(index, new_item)
            self.terminal.scrollTo(index) 

        btn_clear = QPushButton('Очистить')
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(_on_clear)

        wgt = QWidget()
        layout = QVBoxLayout(wgt)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.terminal)
        layout.addWidget(btn_clear)

        self._terminal_on_append = _on_append

        return wgt

    def createButtons(self):
        wgt = QWidget()
        layout = QHBoxLayout(wgt)
        layout.setContentsMargins(0,0,0,0)

        self.buttons = {}
        for (name, key, enabled, action, icon) in (
                ('старт', 'start', True, self._on_start, ':/rc/red-start.png'),
                ('стоп', 'stop', False, self._on_stop, ':/rc/red-stop.png'),
                ('выход', 'exit', True, self._on_quit, ':/rc/red-quit.png')
        ):
            button = QPushButton(name.capitalize())
            button.setEnabled(enabled)
            button.setFixedSize(80, 25)
            button.setIcon(QIcon(icon))
            button.setStyleSheet("text-align: center")

            layout.addWidget(button)
            layout.setSpacing(1)
            if key == 'stop':
                layout.addStretch(2)

            button.clicked.connect(action)
            self.buttons[key] = button

        return wgt

    def createPortbox(self):
        """ Port configuration"""
        wgt = QGroupBox('Настройки порта', self)
        layout = QGridLayout(wgt)

        # Slots
        def _on_update_settings():
            self.portbox_data = {
                "port": wgt.findChild(QComboBox, "port").currentText(),
                "baudrate": int(wgt.findChild(QComboBox, "baudrate").currentText()),
                "interval": int(wgt.findChild(QComboBox, "interval").currentText())
            }

        def _on_find_ports():
            port = wgt.findChild(QComboBox, "port")
            port.clear()
            port.addItems(ioserial.find_ports())
            if not port.isEnabled():
                port.setEnabled(True)

        row = 0
        for key, name, items in (
                ('port', 'Порт', available_ports),
                ('baudrate', 'скорость', ['4800', '9600', '19200', '38400', '57600', '115200']),
                ('bytesize', 'биты данных', ['8']),
                ('parity', 'четность', ['N']),
                ('stopbits', 'стоп', ['1', '1.5', '2']),
                ('interval', 'темп, мс', ['1000'])
        ):
            combo = QComboBox()
            combo.setObjectName(key)
            combo.setFixedWidth(60)

            if items:
                combo.addItems(items)
            else:
                combo.setDisabled(True)

            combo.currentTextChanged['QString'].connect(_on_update_settings)

            layout.addWidget(QLabel(f"{name.capitalize()}:"), row, 0)
            layout.addWidget(combo, row, 1)
            row += 1

        # Button re-find available port
        btnRescan = QPushButton("Обновить")
        btnRescan.setFixedWidth(60)
        layout.addWidget(btnRescan, 0, 2)

        # Connect signal/slot
        btnRescan.clicked.connect(_on_find_ports)

        _on_update_settings()

        return wgt


    def createStatusbar(self):
        counter = QLabel()
        self.statusBar().addPermanentWidget(counter)
        self.status['counter'] = counter

        pix = QLabel()
        self.statusBar().addPermanentWidget(pix)
        self.status['pixmap'] = pix
        self.updatePixmap('noconnect')

    def _center(self):
        """ This method aligned main window related center screen """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def _on_start(self):
        self._lock(True)

        stg = self.get_port_settings()
        self.transceiver.configure(stg)

        self.message_counter = 0

        interval_ms = int(stg['interval'])
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
        data = self.get_message_settings()

        if self.mode == 0:
            message = CompassMessage(data)
        elif self.mode == 1:
            message = SonarMessage(data)
        elif self.mode == 2:
            message = HMRDorient(data)

        # send message to serial
        msg_bytes = message.to_bytes()
        self.transceiver.send(msg_bytes)

        # show message to terminal
        msg_ascii = message.to_ascii()
        self._terminal_on_append(msg_ascii)

        # update status
        self.blinkPixmap()

        self.message_counter += 1
        self.updateStatus("counter", self.message_counter)

    def _lock(self, is_lock):
        self.portbox.setDisabled(is_lock)
        self.deviceType.setDisabled(is_lock)
        self.transmitDirection.setDisabled(is_lock)
        self.buttons['start'].setDisabled(is_lock)
        self.buttons['stop'].setEnabled(is_lock)

    def blinkPixmap(self):
        if self.isBlink:
            self.updatePixmap('tx')
            self.isBlink = False
        else:
            self.updatePixmap('rx')
            self.isBlink = True

    def updatePixmap(self, state="noconnect"):
        self.status['pixmap'].setPixmap(QPixmap(pixmaps[state]['ico']))
        self.status['pixmap'].setToolTip(pixmaps[state]['description'])

    def updateStatus(self, key, value):
        self.status[key].setText(' {}: {}'.format('отправлено', value))

    def on_change_device(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.mode = index

    def get_port_settings(self):
        return self.portbox_data

    def get_message_settings(self):
        return self.stack.currentWidget().get_param()


class UserialMainWindow(Ui):
    pass


if __name__ == '__main__':
    available_ports = ioserial.find_ports()

    app = QApplication(sys.argv)

    # Add icon in the taskbar (only windows))
    if sys.platform == 'win32':
        import ctypes

        myappid = u'navi-dals.kf1-m.udegausswer.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    ex = UserialMainWindow()

    sys.exit(app.exec_())
