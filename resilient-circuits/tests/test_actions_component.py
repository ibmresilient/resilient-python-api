#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2021. All Rights Reserved.

import pytest
from mock import patch
from resilient_circuits import helpers
from resilient_circuits.actions_component import Actions
from resilient_circuits.stomp_events import HeartbeatTimeout
from resilient_lib import IntegrationError

from tests import MockInboundAppComponent
from tests import helpers as test_helpers
from tests import mock_constants
from tests.shared_mock_data import mock_paths

resilient_mock = mock_constants.RESILIENT_MOCK
config_data = mock_constants.CONFIG_DATA


def test_inbound_cmp_raises_error_no_app_configs(circuits_app):
    mock_cmp = MockInboundAppComponent(opts=mock_constants.MOCK_OPTS)
    mock_cmp.app_configs = None
    mock_cmp.register(circuits_app.app.component_loader)
    with pytest.raises(IntegrationError, match=r"does not have app_configs defined"):
        test_helpers.call_inbound_app(circuits_app, mock_constants.MOCK_INBOUND_Q_NAME)


@patch("resilient_circuits.actions_component.helpers.get_fn_names", new=lambda x: [])
def test_actions_on_heartbeat_timeout_no_config(circuits_app, fx_simple_client, caplog):

    mock_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG)
    mock_configs.pop("heartbeat_timeout_threshold")

    with patch("resilient_circuits.actions_component.ResilientComponent.rest_client") as mock_client:
        mock_client.return_value = fx_simple_client[0]
        mock_actions_cmp = Actions(opts=mock_configs)

        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(1))
        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(2))
        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(3))
        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(4))
        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(5))

        assert "Trying to reconnect after STOMP HeartbeatTimeout" in caplog.text
        assert "exiting..." not in caplog.text


@patch("resilient_circuits.actions_component.helpers.get_fn_names", new=lambda x: [])
def test_actions_on_heartbeat_timeout_with_config_set(circuits_app, fx_simple_client, caplog):

    mock_configs = helpers.get_configs(path_config_file=mock_paths.MOCK_APP_CONFIG)

    with patch("resilient_circuits.actions_component.ResilientComponent.rest_client") as mock_client:
        mock_client.return_value = fx_simple_client[0]
        mock_actions_cmp = Actions(opts=mock_configs)

        mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(10))
        assert "Trying to reconnect after STOMP HeartbeatTimeout" in caplog.text

        with pytest.raises(SystemExit) as sys_exit:
            mock_actions_cmp.on_heartbeat_timeout(HeartbeatTimeout(20))

        exit_msg = "'{0}' is set to '{1}s' and '{2}s' have passed since the first HeartbeatTimeout, exiting...".format(
            "heartbeat_timeout_threshold", "5", "10"
        )

        assert exit_msg in caplog.text
        assert sys_exit.type == SystemExit
        assert sys_exit.value.code == 34
