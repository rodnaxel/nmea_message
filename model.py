# -*- coding: utf-8 -*-


import sys
import glob

import serial
import serial.tools.list_ports as tools


def serial_ports():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def find_ports():
    return [info.device for info in tools.comports()]


class Message:
    START = '$'
    END = '\r\n'

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, str(self.__dict__['fields']))
   
    def to_bytes(self):
        return b''.join([char.encode() for char in self._message])

    def to_ascii(self, without_end=True):
        return self._message.rstrip('\r\n') if without_end else self._message

    def checksum(self, data):
        return ',*23'


class SonarMessage(Message):
    def __init__(self, data):
        self.fields = dict.fromkeys(['id',
                                     'field1', 'field2',
                                     'depth', 'depth unit',
                                     'danger', 'danger unit',
                                     'accuracy'], '')

        # Delete unnecessary key from data dictionary
        self._data = {key:data[key] for key in (data.keys() & self.fields.keys())}

        self._create(self._data)

    def _create(self, param):
        data = param.copy()

        print(data['depth'])

        data['depth'] = str(round(data['depth'], 2)).zfill(6)
        data['danger'] = str(round(data['danger'], 2)).zfill(2)
        data['depth unit'] = 'M'
        data['danger unit'] = 'M'

        self.fields.update(data)

        self._message = self.START + ','.join(self.fields.values()) + self.checksum(data) + self.END

class CompassMessage(Message):
    def __init__(self, data):
        self.fields = dict.fromkeys(
            ('id','heading', 'power')
        )

        self._data = {key:data[key] for key in (data.keys() & self.fields.keys())}

        self._create(self._data)

    def _create(self, param):
        data = param.copy()

        data['heading'] = str(round(data['heading'], 1)).zfill(5)

        self.fields.update(data)

        self._message = self.START + ','.join(self.fields.values()) + self.checksum(data) + self.END



class Transmitter:
    def configure(self, settings):
        self._settings = settings

    def send(self, message: bytes):
        with serial.Serial(port=self._settings['port'],
                           baudrate=self._settings['baudrate'],
                           timeout=0.1) as serobj:
            serobj.write(message)

