# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
"""Function implementation"""

import logging
from resilient_circuits import ResilientComponent, handler, inbound_app
from resilient_lib import IntegrationError
from tests import mock_constants


LOG = logging.getLogger(__name__)
PACKAGE_NAME = "fn_main_mock_integration"
QUEUE_NAME = "mock_inbound_q"


class MockInboundAppComponent(ResilientComponent):
    """Component that implements Resilient function 'mock_function_one''"""

    def __init__(self, opts):
        """constructor provides access to the configuration options"""
        super(MockInboundAppComponent, self).__init__(opts)
        self.app_configs = opts.get(PACKAGE_NAME, {})

    @handler("reload")
    def _reload(self, event, opts):
        """Configuration options have changed, save new values"""
        self.app_configs = opts.get(PACKAGE_NAME, {})

    @inbound_app(QUEUE_NAME)
    def _inbound_app_mock_one(self, message, inbound_action):

        if inbound_action == "create":
            msg_content = message.get("content", {})
            LOG.info(u"Creating incident\nIncident Description: %s", msg_content.get("description", "None"))

        elif inbound_action == "close":
            LOG.info(u"Closing incident")

        elif inbound_action == "update":
            LOG.info(u"Updating incident")

        elif inbound_action == "artifact_added":
            LOG.info(u"Updating incident")

        else:
            LOG.error(u"Unsupported functionality. Message: %s", message)

        yield "Done!"

    @inbound_app(mock_constants.MOCK_INBOUND_Q_NAME)
    def inbound_app_mock(self, message, inbound_action):
        assert isinstance(message, dict)
        yield inbound_action

    @inbound_app(mock_constants.MOCK_INBOUND_Q_NAME_CREATE)
    def inbound_app_mock_create(self, message, inbound_action):
        assert inbound_action == "create"
        assert isinstance(message, dict)
        yield u"Mock incident created with unicode զ է ը թ"

    @inbound_app(mock_constants.MOCK_INBOUND_Q_NAME_EX)
    def inbound_app_mock_raise_exception(self, message, inbound_action):
        raise IntegrationError(u"mock error message with unicode զ է ը թ ժ ի լ խ")
