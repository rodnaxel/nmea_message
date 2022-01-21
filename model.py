# -*- coding: utf-8 -*-


from functools import reduce
import operator
import sys
import glob

import serial
import serial.tools.list_ports as tools


def find_ports():
    return [info.device for info in tools.comports()]

def checksum(message):
    return reduce(operator.xor, map(ord, message), 0)


class NMEASentences(object):
    START = '$'
    END = '\r\n'

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, str(self.__dict__['fields']))

    def _create_message(self):
        param_strings = ','.join(self.fields.values())
        self._message = self.START + param_strings + "*" + "{:02X}".format(checksum(param_strings)) + self.END
   
    def to_bytes(self):
        return b''.join([char.encode() for char in self._message])

    def to_ascii(self, without_end=True):
        return self._message.rstrip('\r\n') if without_end else self._message


class SonarMessage(NMEASentences):
    def __init__(self, data):
        self.fields = dict.fromkeys(['id',
                                     'field1', 'field2',
                                     'depth', 'depth unit',
                                     'danger', 'danger unit',
                                     'accuracy'], '')

        # Delete unnecessary key from data dictionary
        self._data = {key:data[key] for key in (data.keys() & self.fields.keys())}
        
        # Formatting input data
        self._data['depth'] = str(round(self._data['depth'], 2)).zfill(6)
        self._data['danger'] = str(round(self._data['danger'], 2)).zfill(2)
        self._data['depth unit'] = 'M'
        self._data['danger unit'] = 'M'

        self.fields.update(self._data)

        self._create_message()

class CompassMessage(NMEASentences):
    def __init__(self, data):
        self.fields = dict.fromkeys(
            ('id','heading', 'power')
        )

        # Delete unnecessary key from data dictionary
        self._data = {key:data[key] for key in (data.keys() & self.fields.keys())}

        # Formatting input data
        self.data['heading'] = str(round(self.data['heading'], 1)).zfill(5)
        self.fields.update(data)

        self._create_message()


class Transmitter:
    def configure(self, settings):
        self._settings = settings

    def send(self, message: bytes):
        with serial.Serial(port=self._settings['port'],
                           baudrate=self._settings['baudrate'],
                           timeout=0.1) as serobj:
            serobj.write(message)

