#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import pytest
from circuits import Event
from mock import patch
from resilient_lib import IntegrationError
from resilient_circuits import ResilientComponent, app_function, StatusMessage, FunctionResult, SubmitTestFunction
from tests import helpers, mock_constants, AppFunctionMockComponent

resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


class TestAppFunctionDecorator:

    def test_basic_decoration(self):
        assert AppFunctionMockComponent._app_function_mock_one.handler is True
        assert AppFunctionMockComponent._app_function_mock_one.function is True
        assert AppFunctionMockComponent._app_function_mock_one.names == (mock_constants.MOCK_APP_FN_NAME_ONE,)
        assert AppFunctionMockComponent._app_function_mock_one.priority == 0
        assert AppFunctionMockComponent._app_function_mock_one.channel == u"functions." + mock_constants.MOCK_APP_FN_NAME_ONE
        assert AppFunctionMockComponent._app_function_mock_one.override is False
        assert AppFunctionMockComponent._app_function_mock_one.event is True

    def test_runs(self, circuits_app):
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_ONE, {"input_one": "abc"}, circuits_app)

    def test_handles_FunctionResult(self, circuits_app):
        mock_fn_inputs = {"input_one": u"abc", "input_two": u"unicode ઠ ડ ઢ ણ ત થ દ ધ ન પ ફ input"}
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        mock_results = helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_ONE, mock_fn_inputs, circuits_app)

        assert mock_results["version"] == 2.0
        assert mock_results["success"] is True
        assert mock_results["reason"] is None
        assert mock_results["inputs"]["input_one"] == mock_fn_inputs["input_one"]
        assert mock_results["inputs"]["input_two"] == mock_fn_inputs["input_two"]
        assert mock_results["content"]["malware"] is True

    def test_handles_StatusMessage(self, circuits_app):
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        mock_status_message = helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_ONE, {"input_one": "abc"}, circuits_app, status_message_only=True)
        assert mock_status_message.text == u"Mock զ է ը թ ժ ի լ StatusMessage 1"

    def test_handles_Exception(self, circuits_app):
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        with pytest.raises(IntegrationError, match=r"mock error message with unicode"):
            helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_EX, {"input_one": "abc"}, circuits_app)

    def test_too_many_function_names(self):
        with pytest.raises(ValueError, match=r"Usage: @app_function\(api_name\)"):
            class AppFunctionMockComponent2(ResilientComponent):
                @app_function("mock_function_2", "mock_function_3")
                def mock_function_2(self, fn_inputs, **kwargs):
                    return
