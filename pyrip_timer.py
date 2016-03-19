# pyrip_timer.py

import time

class Timer(object):
    def __init__(self, interval):
        self._timestamp = time.clock()
        self.interval = interval

    @property
    def elapsed(self):
        return time.clock() - self._timestamp

    @property
    def is_expired(self):
        if self.elapsed > self.interval:
            return True
        return False
  
    @property
    def count(self):
        return self.elapsed // self.interval

    def reset(self):
        self._timestamp = time.clock()