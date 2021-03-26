#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import pytest
from circuits import Event
from mock import patch
from resilient_lib import IntegrationError
from resilient_circuits import constants, ResilientComponent, inbound_app
from tests import helpers


MOCK_PACKAGE_NAME = u"mock_function_package"
MOCK_INBOUND_Q_NAME = u"mock_inbound_q_name"
MOCK_INBOUND_Q_NAME_CREATE = u"{0}_{1}".format(MOCK_INBOUND_Q_NAME, "create")
MOCK_INBOUND_Q_NAME_EX = u"{0}_{1}".format(MOCK_INBOUND_Q_NAME, "raise_exception")


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


class MockInboundAppComponent(ResilientComponent):

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(MockInboundAppComponent, self).__init__(opts)
        self.app_configs = opts.get(MOCK_PACKAGE_NAME, {})

    @inbound_app(MOCK_INBOUND_Q_NAME)
    def inbound_app_mock(self, message, inbound_action):
        assert isinstance(message, dict)
        yield inbound_action

    @inbound_app(MOCK_INBOUND_Q_NAME_CREATE)
    def inbound_app_mock_create(self, message, inbound_action):
        assert inbound_action == "create"
        assert isinstance(message, dict)
        yield u"Mock incident created with unicode զ է ը թ"

    @inbound_app(MOCK_INBOUND_Q_NAME_EX)
    def inbound_app_mock_raise_exception(self, message, inbound_action):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")


class TestInboundAppDecorator:

    def test_basic_decoration(self):
        assert MockInboundAppComponent.inbound_app_mock.handler is True
        assert MockInboundAppComponent.inbound_app_mock.inbound_handler is True
        assert MockInboundAppComponent.inbound_app_mock.names == (MOCK_INBOUND_Q_NAME,)
        assert MockInboundAppComponent.inbound_app_mock.priority == 0
        assert MockInboundAppComponent.inbound_app_mock.channel == "{0}.{1}".format(constants.INBOUND_MSG_DEST_PREFIX, MOCK_INBOUND_Q_NAME)
        assert MockInboundAppComponent.inbound_app_mock.override is False
        assert MockInboundAppComponent.inbound_app_mock.event is True

    def test_inbound_app_mock_runs(self, circuits_app):
        MockInboundAppComponent(opts=mock_opts).register(circuits_app.app.component_loader)
        event_args = helpers.call_inbound_app(circuits_app, MOCK_INBOUND_Q_NAME_CREATE)
        assert event_args[1] == [u"Mock incident created with unicode զ է ը թ"]

    def test_inbound_app_mock_handles_Exception(self, circuits_app):
        MockInboundAppComponent(opts=mock_opts).register(circuits_app.app.component_loader)
        with pytest.raises(IntegrationError, match=r"mock error message with unicode"):
            helpers.call_inbound_app(circuits_app, MOCK_INBOUND_Q_NAME_EX)

    def test_too_many_q_names(self):
        with pytest.raises(ValueError, match=r"Usage: @inbound_app\(<inbound_destination_api_name>\)"):
            class MockInboundAppComponent(ResilientComponent):
                @inbound_app("mock_q_2", "mock_q_3")
                def inbound_app_mock_2(self, message, *args, **kwargs):
                    return
