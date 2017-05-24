# -*- coding: utf-8 -*-

"""Circuits component for Action Module subscription and message handling"""

import ssl
import json
import logging
import os.path
import traceback
from collections import Callable
from signal import SIGINT, SIGTERM
from functools import wraps
import stomp
from stomp.exception import ConnectFailedException
from circuits import BaseComponent, Event, Timer
from circuits.core.handlers import handler
import circuits.six as six
from requests.utils import DEFAULT_CA_BUNDLE_PATH
import co3
import resilient_circuits.actions_test_component as actions_test_component
from resilient_circuits.rest_helper import get_resilient_client, reset_resilient_client
from resilient_circuits.action_message import ActionMessage
from resilient_circuits.stomp_component import StompClient
from resilient_circuits.stomp_events import *

LOG = logging.getLogger(__name__)

STOMP_CLIENT_HEARTBEAT = 0          # no heartbeat from client to server
STOMP_SERVER_HEARTBEAT = 15000      # 15-second heartbeat from server to client
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
        func.required_action_fields = getattr(func,
                                              "required_action_fields", {})
        func.required_action_fields[self.fieldname] = self.input_type
        # The decorated function is unchanged
        return func


class defer(object):
    """Decorator for an event handler, delays it awhile.

       Usage:
       Decorate a Resilient Circuits handler.
       This decorator should go *before* the '@handler(...)'.
       Do not use on 'generic' handlers, only on named-event handlers.

            @defer(delay=5)
            @handler("actions_event_name")
            def _function(self, event, *args, **kwargs):
                # handle the event
                pass
    """
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


def debounce_get_incident_key(event):
    """Callback to return the debounce-key for an event.
       Multiple events with this key will be debounced together.
       Default is: event name and incident id.
    """
    key = "{} for {}".format(event.name, event.message["incident"]["id"])
    return key


class debounce(object):
    """Decorator for an event handler, debounces multiple occurrences.

       Parameters:
           delay= (seconds).  Time before the event will be processed.
                  If another event (with the same key) occurs in this
                  time, the timer starts over.
           discard= (Boolean, optional).  If true, when there are multiple
                  events before the delay expires, only the most recent one
                  is processed, and the previous ones are discarded.

       Usage:
       Decorate a Resilient Circuits handler.
       This decorator should go *before* the '@handler(...)'.
       Do not use on 'generic' handlers, only on named-event handlers.

            @debounce(delay=10, discard=True)
            @handler("actions_event_name")
            def _function(self, event, *args, **kwargs):
                # handle the event
                pass
    """
    def __init__(self, *args, **kwargs):
        self.delay = kwargs.get("delay", 1)
        self.discard = kwargs.get("discard", False)
        self.get_key = kwargs.get("get_key_func", debounce_get_incident_key)
        self.debouncedata = {}
        if len(args) > 0:
            raise Exception("Usage: @debounce(delay=<seconds>, [discard=True])")

    def __call__(self, func):
        """Called at decoration time, with function"""
        LOG.debug("@debounce %s", func)

        @wraps(func)
        def decorated(itself, event, *args, **kwargs):
            LOG.debug("decorated")
            # De-bounce messages for this event and the same key:
            # (key is the incident-id, by default):
            # - Don't handle the message immediately.
            #   - Note that we have a deferred event.
            #   - Defer it for <<delay>>.
            # - If an event arrives and there is any deferred message,
            #   - Reset the timer interval to <<delay>>
            #   - Optionally: throw away the new message.
            #     Otherwise: defer this one too (to be processed
            #     immediately after the first deferred message).
            key = self.get_key(event)
            if event.deferred:
                # We deferred this event earlier,
                # and now it has fired without being reset in the meantime.
                # All the pending events are OK to go!  Forget their timers!
                LOG.info("Handling deferred %s", key)
                event.deferred = False
                self.debouncedata.pop(key, None)
            else:
                # This is a new event.
                # Are there any other deferred events for this [action+incident]?
                if key not in self.debouncedata:
                    # We'll keep a list of all the timers
                    self.debouncedata[key] = []
                else:
                    # Duplicate event
                    if self.discard:
                        # Unregister all the previous timers so they don't fire
                        for timer in self.debouncedata[key]:
                            evt = timer.event
                            LOG.debug("Unregister timer")
                            timer.unregister()
                            if evt:
                                # The timer's event will not fire now.
                                # Mark it as not 'deferred' and fire a 'success' child event
                                # so that it gets ack'd to the message queue.
                                LOG.debug("Fire success")
                                evt.deferred = False
                                channels = getattr(evt, "success_channels", evt.channels)
                                itself.fire(evt.child("success", evt, evt.value.value), *channels)
                        # Now we can get rid of the list of timers
                        self.debouncedata[key] = []
                    else:
                        # Reset all the pending timers
                        for timer in self.debouncedata[key]:
                            timer.reset(interval=self.delay)
                # Defer this new event with a timer.
                LOG.info("Deferring %s", key)
                timer = Timer(self.delay, event)
                timer.register(itself)
                event.deferred = True
                # Remember the new timer so that we can reset it if necessary
                self.debouncedata[key].append(timer)
                # We're done until the timer fires
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
    test_mode = False  # True with --test-actions option

    def __init__(self, opts):
        super(ResilientComponent, self).__init__()
        assert isinstance(opts, dict)
        self.opts = opts
        self._get_fields()
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
                    errmsg = ("Field '{0}' (required by '{1}') is not "
                              "defined in the Resilient appliance.")
                    raise Exception(errmsg.format(field_name, name))
                if input_type is not None:
                    if fielddef["input_type"] != input_type:
                        errmsg = ("Field '{0}' (required by '{1}') "
                                  "must be type '{2}'.")
                        raise Exception(errmsg.format(field_name,
                                                      name, input_type))
            # Do all the action fields exist?
            fields = getattr(func, "required_action_fields", {})
            for (field_name, input_type) in fields.items():
                try:
                    fielddef = self._action_fields[field_name]
                except KeyError:
                    errmsg = ("Action field '{0}' (required by '{1}') "
                              "is not defined in the Resilient appliance.")
                    raise Exception(errmsg.format(field_name, name))
                if input_type is not None:
                    if fielddef["input_type"] != input_type:
                        errmsg = ("Action field '{0}' (required by "
                                  "'{1}') must be type '{2}'.")
                        raise Exception(errmsg.format(field_name,
                                                      name, input_type))

    def _get_fields(self):
        """Get Incident and Action fields"""
        client = self.rest_client()
        self._fields = dict((field["name"], field) for field in client.get("/types/incident/fields"))
        self._action_fields = dict((field["name"], field) for field in client.get("/types/actioninvocation/fields"))

    def rest_client(self):
        """Return a connected instance of the Resilient REST SimpleClient"""
        self.reset_idle_timer()
        return get_resilient_client(self.opts)

    def reset_idle_timer(self):
        """Create an idle-timer that we can use to reset the REST connection"""
        global _idle_timer
        if _idle_timer is None:
            LOG.debug("create idle timer")
            _idle_timer = Timer(IDLE_TIMER_INTERVAL,
                                Event.create("idle_reset"), persist=True)
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

    @handler("reload")
    def reload(self, event, opts):
        """New set of config options"""
        self.opts = opts
        self._get_fields()

class Actions(ResilientComponent):
    """Component that subscribes to Resilient Action Module queues and fires message events"""

    # Whenever a component in the circuit is registered to a channel name "actions.xxxx",
    # this component will subscribe to the corresponding Action Module queue (xxxx)
    # and then fire events for each message that arrives from the queue.
    # After the message is handled, or fails, it acks the message and updates the action status.

    def __init__(self, opts):
        super(Actions, self).__init__(opts)
        self.listeners = dict()

        # Set options for connecting to Action Module with HTTP Proxy
        self._proxy_args = {}
        proxy_host = opts.get("proxy_host")
        if proxy_host:
            proxy_host = proxy_host.replace("http://", "").replace("https://", "")
            self._proxy_args = {"proxy_host": proxy_host,
                                "proxy_port": opts.get("proxy_port"),
                                "proxy_user": opts.get("proxy_user"),
                                "proxy_password": opts.get("proxy_password")}

        # Read the action definitions, into a dict indexed by id
        # we'll refer to them later when dispatching
        self.reconnect_stomp = True
        rest_client = self.rest_client()
        self.org_id = rest_client.org_id
        list_action_defs = rest_client.get("/actions")["entities"]
        self.action_defs = dict((int(action["id"]), action) for action in list_action_defs)
        self.stomp_component = None
        self.logging_directory = None

        if opts.get("test_actions", False):
            # Let user submit test actions from the command line for testing
            LOG.info(("Action Tests Enabled! Run res-action-test "
                      "and type help for usage"))
            test_options = {}
            if opts.get("test_port", None) != None:
                test_options["port"] = int(opts["test_port"])
            if self.opts.get("test_host"):
                test_options["host"] = opts["test_host"]
            actions_test_component.ResilientTestActions(self.org_id,
                                                        **test_options).register(self)

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
            self.action_defs = dict((int(action["id"]),
                                     action) for action in list_action_defs)
            try:
                defn = self.action_defs[action_id]
            except KeyError:
                LOG.exception("Action %s is not defined.", action_id)
                raise

        if defn:
            return defn["name"]

    @handler("Connected")
    def on_stomp_connected(self):
        """Client has connected to the STOMP server"""
        LOG.info("STOMP connected.")

    @handler("HeartbeatTimeout")
    def on_heartbeat_timeout(self):
        """Heartbeat timed out from the STOMP server"""
        LOG.info("STOMP heartbeat timeout!")
        # Set a timer to automatically reconnect
        Timer(5, Event.create("reconnect")).register(self)

    @handler("StompErrorEvent")
    def on_stomp_error(self, headers, message, error):
        """STOMP produced an error."""
        LOG.error('STOMP listener: Error:\n%s', message or error)
        # Just raise the event for anyone listening
        self.fire(Event("exception", "Actions",
                        headers.get("message"), message))

    @handler("MessageEvent")
    def on_stomp_message(self, event, headers, message):
        """STOMP produced a message."""
        # Find the queue name from the subscription id (stomp_listener_xxx)
        subscription = self.stomp_component.get_subscription(event.frame)
        LOG.debug('STOMP listener: message for %s', subscription)
        queue_name = subscription.split(".", 2)[2]
        channel = "actions." + queue_name

        LOG.info("Got Message: %s", event.frame.info())

        try:
            # Expect the message payload to always be JSON
            message = json.loads(message.decode('utf-8'))
            # Construct a Circuits event with the message, and fire it on the channel
            event = ActionMessage(source=self, headers=headers, message=message, frame=event.frame, log_dir=self.logging_directory)
            LOG.info("Event: %s Channel: %s", event, channel)

            self.fire(event, channel)
        except Exception as exc:
            LOG.exception(exc)
            # Normally the event won't be ack'd.  Just report it and carry on.
            if self.ignore_message_failure:
                # Construct and fire anyway, which will ack the message
                LOG.warn("This message failure will be ignored...")
                event = ActionMessage(source=self, headers=headers, message=None, frame=event.frame, log_dir=self.logging_directory)
                self.fire(event, channel)

    # Circuits event handlers

    @handler("idle_reset")
    def idle_reset(self, event):
        LOG.debug("Idle reset")
        reset_resilient_client()

    def _setup_stomp(self):
        rest_client = self.rest_client()
        if not rest_client.actions_enabled:
            # Don't create stomp connection b/c action module is not enabled.
            LOG.warn(("Resilient action module not enabled."
                      "No stomp connection attempted."))
            return

        self.resilient_mock = self.opts["resilient_mock"] or False
        if self.resilient_mock:
            # Using mock API, no need to create a real stomp connection
            LOG.warn("Using Mock. No Stomp connection")
            return

        # Give the STOMP library our TLS/SSL configuration.
        cafile = self.opts.get("stomp_cafile") or self.opts.cafile
        if cafile == "false":
            # Explicitly disable TLS certificate validation, if you need to
            cafile = None
            LOG.warn(("Unverified STOMP TLS certificate (cafile=false)"))
        elif cafile is None:
            # Since the REST API (co3 library) uses 'requests', let's use its default certificate bundle
            # instead of the certificates from ssl.get_default_verify_paths().cafile
            cafile = DEFAULT_CA_BUNDLE_PATH
            LOG.debug("STOMP TLS validation with default certificate file: %s", cafile)
        else:
            LOG.debug("STOMP TLS validation with certificate file: %s", cafile)

        try:
            ca_certs=None
            context = ssl.create_default_context(cafile=cafile)
            context.check_hostname = True if cafile else False
            context.verify_mode = ssl.CERT_REQUIRED if cafile else ssl.CERT_NONE
        except AttributeError as err:
            # Likely an older ssl version w/out true ssl context
            LOG.info("Can't create SSL context. Using fallback method")
            context = None
            ca_certs=cafile

        # Set up a STOMP connection to the Resilient action services
        if not self.stomp_component:
            self.stomp_component = StompClient(self.opts["host"], self.opts["stomp_port"],
                                               username=self.opts["email"],
                                               password=self.opts["password"],
                                               heartbeats=(STOMP_CLIENT_HEARTBEAT,
                                                           STOMP_SERVER_HEARTBEAT),
                                               connected_timeout=STOMP_TIMEOUT,
                                               connect_timeout=STOMP_TIMEOUT,
                                               ssl_context=context,
                                               ca_certs=ca_certs, # For old ssl version
                                               **self._proxy_args)
            self.stomp_component.register(self)
        else:
            # Component exists, just update it
            self.stomp_component.init(self.opts["host"], self.opts["stomp_port"],
                                      username=self.opts["email"],
                                      password=self.opts["password"],
                                      heartbeats=(STOMP_CLIENT_HEARTBEAT,
                                                  STOMP_SERVER_HEARTBEAT),
                                      connected_timeout=STOMP_TIMEOUT,
                                      connect_timeout=STOMP_TIMEOUT,
                                      ssl_context=context,
                                      ca_certs=ca_certs, # For old ssl version
                                      **self._proxy_args)

        # Other special options
        self.ignore_message_failure = self.opts["resilient"].get("ignore_message_failure") == "1"
        self.reconnect(subscribe=False)

    def _setup_message_logging(self):
        """ Store action message logging option """
        self.logging_directory = self.opts["log_http_responses"] or None
        if self.logging_directory:
            try:
                directory = os.path.expanduser(self.logging_directory)
                directory = os.path.expandvars(directory)
                assert(os.path.exists(directory))
                self.logging_directory = directory
            except Exception as e:
                self.logging_directory = None
                raise Exception("Response Logging Directory %s does not exist!" ,
                                self.opts["log_http_responses"])

    @handler("registered")
    def registered(self, event, component, parent):
        """A component has registered.  Subscribe to its message queue(s)."""
        if self is component:
            self.reconnect_stomp = True
            self._setup_message_logging()
            self._setup_stomp()
            return
        for channel in event.channels:
            if not str(channel).startswith("actions."):
                continue
            LOG.info("Component %s registered to %s", str(component), channel)
            queue_name = channel.split(".", 1)[1]
            if queue_name in self.listeners:
                comps = set([component])
                comps.update(self.listeners[queue_name])
                self.listeners[queue_name] = comps
            else:
                self.listeners[queue_name] = set([component])
                # Defer subscribing until all components are loaded
            LOG.debug("Listeners: %s", self.listeners)

    @handler("load_all_success")
    def subscribe_to_queues(self):
        """ Subscribe to all message queues """
        for queue_name in self.listeners:
            self._subscribe(queue_name)

    @handler("prepare_unregister")
    def prepare_unregister(self, event, component):
        """A component is unregistering.  Unsubscribe its message queue(s)."""
        LOG.debug("component %s has unregistered", component)
        if self is component:
            LOG.info("disconnecting Actions component from stomp queue")
            self.disconnect()
            self.reconnect_stomp = False
            if self.stomp_component:
                # TODO: Confirm the stomp component gets garbage collected automatically
                self.stomp_component.unregister()
                self.stomp_component = None

        for channel in event.channels:
            if not str(channel).startswith("actions."):
                continue
            LOG.info("Component %s unregistered from %s",
                     str(component), channel)
            queue_name = channel.partition(".")[2]
            if queue_name not in self.listeners:
                LOG.error("Channel %s was not subscribed", queue_name)
                continue
            comps = self.listeners[queue_name]
            if component not in comps:
                LOG.error("Component %s was not subscribed", component)
                continue
            comps.remove(component)
            if not comps:
                # All components have unsubscribed this destination; stop listening
                self._unsubscribe(queue_name)
            self.listeners[queue_name] = comps
            LOG.debug("Listeners: %s", self.listeners)

    def _subscribe(self, queue_name):
        """Actually subscribe the STOMP queue.  Note: this use client-ack, not auto-ack"""
        if self.resilient_mock:
            return
        if self.stomp_component and self.stomp_component.connected and self.listeners[queue_name]:
            if queue_name in self.stomp_component.subscribed:
                LOG.info("Ignoring request to subscribe to %s.  Already subscribed", queue_name)
            LOG.info("Subscribe to message destination '%s'", queue_name)
            destination="actions.{0}.{1}".format(self.org_id, queue_name)
            self.fire(Subscribe(destination))
        else:
            LOG.error("Invalid reqest to subscribe to %s in state Connected? [%s] with %d listeners",
                      queue_name,
                      self.stomp_component.connected if self.stomp_component else "NO COMPONENT",
                      len(self.listeners[queue_name]))

    def _unsubscribe(self, queue_name):
        """Unsubscribe the STOMP queue"""
        if self.stomp_component and self.stomp_component.connected and self.listeners[queue_name]:
            LOG.info("Unsubscribe from message destination '%s'",
                     queue_name)
            destination="actions.{0}.{1}".format(self.org_id, queue_name)
            self.fire(Unsubscribe(destination))

    def disconnect(self):
        """disconnect stomp connection"""
        if self.stomp_component:
            self.fire(Disconnect())

    @handler("reconnect")
    def reconnect(self, subscribe=True):
        """Try (re)connect to the STOMP server"""
        if self.resilient_mock:
            return
        if self.stomp_component and self.stomp_component.connected:
            LOG.warn("STOMP reconnect requested when already connected")
        elif self.opts["resilient"].get("stomp") == "0":
            LOG.info("STOMP connection is not enabled")
        else:
            LOG.info("STOMP attempting to connect")
            self.fire(Connect(subscribe=subscribe))

    @handler("Connect_success")
    def connected_succesfully(self, event, *args, **kwargs):
        """ Connected to stomp, subscribe if required """
        # This is used to automatically re-subscribe to queues on a reconnect
        if event.parent.subscribe:
            self.subscribe_to_queues()

    @handler("Disconnected")
    @handler("ConnectionFailed")
    def retry_connection(self, event, *args, **kwargs):
        # Try again later
        reloading = getattr(self.parent, "reloading", False)
        if event.reconnect and not reloading:
            Timer(60, Event.create("reconnect")).register(self)

    @handler("exception")
    def exception(self, etype, value, _traceback, handler=None, fevent=None):
        """Report an exception thrown during handling of an action event"""
        try:
            if etype:
                message = etype.__name__ + u": <" + u"{}".format(value) + u">"
            else:
                message = u"Processing failed"
            if _traceback and isinstance(traceback, list):
                message = message + "\n" + ("".join(_traceback))
            LOG.error(u"%s (%s): %s", repr(fevent), repr(etype), message)
            if fevent and isinstance(fevent, ActionMessage):
                fevent.stop()  # Stop further event processing
                status = 1
                headers = fevent.hdr()
                # Ack the message
                message_id = headers['message-id']
                if not fevent.test and self.stomp_component:
                    self.fire(Ack(fevent.frame))
                    LOG.debug("Ack %s", message_id)
                # Reply with error status
                reply_to = headers['reply-to']
                correlation_id = headers['correlation-id']
                reply_message = json.dumps({"message_type": status,
                                            "message": message, "complete": True})
                if not fevent.test and self.stomp_component:
                    self.fire(Send(headers={'correlation-id': correlation_id},
                                   body=reply_message,
                                   destination=reply_to))
                else:
                    # Test action, nothing to Ack
                    self.fire(Event.create("test_response",
                                           fevent.test_msg_id, reply_message))
                    LOG.debug("Test Action: No ack done.")
        except Exception as err:
            LOG.error("Exception handler threw exception! Response to action module may not have sent.")
            LOG.error(_traceback)

    @handler("signal")
    def _on_signal(self, signo, stack):
        """We implement a default-event handler, which means we don't get default signal handling - add it back
           (see FallBackSignalHandler in circuits/core/helpers.py)
        """
        if signo in [SIGINT, SIGTERM]:
            raise SystemExit(0)

    @handler("reload", priority=999)
    def reload(self, event, opts):
        """New config, reconnect to stomp if required"""
        event.success = False
        super(Actions, self).reload(event, opts)
        if self.stomp_component:
            self.fire(Disconnect())
            yield self.wait("Disconnect_success")
            self._setup_stomp()
            yield self.wait("Connect_success")
            self.subscribe_to_queues()
        event.success=True

    @handler()
    def _on_event(self, event, *args, **kwargs):
        """Report the successful handling of an action event"""
        if isinstance(event.parent, ActionMessage) and event.name.endswith("_success"):
            fevent = event.parent
            if fevent.deferred:
                LOG.debug("Not acking deferred message %s", str(fevent))
            else:
                value = event.parent.value.getValue()
                LOG.debug("success! %s, %s", value, fevent)
                fevent.stop()  # Stop further event processing
                # value will be None if there was no handler or a handler returned None
                if value:
                    if isinstance(value, list):
                        message = u" ".join(value)
                    else:
                        message = value
                else:
                    message= u"No handler returned a result for this action"
                LOG.debug("Message: %s", message)
                status = 0
                headers = fevent.hdr()
                # Ack the message
                message_id = headers['message-id']
                if not fevent.test:
                    LOG.debug("Ack %s", message_id)
                    self.fire(Ack(fevent.frame))
                # Reply with success status
                reply_to = headers['reply-to']
                correlation_id = headers['correlation-id']
                reply_message = json.dumps({"message_type": status,
                                            "message": message,
                                            "complete": True})
                if not fevent.test:
                    self.fire(Send(headers={'correlation-id': correlation_id},
                                   body=reply_message,
                                   destination=reply_to))
                else:
                    # Test action, nothing to Ack
                    self.fire(Event.create("test_response", fevent.test_msg_id,
                                           reply_message), '*')
                    LOG.debug("Test Action: No ack done.")
