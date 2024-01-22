import operator
from functools import reduce

import serial
from serial.tools import list_ports as tools


def checksum(message):
    return reduce(operator.xor, map(ord, message), 0)


def find_ports():
    return [info.device for info in tools.comports()]


class SerialPort:
    def configure(self, settings):
        self._settings = settings

    def send(self, message: bytes):
        with serial.Serial(port=self._settings['port'],
                           baudrate=self._settings['baudrate'],
                           timeout=0.1) as serobj:
            serobj.write(message)