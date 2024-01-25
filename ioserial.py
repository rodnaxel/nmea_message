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


class NmeaDriver(object):
    is_running: bool
    serial_port: serial.Serial

    def __init__(self):
        self.is_running = False
        self.serial_port = None

    def open(self, settings: dict) -> None:
        self.serial_port = serial.Serial(**settings)

    def close(self):
        self.serial_port.close()

    def recieve(self) -> None:
        return None  # TODO: stub
        while self.is_running:
            if self.serial_port.in_waiting > 0:
                raw_message = self.serial_port.readline().decode('utf-8')
        if self.serial_port:
            self.serial_port.close()

    def send(self, message: str) -> int:
        return self.serial_port.write(message.encode('utf-8'))
