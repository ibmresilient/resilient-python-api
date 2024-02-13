#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

import copy
import logging
from random import randint
from multiprocessing.pool import ThreadPool

from mock import patch
from resilient_circuits import constants, rest_helper

from resilient import SimpleHTTPException
from resilient import constants as res_constants

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

    rest_helper.reset_resilient_client()

    opts = copy.deepcopy(mock_constants.MOCK_OPTS)

    opts.update({
        res_constants.APP_CONFIG_MAX_CONNECTION_RETRIES: 10,
        res_constants.APP_CONFIG_REQUEST_MAX_RETRIES: 10,
        res_constants.APP_CONFIG_REQUEST_RETRY_DELAY: 10,
        res_constants.APP_CONFIG_REQUEST_RETRY_BACKOFF: 10
    })

    res_client = rest_helper.get_resilient_client(opts, log_version=False)

    assert res_client.max_connection_retries == 10
    assert res_client.request_max_retries == 10
    assert res_client.request_retry_delay == 10
    assert res_client.request_retry_backoff == 10

@patch("resilient_circuits.rest_helper.get_resilient_server_version") # use this method as a proxy to count misses
def test_resilient_client_cache(patch_get_client):

    opts = copy.deepcopy(mock_constants.MOCK_OPTS)
    opts["cafile"] = False # to be used to flip later to trigger cache miss

    rest_helper.reset_resilient_client()
    res_client = rest_helper.get_resilient_client(opts, log_version=False)
    old_org_id = res_client.org_id

    for _ in range(rest_helper.CACHE_SIZE - 1):
        client = rest_helper.get_resilient_client(opts, log_version=False)
        assert client is res_client # make sure same exact object
        client.org_id = old_org_id - 100 # move org_id around on new client and assert same on old client
        assert client.org_id == res_client.org_id
        client.org_id = old_org_id # reset org_id

    opts["cafile"] = not opts["cafile"]
    new_cafile_client = rest_helper.get_resilient_client(opts, log_version=False)
    assert new_cafile_client is not res_client

    # test reset
    rest_helper.reset_resilient_client(opts)
    assert patch_get_client.call_count == 2

    # create new that won't be found
    assert rest_helper.get_resilient_client(opts, log_version=False) is not res_client

def test_resilient_client_cached_in_threads():
    client_count = rest_helper.CACHE_SIZE * 2 # double size of cache to ensure not all will be found
    thread_pool = ThreadPool(client_count)
    rest_helper.reset_resilient_client()

    def threaded_func(host):
        opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        opts["host"] = host
        rest_helper.get_resilient_client(opts, log_version=False)

    mock_hosts = ["{0}.{0}.{0}.{0}".format(i) for i in range(client_count)]
    thread_pool.map(threaded_func, mock_hosts) # apply threaded func to all mocked hosts


    opts = copy.deepcopy(mock_constants.MOCK_OPTS)
    opts["host"] = "0.0.0.0" # this was the first, but should be a miss
    rest_helper.get_resilient_client(opts, log_version=False)

@patch("resilient_circuits.rest_helper.get_resilient_server_version") # use this method as a proxy to count misses
def test_reset_resilient_client(patch_get_client):
    opts = copy.deepcopy(mock_constants.MOCK_OPTS)
    rest_helper.reset_resilient_client()

    opts["cafile"] = False # to be used to flip later to trigger cache miss
    res_client = rest_helper.get_resilient_client(opts, log_version=False)

    opts["cafile"] = not opts["cafile"]
    new_cafile_client = rest_helper.get_resilient_client(opts, log_version=False)
    # check two different clients and size of cache matches that info
    assert new_cafile_client is not res_client
    assert patch_get_client.call_count == 2
    assert rest_helper.CACHE.currsize == 2

    # test reset with opts
    rest_helper.reset_resilient_client(opts)
    assert rest_helper.CACHE.currsize == 1

    # test reset without opts (clears whole cache)
    rest_helper.reset_resilient_client()
    assert rest_helper.CACHE.currsize == 0

def test_reset_resilient_client_with_threads():
    client_count = rest_helper.CACHE_SIZE // 2 # half size of cache to ensure there will be some hits
    thread_pool = ThreadPool(client_count)
    rest_helper.reset_resilient_client()

    mod = 3

    def threaded_func(host):
        opts = copy.deepcopy(mock_constants.MOCK_OPTS)
        opts["host"] = host
        rest_helper.get_resilient_client(opts)
        num = randint(0,5)
        if num % mod == 0: # every so often reset the client based on random number
            rest_helper.reset_resilient_client(opts)

    mock_hosts = ["0.0.0.{0}".format(i % mod) for i in range(client_count)]
    thread_pool.map(threaded_func, mock_hosts) # apply threaded func to all mocked hosts


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
