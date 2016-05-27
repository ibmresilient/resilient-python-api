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

"""Circuits component for Action Module subscription and message handling"""

from circuits import BaseComponent, Event, Timer, Worker
from circuits.core.handlers import handler

import co3
import stomp
from stomp.exception import ConnectFailedException
import ssl
import json
import re
import random
import datetime
from functools import wraps
from resilient_circuits.rest_helper import get_resilient_client, reset_resilient_client
from collections import Callable
import logging
LOG = logging.getLogger(__name__)


STOMP_CLIENT_HEARTBEAT = 0          # no heartbeat from client to server
STOMP_SERVER_HEARTBEAT = 10000      # 10-second heartbeat from server to client
STOMP_TIMEOUT = 120                 # 2-minute socket timeout


def validate_cert(cert, hostname):
    """Utility wrapper for SSL validation on the STOMP connection"""
    try:
        co3.match_hostname(cert, hostname)
    except Exception as exc:
        return (False, str(exc))
    return (True, "Success")


class required_field(object):
    """Decorator, declares a required field for a ResilientComponent or its methods"""
    def __init__(self, fieldname, input_type=None):
        self.fieldname = fieldname
        self.input_type = input_type

    def __call__(self, func):
        """Called at decoration time"""
        # Set or extend the function's "custom_fields" attribute
        func.required_fields = getattr(func, "required_fields", {})
        func.required_fields[self.fieldname] = self.input_type
        # The decorated function is unchanged
        return func


class required_action_field(object):
    """Decorator, declares a required field for a ResilientComponent or its methods"""
    def __init__(self, fieldname, input_type=None):
        self.fieldname = fieldname
        self.input_type = input_type

    def __call__(self, func):
        """Called at decoration time"""
        # Set or extend the function's "action_fields" attribute
        func.required_action_fields = getattr(func, "required_action_fields", {})
        func.required_action_fields[self.fieldname] = self.input_type
        # The decorated function is unchanged
        return func


class defer(object):
    """Decorator for an event handler, delays it awhile"""
    def __init__(self, *args, **kwargs):
        self.delay = kwargs.get("delay", None)
        if len(args) > 0:
            raise Exception("Usage: @defer() or @defer(delay=<seconds>)")

    def __call__(self, func):
        """Called at decoration time, with function"""
        LOG.debug("@defer %s", func)
        @wraps(func)
        def decorated(itself, event, *args, **kwargs):
            LOG.debug("decorated")
            if event.defer(itself, delay=self.delay):
                # OK, let's handle it later
                return
            return func(itself, event, *args, **kwargs)
        return decorated


# Global idle timer, fires after 10 minutes to reset the REST connection
IDLE_TIMER_INTERVAL = 600
_idle_timer = None


class ResilientComponent(BaseComponent):
    """A Circuits base component with a connection to the Resilient REST API

       This is a convenient superclass for custom components that use the
       Resilient Action Module.
    """

    def __init__(self, opts):
        super(ResilientComponent, self).__init__()
        assert isinstance(opts, dict)
        self.opts = opts
        client = self.rest_client()
        self._fields = {field["name"]: field for field in client.get("/types/incident/fields")}
        self._action_fields = {field["name"]: field for field in client.get("/types/actioninvocation/fields")}
        # Check that decorated requirements are met
        callables = ((x, getattr(self, x)) for x in dir(self) if isinstance(getattr(self, x), Callable))
        for name, func in callables:
            if name == "__class__":
                name = func.__name__
            # Do all the custom fields exist?
            fields = getattr(func, "required_fields", {})
            for (field_name, input_type) in fields.items():
                try:
                    fielddef = self._fields[field_name]
                except KeyError:
                    raise Exception("Field '{}' (required by '{}') is not defined in the Resilient appliance.".format(field_name, name))
                if input_type is not None:
                    if fielddef["input_type"] != input_type:
                        raise Exception("Field '{}' (required by '{}') must be type '{}'.".format(field_name, name, input_type))
            # Do all the action fields exist?
            fields = getattr(func, "required_action_fields", {})
            for (field_name, input_type) in fields.items():
                try:
                    fielddef = self._action_fields[field_name]
                except KeyError:
                    raise Exception("Action field '{}' (required by '{}') is not defined in the Resilient appliance.".format(field_name, name))
                if input_type is not None:
                    if fielddef["input_type"] != input_type:
                        raise Exception("Action field '{}' (required by '{}') must be type '{}'.".format(field_name, name, input_type))

    def rest_client(self):
        """Return a connected instance of the Resilient REST SimpleClient"""
        self.reset_idle_timer()
        return get_resilient_client(self.opts)

    def reset_idle_timer(self):
        """Create an idle-timer that we can use to reset the REST connection"""
        global _idle_timer
        if _idle_timer is None:
            LOG.debug("create idle timer")
            _idle_timer = Timer(IDLE_TIMER_INTERVAL, Event.create("idle_reset"), persist=True)
            _idle_timer.register(self)
        else:
            LOG.debug("Reset idle timer")
            _idle_timer.reset()

    def get_incident_field(self, fieldname):
        """Get the definition of an incident-field"""
        return self._fields[fieldname]

    def get_incident_fields(self):
        """Get the definitions of all incident-fields, as a list"""
        return self._fields.values()

    def get_field_label(self, fieldname, value_id):
        """Get the label for an action-field id"""
        field = self._fields[fieldname]
        for value in field["values"]:
            if value["enabled"]:
                if value["value"] == value_id:
                    return value["label"]
        return value_id

    def get_action_field(self, fieldname):
        """Get the definition of an action-field"""
        return self._action_fields[fieldname]

    def get_action_fields(self):
        """Get the definitions of all action-fields, as a list"""
        return self._action_fields.values()

    def get_action_field_label(self, fieldname, value_id):
        """Get the label for an action-field id"""
        field = self._action_fields[fieldname]
        for value in field["values"]:
            if value["enabled"]:
                if value["value"] == value_id:
                    return value["label"]
        return str(value_id)  # fallback


class ActionMessage(Event):
    """A Circuits event for a Resilient Action Module message"""

    # This is a generic event that holds details of the Action Module message,
    # including its context (the incident, task, artifact... where the action
    # was triggered).
    #
    # These events are named by the action that triggered them (lowercased).
    # So a custom action named "Manual Action" will generate an event with name
    # "manual_action".  To handle that event, you should implement a Component
    # that has a method named "manual_action":  the Circuits framework will call
    # your component's methods based on the name of the event.
    #
    # The parameters for your event-handler method are:
    #   event: this event object
    #   source: the component that fired the event
    #   headers: the Action Module message headers (dict)
    #   message: the Action Module message (dict)
    # For convenience, the message is also broken out onto event properties,
    #   event.incident: the incident that the event relates to
    #   event.artifact: the artifact that the event was triggered from (if any)
    #   event.task: the task that the event was triggered from (if any)
    #   (etc).
    #
    # To have your component's method with a different name from the action,
    # you can use the '@handler' decorator:
    #
    #    @handler("the_action_name")
    #    def _any_method_name(self, event, source=None, headers=None, message=None) ...
    #
    # To have a method handle *any* event on the component's channel,
    # use the '@handler' decorator with no event name,
    #
    #    @handler()
    #    def _any_method_name(self, event, source=None, headers=None, message=None) ...

    def __init__(self, source=None, headers=None, message=None):
        super(ActionMessage, self).__init__(source=source, headers=headers, message=message)
        if headers is None:
            headers = {}
        if message is None:
            message = {}
        LOG.debug("Source: %s", source)
        LOG.debug("Headers: %s", json.dumps(headers, indent=2))
        LOG.debug("Message: %s", json.dumps(message, indent=2))

        self.deferred = False
        self.message = message
        self.context = headers.get("Co3ContextToken")
        self.action_id = message.get("action_id")
        self.object_type = message.get("object_type")

        self.timestamp = None
        ts = headers.get("timestamp")
        if ts is not None:
            self.timestamp = datetime.datetime.utcfromtimestamp(float(ts)/1000)

        if source is None:
            # fallback
            self.displayname = "Unknown"
        elif isinstance(source, str):
            # just for testing
            self.displayname = source
        else:
            assert isinstance(source, Actions)
            self.displayname = source.action_name(self.action_id)

        # The name of this event (=the function that subscribers implement)
        # is determined from the name of the action.
        # In future, this should be the action's "programmatic name",
        # but for now it's the downcased displayname with underscores.
        self.name = re.sub(r'\W+', '_', self.displayname.strip().lower())

        # Fire a {name}_success event when this event is successfully processed
        self.success = True

    def __repr__(self):
        "x.__repr__() <==> repr(x)"
        if len(self.channels) > 1:
            channels = repr(self.channels)
        elif len(self.channels) == 1:
            channels = str(self.channels[0])
        else:
            channels = ""
        return "<%s[%s] (%s) %s>" % (self.name, channels, self.action_id, self.timestamp)

    def __getattr__(self, name):
        """Message attributes are made accessible as properties
           ("incident", "task", "note", "milestone". "task", "artifact";
           and "properties" for the action fields on manual actions)
        """
        if name == "message":
            raise AttributeError()
        try:
            return self.message[name]
        except KeyError:
            raise AttributeError()

    def hdr(self):
        """Get the headers (dict)"""
        return self.kwargs["headers"]

    def msg(self):
        """Get the message (dict)"""
        return self.kwargs["message"]

    def defer(self, component, delay=None):
        """Defer this message for handling later"""
        if self.deferred:
            # This message was already deferred.  You should just handle it.
            # (Mark it as no longer deferred, so that it will ack now)
            self.deferred = False
            return False
        # Fire me again after a dela
        if delay is None:
            delay = 0.5 + random.random()
        self.deferred = True
        LOG.debug("Deferring %s (%s)", self, self.hdr().get("message-id"))
        Timer(delay, self).register(component)
        return True


class Actions(ResilientComponent):
    """Component that subscribes to Resilient Action Module queues and fires message events"""

    # Whenever a component in the circuit is registered to a channel name "actions.xxxx",
    # this component will subscribe to the corresponding Action Module queue (xxxx)
    # and then fire events for each message that arrives from the queue.
    # After the message is handled, or fails, it acks the message and updates the action status.

    def __init__(self, opts):
        super(Actions, self).__init__(opts)
        self.listeners = dict()

        # Create a worker pool, for components that choose to use it
        # The default pool uses 10 threads (not processes).
        Worker(process=False, workers=10).register(self)

        # Read the action definitions, into a dict indexed by id
        # we'll refer to them later when dispatching
        rest_client = self.rest_client()
        self.org_id = rest_client.org_id
        list_action_defs = rest_client.get("/actions")["entities"]
        self.action_defs = {int(action["id"]): action for action in list_action_defs}

        # Set up a STOMP connection to the Resilient action services
        host_port = (opts["host"], opts["stomp_port"])
        self.conn = stomp.Connection(host_and_ports=[(host_port)],
                                     heartbeats=(STOMP_CLIENT_HEARTBEAT, STOMP_SERVER_HEARTBEAT),
                                     timeout=STOMP_TIMEOUT,
                                     keepalive=True,
                                     try_loopback_connect=False)

        # Give the STOMP library our TLS/SSL configuration.
        validator = validate_cert
        cert_file = opts.get("cafile")
        if cert_file is None:
            validator = None
        self.conn.set_ssl(for_hosts=[host_port],
                          ca_certs=cert_file,
                          ssl_version=ssl.PROTOCOL_TLSv1,
                          cert_validator=validator)

        # Other special options
        self.ignore_message_failure = opts["resilient"].get("ignore_message_failure") == "1"

        class StompListener(object):
            """A shim for the STOMP callback"""

            def __init__(self, component):
                self.component = component

            def on_error(self, headers, message):
                """STOMP produced an error."""
                self.component.on_stomp_error(headers, message)

            def on_connecting(self, host_and_port):
                pass

            def on_connected(self, headers, message):
                """Client has connected to the STOMP server"""
                self.component.on_stomp_connected(headers, message)

            def on_disconnected(self):
                """Client has disconnected from the STOMP server"""
                self.component.on_stomp_disconnected()

            def on_message(self, headers, message):
                """STOMP produced a message."""
                self.component.on_stomp_message(headers, message)

            def on_heartbeat(self):
                """STOMP heartbeat"""
                pass

            def on_heartbeat_timeout(self):
                """STOMP heartbeat timed out"""
                self.component.on_heartbeat_timeout()

        # When queued events happen, the listener shim will handle them
        self.conn.set_listener('', StompListener(self))

    # Public Utility methods

    def action_name(self, action_id):
        """Get the name of an action, from its id"""
        if action_id is None:
            LOG.warn("Action: None")
            return ""
        try:
            defn = self.action_defs[action_id]
        except KeyError:
            LOG.warn("Action %s is unknown.", action_id)
            # Refresh the list of action definitions
            list_action_defs = self.rest_client().get("/actions")["entities"]
            self.action_defs = {int(action["id"]): action for action in list_action_defs}
            try:
                defn = self.action_defs[action_id]
            except KeyError:
                LOG.exception("Action %s is not defined.", action_id)
                raise

        if defn:
            return defn["name"]

    # STOMP callbacks

    def on_stomp_connected(self, headers, message):
        """Client has connected to the STOMP server"""
        LOG.info("STOMP connected")
        for queue_name in self.listeners:
            self._subscribe(queue_name)

    def on_stomp_disconnected(self):
        """Client has disconnected from the STOMP server"""
        LOG.info("STOMP disconnected!")
        # Set a timer to automatically reconnect
        Timer(5, Event.create("reconnect")).register(self)

    def on_heartbeat_timeout(self):
        """Heartbeat timed out from the STOMP server"""
        LOG.info("STOMP heartbeat timeout!")
        # Set a timer to automatically reconnect
        Timer(5, Event.create("reconnect")).register(self)

    def on_stomp_error(self, headers, message):
        """STOMP produced an error."""
        LOG.error('STOMP listener: Error:\n%s', message)
        # Just raise the event for anyone listening
        self.fire(Event("exception", "Actions", headers.get("message"), message))

    def on_stomp_message(self, headers, message):
        """STOMP produced a message."""
        # Find the queue name from the subscription id (stomp_listener_xxx)
        subscription = headers["subscription"]
        LOG.debug('STOMP listener: message for %s', subscription)
        queue_name = subscription.partition("-")[2]
        channel = "actions." + queue_name

        try:
            # Expect the message payload to always be JSON
            message = json.loads(message)
            # Construct a Circuits event with the message, and fire it on the channel
            event = ActionMessage(self, headers=headers, message=message)
            LOG.info(event)
            self.fire(event, channel)
        except Exception as exc:
            LOG.exception(exc)
            # Normally the event won't be ack'd.  Just report it and carry on.
            if self.ignore_message_failure:
                # Construct and fire anyway, which will ack the message
                LOG.warn("This message failure will be ignored...")
                event = ActionMessage(self, headers=headers, message=None)
                self.fire(event, channel)

    # Circuits event handlers

    @handler("idle_reset")
    def idle_reset(self, event):
        LOG.debug("Idle reset")
        reset_resilient_client()

    @handler("registered")
    def registered(self, event, component, parent):
        """A component has registered.  Subscribe to its message queue(s)."""
        for channel in event.channels:
            if not channel.startswith("actions."):
                continue
            LOG.info("Component %s registered to %s", str(component), channel)
            queue_name = channel.partition(".")[2]
            if queue_name in self.listeners:
                comps = set([component])
                comps.update(self.listeners[queue_name])
                self.listeners[queue_name] = comps
            else:
                self.listeners[queue_name] = set([component])
                # Actually subscribe the STOMP connection
                self._subscribe(queue_name)
            LOG.debug("Listeners: %s", self.listeners)

    @handler("unregistered")
    def unregistered(self, event, component, parent):
        """A component has unregistered.  Unsubscribe its message queue(s)."""
        for channel in event.channels:
            if not channel.startswith("actions."):
                continue
            LOG.info("Component %s unregistered from %s", str(component), channel)
            queue_name = channel.partition(".")[2]
            if queue_name not in self.listeners:
                LOG.error("Channel %s was not subscribed", queue_name)
                continue
            comps = self.listeners[queue_name]
            if component not in comps:
                LOG.error("Component %s was not subscribed", component)
                continue
            comps.remove(component)
            if self.conn.is_connected() and not comps:
                # All components have unsubscribed this destination; stop listening
                self._unsubscribe(queue_name)
            self.listeners[queue_name] = comps
            LOG.debug("Listeners: %s", self.listeners)

    def _subscribe(self, queue_name):
        """Actually subscribe the STOMP queue.  Note: this use client-ack, not auto-ack"""
        if self.conn.is_connected() and self.listeners[queue_name]:
            LOG.info("Subscribe to message destination '%s'", queue_name)
            self.conn.subscribe(id='stomp-{}'.format(queue_name),
                                destination="actions.{}.{}".format(self.org_id, queue_name),
                                ack='client-individual')

    def _unsubscribe(self, queue_name):
        """Unsubscribe the STOMP queue"""
        try:
            if self.conn.is_connected() and self.listeners[queue_name]:
                LOG.info("Unsubscribe from message destination '%s'", queue_name)
                self.conn.unsubscribe(id='stomp-{}'.format(queue_name),
                                      destination="actions.{}.{}".format(self.org_id, queue_name))
        except:
            pass

    @handler("started")
    def started(self, event, component):
        """Started Event Handler"""
        LOG.debug("Started")
        self.reconnect()

    @handler("stopped")
    def stopped(self, event, component):
        """Started Event Handler"""
        LOG.debug("Stopped")
        if self.conn.is_connected():
            for queue_name in self.listeners:
                self._unsubscribe(queue_name)
            self.conn.disconnect()

    @handler("reconnect")
    def reconnect(self):
        """Try (re)connect to the STOMP server"""
        if self.conn.is_connected():
            LOG.error("STOMP reconnect when already connected")
        elif self.opts["resilient"].get("stomp") == "0":
            LOG.info("STOMP connection is not enabled")
        else:
            LOG.info("STOMP attempting to connect")
            try:
                self.conn.start()
                self.conn.connect(login=self.opts["email"], passcode=self.opts["password"])
            except ConnectFailedException:
                # Try again later
                Timer(5, Event.create("reconnect")).register(self)

    @handler("exception")
    def exception(self, etype, value, traceback, handler=None, fevent=None):
        """Report an exception thrown during handling of an action event"""
        LOG.error("%s (%s): %s", repr(fevent), repr(etype), repr(value))
        if fevent and isinstance(fevent, ActionMessage):
            fevent.stop()  # Stop further event processing
            message = str(value or "Processing failed")
            LOG.warn(message)
            status = 1
            headers = fevent.hdr()
            # Ack the message
            message_id = headers['message-id']
            subscription = headers["subscription"]
            LOG.debug("Ack %s", message_id)
            self.conn.ack(message_id, subscription, transaction=None)
            # Reply with error status
            reply_to = headers['reply-to']
            correlation_id = headers['correlation-id']
            reply_message = json.dumps({"message_type": status, "message": message, "complete": True})
            self.conn.send(reply_to, reply_message, headers={'correlation-id': correlation_id})

    @handler()
    def _on_event(self, event, *args, **kwargs):
        """Report the successful handling of an action event"""
        if isinstance(event.parent, ActionMessage) and event.name.endswith("_success"):
            fevent = event.parent
            if fevent.deferred:
                LOG.debug("Not acking deferred message %s", str(fevent))
            else:
                value = event.parent.value
                LOG.debug("success! %s, %s", str(value), str(fevent))
                fevent.stop()  # Stop further event processing
                message = str(value or "Processing complete")
                LOG.debug("Message: %s", message)
                status = 0
                headers = fevent.hdr()
                # Ack the message
                message_id = headers['message-id']
                subscription = headers["subscription"]
                LOG.debug("Ack %s", message_id)
                self.conn.ack(message_id, subscription, transaction=None)
                # Reply with success status
                reply_to = headers['reply-to']
                correlation_id = headers['correlation-id']
                reply_message = json.dumps({"message_type": status, "message": message, "complete": True})
                self.conn.send(reply_to, reply_message, headers={'correlation-id': correlation_id})
