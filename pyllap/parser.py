import re
from . import messages
from .constants import *


def read(string):
    if len(string) != LLAP_LEN:
        return None
    if string[:1] != LLAP_START:
        return None

    device = string[1:3]
    body = re.sub(LLAP_FILL, '', string[3:])

    if body == 'ACK':
        return messages.Ack(device)
    if body.startswith('APVER'):
        if body == 'APVER':
            return messages.ProtocolVersion(devices)
        match = re.match('APVER(\d\.\d\d?)', body)
        if match:
            return messages.ProtocolVersion(device, match.group(1))
    if body == 'AWAKE':
        return messages.Awake(device)
    if body.startswith('BATT'):
        if body == 'BATT':
            return messages.Battery(device)
        if body == 'BATTLOW':
            return messages.BatteryLow(device)
        match = re.match('BATT(\d\.\d\d)', body)
        if match:
            return messages.Battery(device, match.group(1))
    if body.startswith('FVER'):
        if body == 'FVER':
            return messages.FirmwareVersion(device)
        match = re.match('FVER(\d\.\d\d.)', body)
        if match:
            return messages.FirmwareVersion(device, match.group(1))
    if body == 'HELLO':
        return messages.Hello(device)
    if body == 'REBOOT':
        return messages.Reboot(device)
    if body == 'SLEEP':
        return messages.Sleep(device)
    if body == 'SLEEPING':
        return messages.Sleeping(device)
    if body == 'STARTED':
        return messages.Started(device)
    if body == 'WAKE':
        return messages.Wake(device)

    # Button messages are 'complex' because there are several types and the
    # messages are customisable. So, best guesses for now

    match = re.match('(.*)(A|B)$', body)
    if match:
        return messages.ButtonPress(device, match.group(1), match.group(2))

    match = re.match('(.*)(A|B)(ON|OFF?)$', body)
    if match:
        state = True if (match.group(3) == 'ON') else False
        return messages.ButtonDoor(device, match.group(1),
                                   match.group(2), state)

    match = re.match('(.*)(ON|OFF)$', body)
    if match:
        state = True if (match.group(3) == 'ON') else False
        return messages.ButtonSwitch(device, match.group(1), state)

    return messages.Message(device, body)
