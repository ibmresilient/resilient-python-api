# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.

"""Circuits component for Action Module subscription and message handling"""

from inspect import getargspec
import circuits.core.handlers


# for convenience we alias the circuits 'handler'
handler = circuits.core.handlers.handler


def function(*names, **kwargs):
    """Creates a Function Handler.

    This decorator can be applied to methods of classes derived from :class:`ResilientComponent`.
    It marks the method as a handler for the events passed as arguments to the :func:`function` decorator.
    Specify the function's API name as parameter to the decorator.
    The function handler will automatically be subscribed to the function's message destination.
    """
    # This is an extended copy of circuits.core.handlers:handler
    def wrapper(f):
        if names and isinstance(names[0], bool) and not names[0]:
            f.handler = False
            return f

        if not names:
            raise ValueError("Function name must be specified.")

        f.handler = True
        f.function = True

        # Circuits properties
        f.names = names
        f.priority = kwargs.get("priority", 0)
        f.channel = kwargs.get("channel", ",".join(["functions.{}".format(name) for name in names]))
        f.override = kwargs.get("override", False)

        # Resilient properties that define the function's interface
        f.function_definition_def = kwargs.get("definition", None)
        f.function_parameters_def = kwargs.get("parameters", None)

        args = getargspec(f)[0]

        if args and args[0] == "self":
            del args[0]
        f.event = getattr(f, "event", bool(args and args[0] == "event"))

        return f

    return wrapper


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
