# -*- coding: utf-8 -*-

from ioserial import checksum


class BaseSentence(object):
    def to_bytes(self):
        raise NotImplementedError

    def to_ascii(self):
        raise NotImplementedError


class NMEASentences(BaseSentence):
    START = '$'
    END = '\r\n'

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, str(self.__dict__['fields']))

    def _create_message(self):
        param_strings = ','.join(self.fields.values())
        self._message = self.START + param_strings + "*" + "{:02X}".format(checksum(param_strings)) + self.END

    def to_bytes(self) -> bytes:
        return b''.join([char.encode() for char in self._message])

    def to_ascii(self, without_end=True) -> str:
        return self._message.rstrip('\r\n') if without_end else self._message


class SonarMessage(NMEASentences):
    """ Class described NMEA message from PUI to user/repiter """
    fields = dict.fromkeys(['id',
                            'field1', 'field2',
                            'depth', 'depth unit',
                            'danger', 'danger unit',
                            'accuracy'], '')

    def __init__(self, data: dict):
        # Delete unnecessary key from data dictionary
        necessary_keys = self.fields.keys() & data.keys()
        self._data = {key: data[key] for key in necessary_keys}

        # Formatting input data
        self._data['depth'] = str(round(self._data['depth'], 2)).zfill(6)
        self._data['depth unit'] = 'M'

        self._data['danger'] = str(round(self._data['danger'], 2)).zfill(2)
        self._data['danger unit'] = 'M'

        self.fields.update(self._data)

        self._create_message()


class CompassMessage(NMEASentences):
    """ Class described NMEA message from compass to user/repiter """
    fields = dict.fromkeys(
        ('id', 'heading', 'power')
    )

    def __init__(self, data):
        # Delete unnecessary key from data dictionary
        necessary_keys = self.fields.keys() & data.keys()
        self._data = {key: data[key] for key in necessary_keys}

        # Formatting input data
        self._data['heading'] = str(round(self._data['heading'], 1)).zfill(5)
        self.fields.update(self._data)

        self._create_message()


def kang2dec(kang, signed=True):
    return round(int.from_bytes(kang, byteorder='little', signed=signed) * 359.9 / 65536.0, 3)


def dec2kang(dec, signed=True):
    return (int(dec * 65536.0 / 359.9)).to_bytes(2, byteorder='little', signed=signed)


def gauss2tesla(gauss):
    return round(int.from_bytes(gauss, byteorder='little', signed=True) * 750.0 / 65536.0, 3)


def tesla2gauss(tesla):
    return (int(tesla * 65536.0 / 750.0)).to_bytes(2, byteorder='little', signed=True)


class HMRSentences(BaseSentence):
    SOP1 = bytes.fromhex("0d")
    SOP2 = bytes.fromhex("0a")
    SOP3 = bytes.fromhex("7e")


class HMRDorient(HMRSentences):
    MID = bytes.fromhex("70")
    LENGTH = (18).to_bytes(1, byteorder='little')

    def __init__(self, data: dict):
        self._data = data

    def to_bytes(self):
        data_bytes = [self.SOP1, self.SOP2, self.SOP3, self.MID, self.LENGTH]
        for key, value in self._data.items():
            if key in ['roll', 'pitch']:
                data_bytes.append(dec2kang(value))
            elif key in ['heading']:
                data_bytes.append(dec2kang(value, signed=False))
            elif key in ['magb', 'magc', 'magz']:
                data_bytes.append(tesla2gauss(value))
            else:
                raise ValueError

        return b''.join(data_bytes)

    def to_ascii(self):
        return self.to_bytes().hex(' ')
