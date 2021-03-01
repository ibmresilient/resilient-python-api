#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_circuits import ResilientComponent, app_function, StatusMessage, FunctionResult, FunctionMessage, SubmitTestFunction
from circuits import Event
import os

# TODO: global vars for PACKAGE_NAME and FN_NAME

resilient_mock = "pytest_resilient_circuits.BasicResilientMock"

config_data = """[mock_function]
url = https://www.example.com"""

mock_opts = {
    "resilient_mock": "pytest_resilient_circuits.BasicResilientMock",
    "org": "Test Organization",
    "email": "admin@example.com",
    "password": "123",
    "host": "192.168.0.1"
}


class MockComponent(ResilientComponent):

    PACKAGE_NAME = "mock_function"

    @app_function("mock_function")
    def mock_function(self, fn_inputs, **kwargs):
        yield StatusMessage("Mock StatusMessage 1")
        yield StatusMessage("Mock StatusMessage 2")
        yield FunctionResult({"malware": True})


def call_fn(circuits_app):

    # Create the submitTestFunction event
    evt = SubmitTestFunction("mock_function", {"input_one": "abc"})

    # Fire a message to the function
    circuits_app.manager.fire(evt)

    # circuits will fire an "exception" event if an exception is raised in the ResilientComponent
    # return this exception if it is raised
    exception_event = circuits_app.watcher.wait("exception", parent=None, timeout=2)

    if exception_event is not False:
        exception = exception_event.args[1]
        raise exception

    # else return the ResilientComponent's results
    else:
        event = circuits_app.watcher.wait("mock_function_result", parent=evt, timeout=2)
        assert event
        assert isinstance(event.kwargs["result"], FunctionResult)
        pytest.wait_for(event, "complete", True)
        return event.kwargs["result"].value


def test_app_function_basic_decoration():
    assert MockComponent.mock_function.handler is True
    assert MockComponent.mock_function.function is True
    assert MockComponent.mock_function.names == ("mock_function",)
    assert MockComponent.mock_function.priority == 0
    assert MockComponent.mock_function.channel == "functions.mock_function"
    assert MockComponent.mock_function.override is False
    assert MockComponent.mock_function.event is True


def test_app_function_validates_fn_inputs():
    # TODO
    pass


def test_app_function_runs_2(circuits_app):
    # TODO
    MockComponent(opts=mock_opts).register(circuits_app.app.component_loader)
    mock_results = call_fn(circuits_app)


def test_app_function_handles_FunctionResult():
    # TODO
    pass


def test_app_function_handles_StatusMessage():
    # TODO
    pass


def test_app_function_handles_Exception():
    # TODO
    pass


def test_too_many_function_names():
    with pytest.raises(ValueError, match=r"Usage: @app_function\(api_name\)"):
        class MockComponent2(ResilientComponent):
            @app_function("mock_function_2", "mock_function_3")
            def mock_function_2(self, fn_inputs, **kwargs):
                return
