# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
"""Test Server component for injecting test Action Module messages"""

from __future__ import print_function
import logging
import time
import json
import struct
from circuits import Component, Event, task, handler
from circuits.net.sockets import TCPServer
from circuits.net.events import write
from resilient_circuits.action_message import ActionMessage
LOG = logging.getLogger(__name__)


class SubmitTestAction(Event):
    """ Circuits event to insert a test Action Message """
    def __init__(self, queue, msg_id, message):
        if not all((queue, msg_id, message)):
            raise ValueError("queue, msg_id, and message are required")
        super(SubmitTestAction, self).__init__(queue=queue, msg_id=msg_id,
                                         message=message)


class ResilientTestActions(Component):
    """ Mock the stomp connection for testing"""

    def __init__(self, org_id, host="localhost", port=8008):
        super(ResilientTestActions, self).__init__()
        self.org_id = org_id
        bind = (host, port)
        LOG.debug("Binding test server to %s:%d", host, port)
        TCPServer(bind).register(self)
        self.messages_in_progress = {}
        self.actions_sent = {}

    def usage(self):
        return "Submit actions with format: <queue> <message json>"

    def SubmitTestAction(self, queue, msg_id, message, channel="*"):
        """ Create and fire an ActionMessage """
        try:
            message_id = "ID:resilient-54199-{val}-6:2:12:1:1".format(val=msg_id)
            reply_to = "/queue/acks.{org}.{queue}".format(org=self.org_id,
                                                          queue=queue)
            destination = "/queue/actions.{org}.{queue}".format(org=self.org_id,
                                                                queue=queue)
            channel = "actions." + queue
            headers = {"reply-to": reply_to,
                       "expires": "0",
                       "timestamp": str(int(time.time()) * 1000),
                       "destination": destination,
                       "correlation-id": "invid:390",
                       "persistent": "True",
                       "priority": "4",
                       "Co3MessagePayload": "ActionDataDTO",
                       "Co3ContentType": "application/json",
                       "message-id": message_id,
                       "Co3ContextToken": "dummy",
                       "subscription": "stomp-{queue}".format(queue=queue)}
            try:
                sock = self.actions_sent.get(msg_id)
                if not isinstance(message, dict):
                    message = json.loads(message)
                    assert(isinstance(message, dict))
            except Exception as e:
                LOG.exception("Bad Message<action %d>: %s", msg_id, message)
                if sock:
                    msg = "Bad Message<action %d>! %s" % (msg_id, str(e))
                    self.fire_message(sock, msg)
                return

            event = ActionMessage(source=self.parent,
                                  headers=headers,
                                  message=message,
                                  test=True,
                                  test_msg_id=msg_id)
            self.fire(event, channel)
            if sock:
                self.fire_message(sock, "Action Submitted<action %d>" % msg_id)
        except Exception as e:
            LOG.exception("Action Failed<action %d>", msg_id)
            if sock:
                msg = "Action Failed<action %d>: %s" % (msg_id,
                                                        str(e))
                self.fire_message(sock, msg)

    @handler("read")
    def process_data(self, sock, data):
        """ Process data received from TCP stream """
        msg_id = -1  # default
        try:
            data_as_bytes = bytearray(data)
            if sock not in self.messages_in_progress:
                # New message, parse size out
                msg_size = struct.unpack('>I', data_as_bytes[:4])[0]
                partial_msg = data_as_bytes[4:msg_size + 4]
            else:
                # Retrieve what we had so far
                msg_size, partial_msg = self.messages_in_progress.pop(sock)
                partial_msg = partial_msg + data_as_bytes

            if len(partial_msg) < msg_size:
                # Store what we have so far and wait for more
                self.messages_in_progress[sock] = msg_size, partial_msg
                return
            else:
                # Complete message, parse out msg_id, queue, and msg
                msg_id = struct.unpack('>I', partial_msg[:4])[0]
                data = partial_msg[4:msg_size]
                remainder = partial_msg[msg_size:]
                data = data.strip().decode('utf-8')
                if ' ' not in data or len(data) < 2:
                    # Bad Command
                    msg = ("<action %d>: " % msg_id) + self.usage()
                    self.fire_message(sock, msg)
                else:
                    queue, message = data.split(' ', 1)
                    self.actions_sent[msg_id] = sock
                    self.fire(SubmitTestAction(queue, msg_id, message))

                if remainder:
                    # Process remainder
                    self.process_data(sock, remainder)
        except Exception as e:
            LOG.exception("Action Failed<action %d>", msg_id)
            msg = "Action Failed<action %d>: %s" % (msg_id, str(e))
            self.fire_message(sock, msg)

    def connect(self, sock, host, port):
        """Triggered for new connecting TCP clients"""
        pass

    def test_response(self, msg_id, message):
        """ If action orginated from test client, send response"""
        LOG.debug("Received message for test client")
        sock = self.actions_sent.get(msg_id)
        if sock:
            msg = "RESPONSE<action %d>: %s" % (msg_id, message)
            self.fire_message(sock, msg)

    def done(self, event):
        status = yield self.wait(event)
        status = status.value
        sock = self.actions_sent.get(event.test_msg_id)
        if isinstance(status, Exception):
            msg = "Action Failed<action %d>: %s" % (event.test_msg_id,
                                                    str(Exception))
            self.fire_message(sock, msg)
            raise status
        else:
            status = status + "\n"
            msg = "Action Completed<action %d>: %s" % (event.test_msg_id,
                                                       status)
            self.fire_message(sock, msg)

    def fire_message(self, sock, message):
        """ Prefix message with length before firing"""
        message = message.encode()
        message = struct.pack('>I', len(message)) + message
        LOG.debug("Firing Message: %s", message)
        self.fire(write(sock, message))
