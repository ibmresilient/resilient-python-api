#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_lib import IntegrationError
from resilient_circuits import StatusMessage
from tests import mock_constants, AppFunctionMockComponent


resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


def test_status_message(circuits_app):
    mock_msg = u"Custom message with unicode լ խ ծ կ հ ձ ղ ճ"
    mock_cmp = AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS)
    mock_status_message = mock_cmp.status_message(mock_msg)
    assert isinstance(mock_status_message, StatusMessage)
    assert mock_status_message.text == mock_msg
