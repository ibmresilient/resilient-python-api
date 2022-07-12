#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from resilient_lib import IntegrationError, RequestsCommon
from resilient_circuits import StatusMessage
from tests import mock_constants, AppFunctionMockComponent


resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


def test_basic_instantiation(circuits_app):
    mock_cmp = AppFunctionMockComponent(
        opts=mock_constants.MOCK_OPTS,
        package_name=mock_constants.MOCK_PACKAGE_NAME,
        required_app_configs=mock_constants.MOCK_REQUIRED_APP_CONFIGS)

    assert mock_cmp.PACKAGE_NAME == mock_constants.MOCK_PACKAGE_NAME
    assert mock_cmp.opts == mock_constants.MOCK_OPTS
    assert mock_cmp.required_app_configs == mock_constants.MOCK_REQUIRED_APP_CONFIGS
    assert isinstance(mock_cmp.rc, RequestsCommon)
    assert mock_cmp.app_configs.url == "https://www.mockexample.com"
    assert mock_cmp.options == mock_cmp._app_configs_as_dict


def test_status_message(circuits_app):
    mock_msg = u"Custom message with unicode լ խ ծ կ հ ձ ղ ճ"
    mock_cmp = AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS)
    mock_status_message = mock_cmp.status_message(mock_msg)
    assert isinstance(mock_status_message, StatusMessage)
    assert mock_status_message.text == mock_msg


def test_log_message(circuits_app, caplog):
    mock_msg = u"Custom message with unicode լ խ ծ կ հ ձ ղ ճ"
    mock_cmp = AppFunctionMockComponent(opts=mock_constants.MOCK_OPTS, package_name=mock_constants.MOCK_PACKAGE_NAME)
    mock_cmp.LOG.info(mock_msg)
    assert mock_msg in caplog.text
