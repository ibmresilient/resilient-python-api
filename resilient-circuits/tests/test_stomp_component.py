#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import pytest
from mock import MagicMock, patch

from resilient_circuits.stomp_component import StompClient, StompConnectionError
from resilient_circuits.stomp_events import ConnectionFailed
from resilient_circuits import constants

def test_stomp_reconnect_two_consecutive_failures(caplog):

    client = StompClient(host="example.com", port=443)

    assert client._stomp_max_connection_errors == constants.STOMP_MAX_CONNECTION_ERRORS

    # standard successfull connection
    mock_evt = MagicMock()
    with patch("resilient_circuits.stomp_component.Stomp.connect") as patch_stomp_library_connect:
        with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
            patch_stomp_library_connect.side_effect = None
            patch_connected_state.return_value = True
            client.connect(mock_evt)


            # first a StompConnectionError with a different error (this could be possible in real world)
            patch_stomp_library_connect.side_effect = StompConnectionError("A different STOMP error")
            client.connect(mock_evt)
            assert client._stomp_connection_errors == 0

            # now a StompConnectionError with "no more data" error
            # this should trigger the max, and throw a sys.exit(1)
            patch_stomp_library_connect.side_effect = StompConnectionError("Some preamble. No more data received from STOMP")
            with pytest.raises(SystemExit):
                client.connect(mock_evt)
                assert "Exiting due to unrecoverable error" in caplog.text
            assert client._stomp_connection_errors == 1

def test_stomp_reconnect_one_failure_followed_by_successful_reconnect(caplog):

    max_connection_errors_override = 5
    client = StompClient(host="example.com", port=443, stomp_max_connection_errors=max_connection_errors_override)

    assert client._stomp_max_connection_errors == max_connection_errors_override

    # standard successfull connection
    mock_evt = MagicMock()
    with patch("resilient_circuits.stomp_component.Stomp.connect") as patch_stomp_library_connect:
        with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
            patch_stomp_library_connect.side_effect = None
            patch_connected_state.return_value = True
            client.connect(mock_evt)

            # as we've changed the max_connection errors limit to 5, run this 4 times but
            # then reconnect successfully and observe it is reset to 0
            for i in range(max_connection_errors_override-1):
                # first StompConnectionError with "no more data" error
                patch_stomp_library_connect.side_effect = StompConnectionError("No more data received from STOMP")
                client.connect(mock_evt)
                assert client._stomp_connection_errors == i+1

            # successful reconnect now should reset count to 0
            patch_stomp_library_connect.side_effect = None
            client.connect(mock_evt)
            assert client._stomp_connection_errors == 0