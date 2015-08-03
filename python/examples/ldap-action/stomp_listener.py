#!/usr/bin/env python

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
# The stomp library will call our listener's on_message when a message is received.

"""Simple class to handle messages arriving on STOMP queues"""

from __future__ import print_function

import json
import logging
logger = logging.getLogger(__name__)


class StompListener(object):
    """Listener for STOMP connection to the Resilient server"""

    def __init__(self, conn, handler):
        """Initialize with a Stomp connection, and a handler function that we'll call"""
        self.conn = conn
        self.handler = handler
        self.is_connected = False

    def on_error(self, headers, message):
        """STOMP produced an error."""
        logger.error('STOMP listener: Error:\n%s', message)
        logger.debug(headers)
        # TODO reconnections, etc
        if self.is_connected:
            logger.error("TODO reconnect")
        exit(1)

    def on_connected(self, headers, message):
        """Client has connected to the STOMP server"""
        logger.debug("STOMP connected")
        self.is_connected = True

    def on_disconnected(self):
        """Client has disconnected from the STOMP server"""
        logger.debug("STOMP disconnected!")
        self.is_connected = False

    def on_message(self, headers, message):
        """STOMP produced a message."""
        if message == "SHUTDOWN":
            logger.info("Shutting down")
            self.conn.disconnect()
            raise Exception("STOMP channel is shutting down")

        # Get the relevant headers.
        reply_to = headers['reply-to']
        correlation_id = headers['correlation-id']
        context = headers['Co3ContextToken']

        # All our messages are JSON.  Parse into to a dictionary.
        json_message = json.loads(message)

        # Have the handler process the message
        result = None
        try:
            result = self.handler(json_message, context)
            message = "Processing complete"
            status = 0
        except Exception as exc:
            logger.exception("Exception in handler")
            message = "ERROR: {}".format(exc)
            status = 1  # error

        # Reply with a status message incidating error or completion
        reply_message = json.dumps({"message_type": status, "message": message, "complete": True})
        self.conn.send(reply_to, reply_message, headers={'correlation-id': correlation_id})
