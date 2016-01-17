import time
import math


class TimeManager:
    def __init__(self):
        self._tic = 0
        self._elapsed = 0

    def tic(self):
        self._tic = time.time()

    def toc(self, resolution):
        # Compute the elapsed time since the tic() method was called
        self._elapsed = time.time() - self._tic
        if resolution == 'sf':
            return self._elapsed
        elif resolution == 's':
            return int(math.floor(self._elapsed))
        elif resolution == 'ms':
            s = int(math.floor(self._elapsed))
            ms = int(math.floor((self._elapsed - s) * 1e3))
            return int(s * 1e3 + ms)
        elif resolution == 'us':
            s = int(math.floor(self._elapsed))
            us = int(math.floor((self._elapsed - s) * 1e6))
            return int(s * 1e6 + us)
        elif resolution == 'ns':
            s = int(math.floor(self._elapsed))
            ns = int(math.floor((self._elapsed - s) * 1e9))
            return int(s * 1e9 + ns)
        else:
            print "Please provide a valid resolution format"

    def round(self, resolution):
        tmp = self.toc(resolution)
        self.tic()
        return tmp
