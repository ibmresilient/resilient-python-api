#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

import io
import os
import json
from tests.shared_mock_data import mock_paths


def test_post_attachment_file_path(fx_base_client, fx_mk_temp_dir):

    incident_id = 1001
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}/attachments'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"result": "attached"}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))

    uri = "/incidents/{0}/attachments".format(incident_id)
    temp_file_name = "mock_attachment.txt"
    temp_file_path = os.path.join(mock_paths.TEST_TEMP_DIR, temp_file_name)

    with open(temp_file_path, mode="w", encoding="utf-8") as temp_file:
        temp_file.write("This is a mock file")

    r = base_client.post_attachment(
        uri=uri,
        filepath=temp_file_path,
        filename=temp_file_name
    )

    assert r.get("result") == "attached"


def test_post_attachment_bytes_handle(fx_base_client):

    incident_id = 1001
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}/attachments'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"result": "attached"}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))

    uri = "/incidents/{0}/attachments".format(incident_id)
    temp_file_name = "mock_attachment.txt"
    bytes_handle = io.BytesIO(b"these are mock bytes")

    r = base_client.post_attachment(
        uri=uri,
        filepath=None,
        filename=temp_file_name,
        bytes_handle=bytes_handle
    )

    assert r.get("result") == "attached"
