# -*- coding: utf-8 -*-
""" Circuits events for Stomp Client """

import logging
from circuits import Event

LOG = logging.getLogger(__name__)


class StompEvent(Event):
    """A Circuits event with less verbose repr"""

    def _repr(self):
        return ""

    def __repr__(self):
        "x.__repr__() <==> repr(x)"

        if len(self.channels) > 1:
            channels = repr(self.channels)
        elif len(self.channels) == 1:
            channels = str(self.channels[0])
        else:
            channels = ""

        data = self._repr()

        return "<%s[%s] (%s)>" % (self.name, channels, data)

class DisconnectedEvent(StompEvent):
    pass

class Disconnect(StompEvent):
    pass

class MessageEvent(StompEvent):
    def __init__(self, frame):
        super(MessageEvent, self).__init__(headers=frame.headers,
                                           message=frame.body)
        self.frame = frame

class Send(StompEvent):
    def __init__(self, headers, body, destination):
        super(Send, self).__init__(headers=headers,
                                        body=body,
                                        destination=destination)

class ClientHeartbeat(StompEvent):
    pass

class ServerHeartbeat(StompEvent):
    pass

class Connect(StompEvent):
    pass

class Connected(StompEvent):
    pass

class ConnectionFailed(StompEvent):
    pass

class StompErrorEvent(StompEvent):
    def __init__(self, frame, err):
        headers = frame.headers if frame else {}
        body = frame.body if frame else None
        super(StompErrorEvent, self).__init__(headers=headers,
                                              message=body,
                                              error=err)
        self.frame = frame

class HeartbeatTimeout(StompEvent):
    pass

class Subscribe(StompEvent):
    def __init__(self, destination):
        super(Subscribe, self).__init__(destination=destination)
        self.destination=destination

class Unsubscribe(StompEvent):
    def __init__(self, destination):
        super(Unsubscribe, self).__init__(destination=destination)
        self.destination=destination

class Ack(StompEvent):
    def __init__(self, frame):
        super(Ack, self).__init__(frame=frame)
        self.frame=frame
