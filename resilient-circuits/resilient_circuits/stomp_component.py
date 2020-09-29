# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

""" Circuits component for handling Stomp Connection """

import logging
import ssl
import time
import sys
import traceback
from circuits import BaseComponent, Timer
from circuits.core.handlers import handler
from stompest.config import StompConfig
from stompest.protocol import StompSpec, StompSession
from stompest.sync import Stomp
from stompest.error import StompConnectionError, StompError, StompProtocolError
from stompest.sync.client import LOG_CATEGORY
from resilient_circuits.stomp_events import *
from resilient_circuits.stomp_transport import EnhancedStompFrameTransport


StompSpec.DEFAULT_VERSION = '1.2'
ACK_CLIENT_INDIVIDUAL = StompSpec.ACK_CLIENT_INDIVIDUAL
ACK_AUTO = StompSpec.ACK_AUTO
ACK_CLIENT = StompSpec.ACK_CLIENT
ACK_MODES = (ACK_CLIENT_INDIVIDUAL, ACK_AUTO, ACK_CLIENT)

DEFAULT_MAX_RECONNECT_ATTEMPTS = 3
DEFAULT_STARTUP_MAX_RECONNECT_ATTEMPTS = 3

LOG = logging.getLogger(__name__)


class StompClient(BaseComponent):

    channel = "stomp"

    def init(self, host, port, username=None, password=None,
             connect_timeout=3, connected_timeout=3,
             version=StompSpec.VERSION_1_2, accept_versions=["1.0", "1.1", "1.2"],
             heartbeats=(0, 0), ssl_context=None,
             use_ssl=True,
             key_file=None,
             cert_file=None,
             ca_certs=None,
             ssl_version=ssl.PROTOCOL_SSLv23,  # means 'latest available'
             key_file_password=None,
             proxy_host=None,
             proxy_port=None,
             proxy_user=None,
             proxy_password=None,
             channel=channel,
             stomp_params=None):
        """ Initialize StompClient.  Called after __init__ """
        self.channel = channel
        if proxy_host:
            LOG.info("Connect to %s:%s through proxy %s:%d", host, port, proxy_host, proxy_port)
        else:
            LOG.info("Connect to %s:%s", host, port)

        if use_ssl and not ssl_context:

            ssl_params = dict(key_file=key_file,
                              cert_file=cert_file,
                              ca_certs=ca_certs,
                              ssl_version=ssl_version,
                              password=key_file_password)
            LOG.info("Request to use old-style socket wrapper: %s", ssl_params)
            ssl_context = ssl_params

        if use_ssl:
            uri = "ssl://%s:%s" % (host, port)
        else:
            uri = "tcp://%s:%s" % (host, port)

        # Configure failover options so it only tries based on settings
        # build any parameters passed
        # every connection has at least these two: maxReconnectAttempts, startupMaxReconnectAttempts
        items = [item.split("=", 2) for item in stomp_params.split(",")] if stomp_params else None
        connection_params = {item[0].strip():item[1].strip() for item in items} if items else {}

        if "maxReconnectAttempts" not in connection_params:
            connection_params['maxReconnectAttempts'] = DEFAULT_MAX_RECONNECT_ATTEMPTS
        if "startupMaxReconnectAttempts" not in connection_params:
            connection_params['startupMaxReconnectAttempts'] = DEFAULT_STARTUP_MAX_RECONNECT_ATTEMPTS

        self._stomp_server = "failover:({0})?{1}".format(uri, ",".join(["{}={}".format(k, v) for k, v in connection_params.items()]))
        LOG.debug("Stomp uri: {}".format(self._stomp_server))

        self._stomp_config = StompConfig(uri=self._stomp_server, sslContext=ssl_context,
                                         version=version,
                                         login=username,
                                         passcode=password)

        self._heartbeats = heartbeats
        self._accept_versions = accept_versions
        self._connect_timeout = connect_timeout
        self._connected_timeout = connected_timeout
        Stomp._transportFactory = EnhancedStompFrameTransport
        Stomp._transportFactory.proxy_host = proxy_host
        Stomp._transportFactory.proxy_port = proxy_port
        Stomp._transportFactory.proxy_user = proxy_user
        Stomp._transportFactory.proxy_password = proxy_password
        self._client = Stomp(self._stomp_config)
        self._subscribed = {}
        self.server_heartbeat = None
        self.client_heartbeat = None
        self.last_heartbeat = 0
        self.ALLOWANCE = 2  # multiplier for heartbeat timeouts

    @property
    def connected(self):
        if self._client.session:
            return self._client.session.state == StompSession.CONNECTED
        else:
            return False

    @property
    def socket_connected(self):
        try:
            if self._client._transport:
                return True
        except:
            pass
        return False

    @property
    def subscribed(self):
        return self._subscribed.keys()

    @property
    def stomp_logger(self):
        return LOG_CATEGORY

    @handler("Disconnect")
    def _disconnect(self, receipt=None, flush=True, reconnect=False):
        try:
            if flush:
                self._subscribed = {}
            if self.connected:
                self._client.disconnect(receipt=receipt)
        except Exception as e:
            LOG.error("Failed to disconnect client")
        try:
            self.fire(Disconnected(reconnect=reconnect))
            self._client.close(flush=flush)
        except Exception as e:
            LOG.error("Failed to close client connection")

        return "disconnected"

    def start_heartbeats(self):
        LOG.info("Client HB: %s  Server HB: %s", self._client.clientHeartBeat, self._client.serverHeartBeat)
        if self._client.clientHeartBeat:
            if self.client_heartbeat:
                # Timer already exists, just reset it
                self.client_heartbeat.reset()
            else:
                LOG.info("Client will send heartbeats to server")
                # Send heartbeats at 80% of agreed rate
                self.client_heartbeat = Timer((self._client.clientHeartBeat / 1000.0) * 0.8,
                                              ClientHeartbeat(), persist=True)
                self.client_heartbeat.register(self)
        else:
            LOG.info("No Client heartbeats will be sent")

        if self._client.serverHeartBeat:
            if self.server_heartbeat:
                # Timer already exists, just reset it
                self.server_heartbeat.reset()
            else:
                LOG.info("Requested heartbeats from server.")
                # Allow a grace period on server heartbeats
                self.server_heartbeat = Timer((self._client.serverHeartBeat / 1000.0) * self.ALLOWANCE,
                                              ServerHeartbeat(), persist=True)
                self.server_heartbeat.register(self)
        else:
            LOG.info("Expecting no heartbeats from Server")

    @handler("Connect")
    def connect(self, event, host=None, *args, **kwargs):
        """ connect to Stomp server """
        LOG.info("Connect to Stomp...")
        try:
            self._client.connect(heartBeats=self._heartbeats,
                                 host=host,
                                 versions=self._accept_versions,
                                 connectTimeout=self._connect_timeout,
                                 connectedTimeout=self._connected_timeout)
            LOG.debug("State after Connection Attempt: %s", self._client.session.state)
            if self.connected:
                LOG.info("Connected to %s", self._stomp_server)
                self.fire(Connected())
                self.start_heartbeats()
                return "success"

        except StompConnectionError as err:
            LOG.debug(traceback.format_exc())
            self.fire(ConnectionFailed(self._stomp_server))
            event.success = False
        # This logic is added to trap the situation where resilient-circuits does not reconnect from a loss of connection
        #   with the resilient server. In these cases, this error is not survivable and it's best to kill resilient-circuits.
        #   If resilient-circuits is running as a service, it will restart and state would clear for a new stomp connection.
        except StompProtocolError as err:
            LOG.error(traceback.format_exc())
            LOG.error("Exiting due to unrecoverable error")
            sys.exit(1) # this will exit resilient-circuits
        return "fail"

    @handler("ServerHeartbeat")
    def check_server_heartbeat(self, event):
        """ Confirm that heartbeat from server hasn't timed out """
        now = time.time()
        self.last_heartbeat = self._client.lastReceived or self.last_heartbeat
        if self.last_heartbeat:
            elapsed = now-self.last_heartbeat
        else:
            elapsed = -1
        if ((self._client.serverHeartBeat / 1000.0) * self.ALLOWANCE + self.last_heartbeat) < now:
            LOG.error("Server heartbeat timeout. %d seconds since last heartbeat.", elapsed)
            event.success = False
            self.fire(HeartbeatTimeout())

    @handler("ClientHeartbeat")
    def send_heartbeat(self, event):
        if self.connected:
            LOG.debug("Sending heartbeat")
            try:
                self._client.beat()
            except (StompConnectionError, StompError) as err:
                event.success = False
                self.fire(OnStompError(None, err))

    @handler("generate_events")
    def generate_events(self, event):
        event.reduce_time_left(0.1)
        if not self.connected:
            return
        try:
            if self._client.canRead(0):
                frame = self._client.receiveFrame()
                LOG.debug("Recieved frame %s", frame)
                if frame.command == StompSpec.ERROR:
                    self.fire(OnStompError(frame, None))
                else:
                    self.fire(Message(frame))
        except (StompConnectionError, StompError) as err:
            LOG.error("Failed attempt to generate events.")
            self.fire(OnStompError(None, err))

    @handler("Send")
    def send(self, event, destination, body, headers=None, receipt=None):
        LOG.debug("send()")
        try:
            self._client.send(destination, body=body.encode('utf-8'), headers=headers, receipt=receipt)
            LOG.debug("Message sent")
        except (StompConnectionError, StompError) as err:
            LOG.error("Error sending frame")
            event.success = False
            self.fire(OnStompError(None, err))
            raise  # To fire Send_failure event

    @handler("Subscribe")
    def _subscribe(self, event, destination, additional_headers=None, ack=ACK_CLIENT_INDIVIDUAL):
        if ack not in ACK_MODES:
            raise ValueError("Invalid client ack mode specified")
        if destination in self._client.session._subscriptions:
            LOG.debug("Ignoring subscribe request to %s. Already subscribed.", destination)
        LOG.info("Subscribe to message destination %s", destination)
        try:
            headers = {StompSpec.ACK_HEADER: ack,
                       'id': destination}
            if additional_headers:
                headers.update(additional_headers)

            # Set ID to match destination name for easy reference later
            frame, token = self._client.subscribe(destination,
                                                  headers)
            self._subscribed[destination] = token
        except (StompConnectionError, StompError) as err:
            LOG.error("Failed to subscribe to queue.")
            event.success = False
            LOG.debug(traceback.format_exc())
            self.fire(OnStompError(None, err))
        # This logic is added to trap the situation where resilient-circuits does not reconnect from a loss of connection
        #   with the resilient server. In these cases, this error is not survivable and it's best to kill resilient-circuits.
        #   If resilient-circuits is running as a service, it will restart and state would clear for a new stomp connection.
        except StompProtocolError as err:
            LOG.error(traceback.format_exc())
            LOG.error("Exiting due to unrecoverable error")
            sys.exit(1) # this will exit resilient-circuits

    @handler("Unsubscribe")
    def _unsubscribe(self, event, destination):
        if destination not in self._subscribed:
            LOG.error("Unsubscribe Request Ignored. Not subscribed to %s", destination)
            return
        try:
            token = self._subscribed.pop(destination)
            frame = self._client.unsubscribe(token)
            LOG.debug("Unsubscribed: %s", frame)
        except (StompConnectionError, StompError) as err:
            event.success = False
            LOG.error("Unsubscribe Failed.")
            self.fire(OnStompError(frame, err))

    @handler("Message")
    def on_message(self, event, headers, message):
        LOG.debug("Stomp message received")

    @handler("Ack")
    def ack_frame(self, event, frame):
        LOG.debug("ack_frame()")
        try:
            self._client.ack(frame)
            LOG.debug("Ack Sent")
        except (StompConnectionError, StompError) as err:
            LOG.error("Error sending ack")
            event.success = False
            self.fire(OnStompError(frame, err))
            raise  # To fire Ack_failure event

    def get_subscription(self, frame):
        """ Get subscription from frame """
        _, token = self._client.message(frame)
        return self._subscribed[token]
