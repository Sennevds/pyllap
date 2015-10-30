import time
from .constants import *


class Message(object):
    def __init__(self, device, body):
        self.device = device
        self.body = body
        self.retries = 0
        self.time = time.time()
        self.requires_ack = True

    def is_response(self, message):
        return self == message

    def to_llap(self):
        message = LLAP_START + self.device + self.body
        message = message + (LLAP_FILL * (LLAP_LEN-len(message)))
        return message

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.device == other.device and self.body == other.body


class Ack(Message):
    def __init__(self, device):
        super(Ack, self).__init__(device, 'ACK')
        self.requires_ack = False


class Awake(Message):
    def __init__(self, device):
        super(Awake, self).__init__(device, 'AWAKE')
        self.requires_ack = False


class Battery(Message):
    def __init__(self, device, voltage=None):
        body = 'BATT'
        self.voltage = voltage
        if voltage:
            body = body+voltage
        super(Battery, self).__init__(device, body)
        self.requires_ack = False

    def is_response(self, message):
        if self.device != message.device:
            return False

        return isinstance(message, self.__class__)


class BatteryLow(Message):
    def __init__(self, device):
        super(BatteryLow, self).__init__(device, 'BATTLOW')


class ButtonDoor(Message):
    def __init__(self, device, message, input, state):
        self.message = message
        self.input = input
        self.state = state
        body = 'ON' if state else 'OFF'
        super(ButtonDoor, self).__init__(device, message + input + body)


class ButtonPress(Message):
    def __init__(self, device, message, input):
        self.message = message
        self.input = input
        super(ButtonPress, self).__init__(device, message + input)


class ButtonSwitch(Message):
    def __init__(self, device, message, state):
        self.message = message
        self.state = state
        body = 'ON' if state else 'OFF'
        super(ButtonSwitch, self).__init__(device, message + body)


class FirmwareVersion(Message):
    def __init__(self, device, version=None):
        body = 'FVER'
        self.version = version
        if version:
            body = body+version
        super(FirmwareVersion, self).__init__(device, body)
        self.requires_ack = False

    def is_response(self, message):
        if self.device != message.device:
            return False

        return isinstance(message, self.__class__)


class Hello(Message):
    def __init__(self, device):
        super(Hello, self).__init__(device, 'HELLO')
        self.requires_ack = False


class ProtocolVersion(Message):
    def __init__(self, device, version=None):
        body = 'APVER'
        self.version = version
        if version:
            body = body+version
        super(ProtocolVersion, self).__init__(device, body)
        self.requires_ack = False

    def is_response(self, message):
        if self.device != message.device:
            return False

        return isinstance(message, self.__class__)


class Reboot(Message):
    def __init__(self, device):
        super(Reboot, self).__init__(device, 'REBOOT')
        self.requires_ack = False


class Sleep(Message):
    def __init__(self, device):
        super(Sleep, self).__init__(device, 'SLEEP')

    def is_response(self, message):
        if self.device != message.device:
            return False
        return isinstance(message, Sleeping)


class Sleeping(Message):
    def __init__(self, device):
        super(Sleeping, self).__init__(device, 'SLEEPING')
        self.requires_ack = False


class Started(Message):
    def __init__(self, device):
        super(Started, self).__init__(device, 'STARTED')


class Wake(Message):
    def __init__(self, device):
        super(Wake, self).__init__(device, 'WAKE')
        self.requires_ack = False


class WakeCount(Message):
    def __init__(self, device, count):
        super(WakeCount, self).__init__(device, 'WAKEC' + format(count, '03d'))
        self.count = count
        self.requires_ack = False
