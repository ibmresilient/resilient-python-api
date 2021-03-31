#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import os
import pytest
from resilient_lib import IntegrationError
from resilient_circuits import constants, ResilientComponent, inbound_app
from tests import helpers, mock_constants, MockInboundAppComponent


resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


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
