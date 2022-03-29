#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

"""
Common place for helper functions used in tests
"""

from resilient_circuits import SubmitTestInboundApp, SubmitTestFunction, FunctionResult


def call_app_function(fn_name, fn_inputs, circuits_app, status_message_only=False, full_result_obj=False):

    assert isinstance(fn_inputs, dict)

    # Create the submitTestFunction event
    evt = SubmitTestFunction(fn_name, fn_inputs)

    # Fire a message to the function
    circuits_app.manager.fire(evt)

    # circuits will fire an "exception" event if an exception is raised in the ResilientComponent
    # return this exception if it is raised
    exception_event = circuits_app.watcher.wait("exception", parent=None, timeout=2)

    if exception_event:
        exception = exception_event.args[1]
        raise exception

    if status_message_only:
        status_message_event = circuits_app.watcher.wait("StatusMessageEvent", parent=None, timeout=2)
        return status_message_event.value.event

    event = circuits_app.watcher.wait(fn_name + u"_result", parent=evt, timeout=2)
    result = event.kwargs.get("result")
    assert isinstance(result, FunctionResult)

    if full_result_obj:
        return result

    return result.value


def call_inbound_app(circuits_app, queue_name, action="create", msg_content={}, message=None):
# TODO: add doc string
    evt = SubmitTestInboundApp(queue_name, action, msg_content, message)

    # Fire a message to the inbound app
    circuits_app.manager.fire(evt)

    # circuits will fire an "exception" event if an exception is raised in the ResilientComponent
    # return this exception if it is raised
    exception_event = circuits_app.watcher.wait("exception", parent=None, timeout=2)

    if exception_event:
        exception = exception_event.args[1]
        raise exception

    event = circuits_app.watcher.wait(queue_name + u"_success", parent=evt, timeout=2)

    if event:
        return event.args

    return False
