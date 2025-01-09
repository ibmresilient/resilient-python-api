# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Circuits component for handling Stomp Connection """

import logging
import sys
import traceback

import stomp
from circuits import BaseComponent
from circuits.core.handlers import handler

from resilient_circuits import constants
from resilient_circuits.stomp_events import (Connected, ConnectionFailed,
                                             Disconnect, Disconnected, Message,
                                             OnStompError)

DEFAULT_MAX_RECONNECT_ATTEMPTS = 3
DEFAULT_STARTUP_MAX_RECONNECT_ATTEMPTS = 3

LOG = logging.getLogger(__name__)


class StompClient(BaseComponent):
    """
    STOMP Component. Implements the circuits base component and is registered to the component
    tree to handle events, mostly those events fired from Action component.

    Uses the stomp.py library to implement STOMP connections. The SOARStompListener implements
    the events triggered by the stomp.py library to handle stomp events from the server.
    """

    channel = "stomp"

    def __init__(self, *args, **kwargs):
        # define all class variables with initials here, to be actually filled in the 'init' method
        self._subscribed = {}
        self._stomp_connection_errors = 0
        self._stomp_max_connection_errors = None
        self._api_key = None
        self._api_secret = None
        self._stomp_host = tuple()
        self._stomp_client = None

        # call to super.__init__ must happen at the end so that 'init' method is called
        # from BaseComponent constructor
        super(StompClient, self).__init__(*args, **kwargs)

    def init(self, host, port,
             *_args,
             username=None, password=None,
             heartbeats=(0, 0),
             ca_certs=None,
             connect_timeout=120,
             stomp_max_connection_errors=constants.STOMP_MAX_CONNECTION_ERRORS,
             heart_beat_receive_scale=2,
             **_kwargs):


        # connect timeout has to be greater than the heartbeat scale
        # multiplied by the heartbeat for server. otherwise we would get
        # continuous timeouts on connect (see https://github.com/jasonrbriggs/stomp.py/issues/366)
        heart_beat_true_seconds = heart_beat_receive_scale * heartbeats[1]/1000 # divide by 1000 to get seconds
        if heart_beat_true_seconds > connect_timeout:
            LOG.warning("'stomp_timeout' set to a value lower than heartbeats")
            connect_timeout = 1.5 * heart_beat_true_seconds # 1.5 scale here to be sure in the clear
            LOG.info("Automatically adjusting STOMP timeout to '%s' so that it fits outside of heartbeats", connect_timeout)

        self._subscribed = {}

        self._stomp_connection_errors = 0
        self._stomp_max_connection_errors = stomp_max_connection_errors

        self._api_key = username
        self._api_secret = password
        self._stomp_host = [(host, port)]


        LOG.info("Connect to STOMP at '%s:%s'", host, port)
        self._stomp_client = stomp.StompConnection12(
            self._stomp_host,
            reconnect_attempts_max=-1,
            reconnect_sleep_initial=1,
            reconnect_sleep_increase=3,
            timeout=connect_timeout,
            keepalive=True,
            heartbeats=heartbeats,
            heart_beat_receive_scale=2
        )
        LOG.debug("Set SSL for STOMP client for hosts '%s' and certs '%s'", self._stomp_host, ca_certs)
        self._stomp_client.set_ssl(for_hosts=self._stomp_host, ca_certs=ca_certs)
        self._stomp_client.set_listener("", SOARStompListener(self))


    @property
    def connected(self):
        return self._stomp_client.is_connected()

    @property
    def subscribed(self):
        return self._subscribed


    @handler("Connect")
    def connect(self, event, host=None, _subscribe=None):
        """ connect to Stomp server """
        LOG.info("Connect to STOMP...")
        try:
            self._stomp_client.connect(
                username=self._api_key,
                passcode=self._api_secret,
                wait=True,
                with_connect_command=True
            )
            # LOG.debug("State after Connection Attempt: %s", self._client.session.state)
            if self.connected:
                LOG.info("Connected to STOMP at %s", self._stomp_host)
                self.fire(Connected())
                self._stomp_connection_errors = 0 # restart counter
                return "success"

        except (stomp.exception.ConnectFailedException, stomp.exception.NotConnectedException) as err:
            LOG.debug(traceback.format_exc())
            # Since switching to stomp.py library, this error hasn't been seen
            # but we're keeping around just in case it pops up somewhere...
            if "no more data" in str(err).lower():
                self._stomp_connection_errors += 1
                if self._stomp_max_connection_errors and self._stomp_connection_errors >= self._stomp_max_connection_errors:
                    LOG.error("Exiting due to unrecoverable error")
                    sys.exit(1) # this will exit resilient-circuits


        # This logic is added to trap the situation where resilient-circuits does not reconnect from a loss of connection
        #   with the resilient server. In these cases, this error is not survivable and it's best to kill resilient-circuits.
        #   If resilient-circuits is running as a service, it will restart and state would clear for a new stomp connection.
        except stomp.exception.StompException:
            LOG.error(traceback.format_exc())
            LOG.error("Exiting due to unrecoverable error")
            sys.exit(1) # this will exit resilient-circuits

        event.success = False
        self.fire(ConnectionFailed(self._stomp_host))
        return "fail"

    @handler("Disconnect")
    def _disconnect(self, receipt=None, flush=True, reconnect=False):
        try:
            if flush:
                self._subscribed = {}
            if self.connected:
                self._stomp_client.disconnect(receipt=receipt)
        except stomp.exception.StompException:
            LOG.error("Failed to disconnect client")

        self.fire(Disconnected(reconnect=reconnect))

        return "disconnected"

    @handler("Unsubscribe")
    def _unsubscribe(self, event, destination):
        if destination not in self._subscribed:
            LOG.error("Unsubscribe request ignored. Not subscribed to '%s'", destination)
            return
        try:
            self._stomp_client.unsubscribe(destination)
            self._subscribed.pop(destination)
            LOG.debug("Unsubscribed: %s", destination)
        except stomp.exception.StompException:
            event.success = False
            LOG.error("Unsubscribe Failed.")
            # self.fire(OnStompError(frame, err))

    @handler("Subscribe")
    def _subscribe(self, event, destination, additional_headers=None):
        if destination in self._subscribed:
            LOG.debug("Ignoring subscribe request to %s. Already subscribed.", destination)
        try:
            headers = {"ack": "client-individual",
                       "id": destination}
            if additional_headers:
                headers.update(additional_headers)

            # Set ID to match destination name for easy reference later
            self._stomp_client.subscribe(destination=destination, id=destination, ack="client-individual", headers=headers)
            self._subscribed[destination] = True
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
        LOG.debug("STOMP message received")

class SOARStompListener(stomp.ConnectionListener):

    def __init__(self, component):
        super(SOARStompListener, self).__init__()
        self.component = component

        LOG.debug("STOMP listener initiated and listening for STOMP events")

    def on_error(self, frame):
        LOG.info("Received an error '%s'", frame.headers.get("message", "UNKNOWN"))
        if "unable to connect to authentication service" not in frame.headers.get("message", "").lower():
            self.component.fire(OnStompError(frame, frame.body))
        else:
            # ignore "unable to connect to authentication service" error
            # because it just means that ActiveMQ is up, but not authenticatable;
            # stomp client will automatically disconnect and reconnect once the authentication
            # service is back up
            LOG.warning("Messaging service is up but authentication service is not. Disconnect to retry...")

    def on_message(self, frame):
        LOG.debug("STOMP received message from destination: '%s'", frame.headers.get("reply-to") or frame.headers.get("subscription"))
        self.component.fire(Message(frame))

    def on_disconnected(self):
        LOG.error("STOMP disconnected. Firing disconnected event with reconnect=True")
        self.component.fire(Disconnect(reconnect=True))

    def on_connected(self, frame):
        LOG.debug("STOMP connected!")

    def on_connecting(self, host_and_port):
        LOG.debug("STOMP connecting to '%s'", host_and_port)

    def on_heartbeat(self):
        LOG.debug("STOMP heartbeat received")

    def on_heartbeat_timeout(self):
        LOG.error("STOMP heartbeat timed-out...")
