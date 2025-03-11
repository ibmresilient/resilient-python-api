# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Circuits component for Action Module subscription and message handling"""

import inspect as _inspect
import logging
import threading
from collections import namedtuple
from functools import wraps
from types import GeneratorType

import circuits.core.handlers
from circuits import Event, Timer, task
from resilient_circuits import constants, helpers
from resilient_circuits.action_message import (FunctionError_,
                                               FunctionErrorEvent,
                                               FunctionResult, LowCodeResult,
                                               StatusMessage,
                                               StatusMessageEvent)
from resilient_circuits.filters import RedactingFilter
from resilient_lib import LowCodePayload, ResultPayload, validate_fields

LOG = logging.getLogger(__name__)
LOG.addFilter(RedactingFilter())

# for convenience we alias the circuits 'handler'
handler = circuits.core.handlers.handler


class function(object):
    """Creates a Function Handler.

    This decorator can be applied to methods of classes derived from :class:`ResilientComponent`.
    It marks the method as a handler for the events passed as arguments to the :func:`function` decorator.
    Specify the function's API name as parameter to the decorator.
    The function handler will automatically be subscribed to the function's message destination.
    """
    # This is an extended version of circuits.core.handlers:handler

    def __init__(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError("Usage: @function(api_name)")
        self.names = args
        self.kwargs = kwargs

    def __call__(self, func):
        """Called at decoration time, with the bare function being decorated"""
        LOG.debug("@function %s", func)

        func.handler = True
        func.function = True

        # Circuits properties
        func.names = self.names
        func.priority = self.kwargs.get("priority", 0)
        func.channel = self.kwargs.get("channel", ",".join(["functions.{}".format(name) for name in self.names]))
        func.override = self.kwargs.get("override", False)

        # If getfullargspec if available to us
        if hasattr(_inspect, 'getfullargspec'):
            args = _inspect.getfullargspec(func)[0]
        else:  # fall back to deprecated getargspec
            args = _inspect.getargspec(func)[0]

        if args and args[0] == "self":
            del args[0]
        func.event = getattr(func, "event", bool(args and args[0] == "event"))

        @wraps(func)
        def decorated(itself, event, *args, **kwargs):
            """the decorated function"""
            LOG.debug("decorated")
            function_parameters = event.message.get("inputs", {})

            def _the_task(event, *args, **kwargs):
                return func(itself, event, *args, **kwargs)

            def _call_the_task(evt, **kwds):
                # On the worker thread, call the function, and handle a single or generator result.
                LOG.debug("%s: _call_the_task", threading.current_thread().name)
                result_list = []
                task_result_or_gen = _the_task(evt, *args, **kwds)
                if not isinstance(task_result_or_gen, GeneratorType):
                    task_result_or_gen = [task_result_or_gen]
                for val in task_result_or_gen:
                    if isinstance(val, StatusMessage):
                        # Fire the wrapped status message event to notify resilient
                        LOG.info("[%s] StatusMessage: %s", evt.name, val)
                        itself.fire(StatusMessageEvent(parent=evt, message=val.text))
                    elif isinstance(val, FunctionResult):
                        # Collect the result for return
                        LOG.debug("[%s] FunctionResult: %s", evt.name, val)
                        val.name = evt.name
                        result_list.append(val)
                    elif isinstance(val, Event):
                        # Some other event, just fire it
                        LOG.debug(val)
                        itself.fire(val)
                    elif isinstance(val, FunctionError_):
                        LOG.error("[%s] FunctionError: %s", evt.name, val)
                        itself.fire(FunctionErrorEvent(parent=evt, message=str(val)))
                        evt.success = False
                        return  # Don't wait for more results!
                    elif isinstance(val, Exception):
                        raise val
                    else:
                        # Whatever this is, add it to the results
                        LOG.debug(val)
                        result_list.append(val)
                return result_list

            the_task = task(_call_the_task, event, **function_parameters)
            ret = yield itself.call(the_task, "functionworker")
            xxx = ret.value
            # Return value is the result_list that was yielded from the wrapped function
            yield xxx
        return decorated


class inbound_app(object):
    def __init__(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError("Usage: @inbound_app(<{0}>)".format(constants.INBOUND_MSG_APP_CONFIG_Q_NAME))
        self.names = args
        self.kwargs = kwargs

    def __call__(self, ia):
        """
        Called at decoration time, with the bare method being decorated

        :param ia: The method to decorate
        :type ia: resilient_circuits.ResilientComponent
        """
        ia.handler = True
        ia.inbound_handler = True

        # Circuits properties
        ia.names = self.names
        ia.priority = self.kwargs.get("priority", 0)
        ia.channel = "{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, self.names[0])
        ia.override = self.kwargs.get("override", False)
        ia.event = True

        @wraps(ia)
        def inbound_app_decorator(itself, event, *args, **kwargs):
            """
            The decorated method

            :param itself: The method to decorate
            :type itself: resilient_circuits.ResilientComponent
            :param event: The Event with the StompFrame and the Message read off the Message Destination
            :type event: resilient_circuits.action_message.InboundMessage
            """

            def _invoke_inbound_app(evt, **kwds):
                """
                The code to call when a method with the decorator `@inbound_app(<inbound_destination_api_name>)`
                is invoked.

                Returns result_list when method with the decorator `@inbound_app(<inbound_destination_api_name>)` is
                finished processing.

                A method that has this handler should yield a str when done
                    -  E.g:
                        `yield "Processing Complete!"`

                The method that is wrapped with this handler should will receive three items:
                    - message
                    - headers
                    - inbound action

                The subclass of ``ResilientComponent`` is also required to set the
                ``app_configs`` attribute.

                Example:

                .. code-block:: python

                    class SoarInboundConsumer(ResilientComponent):
                        def __init__(self, opts):
                            super(SoarInboundConsumer, self).__init__(opts)
                            self.opts = opts
                            self.app_configs = opts.get(PACKAGE_NAME, {})

                        @inbound_app(QUEUE_NAME)
                        def _inbound_soar_escalator(self, message, headers, inbound_action):
                            pass

                :param evt: The Event with the StompFrame and the Message read off the Message Destination
                :type ia: resilient_circuits.action_message.FunctionMessage
                """
                result_list = []
                LOG.debug("Running _invoke_inbound_app in Thread: %s", threading.current_thread().name)

                # Invoke the actual Function
                # Pass along the message, the headers, and the action if present in the message
                ia_results = ia(itself, evt.message, evt.headers, evt.message.get("action", "Unknown"))

                for r in ia_results:
                    LOG.debug(r)
                    result_list.append(r)

                return result_list

            invoke_inbound_app = task(_invoke_inbound_app, event)
            ia_result = yield itself.call(invoke_inbound_app, "functionworker")
            yield ia_result.value

        return inbound_app_decorator


class app_function(object):
    """
    Creates a new :class:`@app_function <app_function>` decorator.

    This decorator can be applied to methods of the :class:`~resilient_circuits.app_function_component.AppFunctionComponent` class.

    It marks the method as a handler for the events passed as arguments to the decorator.

    Specify the function's API name as parameter to the decorator. **It only accepts 1** ``api_name`` **as an argument.**

    The function handler will automatically be subscribed to the function's ``message destination``.
    """

    def __init__(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError("Usage: @app_function(api_name)")
        self.names = args
        self.kwargs = kwargs

    def __call__(self, fn):
        """
        Called at decoration time, with the bare function being decorated

        :param fn: The function to decorate
        :type fn: resilient_circuits.ResilientComponent
        """
        fn.handler = True
        fn.function = True

        # Circuits properties
        fn.names = self.names
        fn.priority = self.kwargs.get("priority", 0)
        fn.channel = "functions.{0}".format(self.names[0])
        fn.override = self.kwargs.get("override", False)
        fn.event = True

        @wraps(fn)
        def app_function_decorator(itself, event, *args, **kwargs):
            """
            The decorated function

            :param itself: The function to decorate
            :type itself: resilient_circuits.ResilientComponent
            :param event: The Event with the StompFrame and the Message read off the Message Destination
            :type event: resilient_circuits.action_message.FunctionMessage
            """
            function_inputs = event.message.get("inputs", {})

            def _invoke_app_function(evt, **kwds):
                """
                The code to call when a function with the decorator `@app_function(api_name)`
                is invoked.

                Returns result_list when function with the decorator `@app_function(api_name)` is
                finished processing.

                A method that has this handler should yield a StatusMessage or a FunctionResult
                    -   When a StatusMessage is yield'ed a StatusMessageEvent is fired with the text of the StatusMessage
                    -   When a FunctionResult is yield'ed it calls resilient-lib.ResultPayload.done() with the parameters of
                        FunctionResult being passed to it and appends the result to result_list. E.g:
                            `yield FunctionResult({"key":"value"})`
                            `yield FunctionResult({"key": "value"}, success=False, reason="Bad call")`

                :param evt: The Event with the StompFrame and the Message read off the Message Destination
                :type fn: resilient_circuits.action_message.FunctionMessage
                """
                LOG.debug("Running _invoke_app_function in Thread: %s", threading.current_thread().name)

                result_list = []

                # Validate the fn_inputs in the Message
                fn_inputs = validate_fields([], kwds)
                LOG.info("[%s] Validated function inputs", evt.name)
                LOG.debug("[%s] fn_inputs: %s", evt.name, fn_inputs)

                rp = ResultPayload(itself.PACKAGE_NAME, version=constants.APP_FUNCTION_PAYLOAD_VERSION, **fn_inputs)

                # make sure to sub AFTER the ResultPayload is instantiated so that any subbed values
                # won't be logged or included in the returned inputs.
                # substitute any secrets denoted with $, ^, ${}, or ^{} in the function inputs.
                # NOTE: it is crucial to first "validate_fields" as that function will convert any
                # non-string fields that should be strings to strings (like select)
                fn_inputs = helpers.sub_fn_inputs_from_protected_secrets(fn_inputs, itself.opts)
                fn_inputs_tuple = namedtuple("fn_inputs", fn_inputs.keys())(*fn_inputs.values())

                # Set evt.message in local thread storage
                itself.set_fn_msg(evt.message)

                # Invoke the actual Function
                fn_results = fn(itself, fn_inputs_tuple)

                for r in fn_results:
                    if isinstance(r, StatusMessage):
                        LOG.info("[%s] StatusMessage: %s", evt.name, r)
                        itself.fire(StatusMessageEvent(parent=evt, message=r.text))

                    elif isinstance(r, FunctionResult):
                        r.name = evt.name
                        if not r.custom_results:
                            r.value = rp.done(
                                content=r.value,
                                success=r.success,
                                reason=r.reason)
                        LOG.info("[%s] Returning results", r.name)
                        result_list.append(r)

                    elif isinstance(r, Exception):
                        raise r

                    else:
                        # Whatever this is, add it to the results
                        LOG.debug(r)
                        result_list.append(r)

                return result_list

            invoke_app_function = task(_invoke_app_function, event, **function_inputs)
            fn_result = yield itself.call(invoke_app_function, "functionworker")
            yield fn_result.value

        return app_function_decorator


class low_code_function(object):
    """
    Decorator for the low code framework when running through app host.
    The decorator takes optional low-code queues as arguments, however,
    generally those queue names are defined in the app.config and loaded
    in dynamically at component binding time (in component_loader.py).

    NOTE: results from a ``low_code_function`` function can either be of type
    ``FunctionResult`` or ``LowCodeResult``. The eventual result will be cast to a
    ``LowCodeResult`` before being built to a ``LowCodePayload`` object
    and returned to the queue in SOAR.

    Example use:

    .. code-block::

        class FunctionComponent(AppFunctionComponent):

            def __init__(self, opts):
                super(FunctionComponent, self).__init__(opts, PACKAGE_NAME)

            @low_code_function()
            def _run_low_code(self, fn_inputs):
                yield self.status_message("Low Code execution started")
                ...
                yield FunctionResult({"results": "value"})

    :param object: _description_
    :type object: _type_
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        # because this has to be set dynamically based on app.config values,
        # names is set in component loader
        self.names = args

    def __call__(self, fn):
        """
        Called at decoration time, with the bare function being decorated

        :param fn: The function to decorate
        :type fn: resilient_circuits.ResilientComponent
        """
        fn.handler = True
        fn.low_code_handler = True


        # Circuits properties
        fn.names = self.names
        fn.priority = self.kwargs.get("priority", 0)
        fn.channel = constants.LOW_CODE_MSG_DEST_PREFIX
        fn.override = self.kwargs.get("override", False)
        fn.event = True

        @wraps(fn)
        def low_code_decorator(itself, event, *args, **kwargs):
            low_code_message = event.message    # {"request_originator": {}, "request_payload": {}}
            invoke_low_code_function = task(_invoke_low_code_function, event, itself, fn, **low_code_message)
            fn_result = yield itself.call(invoke_low_code_function, "functionworker")
            yield fn_result.value

        return low_code_decorator

def _invoke_low_code_function(event, app_fn_component_obj, the_function, **kwds):
    LOG.debug("Running _invoke_low_code_function in Thread: %s", threading.current_thread().name)

    result_list = []

    # Validate the fn_inputs in the Message
    connector_inputs = validate_fields(["request_originator","request_payload"], kwds)
    LOG.info("[%s] Validated connector inputs", event.name)
    LOG.debug("[%s] connector_inputs: %s", event.name, connector_inputs)

    lc_payload = LowCodePayload(app_fn_component_obj.PACKAGE_NAME, version=constants.LOW_CODE_PAYLOAD_VERSION, **connector_inputs)

    connector_inputs = helpers.sub_fn_inputs_from_protected_secrets(connector_inputs, app_fn_component_obj.opts)

    # Set evt.message in local thread storage
    app_fn_component_obj.set_fn_msg(event.message)

    # Pull out the request_payload, this is all we need to execute the request
    low_code_request = connector_inputs.get("request_payload")

    # Invoke the actual Function
    fn_results = the_function(app_fn_component_obj, low_code_request)

    for result in fn_results:
        # if a FunctionResult comes through, convert it to a LowCodeResult
        # first before continuing with the rest of the result processing
        if isinstance(result, FunctionResult):
            result = LowCodeResult.from_function_result(result)

        # handle the result as necessary; send status message, or ack result
        if isinstance(result, StatusMessage):
            LOG.info("[%s] StatusMessage: %s", event.name, result)
            app_fn_component_obj.fire(StatusMessageEvent(parent=event, message=result.text))

        elif isinstance(result, LowCodeResult):
            result.name = event.name
            if not result.custom_results:
                result.value = lc_payload.done(
                    content=result.value.get("content"),
                    success=result.success,
                    reason=result.reason,
                    content_type=low_code_request.get("response_content_type", None),
                    status_code=result.value.get("status_code"))
            LOG.info("[%s] Returning results", result.name)
            result_list.append(result)

        elif isinstance(result, Exception):
            raise result

        else:
            # Whatever this is, add it to the results
            LOG.debug(result)
            result_list.append(result)

    return result_list

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
       This decorator should go *before* the `@handler(...)`.
       Do not use on 'generic' handlers, only on named-event handlers.

       .. code-block:: python

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
            """the decorated function"""
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

       :param delay: (seconds).  Time before the event will be processed.
                  If another event (with the same key) occurs in this
                  time, the timer starts over.
       :param discard: (Boolean, optional).  If true, when there are multiple
                  events before the delay expires, only the most recent one
                  is processed, and the previous ones are discarded.

       Usage:
       Decorate a Resilient Circuits handler.
       This decorator should go *before* the `@handler(...)`.
       Do not use on 'generic' handlers, only on named-event handlers.

       .. code-block:: python

            @debounce(delay=10, discard=True)
            @handler("actions_event_name")
            def _my_action_handler(self, event, *args, **kwargs):
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
            """the decorated function"""
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
