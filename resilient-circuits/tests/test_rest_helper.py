#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

import copy

from .shared_mock_data import mock_constants
from resilient import constants as res_constants
from resilient_circuits import constants, rest_helper


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

def test_get_resilient_server_version(fx_mock_resilient_client):

    const = fx_mock_resilient_client.get_const()
    assert "major" in const.get("server_version", {})
    assert "minor" in const.get("server_version", {})
