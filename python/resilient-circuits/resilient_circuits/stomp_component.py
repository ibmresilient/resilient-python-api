# -*- coding: utf-8 -*-
""" Circuits component for handling Stomp Connection """

import json
import logging
import ssl
import time
import traceback
from signal import SIGINT, SIGTERM
from circuits import Component, Event, Timer
from circuits.io.events import ready
from circuits.core.utils import findcmp
from circuits.core.handlers import handler
from stompest.config import StompConfig
from stompest.protocol import StompSpec, StompSession
from stompest.sync import Stomp
from stompest.error import StompConnectionError, StompError
from stompest.sync.client import LOG_CATEGORY
from .stomp_events import *

logging.getLogger(LOG_CATEGORY).setLevel(logging.DEBUG)

StompSpec.DEFAULT_VERSION = '1.1'
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

class StompClient(Component):

    def init(self, host, port, username=None, password=None,
             connect_timeout=3, connected_timeout=3,
             version=StompSpec.VERSION_1_2, accept_versions=["1.0", "1.1", "1.2"],
             heartbeats=(0, 0), ssl_context=None):
        """ Initialize StompClient.  Called after __init__ """
        if ssl_context:
            self._stomp_server = 'ssl://%s:%s' % (host, port)
        else:
            self._stomp_server = 'stomp://%s:%s' % (host, port)

        self._stomp_config = StompConfig(self._stomp_server, sslContext=ssl_context,
                             version=version,
                             login=username,
                             passcode=password)

        self._heartbeats = heartbeats
        self._accept_versions = accept_versions
        self._connect_timeout = connect_timeout
        self._connected_timeout = connected_timeout
        self._client = Stomp(self._stomp_config)
        self._subscribed = {}
        self.server_heartbeat = None
        self.client_heartbeat = None
        self.ALLOWANCE = 3 # multiplier for heartbeat timeouts

    @property
    def connected(self):
        if self._client.session:
            return self._client.session.state == StompSession.CONNECTED
        else:
            return False

    @handler("Disconnect")
    def _disconnect(self):
        if self.connected:
            self._client.disconnect()
        self._client.close(flush=True)
        self.fire(DisconnectedEvent())
        self._subscribed = {}


    def start_heartbeats(self):
        LOG.info("Client HB: %s  Server HB: %s", self._client.clientHeartBeat, self._client.serverHeartBeat)
        if self._client.clientHeartBeat:
            if self.client_heartbeat:
                # Timer already exists, just reset it
                self.client_heartbeat.reset()
            else:
                LOG.info("Client will send heartbeats to server")
                # Send heartbeats at 80% of minimum rate
                self.client_heartbeat = Timer((self._client.clientHeartBeat / 1000.0) * 0.8,
                                     Event.create("ClientHeartbeat"), persist=True)
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
                                              Event.create("ServerHeartbeat"), persist=True)
                self.server_heartbeat.register(self)
        else:
            LOG.info("Expecting no heartbeats from Server")

    @handler("Connect")
    def connect(self):
        """ connect to Stomp server """
        try:
            self._client.connect(heartBeats=self._heartbeats,
                                 versions=self._accept_versions,
                                 connectTimeout=self._connect_timeout,
                                 connectedTimeout=self._connected_timeout)
            LOG.info("State after Connection Attempt: %s", self._client.session.state)
            if self.connected:
                LOG.info("Connected to %s", self._stomp_server)
                self.fire(Connected())
                self.start_heartbeats()

        except StompConnectionError as err:
            LOG.debug(traceback.format_exc())
            self.fire(ConnectionFailed(self._stomp_server))

    @handler("ServerHeartbeat")
    def check_server_heartbeat(self):
        """ Confirm that heartbeat from server hasn't timed out """
        now = time.time()
        last = self._client.lastReceived or 0
        if last:
            elapsed = now-last
        else:
            elapsed = -1
        LOG.debug("Last received data %d seconds ago", elapsed)
        if ((self._client.serverHeartBeat / 1000.0) * self.ALLOWANCE + last) < now:
            LOG.error("Server heartbeat timeout. %d seconds since last heartbeat.  Disconnecting.", elapsed)
            #self.fire(HeartbeatTimeout())
            #if self.connected:
            #    self._client.disconnect()
            # TODO: Try to auto-reconnect?

    @handler("ClientHeartbeat")
    def send_heartbeat(self):
        if self.connected:
            LOG.debug("Sending heartbeat")
            try:
                self._client.beat()
            except StompConnectionError as err:
                self.fire(DisconnectedEvent())

    @handler("generate_events")
    def generate_events(self, event):
        if not self.connected:
            return
        try:
            if self._client.canRead(1):
                LOG.info("There is data to read from Stomp")
                frame = self._client.receiveFrame()
                LOG.debug("Recieved frame %s", frame)
                self.fire(MessageEvent(frame))
        except StompConnectionError as err:
            self.fire(DisconnectedEvent())

    @handler("Send")
    def send(self, destination, body, headers=None, receipt=None):
        LOG.debug("send()")
        if not self.connected:
            LOG.error("Can't send when Stomp is disconnected")
            return
        try:
            self._client.send(destination, body=body, headers=headers, receipt=receipt)
            LOG.debug("Message sent")
        except StompConnectionError as err:
            self.fire(DisconnectedEvent())
        except StompError as err:
            LOG.error("Error sending ack")
            self.fire(StompErrorEvent(None, err))

    @handler("Subscribe")
    def _subscribe(self, destination):
        LOG.info("Subscribe to message destination %s", destination)
        try:
            # Set ID to match destination name for easy reference later
            frame, token = self._client.subscribe(destination,
                                                  headers={StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                                                           'id': destination})
            self._subscribed[destination] = token
            LOG.debug("Subscribed: %s %s", frame, token)
        except StompConnectionError as err:
            self.fire(DisconnectedEvent())
        except StompError as err:
            LOG.debug(traceback.format_exc())
            self.fire(StompErrorEvent(None, err))

    @handler("Unsubscribe")
    def _unsubscribe(self, destination):
        if destination not in self._subscribed:
            LOG.error("Unsubscribe Request Ignored. Not subscribed to %s", destination)
            return
        try:
            token = self._subscribed.pop(destination)
            frame = self._client.unsubscribe(token)
            LOG.debug("Unsubscribed: %s", frame)
        except StompConnectionError as err:
            self.fire(DisconnectedEvent())
        except StompError as err:
            LOG.error("Error sending ack")
            self.fire(StompErrorEvent(frame, err))


    @handler("MessageEvent")
    def on_message(self, event, headers, message):
        LOG.info("Got a Message from Stomp! %s", message)

    @handler("Ack")
    def ack_frame(self, frame):
        LOG.debug("ack_frame()")
        try:
            self._client.ack(frame)
            LOG.debug("Ack Sent")
        except StompConnectionError as err:
            LOG.error("Error sending ack")
            self.fire(DisconnectedEvent())
        except StompError as err:
            LOG.error("Error sending ack")
            self.fire(StompErrorEvent(frame, err))

    def get_subscription(self, frame):
        """ Get subscription from frame """
        LOG.info(self._subscribed)
        _, token = self._client.message(frame)
        return self._subscribed[token]


def main():
    logging.basicConfig()
    # Configure and "run" the System.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    StompClient("192.168.56.101", 65001,
                username="kchurch@us.ibm.com",
                password="Pass4Admin",
                heartbeats=(10000, 10000),
                ssl_context=context).run()


if __name__ == "__main__":
    main()
