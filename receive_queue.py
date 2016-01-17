#!/usr/bin/env python
from collections import deque
import threading


class ReceiveQueue:
    def __init__(self, groupkeys, bufferlen, lock_strategy='unsync'):
        # Initialize len(groupkeys) groups of queues
        self._rcv_buffer = {k: dict() for k in groupkeys}

        # Each queue operates like a shift register with a fixed length
        self._bufferlen = bufferlen

        # Lock strategy used
        self._lock_strategy = lock_strategy

        if self._lock_strategy == 'rw':
            # Read Write lock (this allows multiple writers to access in concurrency, but only a reader at a time)
            self._mutex = threading.RLock()
            self._writers_monitor = threading.RLock()
            self._writer_count = 0
        elif self._lock_strategy == 'exclusive':
            self._mutex = threading.RLock()

    def receive(self, groupkey, idx, value):

        # Call this method before append (to notify subclasses about the append)
        self._before_receive(groupkey, idx, value)

        # Check groupkey
        self._check_groupkey(groupkey)

        # The queues inside each group can be dynamically allocated, so we check here the existence by its id
        if not self._check_queue(groupkey, idx):
            self._rcv_buffer[groupkey][idx] = deque(maxlen=self._bufferlen)

        # Finally append the value to the queue
        self._rcv_buffer[groupkey][idx].append(value)

        # Call the process method to be able to perform some computation on the queue after an element is appended
        self._after_receive(groupkey, idx, value)

    def sync_receive(self, groupkey, idx, value):

        if self._lock_strategy == 'rw':
            # Acquire the writers_monitor
            with self._writers_monitor:
                self._writer_count += 1
                # If this is the first writer that has attempted to access the resource
                if self._writer_count == 1:
                    # Acquire the mutex on the reader
                    self._mutex.acquire()
        elif self._lock_strategy == 'exclusive':
            self._mutex.acquire()

        # -- Critical section

        # In this section I'm sure that no readers are attempting to extract data from the buffer
        self.receive(groupkey, idx, value)

        # -- End critical section

        if self._lock_strategy == 'rw':
            # Acquire the writers_monitor
            with self._writers_monitor:
                self._writer_count -= 1
                # If I'm the last writer on the resource, release the lock to provide access to readers
                if self._writer_count == 0:
                    self._mutex.release()
        elif self._lock_strategy == 'exclusive':
            self._mutex.release()

    def _before_receive(self, groupkey, idx, value):
        pass

    def _after_receive(self, groupkey, idx, value):
        pass

    def extract_buffer(self, groupkey, idx):
        # Check groupkey
        self._check_groupkey(groupkey)

        if self._check_queue(groupkey, idx):
            if self._bufferlen > 1:
                return tuple(self._rcv_buffer[groupkey][idx])
            else:
                return tuple(self._rcv_buffer[groupkey][idx], )
        else:
            return tuple()

    def extract_all(self, groupkey):
        """
        Extracts a dict of all buffers from a groupkey (tuple)
        :param groupkey: the selected groupkey
        :return: a dict of tuples
        """
        # Check groupkey
        self._check_groupkey(groupkey)

        if self._bufferlen > 1:
            return {key: tuple(val) for key, val in self._rcv_buffer[groupkey].iteritems()}
        else:
            return {key: tuple(val, ) for key, val in self._rcv_buffer[groupkey].iteritems()}

    def sync_extract_buffer(self, groupkey, idx):
        # Acquire the mutex only on the selected lock_strategies
        if self._lock_strategy == 'exclusive' or self._lock_strategy == 'rw':
            self._mutex.acquire()

        # -- Critical section

        ret = self.extract_buffer(groupkey, idx)

        # -- End critical section

        # Acquire the mutex only on the selected lock_strategies
        if self._lock_strategy == 'exclusive' or self._lock_strategy == 'rw':
            self._mutex.release()

        return ret

    def sync_extract_all(self, groupkey):
        # Acquire the mutex only on the selected lock_strategies
        if self._lock_strategy == 'exclusive' or self._lock_strategy == 'rw':
            self._mutex.acquire()

        # -- Critical section

        ret = self.extract_all(groupkey)

        # -- End critical section

        # Acquire the mutex only on the selected lock_strategies
        if self._lock_strategy == 'exclusive' or self._lock_strategy == 'rw':
            self._mutex.release()

        return ret

    def _check_groupkey(self, groupkey):
        # If the group's key is not defined, raise an error (these keys are statically initialized by the __init__)
        if groupkey not in self._rcv_buffer:
            raise IndexError
        else:
            return True

    def _check_queue(self, groupkey, idx):
        return idx in self._rcv_buffer[groupkey]
