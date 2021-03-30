#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_lib import IntegrationError
from tests import helpers, mock_constants, MockInboundAppComponent


resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


def test_inbound_cmp_raises_error_no_app_configs(circuits_app):
    mock_cmp = MockInboundAppComponent(opts=mock_constants.MOCK_OPTS)
    mock_cmp.app_configs = None
    mock_cmp.register(circuits_app.app.component_loader)
    with pytest.raises(IntegrationError, match=r"does not have app_configs defined"):
        helpers.call_inbound_app(circuits_app, mock_constants.MOCK_INBOUND_Q_NAME)
