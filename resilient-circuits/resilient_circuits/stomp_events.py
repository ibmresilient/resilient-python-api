# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Circuits events for STOMP Client """

import logging
from circuits import Event

LOG = logging.getLogger(__name__)


class StompEvent(Event):
    """A Circuits event with less verbose repr"""
    success = True

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

        return u"<%s[%s] (%s)>" % (self.name, channels, data)


class Disconnected(StompEvent):
    def __init__(self, reconnect=True, receipt=None):
        super(Disconnected, self).__init__(receipt=receipt)
        self.reconnect = reconnect


class Disconnect(StompEvent):
    def __init__(self, reconnect=False, flush=True, receipt=None):
        super(Disconnect, self).__init__(receipt=receipt, reconnect=reconnect, flush=flush)
    pass


class Message(StompEvent):
    def __init__(self, frame):
        super(Message, self).__init__(headers=frame.headers,
                                      message=frame.body)
        self.frame = frame


class Send(StompEvent):
    failure = True

    def __init__(self, headers, body, destination, message_id=None):
        self.headers = headers
        self.body = body
        self.destination = destination
        self.message_id = message_id
        super(Send, self).__init__(headers=headers,
                                   body=body,
                                   destination=destination)


class ClientHeartbeat(StompEvent):
    pass


class ServerHeartbeat(StompEvent):
    pass


class Connect(StompEvent):
    def __init__(self, subscribe=False, host=None):
        super(Connect, self).__init__(host=host)
        self.subscribe = subscribe


class Connected(StompEvent):
    pass


class ConnectionFailed(StompEvent):
    reconnect = True


class OnStompError(StompEvent):
    def __init__(self, frame, err):
        headers = frame.headers if frame else {}
        body = frame.body if frame else None
        super(OnStompError, self).__init__(headers=headers,
                                           message=body,
                                           error=err)
        self.frame = frame


class HeartbeatTimeout(StompEvent):
    pass


class Subscribe(StompEvent):
    def __init__(self, destination, additional_headers=None, **kwargs):
        super(Subscribe, self).__init__(destination=destination, additional_headers=additional_headers, **kwargs)
        self.destination = destination


class Unsubscribe(StompEvent):
    def __init__(self, destination):
        super(Unsubscribe, self).__init__(destination=destination)
        self.destination = destination


class Ack(StompEvent):
    failure = True

    def __init__(self, frame, message_id=None):
        super(Ack, self).__init__(frame=frame)
        self.frame = frame
        self.message_id = message_id
