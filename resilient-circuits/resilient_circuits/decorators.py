# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Circuits component for Action Module subscription and message handling"""

import logging
import threading
import inspect as _inspect
from functools import wraps
from types import GeneratorType
from circuits import Timer, task, Event
import circuits.core.handlers
from resilient_circuits.action_message import FunctionResult, \
    StatusMessage, StatusMessageEvent, \
    FunctionError_, FunctionErrorEvent

LOG = logging.getLogger(__name__)

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
                LOG.debug("%s: _call_the_task", threading.currentThread().name)
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
