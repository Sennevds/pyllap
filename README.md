# pyllap
A Python library for sending and receiving LLAP messages for controlling Ciseco hardware.

## Disclaimer
This is a very basic library I have built as part of a larger project. As such, I have put in it pretty much only what I needed at the time of writing - for example, many message types from the official LLAP reference are missing. I may later decide to make this a much more formal library, but that will depend on free time and if there is any interest. It is provided as-is and support is in no way guaranteed. Please feel free to fork, use as much or as little as you like, raise issues and/or submit pull requests

## Use
There is a controller that leans heavily on the Python threading library to handle I/O and all the important things that must be done like ACKing messages to stop retries. It will also handle transmit retries and sleeping devices.

In my setup, I have a Ciseco Slice of Pi (https://www.wirelessthings.net/slice-of-radio-wireless-rf-transciever-for-the-raspberry-pi) plugged into a Raspberry Pi. The Slice of Pi is in serial passthrough mode.

## Requirements
Until I get around to building the setup.py file, a textual list will do:
* pyserial - https://github.com/pyserial/pyserial
That's it.

## Compatibility
Currently Python 3 is supported, though it's only been tested on 3.4. It probably wouldn't take much to make it Python 2.7 compatible, however.

## Example
Starting the controller is relatively easy. Provide it a serial port, command queue (for sending messages to devices), an event queue (for receiving messages)

```
import pyllap.messages as lm
from pyllap.controller import ControllerThread
from queue import Queue

port = '/dev/ttyAMA0'
event_queue = Queue()
command_queue = Queue()
controller = ControllerThread(port, event_queue, command_queue)
controller.start()
```

You can then pass messages to devices on the command queue (the two character device name passed in as a string):

```
device = 'AA'
hello = lm.Hello(device)
command_queue.put(hello)
```

And receive messages by fetching from the event queue, usually in an loop of some sort:

```
while True:
    message = event_queue.get()
    # Do something with your message here
```

## LLAP Reference
http://openmicros.org/index.php/articles/85-llap-lightweight-local-automation-protocol/297-llap-reference
