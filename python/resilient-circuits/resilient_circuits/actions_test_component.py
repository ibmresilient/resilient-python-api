#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Resilient Systems, Inc. ("Resilient") is willing to license software
# or access to software to the company or entity that will be using or
# accessing the software and documentation and that you represent as
# an employee or authorized agent ("you" or "your") only on the condition
# that you accept all of the terms of this license agreement.
#
# The software and documentation within Resilient's Development Kit are
# copyrighted by and contain confidential information of Resilient. By
# accessing and/or using this software and documentation, you agree that
# while you may make derivative works of them, you:
#
# 1)  will not use the software and documentation or any derivative
#     works for anything but your internal business purposes in
#     conjunction your licensed used of Resilient's software, nor
# 2)  provide or disclose the software and documentation or any
#     derivative works to any third party.
#
# THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Action Module circuits component to mock Resilient stomp server for testing"""

from __future__ import print_function
import logging
import time
import json
import struct
from circuits import Component, Event, task, handler
from circuits.net.sockets import TCPServer
from circuits.net.events import write
import resilient_circuits.actions_component
LOG = logging.getLogger(__name__)


class ResilientTestActions(Component):
    """ Mock the stomp connection for testing"""

    def __init__(self, org_id):
        super(ResilientTestActions, self).__init__()
        self.org_id = org_id
        bind = ("0.0.0.0", 8008)
        TCPServer(bind).register(self)
        self.sock = None

    def usage(self):
        return "Submit actions with format: <queue> <message json>"

    def read(self, sock, data):
        """ Triggered by user submitting action over tcp connection """
        LOG.info("Read %s", data)
        self.sock = sock
        try:
            data =  data.strip().decode('utf-8')
            if ' ' not in data:
                self.fire_message(self.usage())
                return

            queue, message = data.split(' ', 1)

            if not all((queue, message)):
                self.fire_message("queue and message must be supplied")
                return

            channel = "actions." + queue
            headers = {  "reply-to": "/queue/acks.{org}.{queue}".format(org=self.org_id, queue=queue),
                         "expires": "0",
                         "timestamp": str(int(time.time())),
                         "destination": "/queue/actions.{org}.{queue}".format(org=self.org_id, queue=queue),
                         "correlation-id": "invid:390",
                         "persistent": "True",
                         "priority": "4",
                         "Co3MessagePayload": "ActionDataDTO",
                         "Co3ContentType": "application/json",
                         "message-id": "ID:resilient-54199-1476798485700-6:2:12:1:1",
                         "Co3ContextToken": "dummy",
                         "subscription": "stomp-{queue}".format(queue=queue)
            }
            try:
                message = json.loads(message)
                assert(isinstance(message, dict))
            except Exception as e:
                LOG.error("Bad Action Message: %s", message)
                self.fire_message("Bad Action Message! %s" % str(e))
                return

            event = resilient_circuits.actions_component.ActionMessage(source=self.parent,
                                                                       headers=headers,
                                                                       message=message,
                                                                       test=True)
            self.fire(event, channel)
            self.fire_message("Action Submitted")
        except Exception as e:
            LOG.exception("Action Failed")
            self.fire_message(str(e))
    
    def connect(self, sock, host, port):
        """Triggered for new connecting TCP clients"""
        pass
        
    def test_response(self, message):
        """ Send a message out to the client """
        LOG.debug("Received message for test client")
        self.fire_message("RESPONSE: " + message )

    def done(self, event):
        status = yield self.wait(event)
        status = status.value
        
        if isinstance(status, Exception):
            self.fire_message(str(Exception))
            raise status
        else:
            status = status + "\n"
            self.fire_message(status)

    def fire_message(self, message):
        """ Prefix message with length and append newline before firing"""
        message = (message + "\n").encode()
        message = struct.pack('>I', len(message)) + message
        LOG.info("Firing message: %s", message)
        self.fire(write(self.sock, message))
