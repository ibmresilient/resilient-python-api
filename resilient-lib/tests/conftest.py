#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2024. All Rights Reserved.

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

import io
import json
import logging
import os
import re

import pytest
import requests
import requests_mock
from tests.shared_mock_data import mock_paths

LOG = logging.getLogger(__name__)

def _load_json_file(file_path):
    with io.open(file_path, 'r', encoding="utf-8") as template_file:
        return json.load(template_file)

def _split_file_name_into_rest_components(file_name):
    components = file_name.strip().split("_", 3)

    # follow very rigid structure.
    # Ex: "200_JSON_GET__attachments.json" -> 200, GET, /attachments
    # Ex: "404_JSON_POST__types_artifact.json" -> 404, POST, /types/artifact
    resp_code = components[0]
    method = components[2]

    resource_path = components[-1].rsplit(".", 1)[0].replace("_", "/")

    return int(resp_code), method, resource_path


def _load_all_json_files_into_endpoints():
    all_endpoints = {}
    for base_path, _dir_names, file_names in os.walk(mock_paths.MOCK_RESPONSES_DIR):
        for file_name in file_names:
            file_path = os.path.join(base_path, file_name)
            json_content = _load_json_file(file_path)

            rest_comps = _split_file_name_into_rest_components(file_name)

            all_endpoints[file_name] = {
                "json": json_content,
                "status": rest_comps[0],
                "method": rest_comps[1],
                "path": rest_comps[2]
            }

    return all_endpoints

def _custom_matcher(request, endpoint):
    path = endpoint.get("path")
    status = endpoint.get("status")
    method = endpoint.get("method")
    json_data = endpoint.get("json")
    # soar_mock.register_uri(method, path, status_code=status, json=json_data)
    if request.method == method and re.search(path, request.url):
        resp = requests.Response()
        resp.status_code = status
        resp.raw = io.BytesIO(str.encode(json.dumps(json_data)))
        return resp

    return None

@pytest.fixture(scope="function")
def fx_soar_adapter():
    """
    This adapter takes the files found in /tests/shared_mock_data/mock_responses
    to construct a SOAR adapter. To add new endpoints or data to the mock,
    add new files following the same structure there.

    Ex:
        "200_JSON_GET__attachments.json" -> 200, GET, /attachments
        "404_JSON_POST__types_artifact.json" -> 404, POST, /types/artifact
    """

    with requests_mock.Mocker() as soar_mock:

        endpoints = _load_all_json_files_into_endpoints()
        for ep in endpoints:
            endpoint = endpoints.get(ep)
            soar_mock.add_matcher(lambda request, endpoint=endpoint: _custom_matcher(request, endpoint))

        yield soar_mock