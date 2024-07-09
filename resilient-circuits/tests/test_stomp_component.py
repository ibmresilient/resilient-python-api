#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging

import pytest
from mock import MagicMock, patch
from stomp.exception import ConnectFailedException, StompException

from resilient_circuits import constants
from resilient_circuits.stomp_component import StompClient


def test_stomp_reconnect_two_consecutive_failures(caplog):

    client = StompClient(host="example.com", port=443)

    assert client._stomp_max_connection_errors == constants.STOMP_MAX_CONNECTION_ERRORS

    # standard successfull connection
    mock_evt = MagicMock()
    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.connect") as patch_stomp_library_connect:
        with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
            patch_stomp_library_connect.side_effect = None
            patch_connected_state.return_value = True
            client.connect(mock_evt)


            # first a StompConnectionError with a different error (this could be possible in real world)
            patch_stomp_library_connect.side_effect = ConnectFailedException("A different STOMP error")
            client.connect(mock_evt)
            assert client._stomp_connection_errors == 0

            # now a StompConnectionError with "no more data" error
            # this should trigger the max, and throw a sys.exit(1)
            patch_stomp_library_connect.side_effect = ConnectFailedException("Some preamble. No more data received from STOMP")
            with pytest.raises(SystemExit):
                client.connect(mock_evt)
                assert "Exiting due to unrecoverable error" in caplog.text
            assert client._stomp_connection_errors == 1

def test_stomp_reconnect_one_failure_followed_by_successful_reconnect(caplog):

    max_connection_errors_override = 5
    client = StompClient(host="example.com", port=443, stomp_max_connection_errors=max_connection_errors_override)

    assert client._stomp_max_connection_errors == max_connection_errors_override

    # standard successful connection
    mock_evt = MagicMock()
    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.connect") as patch_stomp_library_connect:
        with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
            patch_stomp_library_connect.side_effect = None
            patch_connected_state.return_value = True
            client.connect(mock_evt)

            # as we've changed the max_connection errors limit to 5, run this 4 times but
            # then reconnect successfully and observe it is reset to 0
            for i in range(max_connection_errors_override-1):
                # first StompConnectionError with "no more data" error
                patch_stomp_library_connect.side_effect = ConnectFailedException("No more data received from STOMP")
                client.connect(mock_evt)
                assert client._stomp_connection_errors == i+1

            # successful reconnect now should reset count to 0
            patch_stomp_library_connect.side_effect = None
            client.connect(mock_evt)
            assert client._stomp_connection_errors == 0

# def test_stomp_client_logging_check_server_heartbeat(caplog):
#     caplog.set_level(logging.DEBUG)

#     client = StompClient(host="example.com", port=443)

#     # standard successfull connection
#     mock_evt = MagicMock()

#     client.check_server_heartbeat(mock_evt)
#     assert "Checking server heartbeat" in caplog.text

# def test_stomp_client_logging_send_heartbeat(caplog):
#     caplog.set_level(logging.DEBUG)

#     client = StompClient(host="example.com", port=443)

#     # standard successfull connection
#     mock_evt = MagicMock()

#     with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
#         patch_connected_state.return_value = True

#         client.send_heartbeat(mock_evt)
#         assert "Sending client heartbeat" in caplog.text

# def test_stomp_client_logging_generate_events(caplog):
#     caplog.set_level(logging.DEBUG)

#     client = StompClient(host="example.com", port=443)

#     # standard successfull connection
#     mock_evt = MagicMock()

#     with patch("resilient_circuits.stomp_component.StompClient.connected") as patch_connected_state:
#         with patch("resilient_circuits.stomp_component.stomp.StompConnection12.canRead") as patch_can_read:
#             with patch("resilient_circuits.stomp_component.stomp.StompConnection12.receiveFrame") as patch_receive_frame:
#                 patch_connected_state.return_value = True
#                 patch_can_read.return_value = True
#                 patch_receive_frame.side_effect = None

#                 client.generate_events(mock_evt)
#                 assert "Received frame" in caplog.text

def test_stomp_client_logging_send_success(caplog):
    caplog.set_level(logging.DEBUG)

    client = StompClient(host="example.com", port=443)

    # standard successfull connection
    mock_evt = MagicMock()

    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.send") as patch_send:

        client.send(mock_evt, "dest", "")
        patch_send.assert_called()
        patch_send.assert_called_once_with("dest", body=b"", headers=None, receipt=None)


def test_stomp_client_logging_send_error(caplog):
    caplog.set_level(logging.DEBUG)

    client = StompClient(host="example.com", port=443)

    # standard successfull connection
    mock_evt = MagicMock()

    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.send") as patch_send:
        patch_send.side_effect = StompException("A different STOMP error")

        with pytest.raises(StompException):
            client.send(mock_evt, "dest", "")
        assert "Error sending frame" in caplog.text

def test_stomp_client_logging_ack_frame_success(caplog):
    caplog.set_level(logging.DEBUG)

    client = StompClient(host="example.com", port=443)

    # standard successfull connection
    mock_evt = MagicMock()
    mock_frame = MagicMock()

    mock_ack_dest = "actions.201.fn_mock"
    mock_frame.headers.get.return_value = mock_ack_dest

    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.ack") as patch_send:

        client.ack_frame(mock_evt, mock_frame)
        patch_send.assert_called()
        patch_send.assert_called_once_with(mock_ack_dest)

def test_stomp_client_logging_ack_frame_error(caplog):
    caplog.set_level(logging.DEBUG)

    client = StompClient(host="example.com", port=443)

    # standard successfull connection
    mock_evt = MagicMock()
    mock_frame = MagicMock()

    with patch("resilient_circuits.stomp_component.stomp.StompConnection12.ack") as patch_send:
        patch_send.side_effect = StompException("A different STOMP error")

        with pytest.raises(StompException):
            client.ack_frame(mock_evt, mock_frame)
        assert "Error sending ack" in caplog.text

