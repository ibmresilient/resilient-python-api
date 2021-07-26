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

import os
import copy
import sys
import pytest
import pkg_resources
from resilient import constants as res_constants


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