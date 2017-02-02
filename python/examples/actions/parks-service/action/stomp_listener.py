"""Simple class to handle messages arriving on STOMP queues"""

from __future__ import print_function

import json
import logging
from traceback import format_exc
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
