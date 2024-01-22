#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2020. All Rights Reserved.

"""
Shared pytest fixtures

Note:
    -   Code after the 'yield' statement in a fixture
        is ran after the test (or scope i.e. test session) has complete
    -   fx_ prefixes a 'fixture'
    -   Put fixture logic in separate 'private' function so we
        can share logic between fixtures
    -   Fixture must have BEFORE and AFTER docstring
"""

import copy
import os
import sys

import pkg_resources
import pytest
import requests_mock
from resilient import ImportDefinition
from resilient import constants as res_constants
from resilient.co3 import SimpleClient

from tests.shared_mock_data import mock_paths


@pytest.fixture
def fx_simple_client():
    """
    Before: Creates sample SimpleClient object with mocked URI https://example.com
    After: Nothing
    """
    simple_client = SimpleClient(org_name="Mock Org", base_url="https://example.com")
    requests_adapter = requests_mock.Adapter()
    simple_client.session.mount(u'https://', requests_adapter)
    simple_client.org_id = 201

    mock_inc_fields_uri = "{0}/rest/orgs/{1}/types/incident/fields".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('GET', mock_inc_fields_uri, status_code=200, json={})

    mock_action_fields_uri = "{0}/rest/orgs/{1}/types/actioninvocation/fields".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('GET', mock_action_fields_uri, status_code=200, json={})

    mock_actions_uri = "{0}/rest/orgs/{1}/actions".format(simple_client.base_url, simple_client.org_id)
    requests_adapter.register_uri('GET', mock_actions_uri, status_code=200, json={"entities": []})

    yield (simple_client, requests_adapter)


@pytest.fixture
def fx_clear_cmd_line_args():
    """
    Before: Clear command line arguments
    After: Set the cmd line args back to its original value
    """
    original_cmd_line = copy.deepcopy(sys.argv)

    sys.argv = [sys.argv[0]]

    yield

    sys.argv = original_cmd_line


@pytest.fixture
def fx_add_entry_point(ep_str, path_dist):
    """
    Before: get original pkg_resources.working_set + add Entry Point at path_dist
    After: set pkg_resources.working_set to original

    Params:
        ep_str: str e.g. "mock_component:MockInboundComponent"
        path_dist: str e.g. "user/resilient-circuits/tests/shared_mock_data"
    """
    original_working_set = copy.deepcopy(pkg_resources.working_set)

    ep_name = ep_str.split(":")[1]

    distribution = pkg_resources.Distribution(path_dist)
    ep_obj = pkg_resources.EntryPoint.parse("{0}={1}".format(ep_name, ep_str), dist=distribution)
    distribution._ep_map = {'resilient.circuits.components': {ep_name: ep_obj}}
    pkg_resources.working_set.add(distribution)

    yield

    pkg_resources.working_set = original_working_set


@pytest.fixture
def fx_add_proxy_env_var():
    """
    Before: set HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    After: unset HTTPS_PROXY, HTTP_PROXY and NO_PROXY
    """
    os.environ[res_constants.ENV_HTTPS_PROXY] = "https://192.168.0.5:3128"
    os.environ[res_constants.ENV_HTTP_PROXY] = "http://192.168.0.5:3128"
    os.environ[res_constants.ENV_NO_PROXY] = "subdomain.example.com,192.168.1.5,.example.com"

    yield

    os.environ[res_constants.ENV_HTTPS_PROXY] = ""
    os.environ[res_constants.ENV_HTTP_PROXY] = ""
    os.environ[res_constants.ENV_NO_PROXY] = ""


@pytest.fixture
def fx_read_mock_definition():
    """
    Before: reads the mock_import_definition.txt file and yields an ImportDefinition of it
    After: N/A
    """
    with open(mock_paths.MOCK_IMPORT_DEFINITION, mode="r") as f:
        lines = f.readlines()
        b64 = "\n".join(lines)

    yield ImportDefinition(b64)


@pytest.fixture
def fx_reset_environmental_variables():
    """
    Before: Create a deepcopy of current env variables
    After: Set the current env variables back to their original

    Used in a test where we want to modify the env vars and avoid leaking into other tests
    """
    current_env = copy.deepcopy(os.environ)

    yield

    os.environ = current_env
