#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import logging
import os
import pytest
from resilient_circuits import (ResilientComponent, app_function, constants,
                                inbound_app)
from resilient_circuits.action_message import FunctionException_
from resilient_lib import IntegrationError

from tests import (AppFunctionMockComponent, MockFunctionComponent,
                   MockInboundAppComponent, helpers, mock_constants)

resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


class TestFunctionDecorator:

    def test_runs(self, circuits_app):
        MockFunctionComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        results = helpers.call_app_function(mock_constants.MOCK_FN_NAME_ONE, {"input_one": "abc"}, circuits_app)
        assert results.get("content").get("malware") is True

    def test_handles_StatusMessage(self, circuits_app):
        MockFunctionComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        mock_status_message = helpers.call_app_function(mock_constants.MOCK_FN_NAME_ONE, {"input_one": "abc"}, circuits_app, status_message_only=True)
        assert mock_status_message.text == u"Mock զ է ը թ ժ ի լ StatusMessage 1"

    def test_fn_trap_exception_False(self, circuits_app):
        MockFunctionComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)

        with pytest.raises(FunctionException_, match=r"mock error message with unicode"):
            helpers.call_app_function(mock_constants.MOCK_FN_NAME_EX, {"input_one": "abc"}, circuits_app)


class TestInboundAppDecorator:

    def test_basic_decoration(self):
        assert MockInboundAppComponent.inbound_app_mock.handler is True
        assert MockInboundAppComponent.inbound_app_mock.inbound_handler is True
        assert MockInboundAppComponent.inbound_app_mock.names == (mock_constants.MOCK_INBOUND_Q_NAME,)
        assert MockInboundAppComponent.inbound_app_mock.priority == 0
        assert MockInboundAppComponent.inbound_app_mock.channel == "{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, mock_constants.MOCK_INBOUND_Q_NAME)
        assert MockInboundAppComponent.inbound_app_mock.override is False
        assert MockInboundAppComponent.inbound_app_mock.event is True

    def test_inbound_app_mock_runs(self, circuits_app):
        MockInboundAppComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        event_args = helpers.call_inbound_app(circuits_app, mock_constants.MOCK_INBOUND_Q_NAME_CREATE)
        assert event_args[1] == [u"Mock incident created with unicode զ է ը թ"]

    def test_inbound_app_mock_handles_Exception(self, circuits_app):
        MockInboundAppComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        with pytest.raises(IntegrationError, match=r"mock error message with unicode"):
            helpers.call_inbound_app(circuits_app, mock_constants.MOCK_INBOUND_Q_NAME_EX)

    def test_too_many_q_names(self):
        with pytest.raises(ValueError, match=r"Usage: @inbound_app\(<inbound_destination_api_name>\)"):
            class MockInboundAppComponent2(ResilientComponent):
                @inbound_app("mock_q_2", "mock_q_3")
                def inbound_app_mock_2(self, message, *args, **kwargs):
                    return


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

    def test_handles_FunctionResult(self, circuits_app, fx_reset_environmental_variables, caplog):
        caplog.set_level(logging.DEBUG)
        # set mock env value for normal secret
        secret_key = "STANDARD_SECRET"
        secret_value = "superdupersecret"
        os.environ[secret_key] = secret_value

        mock_fn_inputs = {"input_one": u"abc", "input_two": u"unicode ઠ ડ ઢ ણ ત થ દ ધ ન પ ફ input", "input_three": "$"+secret_key}
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        mock_result_obj = helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_ONE, mock_fn_inputs, circuits_app, full_result_obj=True)

        assert mock_result_obj.name == "app_function_mock_one"
        assert mock_result_obj.success is True
        assert mock_result_obj.reason is None

        mock_results = mock_result_obj.value

        assert mock_results["version"] == 2.0
        assert mock_results["success"] is True
        assert mock_results["reason"] is None
        assert mock_results["inputs"]["input_one"] == mock_fn_inputs["input_one"]
        assert mock_results["inputs"]["input_two"] == mock_fn_inputs["input_two"]
        assert mock_results["inputs"]["input_three"] == mock_fn_inputs["input_three"]
        assert mock_results["inputs"]["input_three"] != secret_value
        assert "$"+secret_key in caplog.text # original inputs are logged at debug level
        assert secret_value not in caplog.text # secret, if found, should never be logged
        assert mock_results["content"]["malware"] is True

    def test_handles_StatusMessage(self, circuits_app):
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        mock_status_message = helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_ONE, {"input_one": "abc"}, circuits_app, status_message_only=True)
        assert mock_status_message.text == u"Mock զ է ը թ ժ ի լ StatusMessage 1"

    def test_app_trap_exception_False(self, circuits_app):
        AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
        with pytest.raises(IntegrationError, match=r"mock error message with unicode"):
            helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_EX, {"input_one": "abc"}, circuits_app)

    def test_too_many_function_names(self):
        with pytest.raises(ValueError, match=r"Usage: @app_function\(api_name\)"):
            class AppFunctionMockComponent2(ResilientComponent):
                @app_function("mock_function_2", "mock_function_3")
                def mock_function_2(self, fn_inputs, **kwargs):
                    return


def test_fn_trap_exception_True(circuits_app):
    circuits_app.app.opts[constants.APP_CONFIG_TRAP_EXCEPTION] = True
    MockFunctionComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app.component_loader)
    results = helpers.call_app_function(mock_constants.MOCK_FN_NAME_EX, {"input_one": "abc"}, circuits_app)
    assert results.get("success") is False
    assert "mock error message with unicode" in results.get("reason")


def test_app_trap_exception_False(circuits_app):
    circuits_app.app.opts[constants.APP_CONFIG_TRAP_EXCEPTION] = False
    AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app)

    with pytest.raises(IntegrationError, match=r"mock error message with unicode"):
        helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_EX, {"input_one": "abc"}, circuits_app)


def test_app_custom_result_True(circuits_app):
    circuits_app.app.opts[constants.APP_CONFIG_TRAP_EXCEPTION] = False
    AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS).register(circuits_app.app)
    results = helpers.call_app_function(mock_constants.MOCK_APP_FN_NAME_CUSTOM_RESULT, {"input_one": "abc"}, circuits_app)
    assert results.get("custom_key", "") == "custom_value"
