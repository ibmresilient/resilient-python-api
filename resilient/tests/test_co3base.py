#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import io
import json
import os
import sys

import pytest
import requests
from tests import helpers
from tests.shared_mock_data import mock_paths

from resilient import constants
from resilient.co3base import BasicHTTPException, RetryHTTPException


def test_set_api_key_authorized(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = "{0}/rest/session".format(base_client.base_url)
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(helpers.get_mock_response("session")))

    base_client.org_name = "Test Organization"
    base_client.set_api_key("123", "456")

    assert base_client.api_key_handle == 4
    assert base_client.org_id == 201


def test_set_api_key_unauthorized(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = "{0}/rest/session".format(base_client.base_url)
    requests_adapter.register_uri('GET', mock_uri, status_code=401)

    with pytest.raises(SystemExit) as sys_exit:
        base_client.set_api_key("123", "456")

    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == constants.ERROR_CODE_CONNECTION_UNAUTHORIZED


def test_set_api_key_retry(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.max_connection_retries = 3
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = "{0}/rest/session".format(base_client.base_url)
    requests_adapter.register_uri('GET', mock_uri, status_code=300)

    with pytest.raises(RetryHTTPException):
        base_client.set_api_key("123", "456")

    assert "retrying in 1 seconds" in caplog.text
    assert len(requests_adapter.request_history) == base_client.max_connection_retries


def test_extract_org_id_cloud_account(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = "73c78395-470f-46a8-af7d-5e7d999a5707"

    mock_response = helpers.get_mock_response("session")

    base_client._extract_org_id(mock_response)

    assert base_client.org_id == 201
    assert len(base_client.all_orgs) == 2


def test_extract_org_id_uuid(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = "61d7ae97-450b-4258-baa3-99b02308b52e"

    mock_response = helpers.get_mock_response("session")

    base_client._extract_org_id(mock_response)

    assert base_client.org_id == 202
    assert len(base_client.all_orgs) == 2


def test_extract_org_id_org_name(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = "Test Organization"

    mock_response = helpers.get_mock_response("session")
    base_client._extract_org_id(mock_response)

    assert base_client.org_id == 201
    assert len(base_client.all_orgs) == 2


def test_extract_org_id_no_orgs(fx_base_client):
    base_client = fx_base_client[0]

    with pytest.raises(Exception, match=r"User is not a member of any orgs"):
        base_client._extract_org_id({"orgs": []})


def test_extract_org_id_no_app_config_value(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = ""

    mock_response = helpers.get_mock_response("session")

    with pytest.raises(Exception, match=r"The user is a member of the following organizations: 'Test Organization'"):
        base_client._extract_org_id(mock_response)


def test_extract_org_id_not_member(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = "Not a Member of this Org"

    mock_response = helpers.get_mock_response("session")

    with pytest.raises(Exception, match=r"The user is not a member of the specified organization"):
        base_client._extract_org_id(mock_response)


def test_extract_org_id_disabled_org(fx_base_client):
    base_client = fx_base_client[0]
    base_client.org_name = "Disabled Org"

    mock_response = helpers.get_mock_response("session")

    with pytest.raises(Exception, match=r"This organization is not accessible to you"):
        base_client._extract_org_id(mock_response)


def test_connect_authorized(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = "{0}/rest/session".format(base_client.base_url)
    requests_adapter.register_uri("POST", mock_uri, status_code=200, text=json.dumps(helpers.get_mock_response("session")), cookies={"JSESSIONID": "abc"})

    base_client.org_name = "Test Organization"
    r = base_client._connect()

    assert r.get("user_id") == 1


def test_connect_retry(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.max_connection_retries = 3
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = "{0}/rest/session".format(base_client.base_url)
    requests_adapter.register_uri("POST", mock_uri, status_code=300)

    with pytest.raises(RetryHTTPException):
        base_client._connect()

    assert "retrying in 1 seconds" in caplog.text
    assert len(requests_adapter.request_history) == base_client.max_connection_retries


def test_get(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.get("/incidents/1001")

    assert r.get("incident_id") == 1001


def test_get_retry(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, 1001)
    requests_adapter.register_uri('GET', mock_uri, status_code=300)

    with pytest.raises(RetryHTTPException, match=r"Response Code: 300"):
        base_client.get("/incidents/1001")

    assert "retrying in 1 seconds" in caplog.text

def test_get_retry_skip(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, 1001)
    requests_adapter.register_uri('GET', mock_uri, status_code=404)

    with pytest.raises(BasicHTTPException, match=r"Response Code: 404"):
        base_client.get("/incidents/1001", skip_retry=[404])


def test_get_const_old_style_version(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = '{0}/rest/const'.format(base_client.base_url)
    mock_response = {"server_version": {"major": 47, "minor": 0, "build_number": 8304, "version": "47.0.8304"}}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.get_const()

    assert r.get("server_version", {}).get("major") == 47
    assert r.get("server_version", {}).get("minor") == 0
    assert r.get("server_version", {}).get("build_number") == 8304
    assert r.get("server_version", {}).get("version") == "47.0.8304"

def test_get_const_new_style_version(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    mock_uri = '{0}/rest/const'.format(base_client.base_url)
    mock_response = {"server_version": {"v": 51,
            "r": 2,
            "m": 3,
            "f": 4,
            "build_number": 5678,
            "major": 0,
            "minor": 0,
            "version": "51.2.3.4.5678"}}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.get_const()

    assert r.get("server_version", {}).get("v") == 51
    assert r.get("server_version", {}).get("r") == 2
    assert r.get("server_version", {}).get("m") == 3
    assert r.get("server_version", {}).get("f") == 4
    assert r.get("server_version", {}).get("build_number") == 5678
    assert r.get("server_version", {}).get("version") == "51.2.3.4.5678"


def test_post(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.post("/incidents/1001", {"incident_name": "Mock Incident"})

    assert r.get("incident_id") == 1001

def test_post_with_absolute_uri(fx_base_client):
    # test again with URI absolute
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.post("/orgs/201/incidents/1001", {"incident_name": "Mock Incident"}, is_uri_absolute=True)

    assert r.get("incident_id") == 1001


def test_post_retry(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, 1001)
    requests_adapter.register_uri('POST', mock_uri, status_code=300)

    with pytest.raises(RetryHTTPException, match=r"Response Code: 300"):
        base_client.post("/incidents/1001", {"incident_name": "Mock Incident"})

    assert "retrying in 1 seconds" in caplog.text

    # test skip which isn't part of the list
    with pytest.raises(RetryHTTPException, match=r"Response Code: 300"):
        base_client.post("/incidents/1001", {"incident_name": "Mock Incident"}, skip_retry=404)

def test_post_retry_skip(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, 1001)
    requests_adapter.register_uri('POST', mock_uri, status_code=404)

    with pytest.raises(BasicHTTPException, match=r"Response Code: 404"):
        base_client.post("/incidents/1001", {"incident_name": "Mock Incident"}, skip_retry=[404, 410])

    # single value
    with pytest.raises(BasicHTTPException, match=r"Response Code: 404"):
        base_client.post("/incidents/1001", {"incident_name": "Mock Incident"}, skip_retry=404)

def test_post_with_file(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    export_id = 1234

    mock_uri = '{0}/rest/orgs/{1}/playbooks/exports/{2}'.format(base_client.base_url, base_client.org_id, export_id)
    requests_adapter.register_uri('POST', mock_uri, status_code=200, content=b"12345")
    r = base_client.post(
        "/orgs/201/playbooks/exports/1234",
        is_uri_absolute=True,
        get_response_object=True,
        files={'file_name': (None, "playbook_export.resz")}
    )

    assert isinstance(r, requests.Response)
    assert "file_name" in requests_adapter.request_history[-1].text
    assert "playbook_export.resz" in requests_adapter.request_history[-1].text

def test_client_has_base_headers(fx_base_client):
    base_client = fx_base_client[0]
    headers = base_client.headers

    assert headers.get("content-type") == "application/json"
    assert headers.get(constants.HEADER_MODULE_VER_KEY) == constants.HEADER_MODULE_VER_VALUE


def test_client_with_client_certs_can_get(fx_base_client):
    incident_id = 100
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    mock_cert = ("mock_cert_file_path.pem", "mock_cert_file_key_path.pem")

    base_client.cert = mock_cert

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}

    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))

    uri = '/incidents/{0}'.format(incident_id)

    # make a GET call to the uri
    resp = base_client.get(
        uri=uri,
        co3_context_token=None,
        timeout=None,
        is_uri_absolute=False,
        get_response_object=False
    )

    assert requests_adapter.last_request.cert == mock_cert
    assert resp['incident_id'] == incident_id


def test_make_headers_supports_additional_header(fx_base_client):
    base_client = fx_base_client[0]
    additional_headers = {"Mock-Key": "Mock-Value"}
    headers = base_client.make_headers(additional_headers=additional_headers)

    assert headers.get("content-type") == "application/json"
    assert headers.get(constants.HEADER_MODULE_VER_KEY) == constants.HEADER_MODULE_VER_VALUE
    assert headers.get("Mock-Key") == "Mock-Value"


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

    if sys.version_info.major == 2:
        with open(temp_file_path, mode="w") as temp_file:
            temp_file.write("This is a mock file")

    else:
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


def test_put_with_headers(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_headers = {"content-type": "application/octet-stream"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('PUT',
                                  mock_uri,
                                  status_code=200,
                                  request_headers=test_headers,
                                  text=json.dumps(test_headers))

    uri = "/playbooks/imports"

    r = base_client.put(
        uri,
        "payload",
        headers=test_headers
    )

    assert r['content-type'] == test_headers['content-type']


def test_put_with_text_payload(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_content = 'abc'

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('PUT',
                                  mock_uri,
                                  status_code=200,
                                  text=json.dumps({ "content": test_content}))

    uri = "/playbooks/imports"

    r = base_client.put(
        uri,
        test_content        
    )

    assert r['content'] == test_content


def test_put_with_json_payload(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_content = {"something": "else"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)

    requests_adapter.register_uri('PUT',
                                  mock_uri,
                                  status_code=200,
                                  text=json.dumps({"content": test_content}))

    uri = "/playbooks/imports"

    r = base_client.put(
        uri,
        test_content
    )

    assert r['content'] == test_content

#----
def test_post_with_headers(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_headers = {"content-type": "application/octet-stream"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('POST',
                                  mock_uri,
                                  status_code=200,
                                  request_headers=test_headers,
                                  text=json.dumps(test_headers))

    uri = "/playbooks/imports"

    r = base_client.post(
        uri,
        "payload",
        headers=test_headers
    )

    assert r['content-type'] == test_headers['content-type']


def test_post_with_text_payload(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_content = 'abc'

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('POST',
                                  mock_uri,
                                  status_code=200,
                                  text=json.dumps({"content": test_content}))

    uri = "/playbooks/imports"

    r = base_client.post(
        uri,
        test_content        
    )

    assert r['content'] == test_content


def test_post_with_json_payload(fx_base_client):

    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    test_content = {"something": "else"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)

    requests_adapter.register_uri('POST',
                                  mock_uri,
                                  status_code=200,
                                  text=json.dumps({ "content": test_content}))

    uri = "/playbooks/imports"

    r = base_client.post(
        uri,
        test_content        
    )

    assert r['content'] == test_content

    
def test_post_attachment_bytes_handle_retry(fx_base_client, caplog):

    incident_id = 1001
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}/attachments'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('POST', mock_uri, status_code=300)

    uri = "/incidents/{0}/attachments".format(incident_id)
    temp_file_name = "mock_attachment.txt"
    bytes_handle = io.BytesIO(b"these are mock bytes")

    with pytest.raises(RetryHTTPException, match=r"Response Code: 300"):
        base_client.post_attachment(
            uri=uri,
            filepath=None,
            filename=temp_file_name,
            bytes_handle=bytes_handle
        )

    assert "retrying in 1 seconds" in caplog.text


def test_delete(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('DELETE', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.delete("/incidents/1001")

    assert r.get("incident_id") == 1001


def test_delete_204(fx_base_client):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('DELETE', mock_uri, status_code=204)
    r = base_client.delete("/incidents/1001")

    assert r is None


def test_delete_retry(fx_base_client, caplog):
    base_client = fx_base_client[0]
    requests_adapter = fx_base_client[1]

    base_client.request_max_retries = 2
    base_client.request_retry_backoff = 1
    base_client.request_retry_delay = 1

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, 1001)
    requests_adapter.register_uri('DELETE', mock_uri, status_code=300)

    with pytest.raises(RetryHTTPException, match=r"Response Code: 300"):
        base_client.delete("/incidents/1001")

    assert "retrying in 1 seconds" in caplog.text
