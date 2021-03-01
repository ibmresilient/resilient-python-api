#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import pytest
import re
from circuits import Event
from mock import patch
from resilient_lib import IntegrationError
from resilient_circuits import ResilientComponent, app_function, StatusMessage, FunctionResult, SubmitTestFunction
from tests import helpers


MOCK_PACKAGE_NAME = u"mock_function_package"
MOCK_FN_NAME = u"mock_function"
resilient_mock = u"pytest_resilient_circuits.BasicResilientMock"

config_data = """[{0}]
url = https://www.example.com""".format(MOCK_PACKAGE_NAME)

mock_opts = {
    "host": "192.168.0.1",
    "org": "Test Organization",
    "email": "admin@example.com",
    "password": "123",
    "resilient_mock": resilient_mock
}


class MockComponent(ResilientComponent):

    PACKAGE_NAME = MOCK_PACKAGE_NAME

    @app_function(MOCK_FN_NAME)
    def mock_function(self, fn_inputs, **kwargs):
        yield StatusMessage(u"Mock զ է ը թ ժ ի լ StatusMessage 1")
        yield StatusMessage(u"Mock StatusMessage 2")
        yield FunctionResult({"malware": True})

    @app_function(MOCK_FN_NAME + u"raise_exception")
    def mock_function_raise_exception(self, fn_inputs, **kwargs):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")


def test_app_function_basic_decoration():
    assert MockComponent.mock_function.handler is True
    assert MockComponent.mock_function.function is True
    assert MockComponent.mock_function.names == (MOCK_FN_NAME,)
    assert MockComponent.mock_function.priority == 0
    assert MockComponent.mock_function.channel == u"functions." + MOCK_FN_NAME
    assert MockComponent.mock_function.override is False
    assert MockComponent.mock_function.event is True


def test_app_function_runs(circuits_app):
    MockComponent(opts=mock_opts).register(circuits_app.app.component_loader)
    helpers.call_fn(MOCK_FN_NAME, {"input_one": "abc"}, circuits_app)


def test_app_function_handles_FunctionResult(circuits_app):
    mock_fn_inputs = {"input_one": u"abc", "input_two": u"unicode ઠ ડ ઢ ણ ત થ દ ધ ન પ ફ input"}
    MockComponent(opts=mock_opts).register(circuits_app.app.component_loader)
    mock_results = helpers.call_fn(MOCK_FN_NAME, mock_fn_inputs, circuits_app)

    assert mock_results["version"] == "1.0"
    assert mock_results["success"] is True
    assert mock_results["reason"] is None
    assert mock_results["inputs"]["input_one"] == mock_fn_inputs["input_one"]
    assert mock_results["inputs"]["input_two"] == mock_fn_inputs["input_two"]
    assert mock_results["content"]["malware"] is True


def test_app_function_handles_StatusMessage(circuits_app):
    MockComponent(opts=mock_opts).register(circuits_app.app.component_loader)
    mock_status_message = helpers.call_fn(MOCK_FN_NAME, {"input_one": "abc"}, circuits_app, status_message_only=True)
    assert mock_status_message.text == u"Mock զ է ը թ ժ ի լ StatusMessage 1"


def test_app_function_handles_Exception(circuits_app):
    regex = re.compile(r'mock error message with unicode զ է ը թ ժ ի լ խ', re.U)
    MockComponent(opts=mock_opts).register(circuits_app.app.component_loader)
    with pytest.raises(IntegrationError, match=regex):
        helpers.call_fn(MOCK_FN_NAME + u"raise_exception", {"input_one": "abc"}, circuits_app)


def test_too_many_function_names():
    with pytest.raises(ValueError, match=r"Usage: @app_function\(api_name\)"):
        class MockComponent2(ResilientComponent):
            @app_function("mock_function_2", "mock_function_3")
            def mock_function_2(self, fn_inputs, **kwargs):
                return
