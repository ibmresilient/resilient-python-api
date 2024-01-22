#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import copy
import logging

from mock import patch
from resilient_circuits import constants, rest_helper

from resilient import constants as res_constants, SimpleHTTPException

from .shared_mock_data import mock_constants


def test_resilient_client_has_custom_headers(fx_mock_resilient_client):
    headers = fx_mock_resilient_client.headers

    assert headers.get("content-type") == "application/json"
    assert headers.get(res_constants.HEADER_MODULE_VER_KEY) == res_constants.HEADER_MODULE_VER_VALUE
    assert headers.get(constants.HEADER_CIRCUITS_VER_KEY) == constants.HEADER_CIRCUITS_VER_VALUE


def test_resilient_client_make_headers_has_custom_header(fx_mock_resilient_client):
    headers = fx_mock_resilient_client.make_headers()
    assert headers.get("content-type") == "application/json"
    assert headers.get(res_constants.HEADER_MODULE_VER_KEY) == res_constants.HEADER_MODULE_VER_VALUE
    assert headers.get(constants.HEADER_CIRCUITS_VER_KEY) == constants.HEADER_CIRCUITS_VER_VALUE


def test_resilient_client_retry_args():

    if rest_helper.resilient_client:
        rest_helper.resilient_client = None

    opts = copy.deepcopy(mock_constants.MOCK_OPTS)

    opts.update({
        res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES: 10,
        res_constants.APP_CONFIG_REQUEST_MAX_RETRIES: 10,
        res_constants.APP_CONFIG_REQUEST_RETRY_DELAY: 10,
        res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF: 10
    })

    res_client = rest_helper.get_resilient_client(opts)

    assert res_client.max_connection_retries == 10
    assert res_client.request_max_retries == 10
    assert res_client.request_retry_delay == 10
    assert res_client.request_retry_backoff == 10

def test_get_resilient_server_version_old_style(fx_mock_resilient_client):

    version = rest_helper.get_resilient_server_version(fx_mock_resilient_client)
    assert version == "47.0.8304"

def test_get_resilient_server_version_new_style(fx_mock_resilient_client):

    with patch("resilient.co3.SimpleClient.get_const") as mock_const:
        # for now, leaving default test value at 47.0 so we need to patch in the new style
        # server_version to test with. only patching that, not the whole get_const() object
        mock_const.return_value = {
            "server_version": {
                "v": "51",
                "r": "2",
                "m": "3",
                "f": "4",
                "build_number": "5678",
                "major": "0",
                "minor": "0",
                "version": "51.2.3.4.5678"
            }
        }
        version = rest_helper.get_resilient_server_version(fx_mock_resilient_client)
        assert version == "51.2.3.4.5678"

def test_get_resilient_server_version_not_fond(fx_mock_resilient_client, caplog):
    caplog.set_level(logging.DEBUG)

    def raise_simple_http_exception():
        class FakeResponse:
            reason = None
            text = None
        raise SimpleHTTPException(FakeResponse())

    with patch("resilient.co3.SimpleClient.get_const") as mock_const:
        # for now, leaving default test value at 47.0 so we need to patch in the new style
        # server_version to test with. only patching that, not the whole get_const() object
        mock_const.side_effect = raise_simple_http_exception
        version = rest_helper.get_resilient_server_version(fx_mock_resilient_client)
        assert version == None
        assert "Failed to retrieve version from SOAR server. Continuing gracefully..." in caplog.text