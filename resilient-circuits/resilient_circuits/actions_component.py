# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

"""Circuits component for Action Module subscription and message handling"""

import base64
import json
import logging
import os.path
import ssl
import sys
import traceback
from signal import SIGINT, SIGTERM

if sys.version_info.major < 3:
    from collections import Callable
else:
    from collections.abc import Callable

from circuits import BaseComponent, Worker
from circuits.core.handlers import handler
from circuits.core.manager import ExceptionWrapper
from requests.utils import DEFAULT_CA_BUNDLE_PATH
from six import string_types

import resilient
from resilient import ensure_unicode
from resilient_lib import IntegrationError
import resilient_circuits.actions_test_component as actions_test_component
from resilient_circuits import constants, helpers
from resilient_circuits.action_message import (ActionMessage,
                                               ActionMessageBase,
                                               BaseFunctionError,
                                               FunctionMessage, FunctionResult,
                                               InboundMessage, StatusMessage)
from resilient_circuits.decorators import *  # for back-compatibility, these were previously declared here
from resilient_circuits.rest_helper import (get_resilient_client,
                                            reset_resilient_client)
from resilient_circuits.stomp_component import StompClient
from resilient_circuits.stomp_events import *

LOG = logging.getLogger(__name__)

STOMP_CLIENT_HEARTBEAT = 0          # no heartbeat from client to server
STOMP_SERVER_HEARTBEAT = 15000      # 15-second heartbeat from server to client
RETRY_TIMER_INTERVAL = 60           # Retry failed deliveries every minute
SUBSCRIBE_TO_QUEUES_TIMEOUT = 30    # connect event timeout

# Global idle timer, fires after 10 minutes to reset the REST connection
IDLE_TIMER_INTERVAL = 600
_idle_timer = None

# look for unrecoverable errors
UNRECOVERABLE_ERRORS = ['Already subscribed']

# Errors and Message Destination names will get appended when ran in selftest
SELFTEST_ERRORS = []
SELFTEST_SUBSCRIPTIONS = []


def validate_cert(cert, hostname):
    """Utility wrapper for SSL validation on the STOMP connection"""
    try:
        resilient.match_hostname(cert, hostname)
    except Exception as exc:
        return (False, str(exc))
    return (True, "Success")


class FunctionWorker(Worker):

    channel = "functionworker"

    @handler("signal", channel="*")
    def _on_signal(self, signo, stack):
        """Add a signal handler to the worker processes otherwise they swallow SIGINT, SIGTERM
           (see FallBackSignalHandler in circuits/core/helpers.py)
        """
        if signo in [SIGINT, SIGTERM]:
            LOG.error("Worker interrupted")
            raise SystemExit(0)

    @handler("task", override=True)
    def _on_task(self, f, *args, **kwargs):
        LOG.debug("Task: %s", f)
        result = self.pool.apply_async(f, args, kwargs)
        while not result.ready():
            yield
        try:
            yield result.get()
        except Exception as e:
            str_traceback = traceback.format_exc()
            ignore_exception = False

            if isinstance(self.parent, Actions):
                app_configs = self.parent.opts
                ignore_exception = app_configs.get(constants.APP_CONFIG_TRAP_EXCEPTION, False)

            if ignore_exception:

                err = str(e)

                # Handle strs as unicode if Python 2
                if sys.version_info.major == 2:
                    err = unicode(err, "utf-8")
                    str_traceback = unicode(str_traceback, "utf-8")

                fn_name = constants.DEFAULT_UNKNOWN_STR

                # args being the parameters of the decorator
                if isinstance(args, tuple) and hasattr(args[0], "name"):
                    fn_name = args[0].name

                status_message = u"Error running '{0}'. Config '{1}' set to 'True' so ignoring exception\nERROR:\n{2}".format(fn_name, constants.APP_CONFIG_TRAP_EXCEPTION, err)

                # If the loglevel is DEBUG, the full stacktrace will be added to the StatusMessage
                if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                    status_message = u"{0}\n{1}".format(status_message, str_traceback)

                log_message = u"{0}\n{1}".format(status_message, str_traceback)

                yield StatusMessage(status_message)

                LOG.warning(log_message)

                yield FunctionResult({"success": False, "reason": err})

            else:
                LOG.error(str_traceback)
                yield ExceptionWrapper(e)


class ResilientComponent(BaseComponent):
    """A Circuits base component with a connection to the Resilient APIs.

       This is the superclass for custom Resilient Action Module components.
       If a component inherits from ResilientComponent, it will automatically be loaded,
       and actions and functions will be dispatched to its `handler` and `function` methods.
    """
    test_mode = False  # True with --test-actions option
    IS_SELFTEST = False

    def __init__(self, opts):
        super(ResilientComponent, self).__init__()
        assert isinstance(opts, dict)

        self.opts = opts
        self._fields = {}
        self._action_fields = {}
        self._functions = {}
        self._function_fields = {}
        self.fn_names = helpers.get_fn_names(self)

        # Get fields, message destinations and functions

        self._get_fields(fn_names=self.fn_names)

        # If this component is a function, self.fn_names will be defined
        if self.fn_names:
            LOG.debug("@function handler names: %s", self.fn_names)

            for fn_name in self.fn_names:
                if not helpers.check_exists(fn_name, self._functions):
                    LOG.warning("Function '{0}' is not defined in this Resilient platform!".format(fn_name))

        else:
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
                                "defined in this Resilient platform.")
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
                                "is not defined in this Resilient platform.")
                        raise Exception(errmsg.format(field_name, name))
                    if input_type is not None:
                        if fielddef["input_type"] != input_type:
                            errmsg = ("Action field '{0}' (required by "
                                    "'{1}') must be type '{2}'.")
                            raise Exception(errmsg.format(field_name,
                                                        name, input_type))

    def _get_fields(self, fn_names=None):
        """Get Incident and Action fields"""
        client = self.rest_client()
        self._fields = dict((field["name"], field)
                            for field in client.cached_get("/types/incident/fields"))
        self._action_fields = dict((field["name"], field)
                                   for field in client.cached_get("/types/actioninvocation/fields"))

        if fn_names:

            try:

                for fn_name in fn_names:
                    self._functions[fn_name] = client.cached_get("/functions/{0}?handle_format=names".format(fn_name))

                self._function_fields = dict((field["name"], field) for field in client.cached_get("/types/__function/fields"))

            except resilient.SimpleHTTPException:
                # functions are not available, pre-v30 server
                self._functions = None
                self._function_fields = None

    def rest_client(self):
        """
        Return a connected instance of the :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
        that can be used to access the IBM SOAR REST API.

        .. note::
            An :class:`~resilient_circuits.app_function_component.AppFunctionComponent` inherits a
            ``ResilientComponent`` so will have access to this method

        **Example:**

        .. code-block:: python

            from resilient_circuits import AppFunctionComponent, FunctionResult, app_function

            PACKAGE_NAME = "fn_mock_app"
            FN_NAME = "mock_function"

            class FunctionComponent(AppFunctionComponent):

                def __init__(self, opts):
                    super(FunctionComponent, self).__init__(opts, PACKAGE_NAME)

                @app_function(FN_NAME)
                def _app_function(self, fn_inputs):

                    res_client = self.rest_client()
                    inc = res_client.get("/incidents/{0}".format("1001"))
                    inc_name = inc.get("name")

                    results = {
                        "inc": inc,
                        "inc_name": inc_name
                    }

                    yield FunctionResult(results)

        :return: a connected instance of :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`
        :rtype: :class:`resilient.SimpleClient <resilient.co3.SimpleClient>`

        """
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
            _idle_timer.reset()

    def get_incident_field(self, fieldname):
        """Get the definition of an incident-field"""
        return self._fields[fieldname]

    def get_incident_fields(self):
        """Get the definitions of all incident-fields, as a list"""
        return self._fields.values()

    def get_field_label(self, fieldname, value_id):
        """Get the label for an incident-field value id"""
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
        """Get the label for an action-field value id"""
        field = self._action_fields[fieldname]
        for value in field["values"]:
            if value["enabled"]:
                if value["value"] == value_id:
                    return value["label"]
        return ensure_unicode(value_id)  # fallback

    def get_function_field(self, fieldname):
        """Get the definition of a function input field (parameter)"""
        return self._function_fields[fieldname] if self._function_fields else None

    def get_function_fields(self):
        """Get the definitions of all function input-fields (parameters), as a list"""
        return self._function_fields.values() if self._function_fields else None

    def get_function_field_label(self, fieldname, value_id):
        """Get the label for a function input-field value id"""
        if self._function_fields is None:
            return None
        field = self._function_fields[fieldname]
        for value in field["values"]:
            if value["enabled"]:
                if value["value"] == value_id:
                    return value["label"]
        return ensure_unicode(value_id)  # fallback

    @staticmethod
    def get_select_param(value):
        """Function Helper: get the label from a select- or multi-select parameter"""
        if isinstance(value, list):
            return [ResilientComponent.get_select_param(val) for val in value]
        if isinstance(value, dict):
            return value.get("name")
        return value

    @staticmethod
    def get_textarea_param(value):
        """Function Helper: get the content from a textarea-type parameter"""
        if isinstance(value, dict):
            return value.get("content")
        return value

    @handler("reload")
    def reload(self, event, opts):
        """Event handler called when the configuration options have changed."""
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
        self._proxy_args = {}

        # messages and acks that failed to send over stomp connection
        self._stomp_ack_delivery_failures = {}
        self._resilient_ack_delivery_failures = {}

        # Read the action definitions, into a dict indexed by id
        # we'll refer to them later when dispatching
        self.reconnect_stomp = True
        self.org_id = None
        self.action_defs = dict()
        self.stomp_component = None
        self.logging_directory = None
        self.subscribe_headers = None
        self._configure_opts(opts)
        self.max_retry_count = int(opts.get("stomp_max_retries")) # default from app.py:DEFAULT_STOMP_MAX_RETRIES
        self.stomp_timeout = int(opts.get("stomp_timeout", SUBSCRIBE_TO_QUEUES_TIMEOUT))
        self.heartbeat_timeouts = []

        timer_internal = int(opts['resilient'].get("stomp_timer_interval", RETRY_TIMER_INTERVAL))

        _retry_timer = Timer(timer_internal, Event.create("retry_failed_deliveries"), persist=True)
        _retry_timer.register(self)

        # Make a worker thread-pool that will run functions
        LOG.debug("num_workers set to %s", opts.get("num_workers"))
        self._num_workers = opts.get("num_workers")
        self._functionworker = FunctionWorker(process=False, channel="functionworker", workers=opts.get("num_workers"))
        self._functionworker.register(self.root)

        if opts.get("test_actions", False):
            # Let user submit test actions from the command line for testing
            LOG.info("Action Tests enabled. Run 'resilient-circuits test' for the interactive action test tool.")
            test_options = {}
            if opts.get("test_port", None):
                test_options["port"] = int(opts["test_port"])
            if self.opts.get("test_host"):
                test_options["host"] = opts["test_host"]
            actions_test_component.ResilientTestActions(self.org_id,
                                                        **test_options).register(self)

    def _configure_opts(self, opts):
        """ Handle settings from configuration """
        # Set options for connecting to Action Module with HTTP Proxy
        self._proxy_args = {}
        proxy_host = opts.get("proxy_host")
        if proxy_host:
            proxy_host = proxy_host.replace("http://", "").replace("https://", "")
            self._proxy_args = {"proxy_host": proxy_host,
                                "proxy_port": opts.get("proxy_port"),
                                "proxy_user": opts.get("proxy_user"),
                                "proxy_password": opts.get("proxy_password")}

        rest_client = self.rest_client()
        self.org_id = rest_client.org_id

        list_action_defs = rest_client.get("/actions")["entities"]
        self.action_defs = dict((int(action["id"]), action) for action in list_action_defs)

        self.subscribe_headers = {"activemq.prefetchSize": opts["stomp_prefetch_limit"]}

    # Public Utility methods

    def action_name(self, action_id):
        """Get the name of an action, from its id"""
        if action_id is None:
            # Unnamed action, probably triggered from a v28 workflow
            LOG.info("Action: _unnamed_")
            return "_unnamed_"

        if self.action_defs.get(action_id):
            defn = self.action_defs[action_id]
        else:
            LOG.warning("Action %s is unknown.", action_id)
            # Refresh the list of action definitions
            list_action_defs = self.rest_client().get("/actions")["entities"]
            self.action_defs = dict((int(action["id"]),
                                     action) for action in list_action_defs)

            defn = self.action_defs.get(action_id, {"name": "_unnamed_"})

        if defn:
            return defn.get("name", "_unnamed_")

    @handler("Connected")
    def on_stomp_connected(self):
        """Client has connected to the STOMP server"""
        LOG.info("STOMP connected.")

        # Once STOMP has connected, we want to empty the heartbeat_timeouts list
        self.heartbeat_timeouts = []

        # Stop retrying the failed deliveries from previous session
        # We'll ack them right away if they are re-delivered
        # TODO: We should age these out of here at some point. 24 hours?
        for key in self._stomp_ack_delivery_failures:
            self._stomp_ack_delivery_failures[key]["from_prev_conn"] = True
        for key in self._resilient_ack_delivery_failures:
            self._resilient_ack_delivery_failures[key]["from_prev_conn"] = True

    @handler("HeartbeatTimeout")
    def on_heartbeat_timeout(self, event):
        """
        Handler for a HeartbeatTimeout event

        Checks to see if the 'heartbeat_timeout_threshold' config is set. Keeps
        track of HBs in a list. Each HB has a ts value. If the difference
        between the first and current HB's ts is greater than the config,
        resilient-circuits exits with an exit code of 34
        """

        heartbeat_timeout_threshold = self.opts.get(constants.APP_CONFIG_HEARTBEAT_TIMEOUT_THRESHOLD)

        # If heartbeat_timeout_threshold config is set
        if heartbeat_timeout_threshold:

            # Add the current HB to the list
            self.heartbeat_timeouts.append(event)

            # If more than 1 HBs are in the list
            if len(self.heartbeat_timeouts) > 1:

                # Remove any invalid timeouts and sort the list
                self.heartbeat_timeouts = helpers.filter_heartbeat_timeout_events(self.heartbeat_timeouts)

                # Get the difference in seconds between the oldest and current timeout
                delta = int(self.heartbeat_timeouts[-1].ts - self.heartbeat_timeouts[0].ts)

                # If the delta is greater than the config, log an error and exit resilient-circuits
                if delta > heartbeat_timeout_threshold:
                    LOG.error("'%s' is set to '%ss' and '%ss' have passed since the first HeartbeatTimeout, exiting...",
                              constants.APP_CONFIG_HEARTBEAT_TIMEOUT_THRESHOLD, heartbeat_timeout_threshold, delta)

                    sys.exit(constants.EXIT_STOMP_HEARTBEAT_TIMEOUT)

        LOG.error("Trying to reconnect after STOMP HeartbeatTimeout")

        # Fire a Disconnect event to Reconnect
        self.fire(Disconnect(flush=False, reconnect=True))

    @handler("OnStompError")
    def on_stomp_error(self, headers, message, error):
        """STOMP produced an error."""
        LOG.error('STOMP listener: Error:\n%s', message or error)

        if helpers.is_this_a_selftest(self):
            SELFTEST_ERRORS.append(message or error)

        for unrecoverable_error in UNRECOVERABLE_ERRORS:
            if (message and unrecoverable_error in str(message)) or \
               (error and unrecoverable_error in str(error)):
                LOG.error("Unrecoverable error. Exiting")
                raise SystemExit(0)

        # Just raise the event for anyone listening
        self.fire(Event("exception", "Actions",
                        headers.get("message"), message))

    @handler("Message")
    def on_stomp_message(self, event, headers, message, queue):
        """STOMP produced a message."""
        # Find the queue name from the subscription id (stomp_listener_xxx)
        msg_id = event.frame.headers.get("message-id")
        if not msg_id:
            LOG.error("Received message with no message id. %s", event.frame.info())
            raise ValueError("Stomp message with no message id received")
        elif msg_id in self._resilient_ack_delivery_failures or msg_id in self._stomp_ack_delivery_failures:
            # This is a message we have already processed but we failed to acknowledge
            # Don't process it again, just acknowledge it
            LOG.info("Skipping reprocess of message %s.  Sending saved ack now.", msg_id)
            failure_info = self._resilient_ack_delivery_failures.get(msg_id)
            if failure_info:
                self.fire(Send(headers={'correlation-id': headers['correlation-id']},
                               body=failure_info["result"]["body"],
                               destination=headers['reply-to'],
                               message_id=msg_id))
                self._resilient_ack_delivery_failures.pop(msg_id)
            failure_info = self._stomp_ack_delivery_failures.get(msg_id)
            if failure_info:
                self.fire(Ack(event.frame))
                self._stomp_ack_delivery_failures.pop(msg_id)

        else:
            subscription = self.stomp_component.get_subscription(event.frame)
            LOG.debug('STOMP listener: message for %s', subscription)
            queue_name = subscription.split(".", 2)[2]
            channel = "actions." + queue_name

            LOG.debug("Got Message: %s", event.frame.info())

            try:
                # Expect the message payload to always be UTF8 JSON.
                # However, it may contain surrogate pairs, and in Python 3 that causes problems:
                # - surrogate pairs are not allowed by the default (strict) utf8 decoder,
                # - if we pass them, it will cause downstream issues, so we should re-encode.
                try:
                    mstr = message.decode('utf-8')
                except UnicodeDecodeError:
                    LOG.debug("Failed utf8 decode, trying surrogate")
                    mstr = message.decode('utf-8', "surrogatepass").encode("utf-16", "surrogatepass").decode("utf-16")

                message = json.loads(mstr)
                # Construct a Circuits event with the message, and fire it on the channel
                if queue and queue[0] == constants.INBOUND_MSG_DEST_PREFIX:
                    channel = u"{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, queue[2])
                    event = InboundMessage(source=self,
                                           queue=queue,
                                           headers=headers,
                                           message=message,
                                           frame=event.frame,
                                           log_dir=self.logging_directory)

                elif message.get("function"):
                    channel = "functions." + message["function"]["name"]
                    event = FunctionMessage(source=self,
                                            headers=headers,
                                            message=message,
                                            frame=event.frame,
                                            log_dir=self.logging_directory)
                else:
                    event = ActionMessage(source=self,
                                          headers=headers,
                                          message=message,
                                          frame=event.frame,
                                          log_dir=self.logging_directory)
                LOG.info("Event: %s Channel: %s", event, channel)

                self.fire(event, channel)
            except Exception as exc:
                LOG.exception(exc)
                if not isinstance(message, dict):
                    LOG.error("DATA:%s", base64.b64encode(message))
                # Normally the event won't be ack'd.  Just report it and carry on.
                if self.ignore_message_failure:
                    # Construct and fire anyway, which will ack the message
                    LOG.warning("This message failure will be ignored...")
                    event = ActionMessage(source=self,
                                          headers=headers,
                                          message=None,
                                          frame=event.frame,
                                          log_dir=self.logging_directory)
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
            LOG.warning(("Resilient action module not enabled."
                        "No stomp connection attempted."))
            return

        self.resilient_mock = self.opts["resilient_mock"] or False
        if self.resilient_mock:
            # Using mock API, no need to create a real stomp connection
            LOG.warning("Using Mock. No Stomp connection")
            return

        # Gather the stomp_cafile for if specified or fallback to the resilient host. Used for TLS / SSL
        cafile = self.opts.get("stomp_cafile") or self.opts.cafile
        if cafile is not None and cafile.strip().lower() == "false":
            # Explicitly disable TLS certificate validation, if you need to
            cafile = None
            LOG.warning(("Unverified STOMP TLS certificate (cafile=false)"))
        elif cafile is None:
            # Since the REST API (resilient library) uses 'requests', let's use its default certificate bundle
            # instead of the certificates from ssl.get_default_verify_paths().cafile
            cafile = DEFAULT_CA_BUNDLE_PATH
            LOG.debug("STOMP TLS validation with default certificate file: %s", cafile)
        else:
            LOG.debug("STOMP TLS validation with certificate file: %s", cafile)

        try:
            ca_certs = None
            context = ssl.create_default_context(cafile=cafile)
            context.check_hostname = True if cafile else False
            context.verify_mode = ssl.CERT_REQUIRED if cafile else ssl.CERT_NONE
        except AttributeError as err:
            # Likely an older ssl version w/out true ssl context
            LOG.info("Can't create SSL context. Using fallback method")
            context = None
            ca_certs = cafile

        # Gather the stomp_host if specified or fallback to the resilient host if not
        stomp_host = self.opts["resilient"].get("stomp_host", None) or self.opts["host"]
        #
        #   key_id and key_secret are the preferrable one
        #
        if self.opts.get("api_key_id", None) is not None and self.opts.get("api_key_secret", None) is not None:
            stomp_email = self.opts["api_key_id"]
            stomp_password = self.opts["api_key_secret"]
        else:
            stomp_email = self.opts["email"]
            stomp_password = self.opts["password"]

        # Set up a STOMP connection to the Resilient action services
        stomp_timeout = int(self.opts.get("stomp_timeout")) # default from app.py:DEFAULT_STOMP_TIMEOUT
        # build out all the extra parameters for the stomp connections
        stomp_params = self.opts['resilient'].get('stomp_params')
        if not self.stomp_component:
            self.stomp_component = StompClient(stomp_host, self.opts["stomp_port"],
                                               username=stomp_email,
                                               password=stomp_password,
                                               heartbeats=(STOMP_CLIENT_HEARTBEAT,
                                                           STOMP_SERVER_HEARTBEAT),
                                               connected_timeout=stomp_timeout,
                                               connect_timeout=stomp_timeout,
                                               ssl_context=context,
                                               ca_certs=ca_certs,  # For old ssl version
                                               stomp_params=stomp_params,
                                               stomp_max_connection_errors=self.opts.get("stomp_max_connection_errors", constants.STOMP_MAX_CONNECTION_ERRORS),
                                               **self._proxy_args)
            self.stomp_component.register(self)
        else:
            # Component exists, just update it
            self.stomp_component.init(stomp_host, self.opts["stomp_port"],
                                      username=stomp_email,
                                      password=stomp_password,
                                      heartbeats=(STOMP_CLIENT_HEARTBEAT,
                                                  STOMP_SERVER_HEARTBEAT),
                                      connected_timeout=stomp_timeout,
                                      connect_timeout=stomp_timeout,
                                      ssl_context=context,
                                      ca_certs=ca_certs,  # For old ssl version
                                      stomp_params=stomp_params,
                                      stomp_max_connection_errors=self.opts.get("stomp_max_connection_errors", constants.STOMP_MAX_CONNECTION_ERRORS),
                                      **self._proxy_args)

        # Other special options
        self.ignore_message_failure = self.opts["resilient"].get("ignore_message_failure") == "1"
        self.fire(Event.create("reconnect", subscribe=False))

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
                raise Exception("Response Logging Directory %s does not exist!",
                                self.opts["log_http_responses"])

    @handler("registered")
    def registered(self, event, component, parent):
        """A component has registered.  Subscribe to its message queue(s)."""
        if self is component:
            self.reconnect_stomp = True
            self._setup_message_logging()
            self._setup_stomp()
            return
        # The set of channels for this component is:
        # - the component's channel(s) declared at class level, and
        # - any channel(s) declared at individual handlers
        channels = set(event.channels)
        for handler in component.handlers():
            if handler.channel:
                channels.update(handler.channel.split(","))
        for channel in channels:
            if str(channel).startswith("actions."):
                # Action module handler, channel "actions.xx" subscribes to "xx"
                queue_name = channel.split(".", 1)[1]
                LOG.info("'%s.%s' actions registered to '%s'",
                         type(component).__module__, type(component).__name__, queue_name)
            elif str(channel).startswith("functions.") and component._functions:
                if self.test_mode:
                    continue
                # Function handler, channel "functions.xx" subscribes to the message dest associated with function "xx"
                func_name = channel.split(".", 1)[1]
                if func_name not in component._functions:
                    # Unknown function.  Log it and continue.
                    LOG.warning("'%s.%s' function '%s' is not defined!",
                                type(component).__module__, type(component).__name__, func_name)
                    continue
                queue_name = component._functions[func_name]["destination_handle"]
                LOG.info("'%s.%s' function '%s' registered to '%s'",
                         type(component).__module__, type(component).__name__, func_name, queue_name)

            elif str(channel).startswith(constants.INBOUND_MSG_DEST_PREFIX):
                # If name for inbound q in app.config file, use that
                try:
                    app_config_q_name = component.app_configs.get(constants.INBOUND_MSG_APP_CONFIG_Q_NAME)
                except AttributeError as e:
                    raise IntegrationError(u"'{0}' does not have app_configs defined\n{1}".format(type(component).__name__, str(e)))
                if app_config_q_name:
                    handler_name = app_config_q_name
                else:
                    handler_name = channel.split(".", 1)[1]
                queue_name = u"{0}.{1}.{2}".format(constants.INBOUND_MSG_DEST_PREFIX, self.org_id, handler_name)
                LOG.info("'%s.%s' inbound handler '%s' registered to '%s'", type(component).__module__, type(component).__name__, handler_name, queue_name)

            else:
                continue

            if queue_name in self.listeners:
                comps = set([component])
                comps.update(self.listeners[queue_name])
                self.listeners[queue_name] = comps
            else:
                self.listeners[queue_name] = set([component])
                # Defer subscribing until all components are loaded

    @handler("load_all_success", "subscribe_to_all")
    def subscribe_to_queues(self):
        """ Subscribe to all message queues """
        if not self.stomp_component:
            return
        if not self.stomp_component.connected:
            yield self.wait("Connected", timeout=self.stomp_timeout)
            if not self.stomp_component.connected:
                LOG.error("Can't subscribe to queues with STOMP disconnected, trying reconnect")
                self.fire(Event.create("reconnect"))

        if self.stomp_component.connected:
            LOG.info("resilient-circuits has started successfully and is now running...")

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

        if queue_name.startswith(constants.INBOUND_MSG_DEST_PREFIX):
            self.fire(Subscribe(queue_name, additional_headers=self.subscribe_headers))

        elif self.stomp_component and self.stomp_component.connected and self.listeners[queue_name]:
            if queue_name in self.stomp_component.subscribed:
                LOG.info("Ignoring request to subscribe to %s.  Already subscribed", queue_name)
            LOG.info("Subscribe to message destination '%s'", queue_name)

            if helpers.is_this_a_selftest(self):
                SELFTEST_SUBSCRIPTIONS.append(queue_name)

            destination = "actions.{0}.{1}".format(self.org_id, queue_name)
            self.fire(Subscribe(destination, additional_headers=self.subscribe_headers))
        else:
            LOG.error("Invalid request to subscribe to %s in state Connected? [%s] with %d listeners",
                      queue_name,
                      self.stomp_component.connected if self.stomp_component else "NO COMPONENT",
                      len(self.listeners[queue_name]))

    def _unsubscribe(self, queue_name):
        """Unsubscribe the STOMP queue"""
        if self.stomp_component and self.stomp_component.connected and self.listeners[queue_name]:
            LOG.info("Unsubscribe from message destination '%s'",
                     queue_name)
            destination = "actions.{0}.{1}".format(self.org_id, queue_name)
            self.fire(Unsubscribe(destination))

    def disconnect(self, reconnect=False, flush=True):
        """disconnect stomp connection"""
        if self.stomp_component:
            self.fire(Disconnect(reconnect=reconnect, flush=flush))

    @handler("reconnect")
    def _reconnect(self, subscribe=True):
        """Try (re)connect to the STOMP server"""
        if self.resilient_mock:
            return
        if self.stomp_component and self.stomp_component.connected and self.stomp_component.socket_connected:
            LOG.debug("STOMP reconnect requested when already connected")
        elif self.opts["resilient"].get("stomp") == "0":
            LOG.info("STOMP connection is not enabled")
        else:
            if self.stomp_component.socket_connected:
                LOG.warning("Disconnecting socket before Connect attempt")
                disconnect_event = Disconnect(reconnect=False, flush=False)
                self.fire(disconnect_event)
                yield self.wait(disconnect_event)

            LOG.info("STOMP attempting to connect")
            self.fire(Connect(subscribe=subscribe))

    @handler("Connect_success")
    def connected_succesfully(self, event, *args, **kwargs):
        """ Connected to stomp, subscribe if required """
        LOG.debug("Connected successfully. Resubscribe? %s", event.parent.subscribe)
        # This is used to automatically re-subscribe to queues on a reconnect
        if event.parent.subscribe:
            subscribe_event = Event.create("subscribe_to_all")
            self.fire(subscribe_event)
            yield self.wait(subscribe_event)

    @handler("Disconnected")
    @handler("ConnectionFailed")
    def retry_connection(self, event, *args, **kwargs):
        # Try again later
        reloading = getattr(self.parent, "reloading", False)
        if event.reconnect and not reloading:
            Timer(60, Event.create("reconnect")).register(self)

    @handler("exception")
    def exception(self, etype, value, traceback, handler=None, fevent=None):
        """Report an exception thrown during handling of an action event"""
        try:
            log_message, message = u"", u""
            if etype and issubclass(etype, BaseFunctionError):
                try:
                    message += str(value)
                except UnicodeDecodeError:
                    message += unicode(value)
                log_message = message
            else:
                if etype:
                    message = u"ERROR:\n{0}\n{1}".format(message, value)
                else:
                    message = u"Processing failed"
                if traceback and isinstance(traceback, list):

                    str_traceback = "".join(traceback)

                    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                        message = u"{0}\n{1}".format(message, str_traceback)

                    log_message = u"{0}\n{1}".format(message, str_traceback)

            # any event that had "opts" as an argument to it will be output here with "repr(fevent)"
            # so we have to see if the event has "opts" as an arg. If so, then just output the
            # type of the event, not the whole repr of the event.
            # Example:
            # ERROR [actions_component] Circuits event <class 'resilient_circuits.app_restartable.reload'> raised exception ...
            rep = type(fevent) if hasattr(fevent, "kwargs") and "opts" in fevent.kwargs else repr(fevent)
            LOG.error(u"Circuits event %s raised exception (%s): %s", rep, repr(etype), log_message)

            # Try find the underlying Action or Function message
            if fevent and fevent.args and not isinstance(fevent, ActionMessageBase):
                for arg in fevent.args:
                    if isinstance(arg, ActionMessageBase):
                        fevent = arg
                        break

            if isinstance(fevent, InboundMessage):
                headers = fevent.hdr()
                message_id = headers.get("message-id", None)
                if not fevent.test:
                    LOG.debug("Exception raised.\nAcknowledging InboundMessage: %s for queue: %s", message_id, headers.get("subscription", "Unknown"))
                    self.fire(Ack(fevent.frame))

            elif fevent and isinstance(fevent, ActionMessageBase):
                # For a ActionMessageBase type
                # 1. Ack message
                # 2. Send a message of type 1 containing the exception text
                fevent.stop()  # Stop further event processing
                status = 1
                headers = fevent.hdr()
                # Ack the message
                message_id = headers.get('message-id')
                if not fevent.test and self.stomp_component:
                    self.fire(Ack(fevent.frame, message_id=message_id))
                    LOG.debug("Ack %s", message_id)
                # Reply with error status
                reply_to = headers['reply-to']
                correlation_id = headers['correlation-id']
                reply_message = json.dumps({"message_type": status,
                                            "message": message,
                                            "complete": True})
                if not fevent.test and self.stomp_component:
                    self.fire(Send(headers={'correlation-id': correlation_id},
                                   body=reply_message,
                                   destination=reply_to,
                                   message_id=message_id))
                else:
                    # Test action, nothing to Ack
                    self.fire(Event.create("test_response",
                                           fevent.test_msg_id, reply_message))
                    LOG.debug("Test Action: No ack done.")
        except Exception as err:
            LOG.error("Exception handler threw exception! Response to action module may not have sent.")
            LOG.error(traceback)

    @handler("Ack_failure")
    def _on_ack_failure(self, event, err, *args, **kwargs):
        """STOMP Ack failed to send, add to delivery failures"""
        message_id = event.parent.message_id
        failure = self._stomp_ack_delivery_failures.get(message_id)
        if failure:
            if self.max_retry_count != 0 and failure["retry_count"] > self.max_retry_count:
                LOG.error("Giving up after %d attempts on delivery of STOMP ACK for message %s",
                          failure["retry_count"], message_id)
                self._stomp_ack_delivery_failures.pop(message_id)
        else:
            failure = {"retry_count": 1,
                       "from_prev_conn": False,
                       "message_frame": event.parent.frame}
            self._stomp_ack_delivery_failures[message_id] = failure

        LOG.warning("Failed %d times to deliver stomp ack for message %s", failure["retry_count"], message_id)

    @handler("Ack_success")
    def _on_ack_success(self, event, *args, **kwargs):
        if event.parent.message_id in self._stomp_ack_delivery_failures:
            LOG.info("Retry for sending STOMP ACK for message id %s successful.", event.parent.message_id)
            self._stomp_ack_delivery_failures.pop(event.parent.message_id)

    @handler("Send_success")
    def _on_send_success(self, event, *args, **kwargs):
        if event.parent.message_id in self._resilient_ack_delivery_failures:
            LOG.info("Retry for sending Resilient ACK for message id %s successful.", event.parent.message_id)
            self._resilient_ack_delivery_failures.pop(event.parent.message_id)

    @handler("Send_failure")
    def _on_send_failure(self, event, err, *args, **kwargs):
        """Resilient Ack failed to send, add to delivery failures"""
        message_id = event.parent.message_id

        failure = self._resilient_ack_delivery_failures.get(message_id)
        if failure:
            if self.max_retry_count != 0 and failure["retry_count"] > self.max_retry_count:
                LOG.error("Giving up after %d attempts on delivery of Resilient ACK for message %s",
                          failure["retry_count"], message_id)
                self._resilient_ack_delivery_failures.pop(message_id)
        else:
            failure = {"retry_count": 1,
                       "from_prev_conn": False,
                       "result":  {"headers": event.parent.headers,
                                   "body": event.parent.body,
                                   "destination": event.parent.destination}}
            self._resilient_ack_delivery_failures[message_id] = failure
        LOG.warning("Failed %d times to deliver Resilient ack for message %s", failure["retry_count"], message_id)

    @handler("retry_failed_deliveries")
    def _retry_send_failures(self, event):
        """retry all messages in the delivery_failures dict that are from the current session"""
        if not self.stomp_component:
            # Retries not applicable, probably using a mocked appliance
            return
        if not self.stomp_component.connected:
            LOG.info("Skipping retry of any failed messages because STOMP connection is down")
            return

        to_retry = {key: value for key, value in self._stomp_ack_delivery_failures.items()
                    if not value["from_prev_conn"]}
        for msgid, failure_info in to_retry.items():
            self._stomp_ack_delivery_failures[msgid]["retry_count"] = \
                self._stomp_ack_delivery_failures[msgid]["retry_count"] + 1
            LOG.info("Retrying failed STOMP ACK for message %s", msgid)
            self.fire(Ack(failure_info["message_frame"]))

        to_retry = {key: value for key, value in self._resilient_ack_delivery_failures.items()
                    if not value["from_prev_conn"]}
        for msgid, failure_info in to_retry.items():
            LOG.info("Retrying failed Resilient ACK for message %s", msgid)
            self._resilient_ack_delivery_failures[msgid]["retry_count"] = \
                self._resilient_ack_delivery_failures[msgid]["retry_count"] + 1
            self.fire(Send(headers=failure_info["result"]["headers"],
                           body=failure_info["result"]["body"],
                           destination=failure_info["result"]["destination"],
                           message_id=msgid))

    @handler("signal")
    def _on_signal(self, signo, stack):
        """We implement a default-event handler, which means we don't get default signal handling - add it back
           (see FallBackSignalHandler in circuits/core/helpers.py)
        """
        if signo in [SIGINT, SIGTERM]:
            raise SystemExit(0)

    @handler("SelftestTerminateEvent")
    def _selftest_terminate(self):
        """
        Exits resilient-circuits if a SelftestTerminateEvent
        is fired
        """
        LOG.info("SelftestTerminateEvent, exiting resilient-circuits")
        raise SystemExit(0)

    @handler("reload", priority=999)
    def reload(self, event, opts):
        """New config, check to see if num_workers has been changed, update pool if it has and is valid"""
        reloaded_num_workers = opts.get("num_workers", -1)
        if constants.MIN_NUM_WORKERS <= reloaded_num_workers <= constants.MAX_NUM_WORKERS:
            if reloaded_num_workers != self._num_workers:
                LOG.debug("The num_workers app.config setting has been changed from %s to %s.",
                          self._num_workers, reloaded_num_workers)
                # Unregister the existing worker thread-pool that will run functions.
                self._functionworker.unregister()
                # Re-create and register the new worker thread-pool that will run functions with new num_workers setting.
                self._functionworker = FunctionWorker(process=False, channel="functionworker",
                                                      workers=reloaded_num_workers)
                self._functionworker.register(self.root)
                # Update the instance attribute.
                self._num_workers = reloaded_num_workers
        else:
            LOG.error("The num_workers app.config setting has been changed to an invalid value %s",
                      reloaded_num_workers)

        """New config, reconnect to stomp if required"""
        event.success = False
        super(Actions, self).reload(event, opts)
        self._configure_opts(opts)
        if self.stomp_component:
            self.fire(Disconnect(flush=True, reconnect=False))
            yield self.wait("Disconnect_success")
            self._setup_stomp()
            yield self.wait("Connect_success")
            subscribe_event = Event.create("subscribe_to_all")
            self.fire(subscribe_event)
            yield self.wait(subscribe_event)
        event.success = True

    @handler("StatusMessageEvent", "FunctionErrorEvent")
    def _status(self, event, *args, **kwargs):
        """Report an interim status"""
        if not isinstance(event.parent, ActionMessageBase):
            return
        fevent = event.parent
        # Reply with interim status
        message = event.text
        if not message:
            message = "(No status)"
        if isinstance(event, FunctionErrorEvent):
            status = 1
            complete = True
            fevent.stop()  # Stop further event processing
        else:
            status = 0
            complete = False
        headers = fevent.hdr()
        message_id = headers.get('message-id', None)
        reply_to = headers['reply-to']
        correlation_id = headers['correlation-id']
        reply_message = json.dumps({"message_type": status,
                                    "message": message,
                                    "complete": complete})
        if not fevent.test:
            self.fire(Send(headers={'correlation-id': correlation_id},
                           body=reply_message,
                           destination=reply_to,
                           message_id=message_id))
        else:
            # Test action, nothing to Ack
            # Send a message back to the test client
            self.fire(Event.create("test_response", fevent.test_msg_id, reply_message), '*')
            LOG.debug("Test Action: No ack done.")

    @handler()
    def _on_event(self, event, *args, **kwargs):
        """Report the successful handling of an action event"""
        if isinstance(event.parent, ActionMessageBase) and event.name.endswith("_success"):
            fevent = event.parent
            headers = fevent.hdr()
            message_id = headers.get("message-id", None)

            if fevent.deferred:
                LOG.debug("Not acking deferred message %s", str(fevent))

            elif isinstance(fevent, InboundMessage):
                if not fevent.test:
                    LOG.debug("Acknowledging InboundMessage: %s for queue: %s", message_id, headers.get("subscription", "Unknown"))
                    self.fire(Ack(fevent.frame))
            else:
                value = event.parent.value.getValue()
                LOG.debug("success! %s, %s", value, fevent)
                fevent.stop()  # Stop further event processing

                # At completion, the value might be:
                # - None (if there was no handler or a handler just returned None)
                # - or a single thing, or a list; where each thing could be
                #   - a StatusMessage
                #   - a FunctionResult
                #   - a plain Python object: string, number, dictionary, etc
                # Custom Actions don't have any "result", so all the values are
                # concatenated into a status message.
                # Functions have a result as well as a status message.
                if not isinstance(value, list):
                    value = [value]
                function_result = None
                status_messages = []

                if isinstance(event.parent, ActionMessage):
                    # All the values become the status message.
                    for val in value:
                        if isinstance(val, StatusMessage):
                            status_messages.append(val)
                        elif val is not None and not isinstance(val, FunctionResult):
                            status_messages.append(StatusMessage(val))
                    # If the function didn't return a status message, let's make one.
                    if not status_messages:
                        status_messages.append(StatusMessage(u"No handler returned a result for this action"))

                if isinstance(event.parent, FunctionMessage):
                    # The first (and only the first!) FunctionResult is the result.
                    for val in value:
                        if isinstance(val, FunctionResult):
                            function_result = val
                            break
                    # If there was no FunctionResult, but there was a plain value, convert that to a FunctionResult
                    values = []
                    for val in value:
                        if function_result is None and \
                                not isinstance(val, FunctionResult) and \
                                not isinstance(val, StatusMessage):
                            function_result = FunctionResult(val)
                        else:
                            values.append(val)
                    # All the other values become the status message.
                    for val in values:
                        if isinstance(val, FunctionResult):
                            pass
                        elif isinstance(val, StatusMessage):
                            status_messages.append(val)
                        elif isinstance(val, string_types):
                            status_messages.append(StatusMessage(val))
                    # If the function didn't return a status message, let's make one.
                    if not status_messages:
                        status_messages.append(StatusMessage(u"Completed"))

                messages = []
                for status in status_messages:
                    try:
                        messages.append(str(status))
                    except:
                        messages.append(repr(status))
                message = "\n".join(messages)
                LOG.debug(u"Message: %s", message)
                status = 0
                headers = fevent.hdr()
                # Ack the message
                message_id = headers.get('message-id', None)
                if not fevent.test:
                    LOG.debug("Ack %s", message_id)
                    self.fire(Ack(fevent.frame, message_id=message_id))
                # Reply with success status
                reply_to = headers['reply-to']
                correlation_id = headers['correlation-id']
                # reply_message is an ActionAcknowledgementDTO
                reply_dto = {"message_type": status,
                             "message": message,
                             "complete": True}
                if function_result:
                    LOG.debug("[%s] Result: %s", function_result.name, function_result.value)
                    reply_dto["results"] = function_result.value
                reply_message = json.dumps(reply_dto, indent=2, default=lambda o: "<<non-serializable: {0}>>".format(type(o).__qualname__))
                if not fevent.test:
                    self.fire(Send(headers={'correlation-id': correlation_id},
                                   body=reply_message,
                                   destination=reply_to,
                                   message_id=message_id))
                else:
                    # Test action, nothing to Ack
                    if isinstance(event.parent, FunctionMessage):
                        # Send the value back to the test
                        result = Event.create("{}_result".format(event.parent.name), result=function_result)
                        result.parent = event.parent
                        self.fire(result, '*')
                    # Send a message back to the test client
                    self.fire(Event.create("test_response", fevent.test_msg_id, reply_message), '*')
                    LOG.debug("Test Action: No ack done.")
