import serial
import logging
from . import messages
from . import parser
from .constants import *
import time
import threading
import queue
from logging import NullHandler

logger = logging.getLogger(__name__)


class ControllerThread(threading.Thread):
    WAIT_TIME = 1

    def __init__(self, port, event_queue, command_queue):
        super(ControllerThread, self).__init__()
        self.name = 'ControllerThread'
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.awake_queue = queue.Queue()
        self.pending_list = LockableList()
        self.unanswered_list = LockableList()
        self.event_queue = event_queue
        self.command_queue = command_queue
        self.running = threading.Event()
        ser = serial.Serial(port)
        self.reader = SerialReaderThread(ser, self.read_queue)
        self.writer = SerialWriterThread(ser, self.write_queue)
        self.read_handler = ReadHandlerThread(self.read_queue,
                                              self.write_queue,
                                              self.awake_queue,
                                              self.event_queue,
                                              self.reader,
                                              self.pending_list)
        self.retry_handler = RetryHandlerThread(self.write_queue,
                                                self.pending_list,
                                                self.unanswered_list)
        self.wake_handler = WakeHandlerThread(self.awake_queue,
                                              self.write_queue,
                                              self.unanswered_list)
        self.write_handler = WriteHandlerThread(self.command_queue,
                                                self.write_queue,
                                                self.pending_list)

    def run(self):
        self.reader.start()
        self.writer.start()
        self.read_handler.start()
        self.retry_handler.start()
        self.write_handler.start()
        self.wake_handler.start()
        self.running.set()
        while self.running.is_set():
            time.sleep(1)

        # Give the writer time to write any last messages
        self.writer.join(2)
        self.retry_handler.join(2)
        logger.debug('Shutting down')

    def join(self, timeout=None):
        logger.info('Received shutdown call')
        self.running.clear()
        super(ControllerThread, self).join(timeout)


class SerialReaderThread(threading.Thread):
    def __init__(self, serial, read_queue):
        super(SerialReaderThread, self).__init__()
        self.serial = serial
        self.read_queue = read_queue
        # Reading isn't an atomic action, so if we're being killed we
        # don't need to wait for the reader to shut down
        self.daemon = True
        self._flush = threading.Event()
        self.name = 'SerialReader'

    def run(self):
        self.serial.flushInput()
        while True:
            line = self.serial.read(LLAP_LEN).decode()
            logger.debug('Read: %s' % line)

            self.read_queue.put(line)
            if self._flush.is_set():
                logger.debug('Flushing input')
                self._flush.clear()
                self.serial.flushInput()

    def flush(self):
        logger.debug('Flush requested')
        self._flush.set()


class SerialWriterThread(threading.Thread):
    def __init__(self, serial, write_queue):
        super(SerialWriterThread, self).__init__()
        self.write_queue = write_queue
        self.serial = serial
        self.running = threading.Event()
        # Set as a daemon even though it has a join call
        # join() will give it the chance to finish things off, but if
        # there's nothing left for it (and thus is blocking on queue get())
        # we just let it die.
        self.daemon = True
        self.name = 'SerialWriter'

    def run(self):
        self.running.set()
        self.serial.flushOutput()
        while self.running.is_set():
            to_write = self.write_queue.get()
            self.serial.write(to_write.encode())
            logger.debug("Wrote: %s" % to_write)

    def join(self, timeout=None):
        self.running.clear()
        super(SerialWriterThread, self).join(timeout)


class ReadHandlerThread(threading.Thread):
    RETRY_BUFFER_LENGTH = 0.5

    def __init__(self, read_queue, write_queue, awake_queue,
                 event_queue, reader, pending_list):
        super(ReadHandlerThread, self).__init__()
        self.read_queue = read_queue
        self.write_queue = write_queue
        self.awake_queue = awake_queue
        self.event_queue = event_queue
        self.reader = reader
        self.pending_list = pending_list
        # We don't care about handling events once things shut down
        self.daemon = True
        self.retry_buffer = []
        self.name = "ReadHandler"

    def run(self):
        while True:
            message = parser.read(self.read_queue.get())

            if message is None:
                self.reader.flush()
                continue

            if isinstance(message, messages.Awake):
                self.awake_queue.put(message.device)

            if self.is_retry(message):
                logger.debug('Previous message was a retry')
                if message.requires_ack:
                    self.write(messages.Ack(message.device))
                continue

            if self.check_and_clear_pending(message):
                logger.debug('Previous message was a response')

            if message.requires_ack:
                self.write(messages.Ack(message.device))
                self.retry_buffer.append(message)

            self.event_queue.put(message)

    def write(self, message):
        self.write_queue.put(message.to_llap())

    def is_retry(self, message):
        indexes_to_remove = []
        for idx, item in enumerate(self.retry_buffer):
            if item.time + self.RETRY_BUFFER_LENGTH < time.time():
                indexes_to_remove.append(idx)
                continue

            if item == message:
                return True

        for idx in reversed(indexes_to_remove):
            self.retry_buffer.pop(idx)

        return False

    def check_and_clear_pending(self, message):
        for idx, pending in enumerate(self.pending_list):
            if pending.is_response(message):
                self.pending_list.pop(idx)
                self.pending_list.release()
                return True

        self.pending_list.release()
        return False


class RetryHandlerThread(threading.Thread):
    MAX_RETRIES = 5
    LOOP_SLEEP = 0.01
    RETRY_TIME = 0.1

    def __init__(self, write_queue, pending_list, unanswered_list):
        super(RetryHandlerThread, self).__init__()
        self.write_queue = write_queue
        self.daemon = True
        self.name = 'RetryHandler'
        self.pending_list = pending_list
        self.unanswered_list = unanswered_list
        self.running = threading.Event()

    def run(self):
        self.running.set()
        while self.running.is_set():
            time.sleep(self.LOOP_SLEEP)

            indexes_to_remove = []
            for idx, message in enumerate(self.pending_list):
                if message.retries >= self.MAX_RETRIES:
                    indexes_to_remove.append(idx)
                    self.unanswered_list.append(message)
                    continue
                if (message.time + self.RETRY_TIME) < time.time():
                    message.time = time.time()
                    message.retries = message.retries + 1
                    self.write_queue.put(message.to_llap())

            for idx in reversed(indexes_to_remove):
                self.pending_list.pop(idx)
            self.pending_list.release()

    def join(self, timeout=None):
        self.running.clear()
        super(RetryHandlerThread, self).join(timeout)


class WriteHandlerThread(threading.Thread):
    def __init__(self, command_queue, write_queue, pending_list):
        super(WriteHandlerThread, self).__init__()
        self.command_queue = command_queue
        self.write_queue = write_queue
        self.pending_list = pending_list
        self.name = 'WriteHandler'
        self.daemon = True

    def run(self):
        while True:
            message = self.command_queue.get()
            message.time = time.time()
            # Get the lock first, otherwise we may end up blocking and write
            # to the list after the response has already been received
            self.pending_list.acquire()
            self.write_queue.put(message.to_llap())
            self.pending_list.append(message)
            self.pending_list.release()


class WakeHandlerThread(threading.Thread):
    def __init__(self, awake_queue, write_queue, unanswered_list):
        super(WakeHandlerThread, self).__init__()
        self.awake_queue = awake_queue
        self.write_queue = write_queue
        self.unanswered_list = unanswered_list
        self.name = 'WakeHandler'
        self.daemon = True

    def run(self):
        while True:
            device = self.awake_queue.get()
            indexes_to_remove = []
            for idx, message in enumerate(self.unanswered_list):
                if message.device != device:
                    continue
                self.write_queue.put(message.to_llap())
                indexes_to_remove.append(idx)

            for idx in reversed(indexes_to_remove):
                self.unanswered_list.pop(idx)
            self.unanswered_list.release()


def locking(func):
    def outer_function(self, *args, **kwargs):
        self.lock.acquire()
        try:
            output = func(self, *args, **kwargs)
        except Exception:
            self.lock.release()
            raise
        self.lock.release()
        return output
    return outer_function


class LockableList(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.list = []

    def __iter__(self):
        self.lock.acquire()
        return iter(self.list)

    @locking
    def __getitem__(self, index):
        return self.list.__getitem__(index)

    @locking
    def __len__(self):
        return len(self.list)

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

    @locking
    def append(self, value):
        return self.list.append(value)

    @locking
    def pop(self, idx):
        return self.list.pop(idx)
