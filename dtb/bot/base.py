from urllib import request
from collections import deque
import time


MINUTE = 60


class Bot(object):
    """docstring for Bot."""
    _message_types = {}

    def __init__(self, config, wait_for_limit=True, limit_per_minute=19, emergency_per_minute=1):
        self.config = config
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}

        self._history = []
        self._emergency_history = []
        self.wait_for_limit = wait_for_limit
        self.limit_per_minute = limit_per_minute
        self.emergency_per_minute = emergency_per_minute

    @property
    def limit_per_minute(self):
        return self.history.maxlen

    @limit_per_minute.setter
    def limit_per_minute(self, limit_per_minute):
        self._history = deque(self.history, maxlen=limit_per_minute)

    @property
    def history(self):
        return self._history

    @property
    def emergency_per_minute(self):
        return self.emergency_history.maxlen

    @limit_per_minute.setter
    def emergency_per_minute(self, emergency_per_minute):
        self._emergency_history = deque(
            self.emergency_history, maxlen=emergency_per_minute)

    @property
    def emergency_history(self):
        return self._emergency_history

    def send(self, message):
        if len(self.history) == self.history.maxlen:
            if self.wait_for_limit:
                wait = time.time() - self.history[0][0] - MINUTE
                if wait < 0:
                    print('Wait for limit: {}s'.format(-wait))
                    time.sleep(-wait)
            else:
                # TODO: collect for feed
                return

        # TODO: consider in a thread
        req = request.Request(self.config.url, message.dump(), self.headers)

        with request.urlopen(req) as resp:
            # TODO: process any error here
            # TODO: consider request time or response time
            item = (time.time(), message, req, resp)
            self.history.append(item)
            # TODO: do log more properly
            print(item)
            print(resp.read().decode('utf-8'))

    @classmethod
    def register(cls, name):
        def register_message(cls_):
            from ..message.base import Message
            if not issubclass(cls_, Message):
                raise TypeError(
                    'Register Message class with Bot, while {} is provided.'.format(cls_))
            cls._message_types[name] = cls_
            return cls_

        return register_message

    def __getattr__(self, name):
        def send_registed(*args, **kwargs):
            return self.send(type(self)._message_types[name](*args, **kwargs))
        return send_registed
