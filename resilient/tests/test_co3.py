#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import json

import pytest
from mock import patch

import resilient
from resilient.co3 import SimpleHTTPException


@patch("resilient.co3base.BaseClient.set_api_key")
@patch("resilient.co3base.BaseClient.get")
def test_get_client(mock_get_call, mock_session):

    mock_cert = ("mock_cert_file_path.pem", "mock_cert_file_key_path.pem")
    mock_opts = {
        "org": "Test Organization",
        "host": "example.com",
        "port": 8080,
        "api_key_id": "1234-efgh",
        "api_key_secret": "abcd-56789",
        "cafile": "FALSE",
        "client_auth_cert": mock_cert[0],
        "client_auth_key": mock_cert[1]
    }
    mock_session_info = {
        "orgs": [{"name": "Test Organization", "id": 201}]
    }
    mock_get_org_data = {
        "actions_framework_enabled": False
    }
    mock_session.return_value = mock_session_info
    mock_get_call.return_value = mock_get_org_data

    res_client = resilient.get_client(mock_opts)

    assert res_client.base_url == "https://example.com:8080"
    assert res_client.cert == mock_cert
    assert res_client.actions_enabled == False

def test_client_put(fx_simple_client):

    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

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

def test_client_put_with_error(fx_simple_client):

    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    test_headers = {"content-type": "application/octet-stream"}

    mock_uri = '{0}/rest/orgs/{1}/playbooks/imports'.format(base_client.base_url, base_client.org_id)    

    requests_adapter.register_uri('PUT',
                                  mock_uri,
                                  status_code=403)

    uri = "/playbooks/imports"

    with pytest.raises(SimpleHTTPException):
        base_client.put(
            uri,
            "payload",
            headers=test_headers
        )

def test_client_post(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('POST', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.post("/incidents/{}".format(incident_id), {"incident_name": "Mock Incident"})

    assert r.get("incident_id") == incident_id

def test_client_delete(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"success": True,"title": "title","message": "done","hints": [],"error_code": "","error_payload": { }}
    requests_adapter.register_uri('DELETE', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.delete("/incidents/{}".format(incident_id))

    assert r.get("success") == True

def test_client_delete_with_204(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('DELETE', mock_uri, status_code=204)
    r = base_client.delete("/incidents/{}".format(incident_id))

    assert r == None

def test_client_delete_with_error(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('DELETE', mock_uri, status_code=404)

    with pytest.raises(SimpleHTTPException):
        base_client.delete("/incidents/{}".format(incident_id), skip_retry=[404])

def test_simple_client_get_cached(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    mock_response = {"incident_id": incident_id}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))

    # make one call
    r = base_client.cached_get("/incidents/{}".format(incident_id))
    assert r.get("incident_id") == incident_id

    # make five more calls but now check the adapter to ensure only called once
    for _ in range(5):
        base_client.cached_get("/incidents/{}".format(incident_id))
    assert requests_adapter.call_count == 1

def test_simple_client_get_content(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('GET', mock_uri, status_code=200, content=json.dumps({"content": "content"}).encode("ascii"))

    r = base_client.cached_get("/incidents/{}".format(incident_id))
    assert r == {"content": "content"}

def test_simple_client_get_content_with_error(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]
    incident_id = 1001

    mock_uri = '{0}/rest/orgs/{1}/incidents/{2}'.format(base_client.base_url, base_client.org_id, incident_id)
    requests_adapter.register_uri('GET', mock_uri, status_code=404)

    with pytest.raises(SimpleHTTPException):
        base_client.cached_get("/incidents/{}".format(incident_id), skip_retry=[404])

def test_simple_client_get_const_old_style_version(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    mock_uri = '{0}/rest/const'.format(base_client.base_url)
    mock_response = {"server_version": {"major": 47, "minor": 0, "build_number": 8304, "version": "47.0.8304"}}
    requests_adapter.register_uri('GET', mock_uri, status_code=200, text=json.dumps(mock_response))
    r = base_client.get_const()

    assert r.get("server_version", {}).get("major") == 47
    assert r.get("server_version", {}).get("minor") == 0
    assert r.get("server_version", {}).get("build_number") == 8304
    assert r.get("server_version", {}).get("version") == "47.0.8304"

def test_get_const_new_style_version(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

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

def test_simple_client_raises_error_with_normal_retry(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    old_backoff, old_delay = base_client.request_retry_backoff, base_client.request_retry_delay
    base_client.request_retry_backoff, base_client.request_retry_delay = 0, 0

    mock_uri = '{0}/rest/orgs/{1}/test'.format(base_client.base_url, base_client.org_id)
    requests_adapter.register_uri('GET', mock_uri, status_code=404, reason="An error occurred")

    # make sure that SimpleHTTPException is still the exception raised, despite
    # the fact that a retry exception would be raised in this case
    with pytest.raises(SimpleHTTPException):
        base_client.get("/test")

    # retries should happen so we should see this equality
    assert requests_adapter.call_count == base_client.request_max_retries

    # cleanup
    base_client.request_retry_backoff, base_client.request_retry_delay = old_backoff, old_delay

def test_simple_client_raises_error_with_skip_retry(fx_simple_client):
    base_client = fx_simple_client[0]
    requests_adapter = fx_simple_client[1]

    mock_uri = '{0}/rest/orgs/{1}/test'.format(base_client.base_url, base_client.org_id)
    requests_adapter.register_uri('GET', mock_uri, status_code=404, reason="An error occurred")

    # when skip_retry is met, a BasicHTTPException is raised in co3base, but a
    # SimpleHTTPException is still raised from SimpleClient
    with pytest.raises(SimpleHTTPException):
        base_client.get("/test", skip_retry=[404])

    # key is that this is only 1 call, no retries were made since skip_retry was set
    assert requests_adapter.call_count == 1
