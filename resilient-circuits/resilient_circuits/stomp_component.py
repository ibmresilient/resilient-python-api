# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Circuits component for handling Stomp Connection """

import logging
import ssl
import sys
import time
import traceback

import stomp
from circuits import BaseComponent
from circuits.core.handlers import handler

from resilient_circuits import constants
from resilient_circuits.stomp_events import *

DEFAULT_MAX_RECONNECT_ATTEMPTS = 3
DEFAULT_STARTUP_MAX_RECONNECT_ATTEMPTS = 3

LOG = logging.getLogger(__name__)



class StompClient(BaseComponent):

    channel = "stomp"

    def init(self, host, port,
             username=None, password=None,
             heartbeats=(0, 0),
             ca_certs=None,
             stomp_params=None,
             stomp_max_connection_errors=constants.STOMP_MAX_CONNECTION_ERRORS, *_args, **_kwargs):

        # TODO! Figure out if stomp-py can work with a proxy through a similar mechanism that we're currently using with the stomp_transport.py file
        LOG.info("Connect to stomp at '%s:%s'", host, port)


        # Configure failover options so it only tries based on settings
        # build any parameters passed
        # every connection has at least these two: maxReconnectAttempts, startupMaxReconnectAttempts
        items = [item.split("=", 2) for item in stomp_params.split(",")] if stomp_params else []
        connection_params = {item[0].strip():item[1].strip() for item in items} if items else {}

        if "maxReconnectAttempts" not in connection_params:
            connection_params["maxReconnectAttempts"] = DEFAULT_MAX_RECONNECT_ATTEMPTS
        if "startupMaxReconnectAttempts" not in connection_params:
            connection_params["startupMaxReconnectAttempts"] = DEFAULT_STARTUP_MAX_RECONNECT_ATTEMPTS

        self.api_key = username
        self.api_secret = password
        self.stomp_host = [(host, port)]
        self._stomp_client = stomp.StompConnection12(
            self.stomp_host,
            reconnect_attempts_max=-1,
            reconnect_sleep_initial=1,
            reconnect_sleep_increase=3,
            keepalive=True,
            heartbeats=heartbeats,
            heart_beat_receive_scale=2
        )
        self._stomp_client.set_ssl(for_hosts=self.stomp_host, ca_certs=ca_certs)
        self._stomp_client.set_listener("", SOARStompListener(self))

        self.subscribe_list = []

        self.stomp_connection_errors = 0
        self.stomp_max_connection_errors = stomp_max_connection_errors


    @property
    def connected(self):
        return self._stomp_client.is_connected()

    @property
    def socket_connected(self):
        return self.connected

    @property
    def subscribed(self):
        return self.subscribe_list

    @property
    def stomp_logger(self):
        return __name__


    @handler("Connect")
    def connect(self, event, host=None, _subscribe=None):
        """ connect to Stomp server """
        LOG.info("Connect to Stomp...")
        try:
            self._stomp_client.connect(username=self.api_key, passcode=self.api_secret, wait=True, with_connect_command=True)
            # LOG.debug("State after Connection Attempt: %s", self._client.session.state)
            if self.connected:
                LOG.info("Connected to STOMP at %s", self.stomp_host)
                self.fire(Connected())
                self.stomp_connection_errors = 0 # restart counter
                return "success"

        except (stomp.exception.ConnectFailedException, stomp.exception.NotConnectedException) as err:
            LOG.debug(traceback.format_exc())
            # is this error unrecoverable?
            if "no more data" in str(err).lower():
                self.stomp_connection_errors += 1
                if self.stomp_max_connection_errors and self.stomp_connection_errors >= self.stomp_max_connection_errors:
                    LOG.error("Exiting due to unrecoverable error")
                    sys.exit(1) # this will exit resilient-circuits


        # This logic is added to trap the situation where resilient-circuits does not reconnect from a loss of connection
        #   with the resilient server. In these cases, this error is not survivable and it's best to kill resilient-circuits.
        #   If resilient-circuits is running as a service, it will restart and state would clear for a new stomp connection.
        except stomp.exception.StompException:
            LOG.error(traceback.format_exc())
            LOG.error("Exiting due to unrecoverable error")
            sys.exit(1) # this will exit resilient-circuits
        # return "fail"
        event.success = False
        self.fire(ConnectionFailed(self.stomp_host))

    @handler("Disconnect")
    def _disconnect(self, receipt=None, flush=True, reconnect=False):
        try:
            if self.connected:
                self._stomp_client.disconnect(receipt=receipt)
        except stomp.exception.StompException:
            LOG.error("Failed to disconnect client")

        self.fire(Disconnected(reconnect=reconnect))

        return "disconnected"

    @handler("Unsubscribe")
    def _unsubscribe(self, event, destination):
        # if destination not in self._subscribed:
        #     LOG.error("Unsubscribe Request Ignored. Not subscribed to %s", destination)
        #     return
        try:
            # token = self._subscribed.pop(destination)
            self._stomp_client.unsubscribe(destination)
            LOG.debug("Unsubscribed: %s", destination)
        except stomp.exception.StompException:
            event.success = False
            LOG.error("Unsubscribe Failed.")
            # self.fire(OnStompError(frame, err))

    @handler("Subscribe")
    def _subscribe(self, event, destination, additional_headers=None):
        # if destination in self._stomp_client.:
        #     LOG.debug("Ignoring subscribe request to %s. Already subscribed.", destination)
        try:
            headers = {"ack": "client-individual",
                       "id": destination}
            if additional_headers:
                headers.update(additional_headers)

            # Set ID to match destination name for easy reference later
            self._stomp_client.subscribe(destination=destination, id=destination, ack="client-individual", headers=headers)
            self.subscribe_list.append(destination)
            # self._subscribed[destination] = True
        except stomp.exception.StompException as err:
            LOG.error("Failed to subscribe to queue.")
            event.success = False
            LOG.debug(traceback.format_exc())
            self.fire(OnStompError(None, err))
        # This logic is added to trap the situation where resilient-circuits does not reconnect from a loss of connection
        #   with the resilient server. In these cases, this error is not survivable and it's best to kill resilient-circuits.
        #   If resilient-circuits is running as a service, it will restart and state would clear for a new stomp connection.
        except Exception:
            LOG.error(traceback.format_exc())
            LOG.error("Exiting due to unrecoverable error")
            sys.exit(1) # this will exit resilient-circuits

        LOG.info("Subscribed to message destination %s", destination)

    @handler("Ack")
    def ack_frame(self, event, frame):
        LOG.debug("ack_frame()")
        try:
            # TODO figure args for ack
            self._stomp_client.ack(frame.headers.get("ack"))
            LOG.debug("Ack Sent")
        except stomp.exception.StompException as err:
            LOG.error("Error sending ack. %s", err)
            event.success = False
            self.fire(OnStompError(frame, err))
            raise  # To fire Ack_failure event

    @handler("Send")
    def send(self, event, destination, body, headers=None, receipt=None):
        LOG.debug("send()")
        try:
            self._stomp_client.send(destination, body=body.encode("utf-8"), headers=headers, receipt=receipt)
            LOG.debug("Message sent")
        except stomp.exception.StompException as err:
            LOG.error("Error sending frame. %s", err)
            event.success = False
            self.fire(OnStompError(None, err))
            raise  # To fire Send_failure event

    @handler("Message")
    def on_message(self, *_args, **_kwargs):
        # the rest of this logic is handled in actions_component.on_stomp_message
        # which handles the same "Message" event
        LOG.debug("Stomp message received")

class SOARStompListener(stomp.ConnectionListener):

    def __init__(self, component):
        super(SOARStompListener, self).__init__()
        self.component = component

    def on_error(self, frame):
        LOG.info("Received an error '%s'", frame.headers.get("message", "UNKNOWN"))
        if "unable to connect to authentication service" not in frame.headers.get("message", "").lower():
            self.component.fire(OnStompError(frame, frame.body))
        else:
            # ignore "unable to connect to authentication service" error
            # because it just means that ActiveMQ is up, but not authenticatable;
            # stomp client will automatically disconnect and reconnect once the authentication
            # service is back up
            LOG.info("Messaging service is up but authentication service is not. Disconnect to retry...")

    def on_message(self, frame):
        LOG.info("Received message from '%s'", frame.headers.get("reply-to"))
        self.component.fire(Message(frame))

    def on_disconnected(self):
        LOG.error("STOMP disconnected. Firing disconnected event with reconnect=True")
        self.component.fire(Disconnect(reconnect=True))

    def on_connected(self, frame):
        LOG.info("Connected!")

    def on_connecting(self, host_and_port):
        LOG.info("Connecting to '%s'", host_and_port)

    def on_heartbeat_timeout(self):
        LOG.error("Heartbeat timed-out...")
