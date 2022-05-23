#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

from resilient import constants as res_constants
from resilient_circuits import constants


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
